"""The toilet on the pipes: the big toilet (`🚽.svg`) sits on top of the main pipe, which runs down and ends in a flared spout
(this is the one that pours onto the singer). Pipes come in from the left, from above, up through the tank, and join the main pipe
with T-joints, flanges, rivets, rust and drips. `seed` picks how many pipes there are and where they run.

The picture is 22 x 28 grid units; the toilet is its top, the spout the bottom, and the pipes leave the picture at the left and the top
so the scenery can carry them on. The spout is at x = 0.68 of the width, y = 1.0 (the mud falls from there).
"""
import random

from kaomojilang.artlib import ArtSvg

W, H = 440, 560                 # the canvas (units of its own; the symbol scales it to data-size)
MAIN_X = 300                    # the main pipe's axis
S = 1.3                         # the toilet is drawn this much bigger than its own svg
TOILET_X, TOILET_Y = MAIN_X - 80 * S, 40
DARK, STEEL, LIGHT, SHADE, RUST, MUD = "#2a1a3a", "#6e7479", "#a3aaaf", "#555b60", "#8a5a3a", "#4a3018"


def _inner(svg_text):
    a = svg_text.index(">", svg_text.index("<svg")) + 1
    return svg_text[a:svg_text.rindex("</svg>")]


def _pts(points):
    return " ".join(f"{x:g},{y:g}" for x, y in points)


def pipe(points, w, back=False):
    """A pipe along axis-aligned points: dark outline, steel body, a lit side, flanges at the ends and every so often."""
    body, shade = (SHADE, "#3f4448") if back else (STEEL, SHADE)
    out = [f'<polyline points="{_pts(points)}" fill="none" stroke="{DARK}" stroke-width="{w + 7:g}" stroke-linejoin="round" stroke-linecap="butt"/>',
           f'<polyline points="{_pts(points)}" fill="none" stroke="{body}" stroke-width="{w:g}" stroke-linejoin="round" stroke-linecap="butt"/>']
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if y0 == y1:                                # horizontal run: the lit edge is the upper one, the shade the lower
            out.append(f'<line x1="{x0:g}" y1="{y0 - w * 0.27:g}" x2="{x1:g}" y2="{y1 - w * 0.27:g}" stroke="{LIGHT}" stroke-width="{w * 0.16:g}" stroke-linecap="round"/>')
            out.append(f'<line x1="{x0:g}" y1="{y0 + w * 0.36:g}" x2="{x1:g}" y2="{y1 + w * 0.36:g}" stroke="{shade}" stroke-width="{w * 0.2:g}" stroke-linecap="round"/>')
        else:
            out.append(f'<line x1="{x0 - w * 0.27:g}" y1="{y0:g}" x2="{x1 - w * 0.27:g}" y2="{y1:g}" stroke="{LIGHT}" stroke-width="{w * 0.16:g}" stroke-linecap="round"/>')
            out.append(f'<line x1="{x0 + w * 0.36:g}" y1="{y0:g}" x2="{x1 + w * 0.36:g}" y2="{y1:g}" stroke="{shade}" stroke-width="{w * 0.2:g}" stroke-linecap="round"/>')
    return "".join(out)


def flange(x, y, w, horizontal_pipe, rnd):
    """A collar across a pipe at (x, y) with two bolts."""
    t, L = 9, w + 12
    if horizontal_pipe:
        r = f'<rect x="{x - t / 2:g}" y="{y - L / 2:g}" width="{t}" height="{L:g}" rx="2" fill="#838a8f" stroke="{DARK}" stroke-width="2.6"/>'
        b = f'<circle cx="{x:g}" cy="{y - L / 2 + 4:g}" r="1.7" fill="{DARK}"/><circle cx="{x:g}" cy="{y + L / 2 - 4:g}" r="1.7" fill="{DARK}"/>'
    else:
        r = f'<rect x="{x - L / 2:g}" y="{y - t / 2:g}" width="{L:g}" height="{t}" rx="2" fill="#838a8f" stroke="{DARK}" stroke-width="2.6"/>'
        b = f'<circle cx="{x - L / 2 + 4:g}" cy="{y:g}" r="1.7" fill="{DARK}"/><circle cx="{x + L / 2 - 4:g}" cy="{y:g}" r="1.7" fill="{DARK}"/>'
    return r + b


def drip(x, y, rnd, long=False):
    n = rnd.uniform(14, 26) if long else rnd.uniform(5, 9)
    return (f'<path d="M{x - 2.6:g} {y:g} C{x - 2.6:g} {y + n * 0.6:g} {x - 3:g} {y + n:g} {x:g} {y + n:g} C{x + 3:g} {y + n:g} {x + 2.6:g} {y + n * 0.6:g} {x + 2.6:g} {y:g} Z" '
            f'fill="{MUD}" stroke="{DARK}" stroke-width="1.6" stroke-linejoin="round"/>')


def rust(x, y, rnd):
    return "".join(f'<ellipse cx="{x + rnd.uniform(-6, 6):g}" cy="{y + rnd.uniform(-6, 6):g}" rx="{rnd.uniform(2, 5):g}" ry="{rnd.uniform(1.5, 3.5):g}" fill="{RUST}"/>' for _ in range(3))


def build(svg, seed=0, left=0, top=0):
    """The picture with the pipes running on `left` / `top` more units past its left and top edges (20 units = one grid unit),
    for a scene that wants them to reach the edge of the wall. `generate` is `build` with no extra."""
    rnd = random.Random(seed)
    back, mid, front, extras = [], [], [], []
    main_w = 34
    JOIN_MIN = TOILET_Y + int(200 * S) + 24            # junctions into the main pipe are below the toilet's foot
    # ---- pipes from the left: they run in at some height, step up or down once or twice, and T into the main pipe
    ys = sorted(rnd.sample(range(60, 500, 20), rnd.randint(5, 7)))
    for k, y in enumerate(ys):
        w = rnd.choice([14, 16, 20, 24, 28])
        x1 = rnd.randrange(70, 190, 10)
        y2 = y + rnd.choice([-1, 1]) * rnd.randrange(30, 90, 10)
        y2 = min(max(y2, JOIN_MIN), H - 120)
        ends = MAIN_X - main_w / 2 + 3
        pts = [(-6 - left, y), (x1, y), (x1, y2), (ends, y2)] if rnd.random() < 0.8 else [(-6 - left, y), (ends, y)]
        (back if w < 22 else mid).append(pipe(pts, w, back=w < 22))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = abs(bx - ax) + abs(by - ay)
            for f in range(1, int(L // 70) + 1):
                t = f * 70 / L
                if t < 0.95:
                    (front if w >= 22 else back).append(flange(ax + (bx - ax) * t, ay + (by - ay) * t, w, ay == by, rnd))
        if rnd.random() < 0.8:
            dx = rnd.uniform(20, x1 if x1 > 40 else 40)
            extras.append(drip(dx, y + w / 2 + 2, rnd, rnd.random() < 0.35))
        extras.append(rust(rnd.uniform(10, x1), y, rnd))
        extras.append(flange(ends - 4, y2, w, True, rnd))
    # ---- pipes from above: down along the sides of the tank and across to the main pipe; two go up through the tank's lid
    for x, w in rnd.sample([(30, 20), (70, 16), (110, 24), (150, 14), (190, 18), (236, 16)], rnd.randint(3, 5)):
        yj = rnd.randrange(JOIN_MIN, H - 120, 10)
        pts = [(x, -6 - top), (x, yj), (MAIN_X - main_w / 2 + 3, yj)] if rnd.random() < 0.6 else [(x, -6 - top), (x, yj)]
        mid.append(pipe(pts, w, back=w < 18))
        extras.append(flange(x, rnd.randrange(20, 120, 10), w, False, rnd))
        if rnd.random() < 0.5:
            extras.append(rust(x, rnd.uniform(40, yj), rnd))
    tank_pipes = []
    for x, w in [(TOILET_X + 56 * S, 20), (TOILET_X + 96 * S, 16)]:
        tank_pipes.append(pipe([(x, -6 - top), (x, TOILET_Y + 6 * S)], w))
        tank_pipes.append(flange(x, TOILET_Y - 10, w, False, rnd))
        tank_pipes.append(flange(x, 14, w, False, rnd))
    # ---- the main pipe: from under the toilet to the spout, thick, with a bend-less drop, collars, and the flared mouth
    top, bottom = TOILET_Y + int(196 * S), H - 40
    main = [pipe([(MAIN_X, top), (MAIN_X, bottom)], main_w)]
    for y in range(top + 40, bottom - 20, 60):
        main.append(flange(MAIN_X, y, main_w, False, rnd))
    main.append(rust(MAIN_X - 6, top + 90, rnd))
    # the mouth: a cone with a lip, the mud collar and drips falling from it
    mx, my = MAIN_X, bottom
    main.append(f'<path d="M{mx - 17:g} {my:g} L{mx - 27:g} {my + 24:g} L{mx + 27:g} {my + 24:g} L{mx + 17:g} {my:g} Z" fill="{STEEL}" stroke="{DARK}" stroke-width="3.2" stroke-linejoin="round"/>')
    main.append(f'<rect x="{mx - 31:g}" y="{my + 20:g}" width="62" height="9" rx="3" fill="#838a8f" stroke="{DARK}" stroke-width="2.8"/>')
    main.append(f'<ellipse cx="{mx:g}" cy="{my + 29:g}" rx="22" ry="4" fill="{MUD}"/>')
    for dx in (-17, -5, 9, 19):
        main.append(drip(mx + dx + rnd.uniform(-2, 2), my + 30, rnd, True))
    inner = _inner(svg.text)
    toilet = f'<g transform="translate({TOILET_X:g},{TOILET_Y}) scale({S})">{inner}</g>'
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-left} {-top} {W + left} {H + top}" data-size="{(W + left) / 20:g},{(H + top) / 20:g}">'
            + "".join(back) + "".join(mid) + "".join(main) + toilet + "".join(tank_pipes) + "".join(front) + "".join(extras) + "</svg>")
    return ArtSvg(text, svg.source)


def generate(svg, seed):
    return build(svg, seed)
