"""Brush strokes for artlib scripts: flowing curves, light rough sketch lines, overshoot.

A symbol's `generate()` may return `Stroke`s. They are drawn in *figure* coordinates (grid columns, y already multiplied
by ASPECT), so a symbol can reach out to its neighbours. `layer="under"` strokes are drawn below every part of the
figure (the light rough sketch under the dark lines), `layer="over"` (the default) above the parts.

    from kaomojilang.brush import Stroke, curve, sketch, connect

    def generate(ctx):
        eye = ctx.nearest("ᴀ7")
        return connect(ctx.at, eye.at, bend=0.3)       # a dark curve plus light sketch passes
"""

import math
import random
from dataclasses import dataclass, field

from .drawing import draw


@dataclass
class Stroke:
    points: list                       # [(x, y)] in figure coordinates
    width: float = 0.15                # in grid columns
    color: str = "black"
    opacity: float = 1.0
    layer: str = "over"                # "under" | "over"
    closed: bool = False
    smooth: bool = True                # Catmull-Rom through the points (False: straight segments)
    taper: float = 0.0                 # 0..1: the ends are thinner (drawn as a polygon ribbon)

    def bbox(self):
        xs, ys = [p[0] for p in self.points], [p[1] for p in self.points]
        h = self.width / 2
        return min(xs) - h, min(ys) - h, max(xs) + h, max(ys) + h


# ----------------------------------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------------------------------

def _r(v):
    return round(v, 4)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def angle_to(a, b):
    """Degrees, clockwise from +x (screen coordinates: y points down)."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def polar(p, degrees, r):
    a = math.radians(degrees)
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


def bezier(p0, p1, p2, p3, steps=14):
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def curve(a, b, bend=0.25, out_angle=None, in_angle=None, steps=14):
    """A flowing curve from a to b. `out_angle` is the direction it leaves a, `in_angle` the direction it arrives at b
    (degrees, clockwise from +x). Without them it bows sideways by `bend` (a fraction of the distance)."""
    d = dist(a, b)
    if d < 1e-9:
        return [a, b]
    base = angle_to(a, b)
    ao = base - 90 * bend * 2 if out_angle is None else out_angle
    ai = base + 180 + 90 * bend * 2 if in_angle is None else in_angle + 180
    h = d * 0.38
    return bezier(a, polar(a, ao, h), polar(b, ai, h), b, steps)


def extend(points, amount):
    """Overshoot: push both ends out along their tangents by `amount` (grid columns)."""
    if len(points) < 2 or amount == 0:
        return list(points)
    a0 = angle_to(points[1], points[0])
    a1 = angle_to(points[-2], points[-1])
    return [polar(points[0], a0, amount)] + list(points) + [polar(points[-1], a1, amount)]


# ----------------------------------------------------------------------------------------------------
# A hand holding a pencil
# ----------------------------------------------------------------------------------------------------

def path_length(points, closed=False):
    pts = list(points) + ([points[0]] if closed and points else [])
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(points, step, closed=False):
    """Evenly spaced points (about `step` apart) along the polyline, both ends kept (a closed line: no repeated end)."""
    pts = list(points) + ([points[0]] if closed else [])
    if len(pts) < 2:
        return list(points)
    total = path_length(pts)
    if total < 1e-9:
        return [pts[0]]
    n = max(2, int(round(total / step)) + 1)
    out, seg, run = [], 0, 0.0
    for k in range(n):
        target = total * k / (n - 1)
        while seg < len(pts) - 2 and run + dist(pts[seg], pts[seg + 1]) < target:
            run += dist(pts[seg], pts[seg + 1])
            seg += 1
        d = dist(pts[seg], pts[seg + 1])
        u = 0.0 if d < 1e-12 else min(1.0, max(0.0, (target - run) / d))
        out.append((pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * u, pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * u))
    return out[:-1] if closed else out


def chaikin(points, iterations=2, closed=False):
    """Corner cutting: a control polygon -> the smooth line it describes (ends kept on an open line)."""
    pts = list(points)
    for _ in range(iterations):
        if len(pts) < 3:
            break
        out = [] if closed else [pts[0]]
        n = len(pts)
        for i in range(n if closed else n - 1):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if not closed:
            out.append(pts[-1])
        pts = out
    return pts


def simplify(points, tolerance, closed=False):
    """Douglas-Peucker: the few straight segments that carry the shape (what an artist blocks in first)."""
    pts = list(points)
    if closed and len(pts) > 3:                      # cut a closed line at its two farthest points
        far = max(range(1, len(pts)), key=lambda i: dist(pts[0], pts[i]))
        return simplify(pts[:far + 1], tolerance)[:-1] + simplify(pts[far:] + [pts[0]], tolerance)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    best, at = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = _off(pts[i], a, b)
        if d > best:
            best, at = d, i
    if best <= tolerance:
        return [a, b]
    return simplify(pts[:at + 1], tolerance)[:-1] + simplify(pts[at:], tolerance)


def _off(p, a, b):
    """Distance of p from the segment ab."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    if n < 1e-12:
        return dist(p, a)
    u = min(1.0, max(0.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
    return dist(p, (a[0] + dx * u, a[1] + dy * u))


def _lengthen(base, e0, e1, step):
    """Push the start by e0 and the end by e1 along their tangents (a negative amount: cut the line short)."""
    pts = list(base)
    for end, e in ((0, e0), (1, e1)):
        if abs(e) < 1e-6 or len(pts) < 2:
            continue
        if end == 1:
            pts.reverse()
        if e > 0:
            ang = angle_to(pts[1], pts[0])
            k = max(1, int(e / step))
            pts = [polar(pts[0], ang, e * j / k) for j in range(k, 0, -1)] + pts
        else:
            cut, run = -e, 0.0
            while len(pts) > 3 and run + dist(pts[0], pts[1]) < cut:
                run += dist(pts[0], pts[1])
                pts.pop(0)
        if end == 1:
            pts.reverse()
    return pts


def hand(points, err=0.15, seed=0, bow=1.0, overshoot=0.06, drift=0.5, step=0.45):
    """The line a hand draws when it follows `points`: the same path, left by a slow wander (two low waves and a bow, never
    per-point noise), starting steady and drifting, and starting a little early or late, overshooting the end.
    `err` is the wander in grid columns; `overshoot` how far the ends run on (a fraction of the length)."""
    pts = list(points)
    if len(pts) < 2:
        return pts
    rnd = random.Random(seed)
    base = resample(pts, step)
    length = path_length(base)
    if length < 1e-6:
        return pts
    cap = 0.3 + err * 14
    e0, e1 = (min(cap, length * overshoot * rnd.uniform(0.2, 1.6)) for _ in range(2))
    if rnd.random() < 0.2:
        e0 = -min(length * 0.03, cap / 3)
    if rnd.random() < 0.2:
        e1 = -min(length * 0.03, cap / 3)
    line = _lengthen(base, e0, e1, step)
    n = len(line)
    total = path_length(line)
    lam1, lam2 = max(total * rnd.uniform(0.55, 1.2), 3.0), max(total * rnd.uniform(0.25, 0.5), 1.8)
    ph1, ph2 = rnd.uniform(0, 6.283), rnd.uniform(0, 6.283)
    b, o0, o1 = bow * rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.9, 0.9) * drift
    out, s = [], 0.0
    for i in range(n):
        if i:
            s += dist(line[i - 1], line[i])
        t = s / total if total else 0.0
        a, c = line[max(0, i - 1)], line[min(n - 1, i + 1)]
        tx, ty = c[0] - a[0], c[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl
        steady = 1 - drift * 0.6 * (1 - t)
        d = err * (steady * (0.6 * math.sin(6.283 * s / lam1 + ph1) + 0.22 * math.sin(6.283 * s / lam2 + ph2))
                   + 0.9 * b * math.sin(math.pi * t) + o0 * (1 - t) + o1 * t)
        out.append((line[i][0] + nx * d, line[i][1] + ny * d))
    return out[::2] + ([out[-1]] if len(out) % 2 == 0 else [])


def loop(center, rx, ry, angle=0.0, err=0.15, seed=0, turns=1.12, clockwise=None):
    """A loose ellipse drawn the way a hand draws one: it starts anywhere, comes round a little too big or too small and runs
    past where it began (turns > 1)."""
    rnd = random.Random(seed)
    th0 = rnd.uniform(0, 6.283)
    sign = (1 if clockwise else -1) if clockwise is not None else (-1 if rnd.random() < 0.7 else 1)
    f1, f2, p1, p2 = rnd.uniform(1.4, 2.2), rnd.uniform(2.6, 3.6), rnd.uniform(0, 6.283), rnd.uniform(0, 6.283)
    drift = rnd.uniform(-0.05, 0.06)
    rel = err / max(rx, ry, 1e-6)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    n = max(12, int(turns * 24))
    out = []
    for k in range(n + 1):
        u = k / n
        th = th0 + sign * 6.283 * turns * u
        r = 1 + drift * u + rel * (0.7 * math.sin(6.283 * f1 * u + p1) + 0.3 * math.sin(6.283 * f2 * u + p2))
        x, y = rx * r * math.cos(th), ry * r * math.sin(th)
        out.append((center[0] + x * ca - y * sa, center[1] + x * sa + y * ca))
    return out


def sketch(points, passes=3, overshoot=0.12, wobble=0.07, width=0.07, color="black", opacity=0.3, seed=0, layer="under"):
    """Light rough passes along `points`, the way an artist searches for a line: the first pass is loose and sails past
    the ends, the next ones settle toward the line (smaller wander, darker), each a little different. They taper at both ends
    like a pencil stroke. `wobble` is how far the first pass may stray (in columns, grows a little with the length)."""
    pts = list(points.points) if isinstance(points, Stroke) else list(points)
    if len(pts) < 2:
        return []
    rnd = random.Random(seed)
    length = path_length(pts)
    out = []
    for k in range(passes):
        settle = k / max(1, passes - 1)
        err = wobble * (1.6 - 0.9 * settle) * (1 + 0.12 * length)
        line = hand(pts, err=err, seed=rnd.randrange(1 << 30), overshoot=overshoot * (1.3 - 0.8 * settle), bow=0.8)
        out.append(Stroke(line, width * (0.75 + 0.5 * rnd.random()), color, opacity * (0.7 + 0.5 * settle), layer, taper=0.85))
    return out


def connect(a, b, bend=0.25, out_angle=None, in_angle=None, width=0.14, color="black", sketch_passes=3, overshoot=0.12, opacity=1.0, seed=None):
    """A dark flowing curve from point a to point b and, under it, light rough sketch passes around the same line."""
    pts = curve(a, b, bend, out_angle, in_angle)
    main = Stroke(pts, width, color, opacity, "over")
    seed = int((a[0] * 131 + a[1] * 71 + b[0] * 17 + b[1] * 5) * 100) if seed is None else seed
    return [main] + sketch(pts, sketch_passes, overshoot, width=width * 0.5, color=color, seed=seed)


# ----------------------------------------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------------------------------------

def _catmull(points, closed=False):
    n = len(points)
    if n < 3:
        return "M" + " L".join(f"{_r(x)} {_r(y)}" for x, y in points)
    pts = list(points)
    d = f"M{_r(pts[0][0])} {_r(pts[0][1])}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{_r(c1[0])} {_r(c1[1])} {_r(c2[0])} {_r(c2[1])} {_r(p2[0])} {_r(p2[1])}"
    return d + (" Z" if closed else "")


def _catmull_points(points, closed=False, per=5):
    """Points on the Catmull-Rom curve through `points` (what _catmull draws), `per` per span."""
    n = len(points)
    if n < 3:
        return list(points)
    out = []
    for i in range(n if closed else n - 1):
        p0 = points[(i - 1) % n] if closed or i > 0 else points[0]
        p1, p2 = points[i], points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed or i + 2 < n else points[-1]
        for j in range(per):
            t = j / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    if not closed:
        out.append(tuple(points[-1]))
    return out


def _ribbon(s: Stroke, width_factor):
    """A stroke whose width changes along it (thin ends, full in the middle), as a filled outline."""
    pts = _catmull_points(s.points, False, 4) if s.smooth else list(s.points)
    n = len(pts)
    total = path_length(pts) or 1.0
    left, right, run = [], [], 0.0
    for i in range(n):
        if i:
            run += dist(pts[i - 1], pts[i])
        t = run / total
        w = s.width * width_factor * ((1 - s.taper) + s.taper * max(0.0, math.sin(math.pi * min(1.0, t))) ** 0.7) / 2
        a, c = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = c[0] - a[0], c[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    poly = left + right[::-1]
    d = "M" + " L".join(f"{_r(x)} {_r(y)}" for x, y in poly) + " Z"
    style = dict(fill=s.color, stroke="none")
    if s.opacity < 1.0:
        style["opacity"] = _r(s.opacity)
    return draw.Path(d=d, **style)


def stroke_element(s: Stroke, width_factor=1.0):
    if s.taper > 0 and not s.closed and len(s.points) >= 2:
        return _ribbon(s, width_factor)
    style = dict(fill="none", stroke=s.color, stroke_width=_r(s.width * width_factor), stroke_linecap="round", stroke_linejoin="round")
    if s.opacity < 1.0:
        style["opacity"] = _r(s.opacity)
    if s.smooth and len(s.points) >= 3:
        return draw.Path(d=_catmull(s.points, s.closed), **style)
    flat = [_r(v) for p in s.points for v in p]
    return draw.Lines(*flat, close=s.closed, **style)
