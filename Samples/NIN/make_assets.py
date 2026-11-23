"""Draws the frames of the animated scenery of the sewer stage (run from this folder: python3 make_assets.py).

  svg/crowd_V_F.svg    mud people (artlib/💩.py), V = 0..5 the audience, F = 0..7 the dance
  svg/crowdfar_V_F.svg  the same people, simpler (lod=1), 4 frames: for the back rows
  svg/band_ROLE_F.svg  the band
  svg/worm_V_F.svg     a worm on the ground
  svg/mud_F.svg        the muddy water, 8 cells wide, flows to the right (seamless); svg/fall_F.svg: a stream falling (seamless)
  svg/rain_near_F.svg, svg/rain_far_F.svg   the rain over the whole picture (40 x 22 cells), seamless
  svg/mouth.svg, svg/wall.svg   the sewer's concrete wall and the arched mouth
"""
import importlib.util
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools"))
spec = importlib.util.spec_from_file_location("mud_people", os.path.join(REPO, "artlib", "💩.py"))
mud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mud)
OUT = os.path.join(HERE, "svg")
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)


def crowd():
    for v in range(6):
        for f in range(8):
            write(f"crowd_{v}_{f}.svg", mud.person(v + 1, f / 8, "crowd"))
    for v in range(6):                                          # the far rows: a simpler drawing, 4 frames
        for f in range(4):
            write(f"crowdfar_{v}_{f}.svg", mud.person(v + 1, f / 4, "crowd", lod=1))
    for i, role in enumerate(("guitar", "bass", "drums", "keys")):
        for f in range(8):
            write(f"band_{role}_{f}.svg", mud.person(40 + i, f / 8, role))
    for v in range(3):
        for f in range(8):
            write(f"worm_{v}_{f}.svg", mud.worm(v, f / 8))


def mud_water(frames=12):
    """Muddy water: 80 x 20 units (8 x 2 cells). Streaks and floating scum slide to the right; rain rings open on the surface."""
    r = random.Random(3)
    streaks = [(r.uniform(0, 80), r.uniform(5, 18), r.uniform(10, 26), r.choice(["#6b4a26", "#3a2412", "#7d5c36", "#4a3018"])) for _ in range(9)]
    chunks = [(r.uniform(0, 80), r.uniform(4, 9), r.uniform(1.5, 3.5)) for _ in range(5)]
    rings = [(r.uniform(4, 76), r.uniform(5, 9), r.random()) for _ in range(5)]
    for f in range(frames):
        p = f / frames
        o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20" data-size="8,2">',
             '<rect x="0" y="4" width="80" height="16" fill="#4a3018"/>']
        for k in (-80, 0):
            o.append('<path d="M0 4 ' + " ".join(f"Q{x + 5 + k + 80 * p:g} {4 - 1.8 * (1 if (x // 10) % 2 else -1):g} {x + 10 + k + 80 * p:g} 4" for x in range(0, 80, 10)) + ' L160 20 L-80 20 Z" fill="#4a3018"/>')
        for x, y, ln, c in streaks:
            for k in (-80, 0, 80):
                xx = (x + 80 * p) % 80 + k
                if -30 < xx < 110:
                    o.append(f'<path d="M{xx:g} {y:g} q{ln * .3:g} -1.4 {ln * .6:g} 0 t{ln * .4:g} 0" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>')
        for x, y, s in chunks:
            for k in (-80, 0, 80):
                xx = (x + 80 * p * 0.6) % 80 + k
                o.append(f'<ellipse cx="{xx:g}" cy="{y:g}" rx="{s:g}" ry="{s * .5:g}" fill="#2e1d0c"/>')
        for x, y, off in rings:
            u = (p + off) % 1
            o.append(f'<ellipse cx="{x:g}" cy="{y:g}" rx="{1 + 4 * u:g}" ry="{0.4 + 1.3 * u:g}" fill="none" stroke="#a89878" stroke-width="{1.0 * (1 - u):.2f}"/>')
        o.append('<path d="M0 4 ' + " ".join(f"Q{x + 5 + 80 * p:g} {4 - 1.8 * (1 if (x // 10) % 2 else -1):g} {x + 10 + 80 * p:g} 4" for x in range(-80, 160, 10)).replace("Q", "L", 0) + '" fill="none" stroke="#9a8460" stroke-width="1"/>')
        o.append("</svg>")
        write(f"mud_{f}.svg", "".join(o))


def fall(frames=12):
    """Mud pouring over the lip: 20 x 80 units (2 x 8 cells), stripes sliding down."""
    r = random.Random(5)
    stripes = [(r.uniform(1, 19), r.uniform(0, 80), r.uniform(14, 30), r.choice(["#6b4a26", "#3a2412", "#7d5c36"])) for _ in range(10)]
    for f in range(frames):
        p = f / frames
        o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 80" data-size="2,8"><rect x="0" y="0" width="20" height="80" fill="#4a3018"/>']
        for x, y, ln, c in stripes:
            for k in (-80, 0):
                yy = (y + 160 * p) % 80 + k
                o.append(f'<line x1="{x:g}" y1="{yy:g}" x2="{x:g}" y2="{yy + ln:g}" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>')
        o.append("</svg>")
        write(f"fall_{f}.svg", "".join(o))


def rain(name, n, length, width, color, speed, frames=12, seed=1):
    """Rain over the picture (1200 x 660 units = 120 x 66 cells, so it covers the screen at any zoom): streaks fall (a little slanted) and wrap, so the loop is seamless."""
    r = random.Random(seed)
    H = 660
    drops = [(r.uniform(-30, 1260), r.uniform(0, H), length * r.uniform(0.8, 1.3)) for _ in range(n)]
    for f in range(frames):
        o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 660" data-size="120,66">']
        for x, y, ln in drops:
            yy = (y + H * speed * f / frames) % H
            for k in ((-H, 0) if yy + ln > H else (0,)):
                y0 = yy + k
                o.append(f'<line x1="{x - (y0 - 0) * 0.12:g}" y1="{y0:g}" x2="{x - (y0 + ln) * 0.12:g}" y2="{y0 + ln:g}" stroke="{color}" stroke-width="{width:g}" stroke-linecap="round"/>')
        o.append("</svg>")
        write(f"{name}_{f}.svg", "".join(o))


def wall():
    """The concrete headwall (400 x 330 units = 50 x 41 cells... drawn 52 x 46 cells) with the arched mouth, grate bars and wet stains."""
    W, H = 520, 460
    r = random.Random(9)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" data-size="52,46">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#53575a"/>']
    for y in range(0, H, 46):                                  # concrete panels
        o.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#3a3d40" stroke-width="2.5"/>')
        for x in range((y // 46 % 2) * 65, W, 130):
            o.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 46}" stroke="#3a3d40" stroke-width="2"/>')
    for _ in range(40):                                        # patches and stains
        x, y = r.uniform(0, W), r.uniform(0, H - 60)
        o.append(f'<rect x="{x:g}" y="{y:g}" width="{r.uniform(10, 40):g}" height="{r.uniform(8, 20):g}" fill="{r.choice(["#5d6164", "#494d50", "#4d5452"])}"/>')
    for _ in range(26):                                        # wet streaks running down
        x = r.uniform(0, W)
        o.append(f'<path d="M{x:g} 0 L{x + r.uniform(-8, 8):g} {r.uniform(120, 420):g}" stroke="#35402f" stroke-width="{r.uniform(2, 7):g}" stroke-linecap="round" fill="none"/>')
    cx, base, rw, rh = 260, H, 190, 270                        # the mouth
    o.append(f'<path d="M{cx - rw - 26} {base} L{cx - rw - 26} {base - rh + 40} A{rw + 26} {rw + 26} 0 0 1 {cx + rw + 26} {base - rh + 40} L{cx + rw + 26} {base} Z" fill="#6b6f72" stroke="#26282a" stroke-width="6"/>')
    o.append(f'<path d="M{cx - rw} {base} L{cx - rw} {base - rh + 40} A{rw} {rw} 0 0 1 {cx + rw} {base - rh + 40} L{cx + rw} {base} Z" fill="#0b0a0c" stroke="#26282a" stroke-width="5"/>')
    for k in range(-4, 5):                                     # the keystones
        a = math.radians(90 + k * 17)
        x1, y1 = cx + math.cos(a) * (rw + 26), base - rh + 40 - math.sin(a) * (rw + 26)
        x2, y2 = cx + math.cos(a) * rw, base - rh + 40 - math.sin(a) * rw
        o.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="#26282a" stroke-width="4"/>')
    for x in range(cx - rw + 30, cx + rw, 38):                 # a rusty grate hanging half open at the top
        o.append(f'<line x1="{x}" y1="{base - rh - rw + 60 + abs(x - cx) * 0.35:g}" x2="{x}" y2="{base - rh + 90:g}" stroke="#3a2a22" stroke-width="5"/>')
    o.append(f'<rect x="{cx - rw}" y="{base - rh + 86}" width="{2 * rw}" height="9" fill="#3a2a22"/>')
    o.append(f'<path d="M{cx - rw + 6} {base - 6} L{cx - rw + 6} {base - 120} M{cx + rw - 6} {base - 6} L{cx + rw - 6} {base - 150}" stroke="#16181a" stroke-width="3" fill="none"/>')
    o.append("</svg>")
    write("wall.svg", "".join(o))


def pipes(left=260, top=100, seed=4):
    """artlib/🚽.py: the toilet on its pipes, with the pipes running on to the edge of the wall (13 + 5 cells more)."""
    from kaomojilang.artlib import ArtSvg
    sp = importlib.util.spec_from_file_location("toilet_pipes", os.path.join(REPO, "artlib", "🚽.py"))
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    toilet = ArtSvg(open(os.path.join(REPO, "artlib", "🚽.svg"), encoding="utf-8").read(), "🚽.svg")
    art = mod.build(toilet, seed, left, top)
    write("pipes.svg", art.text)
    return art.size


if __name__ == "__main__":
    crowd()
    mud_water()
    fall()
    rain("rain_near", 400, 26, 1.5, "#aebccb", 2, seed=1)
    rain("rain_far", 900, 12, 0.9, "#78858f", 1, seed=2)
    wall()
    print("pipes picture is", pipes(), "cells")
    print("wrote", len(os.listdir(OUT)), "svg files in", OUT)
