#!/usr/bin/env python3
"""Turn picked drafts into final portraits and battlemap tokens.

    python finish_set.py --picks picks.json

`picks.json` maps slug -> draft index (0-3):  {"josiah_coyle": 2, ...}

Portrait: grain at 0.12, then mounted on a paper card with the name letterpressed
underneath in Playfair Display. The photograph itself stays clean, which matters
because the token is cropped out of it.

Token: square crop centred on the detected face (falling back to a centre crop
for dinosaurs, which no face detector will find), 4x ESRGAN upscale, circular
mask with a faction ring. Deliberately NO grain -- at 96px grain reads as dirt.

Outputs land flat in one folder as <slug>.png and <slug>_token.png, so the set
is straightforward to put under version control.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from filmgrain import add_grain
from workflow_utils import find_node_by_title, load_workflow

HERE = Path(__file__).resolve().parent
FONT = Path(r"D:\Creative\AI\fonts\PlayfairDisplay-Variable.ttf")

# Ring colours are separated by LIGHTNESS as well as hue, so red/green stay
# distinguishable for colour-blind players and on both light and dark maps.
FACTION_RING = {
    "bandit":  (126, 36, 28),    # dark oxblood
    "village": (85, 128, 63),    # mid bottle green
    "neutral": (173, 169, 157),  # light bone grey
}
RING_DARK = (28, 26, 22)         # thin outer stroke, so the ring reads on any ground

PORTRAIT_PX = 1000
MOUNT_BORDER = 22
MOUNT_STRIP = 104
MOUNT_PAPER = (222, 217, 205)
MOUNT_INK = (58, 52, 44)
TOKEN_PX = 512
SS = 4                            # supersample factor for smooth mask and ring edges

_cascade = cv2.CascadeClassifier(
    str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))


def face_box(img: Image.Image):
    """Largest frontal face as (x, y, w, h), or None."""
    grey = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    faces = _cascade.detectMultiScale(grey, scaleFactor=1.08, minNeighbors=6, minSize=(70, 70))
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])


def token_crop(img: Image.Image) -> Image.Image:
    """Square crop for the token: head-and-shoulders if a face is found, else centred."""
    w, h = img.size
    face = face_box(img)
    if face is not None:
        fx, fy, fw, fh = face
        side = min(w, h, int(fh * 3.0))
        cx = fx + fw / 2
        cy = fy + fh / 2 + fh * 0.35          # drop a little to include shoulders
    else:
        side = int(min(w, h) * 0.92)          # dinosaurs: keep the whole animal
        cx, cy = w / 2, h / 2
    left = int(min(max(0, cx - side / 2), w - side))
    top = int(min(max(0, cy - side / 2), h - side))
    return img.crop((left, top, left + side, top + side))


def make_portrait(src: Image.Image, name: str) -> Image.Image:
    plate = add_grain(src, strength=0.12).resize((PORTRAIT_PX, PORTRAIT_PX), Image.LANCZOS)
    card = Image.new("RGB",
                     (PORTRAIT_PX + MOUNT_BORDER * 2,
                      PORTRAIT_PX + MOUNT_BORDER * 2 + MOUNT_STRIP), MOUNT_PAPER)
    card.paste(plate, (MOUNT_BORDER, MOUNT_BORDER))
    d = ImageDraw.Draw(card)
    d.rectangle((MOUNT_BORDER, MOUNT_BORDER,
                 MOUNT_BORDER + PORTRAIT_PX - 1, MOUNT_BORDER + PORTRAIT_PX - 1),
                outline=(150, 145, 135))

    size, tracking = 52, 6
    label = name.upper()
    fnt = ImageFont.truetype(str(FONT), size)
    while True:
        width = sum(d.textlength(c, font=fnt) + tracking for c in label) - tracking
        if width <= PORTRAIT_PX - 80 or size <= 24:
            break
        size -= 2
        fnt = ImageFont.truetype(str(FONT), size)
    x = (card.width - width) / 2
    y = MOUNT_BORDER * 2 + PORTRAIT_PX + (MOUNT_STRIP - size) / 2 - size * 0.22
    for c in label:
        d.text((x, y), c, font=fnt, fill=MOUNT_INK)
        x += d.textlength(c, font=fnt) + tracking
    return card


def make_token(art: Image.Image, faction: str) -> Image.Image:
    S = TOKEN_PX * SS
    art = art.convert("RGB").resize((S, S), Image.LANCZOS)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(art, (0, 0), mask)

    d = ImageDraw.Draw(out)
    ring = max(2, int(S * 0.038))
    thin = max(1, ring // 5)
    d.ellipse((ring // 2, ring // 2, S - 1 - ring // 2, S - 1 - ring // 2),
              outline=FACTION_RING[faction] + (255,), width=ring)
    d.ellipse((thin // 2, thin // 2, S - 1 - thin // 2, S - 1 - thin // 2),
              outline=RING_DARK + (255,), width=thin)
    inner = ring
    d.ellipse((inner, inner, S - 1 - inner, S - 1 - inner),
              outline=RING_DARK + (140,), width=thin)
    return out.resize((TOKEN_PX, TOKEN_PX), Image.LANCZOS)


def esrgan(client: ComfyClient, path: Path, dest: Path, model="RealESRGAN_x4.pth") -> Image.Image:
    """Native 4x ESRGAN pass. Structure-preserving, so the face cannot drift."""
    wf = load_workflow(HERE / "workflows" / "upscale_api.json")
    name = client.upload_image(path)
    wf[find_node_by_title(wf, "load_source_image")]["inputs"]["image"] = name
    wf[find_node_by_title(wf, "upscale_model_loader")]["inputs"]["model_name"] = model
    wf[find_node_by_title(wf, "final_scale")]["inputs"]["scale_by"] = 1.0  # 4x model, no resample
    prefix = f"up_{path.stem}"
    wf[find_node_by_title(wf, "save_upscaled")]["inputs"]["filename_prefix"] = prefix
    history = client.run(wf)
    saved = client.download_outputs(history, dest, prefix)
    if not saved:
        raise ComfyClientError("upscale produced no output image")
    return Image.open(saved[0]).convert("RGB")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--picks", default="picks.json")
    p.add_argument("--root", default=r"D:\Creative\AI\outputs")
    p.add_argument("--out", default=r"D:\Creative\AI\outputs\dino_weird_west")
    p.add_argument("--only", nargs="*")
    p.add_argument("--no-upscale", action="store_true",
                   help="Skip the ESRGAN pass (faster, softer tokens).")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8188)
    args = p.parse_args()

    root = Path(args.root)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    tmp = root / "dww_drafts" / "_tmp"; tmp.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((root / "dww_drafts" / "manifest.json").read_text())
    picks = json.loads(Path(args.picks).read_text())
    if args.only:
        picks = {k: v for k, v in picks.items() if k in set(args.only)}

    client = None if args.no_upscale else ComfyClient(host=args.host, port=args.port)
    no_face = []
    for i, (slug, idx) in enumerate(sorted(picks.items()), 1):
        entry = manifest.get(slug)
        if entry is None:
            print(f"  ! {slug}: not in manifest, skipping", file=sys.stderr); continue
        src_path = root / "dww_drafts" / slug / entry["files"][idx]
        src = Image.open(src_path).convert("RGB")

        make_portrait(src, entry["name"]).save(out / f"{slug}.png")

        crop = token_crop(src)
        if face_box(src) is None:
            no_face.append(slug)
        if client is not None:
            cp = tmp / f"{slug}_crop.png"; crop.save(cp)
            try:
                crop = esrgan(client, cp, tmp)
            except (ComfyExecutionError, ComfyClientError) as e:
                print(f"  ! {slug}: upscale failed ({e}), using raw crop", file=sys.stderr)
        make_token(crop, entry["faction"]).save(out / f"{slug}_token.png")
        print(f"[{i}/{len(picks)}] {slug}  ->  {slug}.png + {slug}_token.png")

    print(f"\nWrote {len(picks)*2} files to {out}")
    if no_face:
        print(f"\nNo face detected (centre-cropped) for {len(no_face)}: {', '.join(no_face)}")
        print("Expected for dinosaurs; check any humans in that list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
