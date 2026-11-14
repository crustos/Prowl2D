"""Smooth outlines for blocky terrain: the cells a skin covers become a rounded, gently wavy silhouette.

The outline of a set of cells is walked as closed loops of grid corners, its corners are cut (Chaikin's algorithm: each round replaces every corner by two
points on its edges, so a staircase becomes a slope and a square corner a curve), and then each point is nudged along its normal by a smooth wave so a flat
floor is not a ruler line. The loops are the *curves*: ``skin_loops`` returns them in cell units for any exporter (an SVG path, a mesh); ``skin_mask`` fills
them to an alpha mask so the tiles' own pictures show through the smooth shape.

The level's edge counts as more of the same, so a rock wall that reaches the edge is not rounded off there.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw

PAD = 2  # cells of the level's edge repeated beyond it


def grid_loops(cells: set, cols: int, rows: int) -> list[list[tuple]]:
    """Closed loops of integer corners around the solid cells (0 <= x < cols, 0 <= y < rows; outside, the nearest edge cell is repeated)."""

    def solid(x, y):  # beyond the level the edge cells repeat for PAD cells, then there is nothing: the loops close out there, off the picture
        if not (-PAD <= x < cols + PAD and -PAD <= y < rows + PAD):
            return False
        return (min(max(x, 0), cols - 1), min(max(y, 0), rows - 1)) in cells

    out: dict = {}
    for y in range(-PAD, rows + PAD):
        for x in range(-PAD, cols + PAD):
            if not solid(x, y):
                continue
            if not solid(x, y - 1):
                out.setdefault((x, y), []).append((x + 1, y))
            if not solid(x + 1, y):
                out.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not solid(x, y + 1):
                out.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not solid(x - 1, y):
                out.setdefault((x, y + 1), []).append((x, y))
    loops = []
    for start in sorted(out):
        while out[start]:
            loop, cur = [start], out[start].pop()
            while cur != start:
                loop.append(cur)
                cur = out[cur].pop()
            loops.append(loop)
    return loops


def _cut(loop, corner: float, rounds: int):
    pts = [(float(x), float(y)) for x, y in loop]
    for _ in range(rounds):
        nxt = []
        for i, (ax, ay) in enumerate(pts):
            bx, by = pts[(i + 1) % len(pts)]
            nxt.append(((1 - corner) * ax + corner * bx, (1 - corner) * ay + corner * by))
            nxt.append((corner * ax + (1 - corner) * bx, corner * ay + (1 - corner) * by))
        pts = nxt
    return pts


def _wave(x: float, y: float, seed: int) -> float:
    """Smooth, repeatable, about -1..1; depends on the place only, so neighbouring loops agree."""
    a, b = seed * 1.7 + 0.9, seed * 2.3 + 0.4
    return (math.sin(1.7 * x + a) * math.cos(1.3 * y + b) + 0.5 * math.sin(3.1 * x - 2.0 * y + a * 2.0)) / 1.5


def skin_loops(cells: set, cols: int, rows: int, corner: float = 0.28, smooth: int = 3, wobble: float = 0.0, seed: int = 0) -> list[list[tuple]]:
    """The skin's outline as closed polylines in cell units (the loops of the cells, corners cut, waved)."""
    result = []
    for loop in grid_loops(cells, cols, rows):
        pts = _cut(loop, min(max(corner, 0.05), 0.5), max(0, int(smooth)))
        if wobble:
            n, moved = len(pts), []
            for i, (x, y) in enumerate(pts):
                px, py = pts[i - 1]
                qx, qy = pts[(i + 1) % n]
                tx, ty = qx - px, qy - py
                norm = math.hypot(tx, ty) or 1.0
                d = wobble * _wave(x, y, seed)
                moved.append((x + ty / norm * d, y - tx / norm * d))  # the loops run clockwise on screen: this is the way out of the solid
            pts = moved
        result.append(pts)
    return result


def skin_mask(loops, size: tuple, px: int, origin: tuple = (0, 0), supersample: int = 4) -> Image.Image:
    """Even-odd fill of the loops as an 'L' mask of ``size`` pixels (a loop inside another is a hole)."""
    s = px * supersample
    big = (size[0] * supersample, size[1] * supersample)
    acc = Image.new("1", big, 0)
    for pts in loops:
        m = Image.new("1", big, 0)
        ImageDraw.Draw(m).polygon([((x - origin[0]) * s, (y - origin[1]) * s) for x, y in pts], fill=1)
        acc = ImageChops.logical_xor(acc, m)
    return acc.convert("L").resize(size, Image.BOX)


def skin_outline(loops, size: tuple, px: int, width: float, origin: tuple = (0, 0), supersample: int = 4) -> Image.Image:
    """The outline as an 'L' mask, ``width`` cells thick."""
    s = px * supersample
    big = (size[0] * supersample, size[1] * supersample)
    m = Image.new("L", big, 0)
    d = ImageDraw.Draw(m)
    w = max(1, round(width * s))
    for pts in loops:
        xy = [((x - origin[0]) * s, (y - origin[1]) * s) for x, y in pts]
        d.line(xy + [xy[0]], fill=255, width=w, joint="curve")
    return m.resize(size, Image.BOX)


def path_data(loops, origin: tuple = (0, 0), scale: float = 1.0) -> str:
    """SVG path data for the loops (``M x y L ... Z`` for each), in ``scale`` units per cell."""
    parts = []
    for pts in loops:
        body = " L".join(f"{(x - origin[0]) * scale:.2f} {(y - origin[1]) * scale:.2f}" for x, y in pts)
        parts.append(f"M{body} Z")
    return " ".join(parts)
