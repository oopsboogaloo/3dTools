#!/usr/bin/env python3
"""Build grids of the FINISHED portraits for quality scoring.

Draft sheets (review_sheets.py) are for picking a winner out of a batch.
These are for judging the shipped article -- grain, mount and label included,
which is where framing or texture problems actually show up.

    python score_sheets.py --out <dir> [--per-sheet 4]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE = 512
GAP = 10
HEADER = 30


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--set-dir", default=r"D:\Creative\AI\outputs\dino_weird_west")
    p.add_argument("--root", default=r"D:\Creative\AI\outputs")
    p.add_argument("--out", required=True)
    p.add_argument("--per-sheet", type=int, default=4)
    a = p.parse_args()

    src = Path(a.set_dir)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((Path(a.root) / "dww_drafts" / "manifest.json").read_text())

    slugs = sorted(f.stem for f in src.glob("*.png") if not f.stem.endswith("_token"))
    try:
        fnt = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 20)
    except OSError:
        fnt = ImageFont.load_default()

    cols = 2
    rows = (a.per_sheet + cols - 1) // cols
    made = 0
    for i in range(0, len(slugs), a.per_sheet):
        chunk = slugs[i:i + a.per_sheet]
        sheet = Image.new("RGB",
                          (cols * TILE + GAP * (cols + 1),
                           rows * (TILE + HEADER) + GAP * (rows + 1)), (18, 18, 18))
        d = ImageDraw.Draw(sheet)
        for j, slug in enumerate(chunk):
            im = Image.open(src / f"{slug}.png").convert("RGB")
            im.thumbnail((TILE, TILE), Image.LANCZOS)
            x = GAP + (j % cols) * (TILE + GAP)
            y = GAP + (j // cols) * (TILE + HEADER + GAP)
            d.text((x, y + 4), f'{slug}  "{manifest[slug]["name"]}"', fill=(250, 214, 60), font=fnt)
            sheet.paste(im, (x + (TILE - im.width) // 2, y + HEADER))
        sheet.save(out / f"score_{i//a.per_sheet:02d}.jpg", quality=88)
        made += 1
    print(f"{made} sheets covering {len(slugs)} portraits -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
