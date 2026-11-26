"""Draws the frames of AphexNIN into svg/ (run from this folder: python3 make_assets.py). It reuses the drawing code of its two parents:

  Samples/NIN2                     the sewer stage: the wall and the pipes (🚽), mud and rain, speakers, rigs with blinking lights, the hunched band, the fog
  Samples/SlimeJumpWindowLicker    the hero (a slime in a white suit), the grinning faces, the rooms (sunbursts, a wall of faces, televisions, a ring of faces)

and adds artlib/👯.py, the mud girls:
  svg/girl_V_F.svg        V 0..5, F 0..11  the audience: dancing, head-banging 3 times a loop (every other one throws mud)
  svg/girlfar_V_F.svg     V 0..5, F 0..5   the same, simpler: the back rows
  svg/stagegirl_V_F.svg   V 0..3, F 0..15  bigger and faster: the girls dancing on the speakers
  svg/mudface_V_F.svg     V 0..3, F 0..5   a girl's face, big, chewing (for the close-up rooms)
  svg/hero_*.svg          the hero and his faces, muddied (the originals are not touched)
"""
import importlib.util
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "svg")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "tools"))
WL_DIR = os.path.join(REPO, "Samples", "SlimeJumpWindowLicker")
sys.path.insert(0, WL_DIR)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nin = load("nin2_assets", os.path.join(REPO, "Samples", "NIN2", "make_assets.py"))
wl = load("wl_gen_svg", os.path.join(WL_DIR, "gen_svg.py"))
girls = load("mud_girls", os.path.join(REPO, "artlib", "👯.py"))
nin.OUT = OUT
wl.OUTDIR = OUT
if os.path.isdir(os.path.join(REPO, "Samples", "NIN2", "svg")) and not os.listdir(os.path.join(REPO, "Samples", "NIN2", "svg")):
    os.rmdir(os.path.join(REPO, "Samples", "NIN2", "svg"))          # (importing NIN2's script made an empty folder)


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def mudify(name, seed, amount, band):
    """Lays mud over one of the hero's drawings (the file in svg/ is rewritten: the originals in the other sample stay as they are)."""
    path = os.path.join(OUT, name)
    text = open(path, encoding="utf-8").read()
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    w, h = float(m.group(1)), float(m.group(2))
    text = text.replace("</svg>", f"<g>{girls.mud_over(w, h, seed, amount, band)}</g></svg>")
    write(name, text)


def girl_frames():
    for v in range(6):
        for f in range(12):
            write(f"girl_{v}_{f}.svg", girls.girl(v, f / 12, cycles=3, throw=(v % 2 == 0)))
        for f in range(6):
            write(f"girlfar_{v}_{f}.svg", girls.girl(v, f / 6, cycles=3, lod=1))
    for v in range(4):
        for f in range(16):
            write(f"stagegirl_{v}_{f}.svg", girls.girl(6 + v, f / 16, mud=0.6, cycles=4))
        for f in range(6):
            write(f"mudface_{v}_{f}.svg", girls.face(v, (0.1, 0.4, 0.8, 1.0, 0.7, 0.3)[f]))


def hero_frames():
    wl.hero_gen()
    wl.face_gen()
    for i in range(6):
        wl.save(f"hero_fish_{i:02d}.svg", wl.fisheye(i))
    for col in ("red", "blue"):
        for lv in range(4):
            wl.save(f"hero_lit_{col}_{lv:02d}.svg", wl.lit(col, lv, open_=(0.4, 0.8, 1.0, 0.6)[lv]))
    for i in range(8):
        mudify(f"hero_dance_{i:02d}.svg", 100 + i, 0.8, False)
    for i in range(4):
        mudify(f"hero_strut_{i:02d}.svg", 120 + i, 0.8, False)
        mudify(f"hero_face_{i:02d}.svg", 130 + i, 1.0, "cap")
    for i in range(3):
        mudify(f"hero_lick_{i:02d}.svg", 140 + i, 1.0, "cap")
    for col in ("red", "blue"):
        for lv in range(4):
            mudify(f"hero_lit_{col}_{lv:02d}.svg", 150 + lv, 0.9, False)
    for i in range(6):
        mudify(f"hero_fish_{i:02d}.svg", 160 + i, 0.9, False)


def rooms():
    for name, c1, c2 in (("hero", "#ffd84a", "#ffb000"), ("pink", "#ff8fc7", "#ffc7e6"), ("lime", "#7ee8b5", "#c8ffe0"), ("blue", "#6ec6ff", "#bfe7ff"), ("lilac", "#c7a3ff", "#e6d6ff"),
                         ("orange", "#ff9a4a", "#ffd0a8"), ("red", "#ff5a5a", "#ffb0b0")):
        wl.save(f"room_{name}.svg", wl.sunburst(320, 180, c1, c2, dot="#ffffff"))
    for i in range(4):
        wl.save(f"facewall_{i:02d}.svg", wl.facewall(i))
        wl.save(f"tvwall_{i:02d}.svg", wl.tvwall(i))
        wl.save(f"static_{i:02d}.svg", wl.static(i))
    for i in range(6):
        wl.save(f"spinring_{i:02d}.svg", wl.spinring(i))


if __name__ == "__main__":
    nin.crowd()
    nin.hardware()
    nin.fog()
    nin.mud_water()
    nin.fall()
    nin.rain("rain_near", 400, 26, 1.5, "#aebccb", 2, seed=1)
    nin.rain("rain_far", 900, 12, 0.9, "#78858f", 1, seed=2)
    nin.wall()
    print("pipes picture is", nin.pipes(), "cells")
    girl_frames()
    hero_frames()
    rooms()
    print("wrote", len(os.listdir(OUT)), "svg files in", OUT)
