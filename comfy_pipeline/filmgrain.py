#!/usr/bin/env python3
"""Add physically-plausible film grain to a rendered image.

Real silver-halide grain is strongest in the midtones and falls away in
blown highlights and blocked shadows, and it clumps rather than sitting
one grain per pixel. Prompted "film grain" gives neither.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image


def add_grain(img, strength=0.12, size=1.6, shadow_lift=0.02, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    h, w, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

    # Grain clumps: noise generated small, then scaled up, reads as clumps
    sh, sw = max(1, int(h / size)), max(1, int(w / size))
    noise = rng.normal(0.0, 1.0, (sh, sw)).astype(np.float32)
    noise = np.asarray(
        Image.fromarray(noise, mode="F").resize((w, h), Image.BICUBIC),
        dtype=np.float32,
    )
    # Soften a touch so grains read as clumps, not per-pixel salt. Pillow's
    # GaussianBlur refuses mode "F", so do it with a small separable kernel.
    k = np.array([0.25, 0.5, 0.25], dtype=np.float32)
    for axis in (0, 1):
        noise = sum(w_ * np.roll(noise, off, axis=axis)
                    for w_, off in zip(k, (-1, 0, 1)))

    # Midtone-weighted response: 4*L*(1-L) peaks at L=0.5, zero at both ends
    response = 4.0 * lum * (1.0 - lum)
    a += (noise * response * strength)[..., None]
    a += shadow_lift * (1.0 - lum)[..., None]   # veil the blacks, as an old plate does
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    p.add_argument("--strength", type=float, default=0.12)
    p.add_argument("--size", type=float, default=1.6)
    p.add_argument("--out-dir", default=".")
    a = p.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(a.images):
        src = Path(f)
        dst = out / f"{src.stem}_grain{src.suffix}"
        add_grain(Image.open(src), a.strength, a.size, seed=i).save(dst)
        print(dst)
