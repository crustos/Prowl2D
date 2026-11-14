"""Tile -> RGBA sprite. Order of preference: SVG, fill/pattern, emoji font, placeholder."""
from __future__ import annotations

import colorsys
import os
import sys
import zlib

from PIL import Image, ImageColor, ImageDraw, ImageFont

from ..emoji import VS16
from .svg import SvgUnavailable, rasterize

_EMOJI_FONTS = [  # (path, size the bitmap font must be opened at)
    ("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109),
    ("/usr/share/fonts/noto/NotoColorEmoji.ttf", 109),
    ("/usr/share/fonts/google-noto-color-emoji/NotoColorEmoji.ttf", 109),
    ("/System/Library/Fonts/Apple Color Emoji.ttc", 160),
    ("C:/Windows/Fonts/seguiemj.ttf", 109),
]
_MONO = ["DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "Menlo.ttc", "consola.ttf", "Courier New.ttf"]


def _emoji_font():
    for path, size in _EMOJI_FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size), size
            except Exception:
                pass
    return None, 0


def _mono(px: int):
    size = max(6, int(px * 0.85))
    for name in _MONO:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


def color(c, default=(255, 0, 255)):
    if c is None:
        return default
    try:
        return ImageColor.getrgb(c) if isinstance(c, str) else tuple(c)
    except ValueError:
        return default


class Sprites:
    def __init__(self, px: int) -> None:
        self.px = px
        self._cache: dict = {}
        self._efont, self._esize = _emoji_font()
        self._mono = None
        self._warned: set = set()

    def _warn(self, key: str, msg: str) -> None:
        if key not in self._warned:
            self._warned.add(key)
            print("levelang:", msg, file=sys.stderr)

    def get(self, tile, wx: int = 0, wy: int = 0, size=None) -> Image.Image:
        pat = tile.pattern
        key = (id(tile), wx % len(pat[0]) if pat and pat[0] else 0, wy % len(pat) if pat else 0, tuple(size) if size else None)
        img = self._cache.get(key)
        if img is None:
            img = self._cache[key] = self._build(tile, int(wx), int(wy), size)
        return img

    def _build(self, tile, wx, wy, size=None) -> Image.Image:
        px = self.px
        tw, th = size or tile.size
        w, h = max(1, int(tw * px)), max(1, int(th * px))
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        drawn = False
        if tile.fill is not None:
            ImageDraw.Draw(img).rectangle([0, 0, w - 1, h - 1], fill=color(tile.fill) + (255,))
            drawn = True
        if tile.pattern:
            self._pattern(img, tile, wx, wy)
            drawn = True
        if tile.svg:
            try:
                img.alpha_composite(rasterize(tile.svg, w, h))
                drawn = True
            except SvgUnavailable as e:
                self._warn("svg", str(e))
            except Exception as e:  # bad SVG: say so once, keep going
                self._warn("svg:" + tile.name, f"couldn't rasterize SVG for {tile.glyph or tile.name}: {e}")
        if not drawn:
            glyph_img = self._emoji(tile.glyph, w, h) if tile.glyph else None
            img.alpha_composite(glyph_img if glyph_img is not None else self._placeholder(tile, w, h))
        return img

    def _pattern(self, img, tile, wx, wy) -> None:
        pat = tile.pattern
        ph, pw = len(pat), max(len(r) for r in pat)
        ch = pat[wy % ph].ljust(pw)[wx % pw]
        if ch.strip():
            if self._mono is None:
                self._mono = _mono(self.px)
            ImageDraw.Draw(img).text((img.width / 2, img.height / 2), ch, font=self._mono, fill=color(tile.stroke, (255, 255, 255)) + (255,), anchor="mm")

    def _emoji(self, glyph: str, w: int, h: int):
        if self._efont is None:
            self._warn("emoji", "no colour emoji font found; undefined emoji draw as coloured placeholders (define tiles with `def 🧱 -> svg:` for exact looks)")
            return None
        try:
            s = self._esize
            canvas = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
            g = glyph if VS16 in glyph else glyph + VS16
            ImageDraw.Draw(canvas).text((s // 2, s // 4), g, font=self._efont, embedded_color=True)
            box = canvas.getbbox()
            if not box:
                return None
            return canvas.crop(box).resize((w, h), Image.LANCZOS)
        except Exception:
            return None

    def _placeholder(self, tile, w, h) -> Image.Image:
        hue = (zlib.crc32((tile.glyph or tile.name).encode()) % 360) / 360
        r, g, b = (int(255 * v) for v in colorsys.hsv_to_rgb(hue, 0.45, 0.85))
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        m = max(1, w // 10)
        d.rounded_rectangle([m, m, w - 1 - m, h - 1 - m], radius=max(1, w // 5), fill=(r, g, b, 255), outline=(r // 2, g // 2, b // 2, 255))
        return img


def default_bot_sprite(px: int) -> Image.Image:
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([px * 0.1, px * 0.1, px * 0.9, px * 0.9], fill=(255, 210, 40, 255), outline=(120, 80, 0, 255))
    d.ellipse([px * 0.55, px * 0.3, px * 0.78, px * 0.53], fill=(255, 255, 255, 255))
    d.ellipse([px * 0.65, px * 0.36, px * 0.75, px * 0.46], fill=(0, 0, 0, 255))
    return img
