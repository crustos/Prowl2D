"""A beard: strands that fall from the jaw. It looks at the outline around it: points of the outline below the symbol (within
reach) each start a strand that sways down and in, longer toward the middle."""
import random

from kaomojilang.brush import Stroke, curve, resample, sketch


def generate(ctx, stroke, width, seed):
    rnd = random.Random(seed)
    x, y = ctx.at
    reach = max(ctx.size[0], 9.0)
    pts = []
    for line in ctx.ink:
        pts += [p for p in resample(line, 0.9) if abs(p[0] - x) < reach and -0.5 < p[1] - y < reach * 0.8]
    if not pts:
        pts = [(x + (i - 5) * 1.0, y) for i in range(11)]
    out = []
    for k, (px, py) in enumerate(sorted(pts)):
        mid = 1 - min(1.0, abs(px - x) / reach)
        length = 2.2 + 3.6 * mid + rnd.uniform(0, 1.0)
        end = (px + (x - px) * 0.2 + rnd.uniform(-0.4, 0.4), py + length)
        line = curve((px, py), end, bend=0.22 * (1 if px < x else -1))
        out.append(Stroke(line, width * 0.75, stroke or "black", 1.0, "over", taper=0.7))
        if k % 2 == 0:
            out += sketch(line, passes=1, overshoot=0.15, wobble=0.04, width=0.06, opacity=0.28, seed=seed + k)
    return out
