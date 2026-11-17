"""Post effects for a cutscene frame: the grain, scanlines, colour splits, glitches and flashes of a late-90s music video (numpy + Pillow)."""
from __future__ import annotations

import numpy as np
from PIL import Image

NAMES = ("grain", "scan", "rgb", "glitch", "vhs", "invert", "posterize", "solarize", "mirror", "kaleido", "blur", "pixel", "tint", "flicker", "vignette", "stutter", "zoom")


def _rng(i: int, k: int = 0):
    return np.random.default_rng(i * 7919 + k * 104729 + 17)


def apply(img: Image.Image, effects: list, i: int) -> Image.Image:
    """`effects` is a list of (name, amount); `i` is the frame number (the noise changes every frame, never at random)."""
    if not effects:
        return img
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    h, w, _ = a.shape
    for n, (name, amt) in enumerate(effects):
        r = _rng(i, n)
        if name == "grain":
            a = a + r.normal(0, 28 * amt, (h, w, 1)).astype(np.int16)
        elif name == "scan":
            a = a.copy()
            a[1::2] = a[1::2] * (1 - 0.45 * min(1, amt))
        elif name == "rgb":
            d = max(1, int(round(w * 0.012 * amt)))
            d += int(r.integers(0, d + 1))
            b = a.copy()
            b[:, :, 0] = np.roll(a[:, :, 0], d, axis=1)
            b[:, :, 2] = np.roll(a[:, :, 2], -d, axis=1)
            a = b
        elif name == "glitch":
            a = a.copy()
            for _ in range(int(3 + 9 * amt)):
                y0 = int(r.integers(0, h))
                hh = int(r.integers(2, max(3, int(h * 0.12))))
                dx = int(r.integers(-int(w * 0.2 * amt) - 1, int(w * 0.2 * amt) + 2))
                a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], dx, axis=1)
            if amt > 0.6:                                           # and a block with the wrong colours
                y0, x0 = int(r.integers(0, h - 12)), int(r.integers(0, w - 24))
                blk = a[y0:y0 + int(r.integers(6, 30)), x0:x0 + int(r.integers(12, 90))]
                blk[:] = blk[:, :, ::-1]
        elif name == "vhs":
            ys = np.arange(h)
            shift = (np.sin(ys / 9.0 + i * 0.9) * 3.0 * amt + np.sin(ys / 31.0 - i * 0.3) * 4.0 * amt).astype(int)
            idx = (np.arange(w)[None, :] - shift[:, None]) % w
            a = a[ys[:, None], idx]
            y0 = int((i * 13) % h)                                  # the tracking bar rolls up the picture
            a = a.copy()
            a[y0:y0 + max(2, int(h * 0.05))] = (a[y0:y0 + max(2, int(h * 0.05))] * 0.5 + 90 * amt).astype(np.int16)
        elif name == "invert":
            a = 255 - a if amt >= 0.5 else (a * (1 - 2 * amt) + (255 - a) * 2 * amt).astype(np.int16)
        elif name == "posterize":
            lv = max(2, int(6 - 4 * min(1, amt)))
            q = 255 // (lv - 1)
            a = (a // max(1, 256 // lv)) * q
        elif name == "solarize":
            a = np.where(a > 128, 255 - a, a) * 2 if amt >= 0.5 else a
        elif name == "mirror":
            a = a.copy()
            a[:, w // 2:] = a[:, :w // 2][:, ::-1][:, : w - w // 2]
        elif name == "kaleido":
            q = a[: h // 2, : w // 2]
            top = np.concatenate([q, q[:, ::-1]], axis=1)[:, :w]
            a = np.concatenate([top, top[::-1]], axis=0)[:h]
        elif name == "blur":
            im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
            s = max(1.01, 1 + 0.12 * amt)
            z = im.resize((int(w * s), int(h * s)), Image.BILINEAR).crop((int(w * (s - 1) / 2), int(h * (s - 1) / 2), int(w * (s - 1) / 2) + w, int(h * (s - 1) / 2) + h))
            a = ((a + np.asarray(z, dtype=np.int16)) // 2)
        elif name == "zoom":
            im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
            s = 1 + 0.35 * amt
            a = np.asarray(im.resize((int(w * s), int(h * s)), Image.BILINEAR).crop((int(w * (s - 1) / 2), int(h * (s - 1) / 2), int(w * (s - 1) / 2) + w, int(h * (s - 1) / 2) + h)), dtype=np.int16)
        elif name == "pixel":
            k = max(2, int(4 + 14 * amt))
            im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
            a = np.asarray(im.resize((max(1, w // k), max(1, h // k)), Image.NEAREST).resize((w, h), Image.NEAREST), dtype=np.int16)
        elif name == "tint":
            col = np.array([255, 60, 172]) if (i // 3) % 2 else np.array([60, 220, 255])
            a = (a * (1 - 0.4 * amt) + col * 0.4 * amt).astype(np.int16)
        elif name == "flicker":
            a = a + int(40 * amt * (1 if i % 2 else -0.6))
        elif name == "vignette":
            yy, xx = np.mgrid[0:h, 0:w]
            d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
            a = (a * (1 - 0.55 * amt * np.clip(d - 0.55, 0, 1)[:, :, None])).astype(np.int16)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))
