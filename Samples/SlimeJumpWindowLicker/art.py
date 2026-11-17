"""art.py: a tiny kit for drawing childlike SVG by code: wobbly outlines, flat colours, thick dark lines.

Every drawing is a function that returns an SVG string; gen_svg.py calls them and writes svg/*.svg.  The drawings are sized in
tenths of a cell (a tile that is 6 x 8 cells has a viewBox of 60 x 80), so they drop into a levelang tile with size(6, 8).
"""
import math
import random

OUT = "#2a1a3a"          # the outline colour of everything
PINK, YELLOW, BLUE, LILAC, MINT = "#ff8fc7", "#ffd84a", "#6ec6ff", "#c7a3ff", "#7ee8b5"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def svg(w, h, body, defs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}">{defs}{body}</svg>'


def path(pts, closed=True, k=0.5):
    """A smooth path through the points (Catmull-Rom as cubic beziers)."""
    n = len(pts)
    if n < 3:
        return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        if not closed:
            p0 = pts[max(i - 1, 0)]
            p3 = pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 3 * 2 / 2, p1[1] + (p2[1] - p0[1]) * k / 3 * 2 / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 3 * 2 / 2, p2[1] - (p3[1] - p1[1]) * k / 3 * 2 / 2)
        d += f" C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + (" Z" if closed else "")


def blob_pts(cx, cy, rx, ry, n=10, wob=0.05, seed=1, flat=0.0):
    """Points of a wobbly ellipse; `flat` > 0 squashes the bottom (a slime sits on the ground)."""
    r = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        w = 1 + (r.random() - 0.5) * 2 * wob
        y = math.sin(a)
        if y > 0:
            y *= 1 - flat
        pts.append((cx + math.cos(a) * rx * w, cy + y * ry * w))
    return pts


def blob(cx, cy, rx, ry, fill, n=10, wob=0.05, seed=1, flat=0.0, sw=2.2, stroke=OUT, extra=""):
    return f'<path d="{path(blob_pts(cx, cy, rx, ry, n, wob, seed, flat))}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'


def poly(pts, fill, sw=2.2, stroke=OUT, smooth=False, closed=True, extra=""):
    d = path(pts, closed) if smooth else "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + (" Z" if closed else "")
    return f'<path d="{d}" fill="{fill if closed else "none"}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def rect(x, y, w, h, fill, r=0, sw=2.2, stroke=OUT, extra=""):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if sw else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(r)}" fill="{fill}"{s} {extra}/>'


def circle(cx, cy, r, fill, sw=2.2, stroke=OUT, extra=""):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if sw else ""
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"{s} {extra}/>'


def line(x0, y0, x1, y1, color=OUT, sw=2.2, extra=""):
    return f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" {extra}/>'


def limb(p0, p1, bend, color, sw=4.2, outline=2.0):
    """A bent limb (an arm or a leg) from p0 to p1: a dark line with a coloured one over it, the elbow pushed sideways by `bend`."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    e = (mx - dy / L * bend, my + dx / L * bend)
    d = f"M{f(p0[0])} {f(p0[1])} Q{f(e[0])} {f(e[1])} {f(p1[0])} {f(p1[1])}"
    return (f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{sw + outline * 2}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>')


def lin_grad(gid, stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


# ---------------------------------------------------------------- faces
def grin(cx, cy, s=1.0, open_=0.0, shades=True, crazy=0.0, seed=3, eyes_y=-6.0):
    """The grin everyone gets: a very wide mouth full of teeth, and sunglasses (or bulging eyes)."""
    out = []
    w, h = 15 * s, (5 + 6 * open_) * s
    my = cy + 5 * s
    # mouth
    out.append(f'<path d="M{f(cx - w)} {f(my - 1.5 * s)} Q{f(cx)} {f(my + h * 1.75)} {f(cx + w)} {f(my - 1.5 * s)} Q{f(cx)} {f(my - 1.5 * s + h * 0.55)} {f(cx - w)} {f(my - 1.5 * s)} Z" '
               f'fill="#7a1230" stroke="{OUT}" stroke-width="{f(2 * s)}" stroke-linejoin="round"/>')
    # teeth: a top row and a bottom row of little squares
    n = 9
    for i in range(n):
        t = (i + 0.5) / n
        x = cx - w + 2 * w * t
        yt = my - 1.5 * s + (1 - (2 * t - 1) ** 2) * h * 0.30
        out.append(rect(x - 1.55 * s, yt - 0.2 * s, 3.1 * s, 3.1 * s, "#fffbe8", r=0.5 * s, sw=0.9 * s))
        yb = my - 1.5 * s + (1 - (2 * t - 1) ** 2) * h * 1.12
        out.append(rect(x - 1.55 * s, yb - 2.4 * s, 3.1 * s, 2.9 * s, "#fffbe8", r=0.5 * s, sw=0.9 * s))
    ey = cy + eyes_y * s
    if shades:
        for sx in (-1, 1):
            out.append(poly([(cx + sx * 3 * s, ey - 3.6 * s), (cx + sx * 12.5 * s, ey - 3.6 * s), (cx + sx * 11.5 * s, ey + 4.4 * s), (cx + sx * 4.5 * s, ey + 4.4 * s)], "#15101c", sw=1.6 * s, smooth=False))
            out.append(line(cx + sx * 5.5 * s, ey - 2 * s, cx + sx * 8 * s, ey - 2 * s, "#8a7ab0", 1.2 * s))
        out.append(line(cx - 3 * s, ey - 3 * s, cx + 3 * s, ey - 3 * s, OUT, 1.8 * s))
    else:
        r = random.Random(seed)
        for sx in (-1, 1):
            rr = (4.4 + 2.2 * crazy) * s
            out.append(circle(cx + sx * 7.5 * s, ey, rr, "#ffffff", sw=1.6 * s))
            out.append(circle(cx + sx * 7.5 * s + (r.random() - 0.5) * crazy * 3 * s, ey + (r.random() - 0.5) * crazy * 3 * s, (1.5 + 0.8 * crazy) * s, "#15101c", sw=0))
    return "".join(out)


def cute_face(cx, cy, s=1.0, blush=PINK, mood="smile", look=0.0):
    """The face the girls have before the grin: two dots, rosy cheeks, a little mouth."""
    out = []
    for sx in (-1, 1):
        out.append(circle(cx + sx * 7 * s, cy - 3 * s, 3.4 * s, "#ffffff", sw=1.4 * s))
        out.append(circle(cx + sx * 7 * s + look * 1.2 * s, cy - 3 * s, 1.7 * s, "#15101c", sw=0))
        out.append(circle(cx + sx * 11.5 * s, cy + 3.2 * s, 2.8 * s, blush, sw=0, extra='opacity="0.8"'))
    if mood == "smile":
        out.append(f'<path d="M{f(cx - 4 * s)} {f(cy + 3.5 * s)} Q{f(cx)} {f(cy + 8 * s)} {f(cx + 4 * s)} {f(cy + 3.5 * s)}" fill="none" stroke="{OUT}" stroke-width="{f(1.6 * s)}" stroke-linecap="round"/>')
    elif mood == "no":
        out.append(line(cx - 3.5 * s, cy + 5 * s, cx + 3.5 * s, cy + 5 * s, OUT, 1.6 * s))
    else:
        out.append(f'<ellipse cx="{f(cx)}" cy="{f(cy + 5 * s)}" rx="{f(2.4 * s)}" ry="{f(3 * s)}" fill="#7a1230" stroke="{OUT}" stroke-width="{f(1.4 * s)}"/>')
    return "".join(out)
