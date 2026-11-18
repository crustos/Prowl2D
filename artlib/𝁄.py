"""Stubble: small dark flecks scattered over the symbol's box, thinner toward the edges."""
import random

from kaomojilang.brush import Stroke


def generate(ctx, stroke, seed):
    rnd = random.Random(seed)
    x, y = ctx.at
    w, h = ctx.size
    w, h = max(w, 6.0), max(h, 3.0)
    out = []
    for _ in range(int(w * h * 1.6)):
        u, v = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
        if u * u + v * v > 1 or rnd.random() < (u * u + v * v) * 0.6:
            continue
        px, py = x + u * w / 2, y + v * h / 2
        a = rnd.uniform(0, 3.14)
        out.append(Stroke([(px, py), (px + 0.22 * 0.5 * (1 if a < 1.5 else -1), py + 0.2)], 0.09, stroke or "black", 0.8, "over"))
    return out
