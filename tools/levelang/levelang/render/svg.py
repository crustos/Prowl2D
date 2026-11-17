"""SVG -> PIL image. Uses cairosvg (``pip install cairosvg``)."""
from __future__ import annotations

import io
import re

from PIL import Image


class SvgUnavailable(RuntimeError):
    pass


def rasterize(svg: str, w: int, h: int) -> Image.Image:
    try:
        import cairosvg
    except Exception as e:  # ImportError, or OSError when libcairo is missing
        raise SvgUnavailable("SVG tiles need cairosvg:  pip install cairosvg") from e
    svg = svg.strip()
    m = re.search(r"<svg\b[^>]*>", svg)
    if m and "xmlns=" not in m.group(0):
        svg = re.sub(r"<svg\b", '<svg xmlns="http://www.w3.org/2000/svg"', svg, count=1)
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=w, output_height=h)
    return Image.open(io.BytesIO(png)).convert("RGBA")
