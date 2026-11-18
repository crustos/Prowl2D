"""Forehead wrinkles: three gentle lines across the symbol's box, each a little different, with a pencil line under it."""
import random

from kaomojilang.brush import Stroke, curve, sketch


def generate(ctx, stroke, width, seed):
    rnd = random.Random(seed)
    x, y = ctx.at
    w = max(ctx.size[0], 8.0)
    out = []
    for k in range(3):
        half = w / 2 * (1 - 0.18 * k)
        yy = y + (k - 1) * 1.1
        a, b = (x - half, yy + rnd.uniform(-0.2, 0.2)), (x + half, yy + rnd.uniform(-0.2, 0.2))
        line = curve(a, b, bend=0.12 * (1 if k % 2 else -1))
        out.append(Stroke(line, width * 0.55, stroke or "black", 0.9, "over", taper=0.8))
        out += sketch(line, passes=1, overshoot=0.12, wobble=0.04, width=0.05, opacity=0.25, seed=seed + k)
    return out
