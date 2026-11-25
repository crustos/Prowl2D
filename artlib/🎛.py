"""Synths, drum machines and racks, played by hunched mud people: a rig that animates (a loop of `phase` 0..1; 16 frames work well).

`rig(kind, phase, variant)` is an SVG text (viewBox 0 0 200 130, data-size 10 x 6.5 cells). kind:

  "synth"  a modular panel with patch cables, a scope, a row of sliders and a keyboard
  "drum"   a drum machine: 4 x 4 pads that light with the sequencer, knobs, a step row and a screen
  "rack"   three rack units: VU meters, a LED matrix and spectrum bars

Everything moves: the step lights run (one step per 1/16 of the loop), knobs turn, sliders slide, the scope draws, the VU needles bounce, patch cables swing, and a
hunched player behind it bangs his head (4 times per loop, under a curtain of muddy hair) while his muddy hands, with worms on them, work the sliders, knobs and pads.
`hands_only=True` draws only the player and his hands (to lay over the same rig drawn on its own, if the two need to be tiles of their own).

As a symbol, 🎛 draws the synth rig, with `seed` as the variant.
"""
import math
import random

from kaomojilang.artlib import ArtSvg

TAU = 2 * math.pi
DARK, PANEL, CHASSIS, METAL = "#14151a", "#2b2d33", "#3a3d45", "#9096a0"
LED = {"r": "#ff3030", "g": "#46ff6a", "a": "#ffb020", "b": "#40a8ff", "m": "#ff40d0"}
MUD, MUD2, MUDH = "#4a3018", "#3a2310", "#7d5c36"
WORM = ["#d98c8c", "#c9786b", "#e0a090"]


def _f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def hsh(*a):
    """A cheap repeatable noise in 0..1."""
    x = 0
    for v in a:
        x = (x * 31 + int(v * 977)) & 0xFFFFFFF
    x = (x ^ (x >> 7)) * 2654435761 & 0xFFFFFFFF
    return (x % 10007) / 10007.0


def knob(x, y, r, ang, col="#c9ccd2"):
    a = math.radians(ang)
    ticks = "".join(f'<circle cx="{_f(x + math.cos(math.radians(-225 + 270 * i / 8)) * (r + 2.6))}" cy="{_f(y + math.sin(math.radians(-225 + 270 * i / 8)) * (r + 2.6))}" r="0.7" fill="#e8e8ea"/>' for i in range(9))
    return (f'{ticks}<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r + 0.8)}" fill="{DARK}"/><circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="{col}" stroke="{DARK}" stroke-width="0.6"/>'
            f'<line x1="{_f(x)}" y1="{_f(y)}" x2="{_f(x + math.cos(a) * r * 0.9)}" y2="{_f(y + math.sin(a) * r * 0.9)}" stroke="{DARK}" stroke-width="1.3" stroke-linecap="round"/>')


def slider(x, y, L, pos, col="#d8d8dc"):
    cy = y + pos * L
    return (f'<rect x="{_f(x - 1.1)}" y="{_f(y - 1)}" width="2.2" height="{_f(L + 2)}" rx="1" fill="{DARK}"/><rect x="{_f(x - 3.6)}" y="{_f(cy - 2.2)}" width="7.2" height="4.4" rx="0.9" fill="{col}" stroke="{DARK}" stroke-width="0.6"/>'
            f'<line x1="{_f(x - 3)}" y1="{_f(cy)}" x2="{_f(x + 3)}" y2="{_f(cy)}" stroke="{DARK}" stroke-width="0.7"/>')


def led(x, y, on, c="r"):
    col = LED[c]
    if on:
        return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="3.6" fill="{col}" opacity="0.35"/><circle cx="{_f(x)}" cy="{_f(y)}" r="1.8" fill="{col}"/><circle cx="{_f(x - 0.5)}" cy="{_f(y - 0.5)}" r="0.6" fill="#ffffff"/>'
    return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="1.8" fill="#3a2a2e" stroke="{DARK}" stroke-width="0.4"/>'


def vu(x, y, w, h, level):
    a = math.radians(-50 + 100 * level)
    cx, cy = x + w / 2, y + h - 3
    ticks = "".join(f'<line x1="{_f(cx + math.sin(math.radians(-50 + 100 * i / 6)) * h * 0.6)}" y1="{_f(cy - math.cos(math.radians(-50 + 100 * i / 6)) * h * 0.6)}" x2="{_f(cx + math.sin(math.radians(-50 + 100 * i / 6)) * h * 0.78)}" y2="{_f(cy - math.cos(math.radians(-50 + 100 * i / 6)) * h * 0.78)}" stroke="{"#c03020" if i > 4 else "#403828"}" stroke-width="0.8"/>' for i in range(7))
    return (f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="1.5" fill="#e8dcb0" stroke="{DARK}" stroke-width="1"/>{ticks}'
            f'<line x1="{_f(cx)}" y1="{_f(cy)}" x2="{_f(cx + math.sin(a) * h * 0.85)}" y2="{_f(cy - math.cos(a) * h * 0.85)}" stroke="{DARK}" stroke-width="1" stroke-linecap="round"/><circle cx="{_f(cx)}" cy="{_f(cy)}" r="1.6" fill="{DARK}"/>')


def scope(x, y, w, h, phase):
    pts = " ".join(f"{_f(x + w * i / 40)},{_f(y + h / 2 + math.sin(TAU * (i / 40 * 2 + phase * 2)) * h * 0.28 + math.sin(TAU * (i / 40 * 5 + phase * 3)) * h * 0.14)}" for i in range(41))
    grid = "".join(f'<line x1="{_f(x + w * i / 4)}" y1="{_f(y)}" x2="{_f(x + w * i / 4)}" y2="{_f(y + h)}" stroke="#1d4a2a" stroke-width="0.5"/>' for i in range(1, 4)) + f'<line x1="{_f(x)}" y1="{_f(y + h / 2)}" x2="{_f(x + w)}" y2="{_f(y + h / 2)}" stroke="#1d4a2a" stroke-width="0.5"/>'
    return (f'<rect x="{_f(x - 2)}" y="{_f(y - 2)}" width="{_f(w + 4)}" height="{_f(h + 4)}" rx="3" fill="{DARK}"/><rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="1.5" fill="#06140c"/>{grid}'
            f'<polyline points="{pts}" fill="none" stroke="#6cff8a" stroke-width="1.6" stroke-linejoin="round"/><polyline points="{pts}" fill="none" stroke="#c8ffd4" stroke-width="0.6"/>')


def pad(x, y, s, lit, c="r"):
    col = LED[c]
    return (f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(s)}" height="{_f(s)}" rx="2.5" fill="{col if lit else "#44474f"}" stroke="{DARK}" stroke-width="1"/>'
            + (f'<rect x="{_f(x - 2)}" y="{_f(y - 2)}" width="{_f(s + 4)}" height="{_f(s + 4)}" rx="4" fill="none" stroke="{col}" stroke-width="1.5" opacity="0.6"/>' if lit else f'<rect x="{_f(x + 2)}" y="{_f(y + 2)}" width="{_f(s - 4)}" height="2" rx="1" fill="#5c606a"/>'))


def jack(x, y):
    return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="2.3" fill="{DARK}"/><circle cx="{_f(x)}" cy="{_f(y)}" r="1.2" fill="#6a6e78"/>'


def cable(x0, y0, x1, y1, phase, col, k=0):
    sag = 12 + 4 * math.sin(TAU * (phase + k * 0.3))
    mx, my = (x0 + x1) / 2, max(y0, y1) + sag
    return (f'<path d="M{_f(x0)} {_f(y0)} Q{_f(mx)} {_f(my)} {_f(x1)} {_f(y1)}" fill="none" stroke="{DARK}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<path d="M{_f(x0)} {_f(y0)} Q{_f(mx)} {_f(my)} {_f(x1)} {_f(y1)}" fill="none" stroke="{col}" stroke-width="1.8" stroke-linecap="round"/>')


def limb(x0, y0, x1, y1, w=7):
    return (f'<line x1="{_f(x0)}" y1="{_f(y0)}" x2="{_f(x1)}" y2="{_f(y1)}" stroke="{DARK}" stroke-width="{_f(w + 2.4)}" stroke-linecap="round"/>'
            f'<line x1="{_f(x0)}" y1="{_f(y0)}" x2="{_f(x1)}" y2="{_f(y1)}" stroke="{MUD}" stroke-width="{_f(w)}" stroke-linecap="round"/>'
            f'<line x1="{_f(x0 + 1)}" y1="{_f(y0)}" x2="{_f(x1 + 1)}" y2="{_f(y1)}" stroke="{MUDH}" stroke-width="1.2" stroke-linecap="round"/>')


def hand(x, y, rot=0, press=0.0, worm=0.0, side=1):
    """A mud covered hand, wrist at the top (x, y); `rot` degrees; `press` 0..1 curls the fingers down; a worm hangs on it."""
    fingers = ""
    for i in range(4):
        a = (-24 + i * 16) * (1 - 0.4 * press)
        L = 9 + (3 if i in (1, 2) else 0) - 3 * press
        fx, fy = math.sin(math.radians(a)) * L, 5 + math.cos(math.radians(a)) * L
        fingers += f'<line x1="{_f((i - 1.5) * 3.2)}" y1="4" x2="{_f(fx + (i - 1.5) * 1.6)}" y2="{_f(fy)}" stroke="{DARK}" stroke-width="4.6" stroke-linecap="round"/><line x1="{_f((i - 1.5) * 3.2)}" y1="4" x2="{_f(fx + (i - 1.5) * 1.6)}" y2="{_f(fy)}" stroke="{MUD}" stroke-width="3" stroke-linecap="round"/>'
    thumb = f'<line x1="{_f(-5 * side)}" y1="3" x2="{_f(-11 * side)}" y2="{_f(8 - 3 * press)}" stroke="{DARK}" stroke-width="4.6" stroke-linecap="round"/><line x1="{_f(-5 * side)}" y1="3" x2="{_f(-11 * side)}" y2="{_f(8 - 3 * press)}" stroke="{MUD}" stroke-width="3" stroke-linecap="round"/>'
    w = math.sin(TAU * worm) * 5
    wm = f'<path d="M-3 2 q{_f(4 + w)} 5 {_f(1 - w)} 11 t{_f(w)} 7" fill="none" stroke="{DARK}" stroke-width="3.4" stroke-linecap="round"/><path d="M-3 2 q{_f(4 + w)} 5 {_f(1 - w)} 11 t{_f(w)} 7" fill="none" stroke="{WORM[0]}" stroke-width="1.9" stroke-linecap="round"/>'
    return (f'<g transform="translate({_f(x)} {_f(y)}) rotate({_f(rot)})">{thumb}{fingers}<ellipse cx="0" cy="3" rx="7.4" ry="6" fill="{MUD}" stroke="{DARK}" stroke-width="1.6"/>'
            f'<ellipse cx="-1.5" cy="1.5" rx="3" ry="1.6" fill="{MUDH}"/>{wm}</g>')


def player(phase, variant, hands):
    """The hunched player behind the rig: shoulders, a head that bangs 4 times a loop under whipping hair, and arms (elbows out) to the `hands` [(x, y, rot, press)]."""
    r = random.Random(variant * 17 + 3)
    sp = TAU * phase * 4
    nod = math.sin(sp)
    hy = 17 + 5 * nod
    hx = 100 + 3 * math.sin(sp * 0.5 + variant)
    sw = 9 * math.sin(sp - 0.8)
    o = [f'<ellipse cx="100" cy="36" rx="54" ry="22" fill="{MUD2}" stroke="{DARK}" stroke-width="2.4"/>']
    o.append(f'<g transform="rotate({_f(26 * nod)} {_f(hx)} 26)"><ellipse cx="{_f(hx)}" cy="{_f(hy)}" rx="15" ry="16" fill="{MUDH if variant % 2 else MUD}" stroke="{DARK}" stroke-width="2.4"/>'
             f'<path d="M{_f(hx - 15)} {_f(hy - 3)} Q{_f(hx)} {_f(hy - 24)} {_f(hx + 15)} {_f(hy - 3)} Q{_f(hx)} {_f(hy - 9)} {_f(hx - 15)} {_f(hy - 3)} Z" fill="{MUD2}" stroke="{DARK}" stroke-width="1.6"/>')
    for i in range(8):
        x0 = hx - 13 + i * 3.7
        L = 18 + 6 * ((i * 37) % 5) / 4
        o.append(f'<path d="M{_f(x0 - 2.6)} {_f(hy - 6)} Q{_f(x0 + sw * 0.25)} {_f(hy + L * 0.45)} {_f(x0 + sw * (0.5 + 0.25 * (i % 3)) + (i - 3.5))} {_f(hy + L)} Q{_f(x0 + 1 + sw * 0.1)} {_f(hy + L * 0.4)} {_f(x0 + 2.6)} {_f(hy - 6)} Z" fill="{MUD2 if i % 2 else MUD}" stroke="{DARK}" stroke-width="1.1" stroke-linejoin="round"/>')
    o.append("</g>")
    for k in range(3):                                      # worms in the hair and on the shoulders
        wx, wy = hx + r.uniform(-12, 12), hy - 14 + r.uniform(-1, 3)
        wv = math.sin(TAU * (phase * 2 + k * 0.3)) * 4
        o.append(f'<path d="M{_f(wx)} {_f(wy)} q{_f(3 + wv)} -6 {_f(1 - wv)} -11 t{_f(wv)} -5" fill="none" stroke="{DARK}" stroke-width="4" stroke-linecap="round"/><path d="M{_f(wx)} {_f(wy)} q{_f(3 + wv)} -6 {_f(1 - wv)} -11 t{_f(wv)} -5" fill="none" stroke="{WORM[k % 3]}" stroke-width="2.4" stroke-linecap="round"/>')
    arms = []
    for (hxx, hyy, rot, press), sx in zip(hands, (62, 138)):
        ex, ey = (sx + hxx) / 2 + (-10 if sx < 100 else 10), (46 + hyy) / 2 + 8
        arms.append(limb(sx, 40, ex, ey, 9) + limb(ex, ey, hxx, hyy, 7))
    return "".join(o), "".join(arms)


def _frame(body, hands_markup):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 130" data-size="10,6.5">{body}{hands_markup}</svg>')


def rig(kind="synth", phase=0.0, variant=0, hands_only=False):
    st = int(phase * 16) % 16
    o = []
    hands = []
    if kind == "synth":
        # modular panel: three modules of knobs, jacks and a LED row
        o.append(f'<rect x="4" y="38" width="192" height="44" rx="3" fill="{CHASSIS}" stroke="{DARK}" stroke-width="2"/>')
        jacks = []
        for m in range(3):
            x0 = 10 + m * 62
            o.append(f'<rect x="{x0}" y="42" width="58" height="36" rx="2" fill="{PANEL}" stroke="{DARK}" stroke-width="1.2"/>')
            for i in range(4):
                kx, ky = x0 + 10 + (i % 2) * 20, 52 + (i // 2) * 14
                o.append(knob(kx, ky, 4.4, -135 + 270 * (0.5 + 0.45 * math.sin(TAU * (phase * (1 + (i + m) % 3) + hsh(m, i)))) if (m, i) != (1, 0) else -135 + 360 * phase))
            for i in range(3):
                jx, jy = x0 + 44, 48 + i * 10
                o.append(jack(jx, jy)); jacks.append((jx, jy))
            for i in range(6):
                o.append(led(x0 + 8 + i * 7, 74, hsh(st, m, i) > 0.5, "gar"[i % 3]))
        o.append(cable(jacks[0][0], jacks[0][1], jacks[4][0], jacks[4][1], phase, "#ff4060", 0))
        o.append(cable(jacks[2][0], jacks[2][1], jacks[6][0], jacks[6][1], phase, "#40a8ff", 1))
        o.append(cable(jacks[5][0], jacks[5][1], jacks[8][0], jacks[8][1], phase, "#ffd030", 2))
        # scope, sliders
        o.append(f'<rect x="4" y="84" width="192" height="26" rx="3" fill="{CHASSIS}" stroke="{DARK}" stroke-width="2"/>')
        o.append(scope(12, 88, 54, 18, phase))
        grab = (st // 4) % 8
        for i in range(8):
            pos = 0.5 + 0.4 * math.sin(TAU * (phase * 2 + i * 0.13)) if i == grab else 0.3 + 0.4 * hsh(i, variant)
            o.append(slider(84 + i * 13, 88, 16, pos, LED["a"] if i == grab else "#d8d8dc"))
        sx, sy = 84 + grab * 13, 88 + (0.5 + 0.4 * math.sin(TAU * (phase * 2 + grab * 0.13))) * 16
        hands.append((sx, sy - 3, 8 * math.sin(TAU * phase * 2), 0.6))
        # keyboard
        o.append(f'<rect x="4" y="112" width="192" height="18" rx="2" fill="#d8d6cc" stroke="{DARK}" stroke-width="2"/>')
        for i in range(17):
            o.append(f'<line x1="{_f(8 + i * 11.2)}" y1="112" x2="{_f(8 + i * 11.2)}" y2="130" stroke="{DARK}" stroke-width="0.8"/>')
        for i in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12, 14):
            o.append(f'<rect x="{_f(8 + i * 11.2 + 7)}" y="112" width="7" height="11" fill="{DARK}"/>')
        hands.append((100 + 3 * math.cos(TAU * phase), 49 + 3 * math.sin(TAU * phase), 360 * phase, 0.2))      # the other hand twists a knob
    elif kind == "drum":
        o.append(f'<rect x="4" y="38" width="192" height="90" rx="4" fill="{CHASSIS}" stroke="{DARK}" stroke-width="2"/>')
        hit = [(st * 5) % 16, (st * 3 + 7) % 16]
        for i in range(16):
            px, py = 10 + (i % 4) * 22, 44 + (i // 4) * 21
            o.append(pad(px, py, 19, i in hit or hsh(st, i) > 0.82, "rgbm"[(i // 4) % 4] if (i in hit) else "arab"[(i % 4)]))
        for i in range(8):
            kx, ky = 118 + (i % 4) * 19, 52 + (i // 4) * 17
            o.append(knob(kx, ky, 5, -135 + 270 * (0.5 + 0.45 * math.sin(TAU * (phase * (1 + i % 3) + hsh(i, variant))))))
        for i in range(16):
            o.append(led(108 + i * 5.3, 90, i == st, "r") if i % 4 else led(108 + i * 5.3, 90, i == st or hsh(i) > 0.5, "a"))
        o.append(f'<rect x="108" y="98" width="82" height="26" rx="2" fill="#06140c" stroke="{DARK}" stroke-width="1.5"/>')
        for i in range(14):
            hgt = 3 + 18 * hsh(st, i * 3)
            o.append(f'<rect x="{_f(112 + i * 5.6)}" y="{_f(121 - hgt)}" width="3.6" height="{_f(hgt)}" fill="#6cff8a"/>')
        for k, hh in enumerate(hit):
            px, py = 10 + (hh % 4) * 22, 44 + (hh // 4) * 21
            down = 0.5 + 0.5 * math.cos(TAU * ((phase * 16) % 1))
            hands.append((px + 9.5, py + 6 - 7 * down, 4 * (-1 if k else 1), 0.3 + 0.7 * down))
    else:                                                    # rack
        for u in range(3):
            y0 = 38 + u * 30
            o.append(f'<rect x="4" y="{y0}" width="192" height="28" rx="2" fill="{PANEL}" stroke="{DARK}" stroke-width="2"/>')
            for sx in (8, 192):
                o.append(f'<circle cx="{sx}" cy="{y0 + 5}" r="1.8" fill="{METAL}"/><circle cx="{sx}" cy="{y0 + 23}" r="1.8" fill="{METAL}"/>')
        o.append(vu(14, 42, 34, 20, 0.3 + 0.6 * abs(math.sin(TAU * phase * 2))) + vu(54, 42, 34, 20, 0.2 + 0.7 * hsh(st, 1)))
        for i in range(6):
            o.append(knob(108 + i * 14, 52, 4.4, -135 + 270 * (0.5 + 0.45 * math.sin(TAU * (phase * (1 + i % 3) + i * 0.2))) if i != 2 else -135 + 360 * phase))
        for rrow in range(3):
            for i in range(24):
                o.append(led(14 + i * 5.2, 72 + rrow * 6, hsh(st, i, rrow) > 0.55, "gar"[rrow]))
        for i in range(8):
            o.append(slider(148 + i * 6.2, 68, 14, 0.3 + 0.5 * hsh(i, variant)))
        for i in range(16):
            hgt = 2 + 16 * (0.5 + 0.5 * math.sin(TAU * (phase * 2 + i * 0.21))) * (0.5 + hsh(st, i) * 0.5)
            o.append(f'<rect x="{_f(14 + i * 7.6)}" y="{_f(116 - hgt)}" width="5.4" height="{_f(hgt)}" fill="{LED["g"] if hgt < 11 else LED["a"] if hgt < 15 else LED["r"]}"/>')
        for i in range(5):
            o.append(knob(150 + i * 9, 106, 3.6, -135 + 270 * hsh(i, variant)))
        hands.append((108 + 28 + 3 * math.cos(TAU * phase), 53 + 3 * math.sin(TAU * phase), 360 * phase, 0.3))
        hands.append((148 + 5 * 6.2, 68 + (0.5 + 0.3 * math.sin(TAU * phase * 2)) * 14, 6 * math.sin(TAU * phase * 2), 0.6))
    # a hunched player behind, and his hands over the controls
    hs = [(hx, hy, rot, press) for hx, hy, rot, press in hands[:2]]
    back, arms = player(phase, variant, hs)
    front = arms + "".join(hand(hx, hy - 3, rot * 0 + (rot % 360), press, phase * 2 + k * 0.3, 1 if k else -1) for k, (hx, hy, rot, press) in enumerate(hs))
    table = f'<rect x="0" y="126" width="200" height="4" fill="{DARK}"/>'
    if hands_only:
        return _frame("", back + front)
    return _frame(back + "".join(o) + table, front)


def generate(seed):
    return ArtSvg(rig("synth", 0.0, seed or 0), "🎛")
