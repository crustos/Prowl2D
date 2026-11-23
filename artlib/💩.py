"""A small person covered in mud and worms: a simple figure that can be animated.

`person(variant, phase, role)` is an SVG text (viewBox -8 -18 76 108, feet on y = 88). `variant` picks the figure (height, build, lean, mud colours,
arms, where the worms sit), `phase` (0..1, loops) is the dance: bounce, head-banging, swinging arms, wriggling worms. `role`:
"crowd" (one of the audience), "guitar", "bass", "drums", "keys" (the band: the instrument is drawn on the figure).
`lod=1` is a simpler drawing for the far rows of a crowd (no mud drips, highlights or hands, two worms): a third of the shapes, so a hundred of them animate fast.
`worm(variant, phase)` is one worm alone (viewBox 0 0 30 10) for the ground.

As a symbol, 💩 draws the standing figure; `seed` is the variant:  `face(...)` with 💩 in a drawing, or  `svgs()` over frames made by
`Samples/NIN/make_assets.py`, which calls `person()` for every variant and every frame of the animation.
"""
import math
import random

from kaomojilang.artlib import ArtSvg

DARK = "#1a0f08"
MUDS = [("#4a3018", "#3a2310", "#6b4a26"), ("#5b4126", "#46301a", "#7d5c36"), ("#3f2a14", "#2e1d0c", "#5e4020"), ("#52391f", "#40290f", "#75522a")]
WORMS = ["#d98c8c", "#c9786b", "#e0a090", "#b8745f"]
TAU = 2 * math.pi


def _f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _worm(x, y, ang, length, phase, color, w=2.6, flip=1):
    """A wriggling worm from (x, y), curling along `ang` (degrees): a cubic with the control points swaying with the phase."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    s1, s2 = math.sin(TAU * phase) * 0.35 * length, math.sin(TAU * phase + 2.1) * 0.35 * length
    p1 = (x + ux * length * 0.33 + nx * s1, y + uy * length * 0.33 + ny * s1)
    p2 = (x + ux * length * 0.66 + nx * s2, y + uy * length * 0.66 + ny * s2)
    p3 = (x + ux * length + nx * s1 * 0.5, y + uy * length + ny * s1 * 0.5)
    d = f"M{_f(x)} {_f(y)} C{_f(p1[0])} {_f(p1[1])} {_f(p2[0])} {_f(p2[1])} {_f(p3[0])} {_f(p3[1])}"
    return (f'<path d="{d}" fill="none" stroke="{DARK}" stroke-width="{_f(w + 1.8)}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{_f(w)}" stroke-linecap="round"/>')


def _limb(x0, y0, x1, y1, w, fill):
    return (f'<line x1="{_f(x0)}" y1="{_f(y0)}" x2="{_f(x1)}" y2="{_f(y1)}" stroke="{DARK}" stroke-width="{_f(w + 2.4)}" stroke-linecap="round"/>'
            f'<line x1="{_f(x0)}" y1="{_f(y0)}" x2="{_f(x1)}" y2="{_f(y1)}" stroke="{fill}" stroke-width="{_f(w)}" stroke-linecap="round"/>')


def person(variant=0, phase=0.0, role="crowd", lod=0):
    r = random.Random(variant * 7919 + 13)
    body, dark, wet = r.choice(MUDS)
    head_c = r.choice(MUDS)[0]
    hs = r.uniform(0.9, 1.1)                       # height
    ws = r.uniform(0.85, 1.2)                      # build
    lean = r.uniform(-7, 7)
    arms = r.choice(["up", "up", "one", "swing", "horns", "hug"]) if role == "crowd" else {"guitar": "play", "bass": "play", "keys": "type", "drums": "drum"}[role]
    scream = r.random() < 0.6
    sp = TAU * phase
    bounce = abs(math.sin(sp)) * (3.5 if role != "drums" else 1.5) * r.uniform(0.6, 1.3)
    bang = math.sin(2 * sp + r.random()) * 4                   # head-banging
    sway = math.sin(sp + r.random() * 6) * 4
    foot_y = 88
    out = []
    # ---- legs
    hip = foot_y - 22 * hs - bounce
    if role == "drums":                                         # seated behind the kit
        hip = foot_y - 14
        out.append(_limb(-6, hip, -13, foot_y - 3, 6.5, dark) + _limb(6, hip, 13, foot_y - 3, 6.5, dark))
        out.append(f'<rect x="-14" y="{foot_y - 14}" width="28" height="5" rx="2" fill="{dark}" stroke="{DARK}" stroke-width="1.6"/>')
    else:
        out.append(_limb(-5 * ws, hip, -7 * ws, foot_y - 2, 6.5, dark) + _limb(5 * ws, hip, 7 * ws + math.sin(sp) * 1.5, foot_y - 2 - bounce * 0.2, 6.5, dark))
        out.append(f'<ellipse cx="{_f(-8 * ws)}" cy="{foot_y - 1}" rx="6" ry="3" fill="{dark}" stroke="{DARK}" stroke-width="1.6"/><ellipse cx="{_f(8 * ws)}" cy="{foot_y - 1 - bounce * 0.2:g}" rx="6" ry="3" fill="{dark}" stroke="{DARK}" stroke-width="1.6"/>')
    # ---- torso
    top = hip - 30 * hs
    sh = 12.5 * ws
    out.append(f'<path d="M{_f(-9 * ws)} {_f(hip)} C{_f(-12 * ws)} {_f(hip - 10)} {_f(-sh - 1)} {_f(top + 10)} {_f(-sh)} {_f(top + 3)} Q{_f(-sh)} {_f(top - 2)} {_f(-6)} {_f(top - 2)} L{_f(6)} {_f(top - 2)} '
               f'Q{_f(sh)} {_f(top - 2)} {_f(sh)} {_f(top + 3)} C{_f(sh + 1)} {_f(top + 10)} {_f(12 * ws)} {_f(hip - 10)} {_f(9 * ws)} {_f(hip)} Z" fill="{body}" stroke="{DARK}" stroke-width="2.2" stroke-linejoin="round"/>')
    if not lod:
        out.append(f'<path d="M{_f(-sh + 3)} {_f(top + 6)} C{_f(-sh + 2)} {_f(top + 14)} {_f(-sh + 4)} {_f(top + 18)} {_f(-sh + 3)} {_f(top + 22)}" fill="none" stroke="{wet}" stroke-width="2" stroke-linecap="round"/>')
    for k in range(r.randint(2, 4)):                            # mud sagging down the front
        dx, dl = r.uniform(-8, 8) * ws, r.uniform(4, 10)
        if not lod:
            out.append(f'<path d="M{_f(dx - 2.5)} {_f(hip - 9)} Q{_f(dx)} {_f(hip - 9 + dl * 1.4)} {_f(dx + 2.5)} {_f(hip - 9)} Z" fill="{dark}"/>')
    # ---- the band's instrument, behind the arms
    sx = sh - 1.5
    shoulder_y = top + 4
    if role in ("guitar", "bass"):
        L = 38 if role == "guitar" else 46
        out.append(f'<g transform="translate(0 {_f(hip - 10)}) rotate({-28 if role == "guitar" else -18})"><ellipse cx="0" cy="3" rx="11" ry="8" fill="#6e4a22" stroke="{DARK}" stroke-width="2"/>'
                   f'<rect x="4" y="0" width="{L}" height="3.6" fill="#3a2410" stroke="{DARK}" stroke-width="1.4"/><rect x="{L + 2}" y="-2" width="7" height="8" rx="1.5" fill="{DARK}"/></g>')
    # ---- arms: shoulder (±sx) to hand
    swing = math.sin(sp * 2 + r.random())
    def arm(side, ang, ln=22, w=6):
        a = math.radians(ang)
        hx, hy = side * sx + math.sin(a) * ln * side, shoulder_y + math.cos(a) * ln
        hand = "" if lod else f'<circle cx="{_f(hx)}" cy="{_f(hy)}" r="3.6" fill="{head_c}" stroke="{DARK}" stroke-width="1.6"/>'
        return _limb(side * sx, shoulder_y, hx, hy, w, body) + hand, (hx, hy)
    hands = []
    if arms == "up":
        for side in (-1, 1):
            m, h = arm(side, 168 - 14 * math.sin(sp + side), 24); out.append(m); hands.append(h)
    elif arms == "one":
        m, h = arm(-1, 165 - 12 * math.sin(sp), 24); out.append(m); hands.append(h)
        m, h = arm(1, 24 + 6 * swing, 20); out.append(m)
    elif arms == "swing":
        for side in (-1, 1):
            m, h = arm(side, 32 + 22 * math.sin(sp + (side > 0) * math.pi), 20); out.append(m)
    elif arms == "horns":
        for side in (-1, 1):
            m, h = arm(side, 145 + 8 * math.sin(2 * sp), 18); out.append(m); hands.append(h)
    elif arms == "hug":
        for side in (-1, 1):
            m, h = arm(side, 118 + 4 * math.sin(sp), 16, 7); out.append(m)
    elif arms == "play":
        m, h = arm(1, 118 + 8 * math.sin(2 * sp), 20); out.append(m)
        m, h = arm(-1, 120, 22); out.append(m)
    elif arms == "type":
        out.append(f'<rect x="-24" y="{_f(hip - 8)}" width="48" height="6" rx="2" fill="#2b2b33" stroke="{DARK}" stroke-width="1.8"/><rect x="-20" y="{_f(hip + 0)}" width="4" height="{_f(foot_y - hip)}" fill="{DARK}"/><rect x="16" y="{_f(hip + 0)}" width="4" height="{_f(foot_y - hip)}" fill="{DARK}"/>')
        for side in (-1, 1):
            m, h = arm(side, 130 + 14 * math.sin(2 * sp + side), 22); out.append(m)
    elif arms == "drum":
        out.append(f'<ellipse cx="0" cy="{_f(hip - 6)}" rx="16" ry="5" fill="#5a4a38" stroke="{DARK}" stroke-width="2"/><rect x="-16" y="{_f(hip - 6)}" width="32" height="12" fill="#4a3a28" stroke="{DARK}" stroke-width="2"/>'
                   f'<ellipse cx="-27" cy="{_f(hip - 14)}" rx="8" ry="2.6" fill="#8a7a62" stroke="{DARK}" stroke-width="1.6"/><ellipse cx="27" cy="{_f(hip - 16)}" rx="8" ry="2.6" fill="#8a7a62" stroke="{DARK}" stroke-width="1.6"/>')
        for side in (-1, 1):
            m, h = arm(side, 140 + 30 * math.sin(2 * sp + (side > 0) * math.pi), 22); out.append(m)
    # ---- head
    hx, hy = sway * 0.3 + bang * 0.5, top - 10 * hs + bang * 0.4 + 2
    out.append(f'<rect x="{_f(hx - 2.5)}" y="{_f(top - 6)}" width="5" height="6" fill="{dark}"/>')
    out.append(f'<ellipse cx="{_f(hx)}" cy="{_f(hy)}" rx="{_f(10.5 * ws)}" ry="11" fill="{head_c}" stroke="{DARK}" stroke-width="2.2"/>')
    out.append(f'<path d="M{_f(hx - 8 * ws)} {_f(hy - 4)} Q{_f(hx)} {_f(hy - 15)} {_f(hx + 8 * ws)} {_f(hy - 4)} Q{_f(hx)} {_f(hy - 9)} {_f(hx - 8 * ws)} {_f(hy - 4)} Z" fill="{dark}"/>')   # a mat of mud for hair
    out.append(f'<circle cx="{_f(hx - 4)}" cy="{_f(hy - 1)}" r="2.4" fill="#f2e8d0"/><circle cx="{_f(hx + 4)}" cy="{_f(hy - 1)}" r="2.4" fill="#f2e8d0"/>'
               f'<circle cx="{_f(hx - 3.6)}" cy="{_f(hy - 0.6)}" r="1.1" fill="{DARK}"/><circle cx="{_f(hx + 4.4)}" cy="{_f(hy - 0.6)}" r="1.1" fill="{DARK}"/>')
    if scream:
        out.append(f'<ellipse cx="{_f(hx)}" cy="{_f(hy + 6)}" rx="3.4" ry="{_f(2.2 + 1.8 * abs(math.sin(sp)))}" fill="{DARK}"/>')
    else:
        out.append(f'<path d="M{_f(hx - 3.5)} {_f(hy + 6)} Q{_f(hx)} {_f(hy + 8)} {_f(hx + 3.5)} {_f(hy + 6)}" fill="none" stroke="{DARK}" stroke-width="1.6" stroke-linecap="round"/>')
    # ---- worms: on the head and shoulders, hanging off the arms, a couple on the chest
    spots = [(hx + r.uniform(-8, 8), hy - 9 + r.uniform(0, 2), r.uniform(200, 340)) for _ in range(r.randint(1, 3))]
    spots += [(side * sx * r.uniform(0.6, 1.0), shoulder_y + 1, 90 + side * r.uniform(-20, 40)) for side in (-1, 1) if r.random() < 0.8]
    spots += [(h[0], h[1] + 2, 90 + r.uniform(-30, 30)) for h in hands[:1]]
    spots += [(r.uniform(-7, 7), top + r.uniform(8, 20), r.uniform(0, 360)) for _ in range(r.randint(1, 3))]
    for k, (x, y, a) in enumerate(spots[:2] if lod else spots):
        out.append(_worm(x, y, a, r.uniform(8, 15), phase + k * 0.17, r.choice(WORMS), 2.4))
    ang = lean * 0.7 + sway * 0.4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -18 76 108" data-size="2.1,3"><g transform="translate(30 0) rotate({_f(ang)} 0 {foot_y})">'
            + "".join(out) + "</g></svg>")


def worm(variant=0, phase=0.0):
    """One worm on the ground, wriggling: viewBox 0 0 30 10."""
    r = random.Random(variant * 31 + 5)
    color = r.choice(WORMS)
    pts = []
    n = 14
    for i in range(n + 1):
        u = i / n
        pts.append((3 + 24 * u, 5 + 2.4 * math.sin(TAU * (u * 1.3 - phase)) * math.sin(math.pi * u) * (0.7 + 0.3 * r.random())))
    d = "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 10" data-size="3,1"><path d="{d}" fill="none" stroke="{DARK}" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def generate(seed):
    """The symbol: the standing figure of variant `seed`."""
    return ArtSvg(person(seed or 0, 0.0), "💩")
