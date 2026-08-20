#!/usr/bin/env python3
"""Generate the Dino Weird West portrait set.

Batch size depends on the subject: 4 for people, 12 for creatures. People are
shot seated waist-up with hands on knees and came back with zero anatomical
artefacts across 59 subjects; creatures are full-body and roughly half came back
with an extra, fused or detached limb, so they need far more to cull from.
See subjects.BATCH_BY_KIND.

Resumable -- a subject whose draft folder already holds its full batch is
skipped, so an interrupted run picks up where it stopped.

    python build_set.py                  # everything still outstanding
    python build_set.py --only josiah_coyle wren_halloway
    python build_set.py --dry-run        # print prompts, generate nothing

Drafts land in <root>/dww_drafts/<slug>/. Picking a winner and producing the
final portrait + token is finish_set.py's job, not this script's.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from subjects import SUBJECTS, DEFAULT_FRAMING, batch_size, resolve
from workflow_utils import MODEL_PRESETS, find_node_by_title, load_workflow, random_seed, set_text

HERE = Path(__file__).resolve().parent

# The shared plate treatment. Every subject gets this verbatim so the whole set
# reads as one photographer's work despite the varied backgrounds.
STYLE = (
    "1870s wet-plate collodion tintype, hard raking daylight, heavy coarse film grain, "
    "dense silver halide texture, pronounced collodion process artifacts, unevenly "
    "hand-poured emulsion, chemical swirls streaks and tide marks across the plate, "
    "dust specks, hairline scratches, silver flaking and pitting, blown highlights and "
    "crushed muddy blacks, low contrast, cold grey and dirty sepia tones, edges falling "
    "soft and out of focus, battered antique photograph, photorealistic"
)

WIDTH = HEIGHT = 1024


def build_prompt(subject: dict) -> str:
    framing = subject.get("framing", DEFAULT_FRAMING)
    return f"{resolve(subject)}, {framing}, {subject['bg']}, {STYLE}"


def draft_dir(root: Path, slug: str) -> Path:
    return root / "dww_drafts" / slug


def is_done(root: Path, slug: str, batch: int) -> bool:
    d = draft_dir(root, slug)
    return d.is_dir() and len(list(d.glob("*.png"))) >= batch


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=r"D:\Creative\AI\outputs")
    p.add_argument("--only", nargs="*", help="Limit to these slugs.")
    p.add_argument("--below", type=int, metavar="N",
                   help="Limit to subjects scored below N in scores.json, and force "
                        "their regeneration. Closes the quality loop: score, then "
                        "`--below 4` re-rolls everything judged compromised.")
    p.add_argument("--scores", default="scores.json")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="Regenerate even if drafts exist.")
    p.add_argument("--model", choices=sorted(MODEL_PRESETS), default="distilled")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8188)
    args = p.parse_args()

    root = Path(args.root)
    subjects = SUBJECTS
    if args.only:
        wanted = set(args.only)
        subjects = [s for s in subjects if s["slug"] in wanted]
        missing = wanted - {s["slug"] for s in subjects}
        if missing:
            print(f"ERROR: unknown slug(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    if args.below is not None:
        scores_path = Path(args.scores)
        if not scores_path.is_absolute():
            scores_path = HERE / scores_path
        if not scores_path.exists():
            print(f"ERROR: no scores file at {scores_path}", file=sys.stderr)
            return 1
        scores = json.loads(scores_path.read_text())["scores"]
        low = {slug for slug, v in scores.items() if v < args.below}
        subjects = [s for s in subjects if s["slug"] in low]
        args.force = True  # a rescored subject always needs a fresh roll
        print(f"{len(subjects)} subject(s) scored below {args.below}")

    if args.dry_run:
        for s in subjects:
            print(f"--- {s['slug']} ({s['faction']})\n{build_prompt(s)}\n")
        return 0

    preset = MODEL_PRESETS[args.model]
    client = ComfyClient(host=args.host, port=args.port)
    try:
        client.system_stats()
    except Exception as e:
        print(f"ERROR: could not reach ComfyUI: {e}", file=sys.stderr)
        print("Is `python main.py` running in the ComfyUI venv?", file=sys.stderr)
        return 1

    manifest_path = root / "dww_drafts" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    todo = [s for s in subjects if args.force or not is_done(root, s["slug"], batch_size(s))]
    print(f"{len(todo)} of {len(subjects)} subjects to generate "
          f"({len(subjects) - len(todo)} already have drafts)")

    failures = []
    started = time.time()
    for i, subject in enumerate(todo, 1):
        slug = subject["slug"]
        out = draft_dir(root, slug)
        out.mkdir(parents=True, exist_ok=True)
        prompt = build_prompt(subject)
        seed = random_seed()
        batch = batch_size(subject)

        wf = load_workflow(HERE / "workflows" / "batch_generate_api.json")
        set_text(wf, "positive_prompt", prompt)
        set_text(wf, "negative_prompt", "")
        wf[find_node_by_title(wf, "unet_loader")]["inputs"]["unet_name"] = preset["unet"]
        latent = find_node_by_title(wf, "empty_latent")
        wf[latent]["inputs"].update(width=WIDTH, height=HEIGHT, batch_size=batch)
        wf[find_node_by_title(wf, "scheduler")]["inputs"].update(
            steps=preset["steps"], width=WIDTH, height=HEIGHT)
        wf[find_node_by_title(wf, "guider")]["inputs"]["cfg"] = preset["cfg"]
        wf[find_node_by_title(wf, "noise_seed")]["inputs"]["noise_seed"] = seed
        wf[find_node_by_title(wf, "save_batch")]["inputs"]["filename_prefix"] = slug

        elapsed = time.time() - started
        print(f"[{i}/{len(todo)}] {slug} x{batch} (seed {seed}) ... ", end="", flush=True)
        try:
            history = client.run(wf)
            saved = client.download_outputs(history, out, slug)
        except (ComfyExecutionError, ComfyClientError) as e:
            print(f"FAILED: {e}")
            failures.append((slug, str(e)))
            continue
        print(f"{len(saved)} images  [{elapsed/60:.1f} min elapsed]")

        manifest[slug] = dict(
            name=subject["name"], faction=subject["faction"], seed=seed,
            prompt=prompt, files=[f.name for f in saved],
        )
        manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone in {(time.time()-started)/60:.1f} min. Manifest: {manifest_path}")
    if failures:
        print(f"\n{len(failures)} FAILED -- rerun to retry (finished subjects are skipped):", file=sys.stderr)
        for slug, err in failures:
            print(f"  {slug}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
