#!/usr/bin/env python3
"""Submit a batch text-to-image job to ComfyUI and download every variant.

Example:
    python generate.py --prompt "a weathered Deadlands bounty hunter, dusty coat, \
        cinematic lighting" --negative "blurry, extra fingers, watermark" --batch 4
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from workflow_utils import find_node_by_title, load_workflow, random_seed, set_text

HERE = Path(__file__).resolve().parent


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", required=True, help="Positive prompt text.")
    p.add_argument("--negative", default="", help="Negative prompt text.")
    p.add_argument("--batch", type=int, default=4, help="Number of variants to generate (default 4).")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--cfg", type=float, default=1.0, help="CFG scale for KSampler (FLUX typically wants 1.0; use --guidance for the real prompt-adherence knob).")
    p.add_argument("--guidance", type=float, default=3.5, help="FluxGuidance value.")
    p.add_argument("--sampler", default="euler")
    p.add_argument("--scheduler", default="simple")
    p.add_argument("--seed", type=int, default=None, help="Fixed seed; omit for a random one.")
    p.add_argument("--workflow", default=str(HERE / "workflows" / "batch_generate_api.json"))
    p.add_argument("--out-dir", default=str(HERE / "drafts"))
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8188)
    return p.parse_args()


def main() -> int:
    args = build_args()

    workflow = load_workflow(Path(args.workflow))

    set_text(workflow, "positive_prompt", args.prompt)
    set_text(workflow, "negative_prompt", args.negative)

    latent_node = find_node_by_title(workflow, "empty_latent")
    workflow[latent_node]["inputs"]["width"] = args.width
    workflow[latent_node]["inputs"]["height"] = args.height
    workflow[latent_node]["inputs"]["batch_size"] = args.batch

    sampler_node = find_node_by_title(workflow, "batch_sampler")
    seed = args.seed if args.seed is not None else random_seed()
    workflow[sampler_node]["inputs"].update(
        seed=seed, steps=args.steps, cfg=args.cfg, sampler_name=args.sampler, scheduler=args.scheduler
    )

    guidance_node = find_node_by_title(workflow, "flux_guidance")
    workflow[guidance_node]["inputs"]["guidance"] = args.guidance

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    from workflow_utils import slugify

    slug = slugify(args.prompt)
    prefix = f"{timestamp}_{slug}_seed{seed}"

    save_node = find_node_by_title(workflow, "save_batch")
    workflow[save_node]["inputs"]["filename_prefix"] = prefix

    client = ComfyClient(host=args.host, port=args.port)

    print(f"Checking ComfyUI at {client.base_url} ...")
    try:
        stats = client.system_stats()
    except Exception as e:  # connection refused, etc.
        print(f"ERROR: could not reach ComfyUI server: {e}", file=sys.stderr)
        print("Is `python main.py` running in your ComfyUI venv?", file=sys.stderr)
        return 1
    vram = stats.get("devices", [{}])[0].get("vram_free")
    if vram is not None:
        print(f"GPU VRAM free: {vram / (1024**3):.1f} GB")

    print(f"Queuing batch of {args.batch} (seed={seed}) ...")
    try:
        history_entry = client.run(workflow)
    except ComfyExecutionError as e:
        print(f"ERROR: ComfyUI execution failed: {e}", file=sys.stderr)
        print(
            "If this is a CUDA out-of-memory error, close other GPU workloads "
            "(llama.cpp, Blender) and retry, or reduce --width/--height/--batch.",
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
