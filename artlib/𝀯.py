"""Locks of hair: strands that fall from the symbol's place, swaying, and drift outward (away from the middle of the outline).
A pencil strand under each, like an artist finding the flow of the hair before drawing it."""
import random

from kaomojilang.brush import Stroke, curve, sketch


def generate(ctx, stroke, width, seed):
    rnd = random.Random(seed)
    x, y = ctx.at
    pts = [p for line in ctx.ink for p in line]
    mid = sum(p[0] for p in pts) / len(pts) if pts else x
    out_dir = 1 if x >= mid else -1
    length = max(ctx.size[1] * 2.0, 8.0)
    out = []
    for k in range(5):
        a = (x + (k - 2) * 0.7, y + abs(k - 2) * 0.2)
        b = (a[0] + out_dir * (1.0 + 0.5 * k) + rnd.uniform(-0.3, 0.3), a[1] + length * (0.8 + 0.1 * k) + rnd.uniform(-0.5, 0.5))
        line = curve(a, b, bend=0.25 * (1 if k % 2 else -1), out_angle=80 + out_dir * 10, in_angle=95 + out_dir * 25)
        out.append(Stroke(line, width * (0.85 + 0.2 * rnd.random()), stroke or "black", 1.0, "over", taper=0.6))
        out += sketch(line, passes=2, overshoot=0.1, wobble=0.05, width=0.07, opacity=0.3, seed=seed + k)
    return out
