"""Writes test.lvl: the sewer stage with the singer and a fast, random camera, for trying a song in the HTML player."""
import random
r = random.Random(7)
SEC = 300
out = ['''meta(width=96, height=30)
background("#2a2a22", "#4a4636")
K = "kmj/"
def 🟫 -> fill("#3b2f22"), solid:

def 🟤 -> fill("#2c2418"), bg:

def 🔲 -> fill("#00000000"):

def 🧍 -> kmj(K + "singer.kmj", "singer", fps=8, seconds=60, speed=2), size(14, 11):

for cx in range(0, 96):
    place(🟤, cx, 20)
    for cy in range(21, 30):
        place(🟫, cx, cy)
for cx in range(0, 96):
    for cy in range(0, 20):
        place(🟤, cx, cy)
scene("nin", seconds=%d, fps=24, view=(32, 18), bpm=170)
actor("singer", 🧍, 41, 9.5)
''' % SEC]
SING = (48, 15)
t = 0.0
shots = [(48, 15, 1.0), (48, 16, 2.4), (40, 17, 1.4), (58, 17, 1.4), (48, 13, 3.4), (36, 15, 1.2), (60, 15, 1.2), (48, 17, 1.0), (48, 15, 1.0), (48, 15, 1.6)]
while t < SEC:
    x, y, z = r.choice(shots)
    x += r.uniform(-3, 3); y += r.uniform(-1, 1); z *= r.uniform(0.9, 1.3)
    out.append(f"cut({t:.2f}, {x:.1f}, {y:.1f}, {z:.2f})")
    d = r.choice([0.12, 0.18, 0.25, 0.35, 0.5, 0.7])
    if r.random() < 0.5:
        out.append(f"punch({t:.2f}, {r.uniform(.08, .3):.2f}, {d:.2f})")
    if r.random() < 0.25:
        out.append(f'fx({t:.2f}, {t + d * 0.8:.2f}, "{r.choice(["glitch", "rgb", "flicker", "invert", "vhs", "zoom"])}", {r.uniform(.6, 1.5):.1f})')
    if r.random() < 0.15:
        out.append(f"shake({t:.2f}, {t + d:.2f}, {r.uniform(.2, .6):.2f})")
    t += d
out.append('fx(0, %d, "grain", 0.5)' % SEC)
out.append('fx(0, %d, "vignette", 1.0)' % SEC)
open("test.lvl", "w").write("\n".join(out) + "\n")
