"""Mud girls: the pastel blob girls of Samples/SlimeJumpWindowLicker (a bikini, a bow, and the grin everyone gets), dancing, covered in mud.

`girl(variant, phase, mud, grin, cycles, lod, throw)` is an SVG text (viewBox 0 0 70 92, data-size 7 x 9.2 cells, feet at y 88; childlike thick outline).
  variant   0..5 picks the colour (pink, yellow, blue, lilac, mint, orange), the bikini, the dance (cheer, swing, whip, horns, twist, jump), the mud pattern
  phase     0..1 loops: `cycles` bounces and head-bangs in one loop (3 is fast); the pigtails of matted mud whip with the head
  mud       0..1 how much of her is covered (0.7: brown with her colour showing round the edge; drips, handprints, boots, worms)
  grin      0..1 how far her face has become THE face (shades and a grin full of teeth); None: from the variant (most are all grin, one is half way, one is not yet)
  lod       1: simpler (for the back rows), throw: an arm that winds up and throws a lump of mud once a loop
`face(variant, open_, w, h)` is a close-up of her face (viewBox 220 x 160) chewing, `mud_over(w, h, seed, amount)` is a group of mud splats and drips (SVG text, no <svg>)
to lay over any other drawing in the same viewBox (`band=False`: no band over the top, for a whole body; `band="cap"`: a cap of mud on an oval head), so the hero of the video can be as muddy as the rest.

As a symbol, 👯 draws a mud girl, with `seed` as the variant.
"""
import math
import random

from kaomojilang.artlib import ArtSvg

TAU = 2 * math.pi
OUT = "#2a1a3a"
COLORS = [("#ff8fc7", "#ff4f87"), ("#ffd84a", "#ff8a2a"), ("#6ec6ff", "#2e7bff"), ("#c7a3ff", "#8a4fff"), ("#7ee8b5", "#12b886"), ("#ffb070", "#e04a2a")]
MUD, MUD2, WET = "#5a3c1e", "#3a2412", "#8a6a3e"
WORM = ["#d98c8c", "#c9786b", "#e0a090"]
GRIN_AMOUNT = [1.0, 1.0, 0.55, 1.0, 1.0, 0.0]


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _path(pts, closed=True):
    n = len(pts)
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        if not closed:
            p0, p3 = pts[max(i - 1, 0)], pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + (" Z" if closed else "")


def blob(cx, cy, rx, ry, fill, n=10, wob=0.05, seed=1, flat=0.0, sw=2.2, stroke=OUT):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        a = TAU * i / n - math.pi / 2
        w = 1 + (r.random() - 0.5) * 2 * wob
        y = math.sin(a)
        if y > 0:
            y *= 1 - flat
        pts.append((cx + math.cos(a) * rx * w, cy + y * ry * w))
    return f'<path d="{_path(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'


def circle(cx, cy, r, fill, sw=2.0, stroke=OUT):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if sw else ""
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"{s}/>'


def line(x0, y0, x1, y1, color=OUT, sw=2.2):
    return f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'


def limb(p0, p1, bend, color, sw=4.2, outline=2.0):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    e = (mx - dy / L * bend, my + dx / L * bend)
    d = f"M{f(p0[0])} {f(p0[1])} Q{f(e[0])} {f(e[1])} {f(p1[0])} {f(p1[1])}"
    return (f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{f(sw + outline * 2)}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{f(sw)}" stroke-linecap="round"/>'), e


def mudlimb(p0, p1, bend, color, mud, sw=4.2, lod=0):
    """A limb in her colour whose lower part (from the elbow or knee) is mud, with a wet highlight."""
    s, e = limb(p0, p1, bend, color, sw)
    if mud > 0.2:
        q = (p0[0] + (p1[0] - p0[0]) * 0.42, p0[1] + (p1[1] - p0[1]) * 0.42)
        s += f'<path d="M{f(q[0])} {f(q[1])} L{f(p1[0])} {f(p1[1])}" fill="none" stroke="{OUT}" stroke-width="{f(sw + 3.6)}" stroke-linecap="round"/>'
        s += f'<path d="M{f(q[0])} {f(q[1])} L{f(p1[0])} {f(p1[1])}" fill="none" stroke="{MUD}" stroke-width="{f(sw + 1.2)}" stroke-linecap="round"/>'
        if not lod:
            s += f'<path d="M{f(q[0] + 1)} {f(q[1])} L{f(p1[0] + 1)} {f(p1[1])}" fill="none" stroke="{WET}" stroke-width="1" stroke-linecap="round" opacity="0.8"/>'
    return s


def _worm(x, y, ang, L, phase, col, w=2.6):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    pts = [(x + ux * L * t + nx * math.sin(TAU * (phase + t * 1.2)) * 2.4 * t, y + uy * L * t + ny * math.sin(TAU * (phase + t * 1.2)) * 2.4 * t) for t in (0, 0.33, 0.66, 1)]
    d = _path(pts, closed=False)
    return f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="{f(w + 2)}" stroke-linecap="round"/><path d="{d}" fill="none" stroke="{col}" stroke-width="{f(w)}" stroke-linecap="round"/>'


def grin(cx, cy, s=1.0, open_=0.5, shades=True, crazy=0.0, seed=3, fast=False):
    """THE face: a very wide mouth full of teeth, and sunglasses (or bulging eyes)."""
    o = []
    w, h = 15 * s, (5 + 6 * open_) * s
    my = cy + 5 * s
    o.append(f'<path d="M{f(cx - w)} {f(my - 1.5 * s)} Q{f(cx)} {f(my + h * 1.75)} {f(cx + w)} {f(my - 1.5 * s)} Q{f(cx)} {f(my - 1.5 * s + h * 0.55)} {f(cx - w)} {f(my - 1.5 * s)} Z" fill="#7a1230" stroke="{OUT}" stroke-width="{f(2 * s)}" stroke-linejoin="round"/>')
    if fast:                                                 # small figures: each row of teeth is one dashed stroke
        for yoff, hh, k in ((0.0, 0.30, 3.1), (1.45 * s - 0.2 * s, 1.12, 2.9)):
            y0 = my - 1.5 * s + yoff
            cyq = y0 + 2 * h * hh
            q = f"M{f(cx - w + 1.5 * s)} {f(y0)} Q{f(cx)} {f(cyq)} {f(cx + w - 1.5 * s)} {f(y0)}"
            o.append(f'<path d="{q}" fill="none" stroke="{OUT}" stroke-width="{f((k + 0.9) * s)}"/><path d="{q}" fill="none" stroke="#fffbe8" stroke-width="{f(k * s)}" stroke-dasharray="{f(3.1 * s)} {f(0.9 * s)}"/>')
    else:
        for i in range(9):
            t = (i + 0.5) / 9
            x = cx - w + 2 * w * t
            for yy, hh in ((my - 1.5 * s + (1 - (2 * t - 1) ** 2) * h * 0.30 - 0.2 * s, 3.1 * s), (my - 1.5 * s + (1 - (2 * t - 1) ** 2) * h * 1.12 - 2.4 * s, 2.9 * s)):
                o.append(f'<rect x="{f(x - 1.55 * s)}" y="{f(yy)}" width="{f(3.1 * s)}" height="{f(hh)}" rx="{f(0.5 * s)}" fill="#fffbe8" stroke="{OUT}" stroke-width="{f(0.9 * s)}"/>')
    ey = cy - 6 * s
    if shades:
        for sx in (-1, 1):
            pts = [(cx + sx * 3 * s, ey - 3.6 * s), (cx + sx * 12.5 * s, ey - 3.6 * s), (cx + sx * 11.5 * s, ey + 4.4 * s), (cx + sx * 4.5 * s, ey + 4.4 * s)]
            o.append(f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)} Z" fill="#15101c" stroke="{OUT}" stroke-width="{f(1.6 * s)}" stroke-linejoin="round"/>')
            o.append(line(cx + sx * 5.5 * s, ey - 2 * s, cx + sx * 8 * s, ey - 2 * s, "#8a7ab0", 1.2 * s))
        o.append(line(cx - 3 * s, ey - 3 * s, cx + 3 * s, ey - 3 * s, OUT, 1.8 * s))
    else:
        r = random.Random(seed)
        for sx in (-1, 1):
            o.append(circle(cx + sx * 7.5 * s, ey, (4.4 + 2.2 * crazy) * s, "#ffffff", 1.6 * s))
            o.append(circle(cx + sx * 7.5 * s + (r.random() - 0.5) * crazy * 3 * s, ey + (r.random() - 0.5) * crazy * 3 * s, (1.5 + 0.8 * crazy) * s, "#15101c", 0))
    return "".join(o)


def cute(cx, cy, s=1.0, blush="#ff8fc7", look=0.0):
    o = []
    for sx in (-1, 1):
        o.append(circle(cx + sx * 7 * s, cy - 3 * s, 3.4 * s, "#ffffff", 1.4 * s))
        o.append(circle(cx + sx * 7 * s + look * 1.2 * s, cy - 3 * s, 1.7 * s, "#15101c", 0))
        o.append(circle(cx + sx * 11.5 * s, cy + 3.2 * s, 2.8 * s, blush, 0))
    o.append(f'<path d="M{f(cx - 4 * s)} {f(cy + 3.5 * s)} Q{f(cx)} {f(cy + 8 * s)} {f(cx + 4 * s)} {f(cy + 3.5 * s)}" fill="none" stroke="{OUT}" stroke-width="{f(1.6 * s)}" stroke-linecap="round"/>')
    return "".join(o)


def splat(cx, cy, r, seed, fill=MUD, outline=True, drops=3):
    """An irregular splat of mud with a few drops around it."""
    rr = random.Random(seed)
    pts = [(cx + math.cos(TAU * i / 8) * r * rr.uniform(0.6, 1.25), cy + math.sin(TAU * i / 8) * r * rr.uniform(0.6, 1.1)) for i in range(8)]
    o = f'<path d="{_path(pts)}" fill="{fill}"' + (f' stroke="{MUD2}" stroke-width="0.9"' if outline else "") + ' stroke-linejoin="round"/>'
    for _ in range(drops):
        a = rr.uniform(0, TAU)
        o += circle(cx + math.cos(a) * r * 1.5, cy + math.sin(a) * r * 1.4, r * rr.uniform(0.14, 0.26), fill, 0)
    return o


def drip(x, y, L, w=2.4, fill=MUD):
    return f'<path d="M{f(x)} {f(y)} L{f(x)} {f(y + L)}" stroke="{MUD2}" stroke-width="{f(w + 1.4)}" stroke-linecap="round"/><path d="M{f(x)} {f(y)} L{f(x)} {f(y + L)}" stroke="{fill}" stroke-width="{f(w)}" stroke-linecap="round"/>'


def handprint(x, y, rot, s=1.0):
    o = f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)}) scale({f(s)})"><ellipse cx="0" cy="0" rx="3.4" ry="3.2" fill="{MUD2}" opacity="0.75"/>'
    for i in range(4):
        a = math.radians(-34 + i * 22)
        o += f'<line x1="{f(math.sin(a) * 1.8)}" y1="{f(-math.cos(a) * 2)}" x2="{f(math.sin(a) * 5)}" y2="{f(-math.cos(a) * 6.2)}" stroke="{MUD2}" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>'
    return o + "</g>"


def girl(variant=0, phase=0.0, mud=0.7, grin_=None, cycles=3, lod=0, throw=False):
    r = random.Random(variant * 6151 + 29)
    color, suit = COLORS[variant % 6]
    gl = GRIN_AMOUNT[variant % 6] if grin_ is None else grin_
    mode = ["cheer", "swing", "whip", "horns", "twist", "jump"][(variant + r.randint(0, 2)) % 6]
    if throw:
        mode = "throw"
    sp = TAU * phase * cycles
    ph = r.random() * 6
    bounce = abs(math.sin(sp)) * (6.5 if mode == "jump" else 3.8)
    bob = -bounce
    sway = math.sin(sp + ph) * (5 if mode == "twist" else 3.5)
    nod = math.sin(2 * sp + ph)                                # the head, twice as fast: headbanging
    sq = 0.05 * math.sin(2 * sp)
    cx = 35 + sway * 0.4
    o = []
    # ---- legs: pastel to the knee, mud socks and boots
    for side, ph2 in ((-1, 0), (1, math.pi)):
        lift = max(0.0, math.sin(sp + ph2)) * (7 if mode in ("jump", "cheer") else 4.5)
        foot = (35 + side * 6 + side * 2 * math.sin(sp + ph2) + sway * 0.2, 88 - lift)
        o.append(mudlimb((35 + side * 5 + sway * 0.3, 66 + bob), foot, 2 * side, color, mud, 4.4, lod))
        o.append(f'<ellipse cx="{f(foot[0] + side * 2)}" cy="{f(foot[1])}" rx="5.6" ry="3.2" fill="{MUD2}" stroke="{OUT}" stroke-width="1.5"/>')
    # ---- arms
    arms = []
    for side in (-1, 1):
        a = {"cheer": 0.7 + 0.35 * math.sin(sp + (side > 0) * math.pi), "swing": 0.2 + 0.9 * abs(math.sin(sp + (side > 0) * 1.6)), "whip": 0.95, "horns": 1.0 if side < 0 else 0.1 + 0.2 * math.sin(sp),
             "twist": 0.4 * math.sin(sp * 0.5) + 0.2 * side, "jump": 0.9 + 0.1 * math.sin(sp), "throw": 0.3}[mode]
        if mode == "throw" and side > 0:
            k = phase % 1.0
            u = min(1.0, max(0.0, (k - 0.45) / 0.25))
            a = 1.1 - 1.5 * u * u * (3 - 2 * u)
        sh = (35 + side * 13 + sway * 0.4, 52 + bob)
        hand = (sh[0] + side * (6 + 8 * abs(a)), sh[1] - a * 20)
        s, e = limb(sh, hand, 2 * side, color, 4.2)
        arms.append(mudlimb(sh, hand, 2 * side, color, mud, 4.2, lod))
        arms.append(circle(hand[0], hand[1], 3.2, MUD, 1.5))

        if mode == "throw" and side > 0 and (phase % 1.0) < 0.62:
            arms.append(circle(hand[0], hand[1] - 4, 4.4, "#4a3018", 1.5) + circle(hand[0] - 1.4, hand[1] - 5.4, 1.2, WET, 0))
    o.append("".join(arms))
    # ---- the body, squashing with the beat, leaning with the sway
    body = []
    body.append(blob(35, 52 + bob, 21, 26, color, n=11, wob=0.03, seed=variant + 5, flat=0.2, sw=2.4))
    if mud > 0:
        mm = mud
        body.append(blob(35, 52 + bob + 2, 21 * (0.5 + 0.42 * mm), 26 * (0.5 + 0.42 * mm), MUD, n=12, wob=0.1, seed=variant + 40, flat=0.2, sw=0.8, stroke=MUD2))
        for k in range(1 if lod else 3):                                   # windows in the mud where she is still colourful
            wx, wy = r.uniform(26, 44), r.uniform(60, 72)
            body.append(f'<ellipse cx="{f(wx)}" cy="{f(wy + bob)}" rx="{f(r.uniform(3, 6) * (1.4 - mm * 0.6))}" ry="{f(r.uniform(2.5, 4.5) * (1.4 - mm * 0.6))}" fill="{color}" opacity="0.9"/>')
        for k in range(0 if lod else 5):                                   # wet streaks
            x0, y0 = r.uniform(18, 52), r.uniform(36, 70)
            body.append(f'<path d="M{f(x0)} {f(y0 + bob)} q{f(r.uniform(-3, 3))} 6 {f(r.uniform(-2, 2))} {f(r.uniform(7, 14))}" fill="none" stroke="{WET}" stroke-width="1.3" stroke-linecap="round" opacity="0.85"/>')
        if not lod:
            body.append(handprint(26, 62 + bob, -20) + handprint(44, 58 + bob, 25, 0.9))
    # bikini (a splash of mud over it)
    body.append(f'<path d="M{f(cx - 14)} {f(56 + bob)} q14 8 28 0 l0 6 q-14 8 -28 0 z" fill="{suit}" stroke="{OUT}" stroke-width="1.8" stroke-linejoin="round"/>')
    body.append(f'<path d="M{f(cx - 11)} {f(69 + bob)} q11 7 22 0 l-3 7 q-8 3 -16 0 z" fill="{suit}" stroke="{OUT}" stroke-width="1.8" stroke-linejoin="round"/>')
    if mud > 0:
        body.append(splat(cx + 7, 60 + bob, 4.4, variant + 70, drops=0 if lod else 3) + ("" if lod else splat(cx - 8, 72 + bob, 3.2, variant + 71)))
        if not lod:
            body.append("".join(drip(cx + dx, 74 + bob, r.uniform(3, 7) * (0.5 + mud), 1.8) for dx in (-9, -2, 6, 12)))
    # face: the cute one fades into the grin, as in the video; mud on it too
    fy = 42 + bob
    nodrot = 7 * nod
    face = ""
    if gl < 1:
        face += f'<g opacity="{f(1 - gl)}">{cute(cx, fy, 1.05, suit)}</g>'
    if gl > 0:
        face += f'<g opacity="{f(min(1, gl * 1.4))}">{grin(cx, fy + 2, s=0.95 * (0.5 + 0.5 * gl), open_=0.5 + 0.5 * abs(math.sin(sp)), shades=gl > 0.45, crazy=0.6, fast=True)}</g>'
    if mud > 0:
        face += splat(cx + 11, fy - 1, 3.2, variant + 80, drops=0 if lod else 3) + ("" if lod else drip(cx - 9, fy - 12, 8, 2) + splat(cx - 5, fy - 9, 2.1, variant + 81))
    body.append(f'<g transform="rotate({f(nodrot)} {f(cx)} {f(fy + 14)}) translate({f(nod * 0.8)} {f(abs(nod) * 1.2)})">{face}</g>')
    # bow and pigtails of matted mud whipping with the head
    whip = math.sin(sp * 2 + ph - 0.9)
    bx, by = cx + 6 + nod * 0.6, 28 + bob + abs(nod) * 1.2
    body.append(f'<path d="M{f(bx)} {f(by)} L{f(bx - 10)} {f(by - 6)} L{f(bx - 10)} {f(by + 4)} Z M{f(bx)} {f(by)} L{f(bx + 10)} {f(by - 6)} L{f(bx + 10)} {f(by + 4)} Z" fill="{suit}" stroke="{OUT}" stroke-width="1.5" stroke-linejoin="round"/>' + circle(bx, by, 2.3, suit, 1.4))
    if mud > 0 and not lod:
        body.append(splat(bx + 5, by - 1, 2.0, variant + 90))
    for side in (-1, 1):
        ax, ay = cx + side * 15 + nod * 0.6, 40 + bob + abs(nod) * 1.4
        tipx, tipy = ax + side * 8 + whip * 12 * side + (0 if side > 0 else -0), ay + 11 + 6 * abs(whip)
        pts = [(ax, ay), (ax + side * 5 + whip * 5 * side, ay + 5), (tipx - side * 2, tipy - 3), (tipx, tipy)]
        d = _path(pts, closed=False)
        body.append(f'<path d="{d}" fill="none" stroke="{OUT}" stroke-width="7.2" stroke-linecap="round"/><path d="{d}" fill="none" stroke="{MUD2}" stroke-width="4.6" stroke-linecap="round"/>' + ("" if lod else f'<path d="{d}" fill="none" stroke="{WET}" stroke-width="1" stroke-linecap="round"/>'))
        if not lod:
            body.append(circle(tipx, tipy, 3.2, MUD2, 1.4))
    if not lod and variant % 2 == 0:                         # worms on her shoulder and in her hair
        for k, (wx, wy, a) in enumerate(((cx - 16, 44 + bob, 200), (cx + 15, 52 + bob, -20))):
            body.append(_worm(wx, wy, a, 11, phase * cycles + k * 0.3, WORM[(variant + k) % 3]))
    o.append(f'<g transform="translate({f(35 + sway * 0.3)} 88) rotate({f(sway * 0.8)}) scale({f(1 + sq)} {f(1 - sq)}) translate(-35 -88)">' + "".join(body) + "</g>")
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 70 92" data-size="7,9.2">{"".join(o)}</svg>'


def face(variant=0, open_=0.5, w=220, h=160, mud=0.9):
    """Her face, big: the grin, chewing; mud dripping off the top, a worm crawling over."""
    color, suit = COLORS[variant % 6]
    r = random.Random(variant * 17 + 3)
    o = [blob(110, 90, 92, 66, color, n=12, wob=0.03, seed=9 + variant, flat=0.12, sw=4)]
    o.append(f'<g opacity="0.0"></g>')
    o.append(f'<g>{grin(110, 92, s=3.6, open_=open_, shades=True)}</g>')
    if mud > 0:
        o.append(f'<path d="M24 74 Q40 22 110 24 Q182 22 196 74 Q186 56 168 62 Q160 40 140 58 Q122 38 104 56 Q86 38 70 58 Q50 44 24 74 Z" fill="{MUD}" stroke="{MUD2}" stroke-width="3" stroke-linejoin="round"/>')
        for i in range(9):
            x = 36 + i * 18 + r.uniform(-4, 4)
            L = r.uniform(14, 44)
            o.append(drip(x, 52 + abs(x - 110) * 0.12, L, 6, MUD))
            o.append(circle(x, 52 + abs(x - 110) * 0.12 + L + 3, 4.4, MUD, 0))
        for k in range(7):
            o.append(splat(r.uniform(30, 190), r.uniform(60, 140), r.uniform(5, 12), variant * 10 + k))
        o.append(handprint(60, 118, -25, 3.2) + handprint(164, 112, 30, 3.0))
    o.append(_worm(70, 36, 20, 60, open_, WORM[variant % 3], 7))
    o.append(f'<path d="M96 22 L70 6 L70 40 Z M96 22 L122 6 L122 40 Z" transform="translate(14 8)" fill="{suit}" stroke="{OUT}" stroke-width="3" stroke-linejoin="round"/>' + circle(110, 30, 7, suit, 3))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{"".join(o)}</svg>'


def mud_over(w=220, h=160, seed=1, amount=1.0, band=True):
    """Mud on something else: a thick band at the top dripping down, splats, a handprint; SVG text for a drawing of viewBox w x h."""
    r = random.Random(seed)
    o = []
    n = int(10 * amount) + 3
    if band == "cap":                                        # a cap of mud on a head: viewBox 220 x 160, an oval face
        sx, sy = w / 220, h / 160
        o.append(f'<path d="M{f(24 * sx)} {f(74 * sy)} Q{f(40 * sx)} {f(22 * sy)} {f(110 * sx)} {f(24 * sy)} Q{f(182 * sx)} {f(22 * sy)} {f(196 * sx)} {f(74 * sy)} Q{f(186 * sx)} {f(56 * sy)} {f(168 * sx)} {f(62 * sy)} Q{f(160 * sx)} {f(40 * sy)} {f(140 * sx)} {f(58 * sy)} Q{f(122 * sx)} {f(38 * sy)} {f(104 * sx)} {f(56 * sy)} Q{f(86 * sx)} {f(38 * sy)} {f(70 * sx)} {f(58 * sy)} Q{f(50 * sx)} {f(44 * sy)} {f(24 * sx)} {f(74 * sy)} Z" fill="{MUD}" stroke="{MUD2}" stroke-width="{f(3 * sx)}" stroke-linejoin="round"/>')
        for i in range(8):
            x = (40 + i * 20 + r.uniform(-4, 4)) * sx
            yy = (50 + abs(i * 20 + 40 - 110) * 0.14) * sy
            L = r.uniform(10, 34) * sy * amount
            o.append(drip(x, yy, L, 5 * sx, MUD))
            o.append(circle(x, yy + L + 3 * sy, 3.8 * sx, MUD, 0))
    y0 = 0.04 if band is True else 0.45
    for i in range(n if band != "cap" else 0):
        x = w * (i + r.random() * 0.6) / n
        L = h * r.uniform(0.08, 0.3) * amount
        if band is True or i % 2:
            o.append(drip(x, h * y0, L, w * 0.028, MUD))
            o.append(circle(x, h * y0 + L + w * 0.01, w * 0.019, MUD, 0))
    if band is True:
        o.append(f'<path d="M0 0 L{w} 0 L{w} {f(h * 0.1)} Q{f(w * 0.75)} {f(h * 0.16)} {f(w * 0.5)} {f(h * 0.09)} Q{f(w * 0.25)} {f(h * 0.17)} 0 {f(h * 0.1)} Z" fill="{MUD}" stroke="{MUD2}" stroke-width="{f(w * 0.012)}"/>')
    for k in range(int(8 * amount) + 3):
        o.append(splat(r.uniform(0.05, 0.95) * w, r.uniform(0.15, 0.95) * h, r.uniform(0.02, 0.05) * w, seed * 100 + k))
    o.append(handprint(w * r.uniform(0.2, 0.8), h * r.uniform(0.5, 0.85), r.uniform(-40, 40), w / 70))
    return "".join(o)


def generate(seed):
    return ArtSvg(girl(seed or 0, 0.0), "👯")
