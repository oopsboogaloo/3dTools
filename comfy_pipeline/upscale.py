#!/usr/bin/env python3
"""Upscale a finished image with an ESRGAN-family model -- no diffusion involved.

This is the step to use when you want more pixels rather than more detail.
`refine.py` re-runs the diffusion model at the target resolution, which means it
inherits Klein's coherence ceiling (~2304-2560px; past that the image dissolves).
An ESRGAN upscaler is purely convolutional: it has no resolution limit and cannot
reinvent the subject, so structure survives exactly as-is.

Typical full chain:
    generate.py (1024) -> refine.py x1.5 (1536) -> refine.py x1.5 (2304) -> upscale.py x4 (9216)

Example:
    python upscale.py --image ./final/pick.png --scale 4
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from PIL import Image

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from workflow_utils import default_out_dir, find_node_by_title, load_workflow, slugify

HERE = Path(__file__).resolve().parent

# The ESRGAN model is a fixed 4x. To land on any other factor we let it do its 4x
# and then resample by the remainder, which is still sharper than asking a
# general-purpose resize to do the whole job.
MODEL_NATIVE_SCALE = 4.0


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", required=True, help="Path to the image to upscale.")
    p.add_argument(
        "--scale",
        type=float,
        default=4.0,
        help="Total scale factor (default 4.0, the model's native factor). "
        "Other values run the 4x model then resample by the remainder.",
    )
    p.add_argument("--model", default="RealESRGAN_x4.pth", help="Upscale model filename in ComfyUI/models/upscale_models.")
    p.add_argument("--workflow", default=str(HERE / "workflows" / "upscale_api.json"))
    p.add_argument("--out-dir", default=default_out_dir("final"), help="Default: %(default)s")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8188)
    return p.parse_args()


def main() -> int:
    args = build_args()

    source_path = Path(args.image)
    if not source_path.exists():
        print(f"ERROR: source image not found: {source_path}", file=sys.stderr)
        return 1
    if args.scale <= 0:
        print("ERROR: --scale must be positive.", file=sys.stderr)
        return 1

    workflow = load_workflow(Path(args.workflow))
    client = ComfyClient(host=args.host, port=args.port)

    print(f"Checking ComfyUI at {client.base_url} ...")
    try:
        client.system_stats()
    except Exception as e:
        print(f"ERROR: could not reach ComfyUI server: {e}", file=sys.stderr)
        print("Is `python main.py` running in your ComfyUI venv?", file=sys.stderr)
        return 1

    with Image.open(source_path) as im:
        src_w, src_h = im.size
    target_w = int(src_w * args.scale)
    target_h = int(src_h * args.scale)
    print(f"Source {src_w}x{src_h} -> target {target_w}x{target_h} ({args.scale}x)")

    print(f"Uploading {source_path.name} to ComfyUI input/ ...")
    try:
        uploaded_name = client.upload_image(source_path)
    except ComfyClientError as e:
        print(f"ERROR: upload failed: {e}", file=sys.stderr)
        return 1

    workflow[find_node_by_title(workflow, "load_source_image")]["inputs"]["image"] = uploaded_name
    workflow[find_node_by_title(workflow, "upscale_model_loader")]["inputs"]["model_name"] = args.model
    workflow[find_node_by_title(workflow, "final_scale")]["inputs"]["scale_by"] = args.scale / MODEL_NATIVE_SCALE

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{timestamp}_{slugify(source_path.stem)}_up{args.scale:g}x"
    workflow[find_node_by_title(workflow, "save_upscaled")]["inputs"]["filename_prefix"] = prefix

    print(f"Queuing upscale with {args.model} ...")
    try:
        history_entry = client.run(workflow)
    except ComfyExecutionError as e:
        print(f"ERROR: ComfyUI execution failed: {e}", file=sys.stderr)
        print(
            "ESRGAN upscaling is tiled, so OOM is unusual -- but a very large "
            "target can still exhaust VRAM. Try a smaller --scale.",
            file=sys.stderr,
        )
        return 1
    except ComfyClientError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    saved = client.download_outputs(history_entry, out_dir, prefix)
    if not saved:
        print("WARNING: job finished but no images were found in the output history.", file=sys.stderr)
        return 1

    print(f"Saved {len(saved)} image(s) to {out_dir}/:")
    for path in saved:
        with Image.open(path) as im:
            print(f"  {path}  ({im.size[0]}x{im.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
