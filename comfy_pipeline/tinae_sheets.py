#!/usr/bin/env python3
"""Contact sheets for the This Is Not An Exorcism reference set.

    python tinae_sheets.py                 # one <slug>.jpg per subject, 3x2
    python tinae_sheets.py --section altar

Sheets land in <root>/refs/_sheets/. Drafts are numbered from zero in reading
order so a pick is just {"slug": index}.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE = 512
GAP = 10
BADGE = (250, 214, 60)


def sheet(files, title):
    cols = 3
    rows = (len(files) + cols - 1) // cols
    W = TILE * cols + GAP * (cols + 1)
    H = TILE * rows + GAP * (rows + 1) + 34
    im = Image.new("RGB", (W, H), (18, 18, 18))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
        big = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 30)
    except OSError:
        fnt = big = ImageFont.load_default()
    d.text((GAP, 8), title, fill=(240, 240, 235), font=fnt)
    for i, f in enumerate(files):
        x = GAP + (i % cols) * (TILE + GAP)
        y = 34 + GAP + (i // cols) * (TILE + GAP)
        im.paste(Image.open(f).convert("RGB").resize((TILE, TILE), Image.LANCZOS), (x, y))
        d.rectangle((x + 4, y + 4, x + 36, y + 42), fill=(18, 18, 18))
        d.text((x + 10, y + 6), str(i), fill=BADGE, font=big)
    return im


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=r"D:\Creative\AI\outputs\this_is_not_an_exorcism")
    p.add_argument("--section")
    p.add_argument("--only", nargs="*")
    a = p.parse_args()

    root = Path(a.root)
    refs = root / "refs"
    out = refs / "_sheets"
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((refs / "manifest.json").read_text())

    slugs = a.only or sorted(manifest)
    made = 0
    for slug in slugs:
        entry = manifest.get(slug)
        if not entry:
            continue
        if a.section and entry["section"] != a.section:
            continue
        files = [refs / slug / f for f in entry["files"]]
        files = [f for f in files if f.exists()]
        if not files:
            print(f"  ! {slug}: no drafts on disk")
            continue
        sheet(files, f'{slug}   [{entry["section"]} / {entry["kind"]}]').save(
            out / f'{entry["section"]}__{slug}.jpg', quality=88)
        made += 1
    print(f"{made} sheets -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
