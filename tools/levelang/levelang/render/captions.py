"""The story over the preview: chapter cards (``title``) and speech boxes (``say``)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

_SANS = ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"]
_BOLD = ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "Arial Bold.ttf"]
_fonts: dict = {}


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key not in _fonts:
        f = None
        for name in (_BOLD if bold else _SANS):
            try:
                f = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        _fonts[key] = f or ImageFont.load_default(size)
    return _fonts[key]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and draw.textlength(trial, font=fnt) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def fade(age: float, seconds: float, edge: float = 0.35) -> float:
    """0..1 opacity: fades in and out over `edge` seconds."""
    if age < 0 or age > seconds:
        return 0.0
    return max(0.0, min(1.0, age / edge, (seconds - age) / edge))


def draw_caption(img: Image.Image, cap: dict, age: float) -> None:
    a = fade(age, cap["seconds"])
    if a <= 0:
        return
    W, H = img.size
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    k = max(10, H // 22)
    if cap["kind"] == "title":
        big, small = font(int(k * 2.0), True), font(int(k * 1.0))
        band = int(k * (4.6 if cap.get("sub") else 3.2))
        y0 = (H - band) // 2
        d.rectangle([0, y0, W, y0 + band], fill=(10, 8, 24, int(170 * a)))
        d.text((W // 2, y0 + band // 2 - (k * 0.7 if cap.get("sub") else 0)), cap["text"], font=big, fill=(255, 244, 200, int(255 * a)), anchor="mm")
        if cap.get("sub"):
            d.text((W // 2, y0 + band // 2 + k * 1.2), cap["sub"], font=small, fill=(220, 210, 255, int(255 * a)), anchor="mm")
    else:
        fnt, who_f = font(k), font(k, True)
        pad = k * 0.7
        text_w = int(W * 0.78)
        lines = wrap(d, cap["text"], fnt, text_w)
        who = cap.get("who")
        bh = int(pad * 2 + len(lines) * k * 1.25 + (k * 1.3 if who else 0))
        bw = int(max(d.textlength(l, font=fnt) for l in lines) + pad * 2)
        if who:
            bw = max(bw, int(d.textlength(who, font=who_f) + pad * 2))
        x0, y0 = (W - bw) // 2, H - bh - int(k * 1.2)
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(k * 0.8), fill=(255, 252, 240, int(235 * a)), outline=(60, 40, 90, int(255 * a)), width=2)
        y = y0 + pad
        if who:
            d.text((x0 + pad, y), who, font=who_f, fill=(150, 60, 120, int(255 * a)))
            y += k * 1.3
        for l in lines:
            d.text((x0 + pad, y), l, font=fnt, fill=(40, 30, 60, int(255 * a)))
            y += k * 1.25
    img.alpha_composite(over)
