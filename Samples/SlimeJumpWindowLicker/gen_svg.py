"""gen_svg.py: draws every SVG of the video into svg/ (python3 gen_svg.py).  The drawings are code, so a change is a tweak of a number."""
import math
import os
import random

from art import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "svg")
GREEN = "#8fe388"


def save(name, s):
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as fh:
        fh.write(s)


# ================================================================ the hero: a slime in a white leisure suit, with a cane and an umbrella
def hero(bob=0, lean=0, tilt=0, la=(-12, 6), ra=(12, 6), lf=-5, rf=5, rf_lift=0, lf_lift=0, bend=3, open_=0.2, cane=True, umbrella=0, shades=True, crazy=0.0, w=80, h=92):
    b = []
    hip_y, sh_y = 64 + bob, 46 + bob
    lx, rx = 40 + lean * 0.3, 40 + lean * 0.3
    # legs and shoes (behind the jacket)
    for side, fx, lift in ((-1, lf, lf_lift), (1, rf, rf_lift)):
        hx = 40 + side * 4 + lean * 0.2
        foot = (40 + side * 4 + fx, 88 - lift)
        b.append(limb((hx, hip_y), foot, bend * side * -0.5, "#fffdf4", sw=5.4))
        b.append(f'<ellipse cx="{f(foot[0] + side * 2.2)}" cy="{f(foot[1])}" rx="5.2" ry="2.7" fill="#201428" stroke="{OUT}" stroke-width="1.6"/>')
    # cane (held by the right hand) goes behind the arm
    rh = (40 + 9 + ra[0] + lean * 0.5, sh_y + ra[1])
    lh = (40 - 9 + la[0] + lean * 0.5, sh_y + la[1])
    if cane:
        tip = (rh[0] + 1.5, min(88, rh[1] + 30))
        b.append(line(rh[0], rh[1] - 3, tip[0], tip[1], "#2a1a3a", 3.4))
        b.append(line(rh[0], rh[1] - 3, tip[0], tip[1], "#c9c9d6", 1.8))
        b.append(circle(rh[0], rh[1] - 4, 3.2, "#e8e8f4", sw=1.6))
    # jacket
    b.append(poly([(29 + lean * 0.4, sh_y), (51 + lean * 0.4, sh_y), (53 + lean * 0.2, hip_y + 3), (27 + lean * 0.2, hip_y + 3)], "#fffdf4", sw=2.2, smooth=True))
    b.append(poly([(36 + lean * 0.4, sh_y), (44 + lean * 0.4, sh_y), (40 + lean * 0.4, sh_y + 11)], "#ffd84a", sw=1.6))      # the open shirt
    b.append(line(40 + lean * 0.3, sh_y + 11, 40 + lean * 0.2, hip_y + 2, OUT, 1.4))
    b.append(circle(40 + lean * 0.4, sh_y + 8, 1.2, "#ffb000", sw=0))                                                        # the gold chain
    # arms
    for side, hand in ((-1, lh), (1, rh)):
        b.append(limb((40 + side * 10 + lean * 0.4, sh_y + 2), hand, bend * side, "#fffdf4", sw=4.6))
        b.append(circle(hand[0], hand[1], 2.7, GREEN, sw=1.6))
    # the umbrella (left hand)
    if umbrella:
        ux, uy = lh
        b.append(line(ux, uy, ux - 2 + umbrella * 4, uy - 24, OUT, 2.2))
        top = (ux - 2 + umbrella * 4, uy - 24)
        r = 6 + 14 * umbrella
        b.append(f'<path d="M{f(top[0] - r)} {f(top[1] + 2)} Q{f(top[0])} {f(top[1] - r * 1.2)} {f(top[0] + r)} {f(top[1] + 2)} Q{f(top[0] + r * 0.5)} {f(top[1] - 1)} {f(top[0])} {f(top[1] + 3)} Q{f(top[0] - r * 0.5)} {f(top[1] - 1)} {f(top[0] - r)} {f(top[1] + 2)} Z" fill="#ff5a8a" stroke="{OUT}" stroke-width="2" stroke-linejoin="round"/>')
    # the head
    hx, hy = 40 + lean * 0.6, 27 + bob
    b.append(f'<g transform="rotate({f(tilt)} {f(hx)} {f(hy + 12)})">')
    b.append(blob(hx, hy, 19, 15, GREEN, n=11, wob=0.03, seed=5, flat=0.18, sw=2.4))
    b.append(grin(hx, hy + 1, s=0.98, open_=open_, shades=shades, crazy=crazy))
    b.append("</g>")
    return svg(w, h, "".join(b))


HERO_DANCE = [   # a jerky, rubbery dance, a pose at a time
    dict(lean=-5, tilt=-9, la=(-16, -14), ra=(14, 10), lf=-8, rf=7, rf_lift=0, open_=0.7),
    dict(lean=4, tilt=8, la=(-12, 8), ra=(16, -16), lf=-4, rf=9, lf_lift=7, bob=-2, open_=0.3, umbrella=0.4),
    dict(lean=7, tilt=12, la=(-18, -2), ra=(8, -20), lf=-9, rf=3, rf_lift=9, bob=-3, open_=0.9, umbrella=1.0),
    dict(lean=0, tilt=-3, la=(-10, 14), ra=(10, 14), lf=-2, rf=2, bob=3, open_=0.2, umbrella=1.0),
    dict(lean=-7, tilt=-12, la=(-14, -18), ra=(18, 2), lf=-10, rf=5, lf_lift=10, bob=-4, open_=1.0, umbrella=0.6),
    dict(lean=3, tilt=6, la=(-6, 10), ra=(16, 12), lf=-8, rf=8, bob=2, open_=0.5, umbrella=0.2),
    dict(lean=9, tilt=14, la=(-18, -10), ra=(4, -22), lf=-3, rf=10, rf_lift=11, bob=-3, open_=0.8, umbrella=0.9),
    dict(lean=-3, tilt=-6, la=(-12, 4), ra=(14, -4), lf=-6, rf=6, bob=0, open_=0.4),
]


def hero_gen():
    for i, p in enumerate(HERO_DANCE):
        save(f"hero_dance_{i:02d}.svg", hero(**p))
    strut = [dict(bob=0, lean=-1, ra=(10, 5)), dict(bob=-1.5, lean=0, lf=-3, rf=7, rf_lift=3), dict(bob=0, lean=1), dict(bob=-1.5, lean=0, lf=-7, rf=3, lf_lift=3)]
    for i, p in enumerate(strut):
        save(f"hero_strut_{i:02d}.svg", hero(open_=0.35, **p))
    save("hero_pose_00.svg", hero(lean=2, tilt=-4, la=(-8, 4), ra=(8, 4), open_=0.5, umbrella=0))
    save("hero_pose_01.svg", hero(lean=0, tilt=0, la=(-16, -26), ra=(16, -26), lf=-9, rf=9, bob=-2, open_=1.0, umbrella=0))     # arms up: ta-da


# ================================================================ the hero's face, big (for the close-ups)
def hero_face(open_=0.4, lick=0, w=220, h=160, shades=True, tongue=0.0, crazy=0.0, tilt=0):
    b = [f'<g transform="rotate({f(tilt)} 110 90)">']
    b.append(blob(110, 86, 96, 68, GREEN, n=12, wob=0.03, seed=7, flat=0.12, sw=4))
    b.append(grin(110, 86, s=3.8, open_=open_, shades=shades, crazy=crazy, eyes_y=-6.5))
    if tongue:
        b.append(f'<path d="M{f(95)} 118 q15 {f(34 * tongue)} 30 0 z" fill="#ff6a8c" stroke="{OUT}" stroke-width="3"/>')
    b.append("</g>")
    if lick:   # pressed against a window: glass over the face, a smear
        b = [blob(110, 86, 100 + 6 * lick, 72 - 4 * lick, GREEN, n=12, wob=0.02, seed=7, sw=4), grin(110, 86, s=4.0, open_=0.9, shades=True, eyes_y=-6.5),
             f'<path d="M92 122 q18 {f(46 * lick)} 36 0 q-18 {f(18 * lick)} -36 0 z" fill="#ff6a8c" stroke="{OUT}" stroke-width="3"/>',
             rect(0, 0, w, h, "#bfe9ff", sw=0, extra='opacity="0.35"'), f'<path d="M20 20 L70 8 L60 28 Z M150 130 L205 118 L196 142 Z" fill="#ffffff" opacity="0.55"/>',
             f'<ellipse cx="110" cy="132" rx="{f(40 * lick)}" ry="{f(10 * lick)}" fill="#ffffff" opacity="0.5"/>'] if lick else b
    return svg(w, h, "".join(b))


def face_gen():
    for i, o in enumerate((0.1, 0.5, 1.0, 0.6)):
        save(f"hero_face_{i:02d}.svg", hero_face(open_=o, tilt=(-3, 2, -2, 3)[i]))
    save("hero_face_nosh_00.svg", hero_face(open_=0.6, shades=False, crazy=0.4))
    save("hero_face_nosh_01.svg", hero_face(open_=0.9, shades=False, crazy=1.0, tilt=2))
    for i, l in enumerate((0.4, 0.8, 1.0)):
        save(f"hero_lick_{i:02d}.svg", hero_face(lick=l))


# ================================================================ the dancers: a pink (or yellow, blue, lilac) blob in a bikini, wearing the grin
def dancer(color=PINK, suit="#ff4f87", morph=1.0, sway=0, arms=(-1, -1), legs=(-6, 6), lift=0, bob=0, w=70, h=92, seed=3, bow=True):
    b = []
    cx = 35 + sway * 0.5
    for side, fx in ((-1, legs[0]), (1, legs[1])):
        foot = (35 + side * 5 + fx, 88 - (lift if side == 1 else 0))
        b.append(limb((35 + side * 5 + sway * 0.3, 66 + bob), foot, 2 * side, color, sw=4.4))
        b.append(f'<ellipse cx="{f(foot[0] + side * 2)}" cy="{f(foot[1])}" rx="4.6" ry="2.4" fill="#201428" stroke="{OUT}" stroke-width="1.5"/>')
    for side, a in ((-1, arms[0]), (1, arms[1])):
        sh = (35 + side * 13 + sway * 0.4, 52 + bob)
        hand = (sh[0] + side * (6 + 8 * abs(a)), sh[1] - a * 20)
        b.append(limb(sh, hand, 2 * side, color, sw=4.2))
        b.append(circle(hand[0], hand[1], 2.6, color, sw=1.5))
    b.append(blob(cx, 52 + bob, 21, 26, color, n=11, wob=0.03, seed=seed, flat=0.2, sw=2.4))
    # bikini
    b.append(f'<path d="M{f(cx - 14)} {f(56 + bob)} q14 8 28 0 l0 6 q-14 8 -28 0 z" fill="{suit}" stroke="{OUT}" stroke-width="1.8" stroke-linejoin="round"/>')
    b.append(f'<path d="M{f(cx - 11)} {f(69 + bob)} q11 7 22 0 l-3 7 q-8 3 -16 0 z" fill="{suit}" stroke="{OUT}" stroke-width="1.8" stroke-linejoin="round"/>')
    fy = 42 + bob
    if morph < 1:
        b.append(f'<g opacity="{f(1 - morph)}">{cute_face(cx, fy, 1.05, blush=suit)}</g>')
    if morph > 0:
        b.append(f'<g opacity="{f(min(1, morph * 1.4))}">{grin(cx, fy + 2, s=0.95 * (0.5 + 0.5 * morph), open_=0.5, shades=morph > 0.45, crazy=0.6)}</g>')
    if bow:
        b.append(poly([(cx + 4, 30 + bob), (cx - 6, 24 + bob), (cx - 6, 34 + bob)], suit, sw=1.5))
        b.append(poly([(cx + 4, 30 + bob), (cx + 14, 24 + bob), (cx + 14, 34 + bob)], suit, sw=1.5))
        b.append(circle(cx + 4, 30 + bob, 2.4, suit, sw=1.5))
    return svg(w, h, "".join(b))


DANCE = [dict(sway=-4, arms=(0.9, -0.2), legs=(-8, 5), bob=0), dict(sway=0, arms=(1, 1), legs=(-4, 4), bob=-3, lift=0), dict(sway=4, arms=(-0.2, 0.9), legs=(-5, 8), bob=0),
         dict(sway=0, arms=(0.3, 0.3), legs=(-9, 9), bob=3), dict(sway=-5, arms=(1, 0.5), legs=(-3, 7), bob=-2, lift=6), dict(sway=5, arms=(0.5, 1), legs=(-7, 3), bob=-2)]
COLORS = {"a": (PINK, "#ff4f87"), "b": (YELLOW, "#ff8a2a"), "c": (BLUE, "#2e7bff"), "d": (LILAC, "#8a4fff")}


def dancers_gen():
    for key, (c, s) in COLORS.items():
        for i, d in enumerate(DANCE):
            save(f"dancer_{key}_{i:02d}.svg", dancer(c, s, morph=1.0, seed=ord(key), **d))
    # the transformation: her own face slides into the grin over six steps, and at every step she can dance (6 poses)
    for i, m in enumerate((0.0, 0.2, 0.45, 0.7, 0.9, 1.0)):
        for k, d in enumerate(DANCE):
            save(f"morph_{i}_{k}.svg", dancer(PINK, "#ff4f87", morph=m, seed=97, **d))
            save(f"morphy_{i}_{k}.svg", dancer(YELLOW, "#ff8a2a", morph=m, seed=98, **d))
    save("girl_pink_00.svg", dancer(PINK, "#ff4f87", morph=0.0, seed=97))
    save("girl_yellow_00.svg", dancer(YELLOW, "#ff8a2a", morph=0.0, seed=98))


def dancer_face(color=PINK, morph=1.0, w=220, h=160, seed=9):
    b = [blob(110, 90, 92, 66, color, n=12, wob=0.03, seed=seed, flat=0.12, sw=4)]
    if morph < 1:
        b.append(f'<g opacity="{f(1 - morph)}">{cute_face(110, 92, 3.4, blush="#ff4f87")}</g>')
    if morph > 0:
        b.append(f'<g opacity="{f(min(1, morph * 1.4))}">{grin(110, 92, s=3.6, open_=0.6, shades=True)}</g>')
    return svg(w, h, "".join(b))


def dancer_face_gen():
    for i, m in enumerate((0.0, 0.3, 0.6, 0.85, 1.0)):
        save(f"dface_{i:02d}.svg", dancer_face(PINK, m))
        save(f"dface_y_{i:02d}.svg", dancer_face(YELLOW, m, seed=11))


# ================================================================ cars
def car_front(bounce=0, w=140, h=56):
    y = bounce
    b = [f'<path d="M4 {38 + y} Q4 {26 + y} 18 {26 + y} L120 {26 + y} Q136 {28 + y} 136 {40 + y} L136 {46 + y} L4 {46 + y} Z" fill="#35d0c9" stroke="{OUT}" stroke-width="2.6" stroke-linejoin="round"/>',
         f'<path d="M12 {36 + y} L128 {36 + y}" stroke="#fffbe8" stroke-width="3" stroke-linecap="round"/>',
         circle(124, 34 + y, 3.2, "#fff3a0", sw=1.6), rect(2, 36 + y, 6, 6, "#e8e8f4", r=2, sw=1.6), rect(132, 38 + y, 6, 6, "#e8e8f4", r=2, sw=1.6)]
    for cx in (32, 108):
        b.append(circle(cx, 48 + y * 0.3, 8.6, "#201428", sw=2))
        b.append(circle(cx, 48 + y * 0.3, 4, "#c9c9d6", sw=1.4))
    return svg(w, h, "".join(b))


def car_back(bounce=0, w=140, h=56):
    y = bounce
    b = [f'<path d="M14 {26 + y} L28 {10 + y} L72 {10 + y} L72 {26 + y} Z" fill="#1e8f8a" stroke="{OUT}" stroke-width="2.4" stroke-linejoin="round"/>',
         f'<path d="M72 {26 + y} L72 {8 + y} L96 {9 + y} L112 {26 + y} Z" fill="#bfe9ff" stroke="{OUT}" stroke-width="2.4" stroke-linejoin="round"/>',
         rect(24, 12 + y, 44, 16, "#ff5a8a", r=3, sw=2)]
    return svg(w, h, "".join(b))


def limo_front(w=460, h=62, glass_hole=(296, 340)):
    x0, x1 = glass_hole
    body = f"M10 40 Q4 20 24 18 L430 18 Q452 20 456 40 L456 52 L10 52 Z"
    hole = f"M{x0} 22 L{x1} 22 L{x1} 38 L{x0} 38 Z"
    b = [f'<path d="{body} {hole}" fill-rule="evenodd" fill="#fffdf4" stroke="{OUT}" stroke-width="2.6" stroke-linejoin="round"/>']
    for i in range(10):   # the long row of black windows
        a = 40 + i * 38
        if a + 30 > x0 - 4 and a < x1 + 4:
            continue
        b.append(rect(a, 22, 30, 15, "#1d1830", r=3, sw=1.8))
        b.append(line(a + 5, 26, a + 12, 26, "#6a6a9a", 1.4))
    b.append(rect(x0 - 2, 20, x1 - x0 + 4, 20, "none", r=3, sw=2))
    b.append(line(14, 42, 452, 42, "#e0d8c8", 2))
    b.append(circle(446, 36, 3.6, "#fff3a0", sw=1.6))
    b.append(circle(18, 36, 3, "#ff6a6a", sw=1.4))
    for cx in (70, 120, 360, 410):
        b.append(circle(cx, 52, 8.6, "#201428", sw=2))
        b.append(circle(cx, 52, 4, "#e8e8f4", sw=1.4))
    return svg(w, h, "".join(b))


def limo_back(w=460, h=62, glass_hole=(296, 340)):
    x0, x1 = glass_hole
    return svg(w, h, rect(x0 - 2, 20, x1 - x0 + 4, 20, "#3b1e55", sw=0) + rect(x0 + 4, 32, 14, 8, "#ff5a8a", r=3, sw=0) + circle(x0 + 30, 36, 3, "#ffd84a", sw=0))


def limo_glass(w=460, h=62, glass_hole=(296, 340)):
    x0, x1 = glass_hole
    return svg(w, h, rect(x0 - 1, 20, x1 - x0 + 2, 20, "#141026", r=2, sw=1.5, extra='opacity="0.96"') + f'<path d="M{x0 + 4} 40 L{x0 + 18} 20 L{x0 + 24} 20 L{x0 + 10} 40 Z" fill="#ffffff" opacity="0.22"/>')


# ================================================================ backgrounds
def sky(w, h, top, bottom, horizon):
    return f'<defs>{lin_grad("sk", [(0, top), (1, bottom)])}</defs><rect width="{w}" height="{horizon}" fill="url(#sk)"/>'


def palm(x, base, hgt, lean=8, seed=1, scale=1.0):
    r = random.Random(seed)
    top = (x + lean, base - hgt)
    b = [f'<path d="M{x - 4} {base} Q{x + lean * 0.2} {base - hgt * 0.5} {top[0] - 2} {top[1]} L{top[0] + 3} {top[1]} Q{x + lean * 0.5 + 4} {base - hgt * 0.5} {x + 5} {base} Z" fill="#a8734a" stroke="{OUT}" stroke-width="2.2"/>']
    for i, a in enumerate((-160, -125, -90, -55, -20, 15, 200)):
        L = (26 + r.random() * 8) * scale
        ang = math.radians(a)
        ex, ey = top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L * 0.7 + L * 0.35
        mx, my = top[0] + math.cos(ang) * L * 0.5, top[1] + math.sin(ang) * L * 0.5 - 8 * scale
        b.append(f'<path d="M{f(top[0])} {f(top[1])} Q{f(mx)} {f(my - 4)} {f(ex)} {f(ey)} Q{f(mx)} {f(my + 7)} {f(top[0])} {f(top[1])} Z" fill="#3fbf6a" stroke="{OUT}" stroke-width="2" stroke-linejoin="round"/>')
    b.append(circle(top[0] - 2, top[1] + 4, 3, "#7a4a2a", sw=1.4))
    b.append(circle(top[0] + 3, top[1] + 5, 3, "#7a4a2a", sw=1.4))
    return "".join(b)


def street_bg(w=640, h=210):
    b = [sky(w, h, "#7fd0ff", "#ffe8c0", 130)]
    b.append(f'<path d="M0 118 Q60 80 130 112 T270 104 T420 110 T560 96 T640 112 L640 150 L0 150 Z" fill="#cfa9e0" stroke="{OUT}" stroke-width="2"/>')
    cols = ["#ffb3a7", "#ffe08a", "#a8e6cf", "#a8c8ff", "#ffc4ec", "#ffd3a1", "#b9a8ff"]
    r = random.Random(4)
    x = -10
    i = 0
    while x < w:
        bw = 82 + r.random() * 30
        bh = 52 + r.random() * 46
        top = 150 - bh
        col = cols[i % len(cols)]
        b.append(rect(x, top, bw, bh, col, r=2, sw=2.4))
        for wy in range(int(top + 8), 120, 17):
            for wx in range(int(x + 9), int(x + bw - 14), 19):
                b.append(rect(wx, wy, 11, 10, "#8fd8ff" if r.random() > 0.2 else "#ffe27a", r=1.5, sw=1.4))
        aw = ["#ff4f87", "#2e7bff", "#ffb000"][i % 3]
        b.append(f'<path d="M{f(x - 2)} 132 L{f(x + bw + 2)} 132 L{f(x + bw - 4)} 148 L{f(x + 4)} 148 Z" fill="{aw}" stroke="{OUT}" stroke-width="2"/>')
        for sx in range(int(x + 8), int(x + bw - 6), 14):
            b.append(line(sx, 132, sx - 2, 148, "#ffffff", 3))
        x += bw + 4
        i += 1
    for px, s in ((40, 1), (230, 2), (455, 3), (610, 4)):
        b.append(palm(px, 168, 92 + (s % 2) * 14, lean=10 if s % 2 else -10, seed=s))
    b.append(rect(0, 150, w, 22, "#d9d3e6", sw=2.4))
    for sx in range(0, w, 44):
        b.append(line(sx, 150, sx + 8, 172, "#b8b0cc", 1.6))
    b.append(rect(0, 170, w, 6, "#a49cb8", sw=2))
    b.append(rect(0, 176, w, 34, "#514a68", sw=0))
    for dx in range(10, w, 60):
        b.append(rect(dx, 192, 34, 4, "#ffd84a", r=2, sw=0))
    return svg(w, h, "".join(b))


def beach_bg(w=640, h=210):
    b = [sky(w, h, "#5cc8ff", "#fff0b8", 112)]
    b.append(f'<g transform="translate(470 54)">' + "".join(f'<path d="M0 0 L{f(math.cos(a) * 70)} {f(math.sin(a) * 70)} L{f(math.cos(a + 0.12) * 70)} {f(math.sin(a + 0.12) * 70)} Z" fill="#fff59a"/>' for a in [i * math.pi / 8 for i in range(16)]) + circle(0, 0, 30, "#ffd84a", sw=3) + "</g>")
    b.append(rect(0, 100, w, 46, "#3a9dff", sw=0))
    for j, y in enumerate((108, 120, 133)):
        for wx in range(-10 + j * 14, w, 38):
            b.append(f'<path d="M{wx} {y} q9 -8 19 0 q9 8 19 0" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" opacity="0.85"/>')
    b.append(f'<path d="M60 100 l30 0 l-6 10 l-18 0 z" fill="#ff5a8a" stroke="{OUT}" stroke-width="2"/><path d="M75 100 l0 -26 l16 22 z" fill="#fffdf4" stroke="{OUT}" stroke-width="2"/>')
    b.append(f'<path d="M0 140 Q80 130 180 142 T400 140 T640 142 L640 210 L0 210 Z" fill="#ffe3a8" stroke="{OUT}" stroke-width="2.4"/>')
    r = random.Random(8)
    for _ in range(90):
        b.append(circle(r.random() * w, 150 + r.random() * 58, 1.1, "#e7bf7a", sw=0))
    for px, s in ((20, 1), (180, 2), (400, 3), (590, 4)):
        b.append(palm(px, 164, 100 + (s % 2) * 18, lean=14 if s % 2 else -14, seed=s + 10))
    for ux, col in ((120, "#ff4f87"), (330, "#2e7bff"), (520, "#ffb000")):
        b.append(line(ux, 172, ux + 6, 128, OUT, 2.4))
        b.append(f'<path d="M{ux - 26} 132 Q{ux + 6} 108 {ux + 38} 132 Z" fill="{col}" stroke="{OUT}" stroke-width="2.2" stroke-linejoin="round"/><path d="M{ux + 6} 112 L{ux + 6} 132 M{ux - 10} 124 L{ux - 4} 132 M{ux + 22} 124 L{ux + 16} 132" stroke="#fff" stroke-width="2.4"/>')
    for gx, gy in ((250, 60), (290, 74), (160, 50)):
        b.append(f'<path d="M{gx - 8} {gy} q8 -8 8 0 q0 -8 8 0" fill="none" stroke="{OUT}" stroke-width="2" stroke-linecap="round"/>')
    return svg(w, h, "".join(b))


def interior_bg(w=640, h=210):
    b = [rect(0, 0, w, h, "#2a1448", sw=0)]
    r = random.Random(12)
    for i in range(34):
        b.append(circle(r.random() * w, 6 + r.random() * 96, 2 + r.random() * 6, ["#ff5ac8", "#5ad8ff", "#ffe45a", "#b07aff"][i % 4], sw=0, extra=f'opacity="{f(0.25 + r.random() * 0.5)}"'))
    b.append(rect(0, 100, w, 8, "#ff5ac8", sw=0))
    b.append(rect(0, 112, w, 4, "#5ad8ff", sw=0))
    for wx in range(30, w, 150):
        b.append(rect(wx, 22, 100, 62, "#1a0a30", r=10, sw=2.4))
        for _ in range(14):
            b.append(circle(wx + 6 + r.random() * 88, 28 + r.random() * 50, 1.5 + r.random() * 3, ["#ffe45a", "#ff8ae0", "#8ae8ff"][_ % 3], sw=0, extra='opacity="0.8"'))
    b.append(f'<path d="M0 134 Q320 116 640 134 L640 210 L0 210 Z" fill="#7a2a7a" stroke="{OUT}" stroke-width="2.6"/>')
    for sx in range(20, w, 60):
        b.append(f'<path d="M{sx} 140 L{sx} 206" stroke="#5a1a5a" stroke-width="2"/>')
        b.append(circle(sx, 148, 2.4, "#ffd84a", sw=0))
    b.append(rect(0, 170, w, 40, "#3d1a52", sw=0, extra='opacity="0.7"'))
    return svg(w, h, "".join(b))


def sunburst(w, h, c1, c2, n=20, dot=None):
    cx, cy = w / 2, h / 2
    R = math.hypot(w, h)
    b = [rect(0, 0, w, h, c1, sw=0)]
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 0.5) / n
        b.append(f'<path d="M{f(cx)} {f(cy)} L{f(cx + math.cos(a0) * R)} {f(cy + math.sin(a0) * R)} L{f(cx + math.cos(a1) * R)} {f(cy + math.sin(a1) * R)} Z" fill="{c2}"/>')
    if dot:
        r = random.Random(1)
        for _ in range(26):
            b.append(circle(r.random() * w, r.random() * h, 3 + r.random() * 5, dot, sw=0, extra='opacity="0.6"'))
    return svg(w, h, "".join(b))


# ================================================================ props
def champagne(spray=0.0, shake=0, w=60, h=90):
    b = []
    tilt = -18 + shake
    b.append(f'<g transform="rotate({f(tilt)} 30 80)">')
    b.append(f'<path d="M20 80 L20 44 Q20 36 26 30 L26 14 L34 14 L34 30 Q40 36 40 44 L40 80 Z" fill="#2c8a4a" stroke="{OUT}" stroke-width="2.4" stroke-linejoin="round"/>')
    b.append(rect(25, 12, 10, 8, "#ffd84a", r=1.5, sw=1.8))
    b.append(rect(21, 56, 18, 14, "#fff3c0", r=2, sw=1.6))
    b.append(circle(30, 63, 3, "#ff4f87", sw=0))
    if spray > 0:
        r = random.Random(5)
        b.append(f'<g transform="rotate({f(-tilt)} 30 80)">')
        for i in range(int(6 + 18 * spray)):
            t = i / max(1, int(6 + 18 * spray))
            a = math.radians(-100 + 40 * (r.random() - 0.5) + 25 * t)
            d = (8 + 70 * spray) * (0.3 + 0.7 * t) * (0.8 + 0.4 * r.random())
            x, y = 30 + math.cos(a) * d * 0.7, 12 + math.sin(a) * d
            b.append(circle(x, y, 2.4 + 4 * r.random() * (1 - t * 0.4), "#fffdf4", sw=1.1))
        b.append("</g>")
    b.append("</g>")
    return svg(w, h, "".join(b))


def boombox(pulse=0, w=60, h=36):
    b = [rect(3, 8, 54, 26, "#6a6a82", r=5, sw=2.4), rect(10, 3, 40, 6, "#c9c9d6", r=3, sw=2)]
    for cx in (17, 43):
        b.append(circle(cx, 21, 9 + pulse, "#2a2a3a", sw=2))
        b.append(circle(cx, 21, 4 + pulse * 0.7, "#9a9ab2", sw=1.5))
    b.append(rect(25, 14, 10, 6, "#ffd84a", r=1, sw=1.4))
    return svg(w, h, "".join(b))


def arch(w=100, h=100):
    b = [rect(6, 24, 12, 74, "#ffffff", r=3, sw=2.6), rect(82, 24, 12, 74, "#ffffff", r=3, sw=2.6),
         f'<path d="M6 30 Q50 -14 94 30 L94 44 Q50 4 6 44 Z" fill="#ff8fc7" stroke="{OUT}" stroke-width="2.6" stroke-linejoin="round"/>']
    for i, cx in enumerate((20, 34, 50, 66, 80)):
        b.append(circle(cx, 28 - 12 * math.sin(math.pi * (cx - 6) / 88) + 6, 5, ["#ffd84a", "#ff4f87", "#fff", "#ff4f87", "#ffd84a"][i], sw=1.6))
    return svg(w, h, "".join(b))


def veil_girl(w=70, h=92):
    return dancer(PINK, "#ffffff", morph=1.0, arms=(0.2, 0.2), legs=(-4, 4), seed=3, bow=False).replace("</svg>", f'<path d="M20 28 Q35 8 50 28 L58 70 Q35 60 12 70 Z" fill="#ffffff" opacity="0.7" stroke="{OUT}" stroke-width="1.8"/></svg>')


def main():
    hero_gen()
    face_gen()
    dancers_gen()
    dancer_face_gen()
    for i, y in enumerate((0, 1.5)):
        save(f"car_front_{i:02d}.svg", car_front(y))
        save(f"car_back_{i:02d}.svg", car_back(y))
    save("limo_front.svg", limo_front())
    save("limo_back.svg", limo_back())
    save("limo_glass.svg", limo_glass())
    save("street_bg.svg", street_bg())
    save("beach_bg.svg", beach_bg())
    save("interior_bg.svg", interior_bg())
    for name, c1, c2 in (("hero", "#ffd84a", "#ffb000"), ("pink", "#ff8fc7", "#ffc7e6"), ("lime", "#7ee8b5", "#c8ffe0"), ("blue", "#6ec6ff", "#bfe7ff"), ("lilac", "#c7a3ff", "#e6d6ff"), ("teal", "#5fe0d0", "#b8fff4"), ("orange", "#ff9a4a", "#ffd0a8"), ("red", "#ff5a5a", "#ffb0b0"), ("purple", "#8a5aff", "#d0b8ff"), ("sun", "#ffe45a", "#ff9a4a")):
        save(f"room_{name}.svg", sunburst(320, 180, c1, c2, dot="#ffffff"))
    for i, (s, sh) in enumerate(((0, 0), (0.15, 3), (0.5, -3), (0.9, 4), (1.0, -2), (0.7, 2), (0.35, -4), (0.1, 0))):
        save(f"champagne_{i:02d}.svg", champagne(s, sh))
    for i, p in enumerate((0, 2.2, 0.8)):
        save(f"boombox_{i:02d}.svg", boombox(p))
    save("arch.svg", arch())
    save("bride.svg", veil_girl())
    print("wrote", len(os.listdir(OUTDIR)), "svg files to", OUTDIR)


if __name__ == "__main__":
    main()
