#!/usr/bin/env python3
"""Run a chosen draft image through a low-denoise refine/upscale pass.

Example:
    python refine.py --image ./drafts/20260818_bounty_hunter_seed123_2.png \
        --prompt "a weathered Deadlands bounty hunter, dusty coat, cinematic lighting" \
        --denoise 0.4
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from PIL import Image

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from workflow_utils import (
    MODEL_PRESETS,
    default_out_dir,
    find_node_by_title,
    load_workflow,
    random_seed,
    set_text,
    slugify,
)

HERE = Path(__file__).resolve().parent


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", required=True, help="Path to the draft image to refine (e.g. from ./drafts).")
    p.add_argument("--prompt", required=True, help="Positive prompt (usually the same one used to draft it).")
    p.add_argument("--negative", default="", help="Negative prompt; effective because refine runs the base model at cfg > 1.")
    p.add_argument("--denoise", type=float, default=0.4, help="0.3-0.5 keeps composition, adds detail.")
    p.add_argument("--upscale-by", type=float, default=1.5, help="Latent upscale factor.")
    p.add_argument(
        "--model",
        choices=sorted(MODEL_PRESETS),
        default="base",
        help="base (default) does real CFG, so negative prompts and detail recovery work. "
        "distilled is faster but ignores the negative prompt.",
    )
    p.add_argument("--steps", type=int, default=None, help="Override the preset step count.")
    p.add_argument("--cfg", type=float, default=None, help="Override the preset CFG scale. At 1.0 the negative prompt is ignored.")
    p.add_argument("--sampler", default="euler")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--workflow", default=str(HERE / "workflows" / "refine_upscale_api.json"))
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

    preset = MODEL_PRESETS[args.model]
    steps = args.steps if args.steps is not None else preset["steps"]
    cfg = args.cfg if args.cfg is not None else preset["cfg"]

    if args.negative and cfg == 1.0:
        print(
            f"WARNING: --negative is ignored at cfg 1.0 (model '{args.model}'). "
            f"Use --model base for negative prompts.",
            file=sys.stderr,
        )

    workflow = load_workflow(Path(args.workflow))
    workflow[find_node_by_title(workflow, "unet_loader")]["inputs"]["unet_name"] = preset["unet"]
    client = ComfyClient(host=args.host, port=args.port)

    print(f"Checking ComfyUI at {client.base_url} ...")
    try:
        client.system_stats()
    except Exception as e:
        print(f"ERROR: could not reach ComfyUI server: {e}", file=sys.stderr)
        print("Is `python main.py` running in your ComfyUI venv?", file=sys.stderr)
        return 1

    print(f"Uploading {source_path.name} to ComfyUI input/ ...")
    try:
        uploaded_name = client.upload_image(source_path)
    except ComfyClientError as e:
        print(f"ERROR: upload failed: {e}", file=sys.stderr)
        return 1

    load_node = find_node_by_title(workflow, "load_source_image")
    workflow[load_node]["inputs"]["image"] = uploaded_name

    set_text(workflow, "positive_prompt", args.prompt)
    set_text(workflow, "negative_prompt", args.negative)

    upscale_node = find_node_by_title(workflow, "latent_upscale")
    workflow[upscale_node]["inputs"]["scale_by"] = args.upscale_by

    # The Flux2 scheduler picks its sigma shift from the resolution, so it has to be
    # told the *post-upscale* size, not the source size.
    with Image.open(source_path) as im:
        src_w, src_h = im.size
    target_w = int(src_w * args.upscale_by)
    target_h = int(src_h * args.upscale_by)
    print(f"Source {src_w}x{src_h} -> refine target {target_w}x{target_h}")

    scheduler_node = find_node_by_title(workflow, "scheduler")
    workflow[scheduler_node]["inputs"].update(steps=steps, width=target_w, height=target_h)

    # Partial denoise is done by taking the tail of the sigma schedule, since
    # SamplerCustomAdvanced has no denoise input of its own.
    workflow[find_node_by_title(workflow, "denoise_split")]["inputs"]["denoise"] = args.denoise

    workflow[find_node_by_title(workflow, "sampler_select")]["inputs"]["sampler_name"] = args.sampler
    workflow[find_node_by_title(workflow, "guider")]["inputs"]["cfg"] = cfg

    seed = args.seed if args.seed is not None else random_seed()
    workflow[find_node_by_title(workflow, "noise_seed")]["inputs"]["noise_seed"] = seed

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(args.prompt)
    prefix = f"{timestamp}_{slug}_refine_seed{seed}"

    save_node = find_node_by_title(workflow, "save_final")
    workflow[save_node]["inputs"]["filename_prefix"] = prefix

    print(
        f"Queuing refine pass ({args.model}, {steps} steps, cfg {cfg}, "
        f"denoise={args.denoise}, upscale_by={args.upscale_by}, seed={seed}) ..."
    )
    try:
        history_entry = client.run(workflow)
    except ComfyExecutionError as e:
        print(f"ERROR: ComfyUI execution failed: {e}", file=sys.stderr)
        print(
            "If this is a CUDA out-of-memory error, the upscale target is likely too "
            "large for available VRAM -- lower --upscale-by and retry.",
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
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
