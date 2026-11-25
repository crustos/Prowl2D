"""Speaker stacks for the stage: `stack(kind, phase, variant)` is an SVG text whose cones pulse with the beat (phase 0..1 loops; 8 to 12 frames work well).

kind: "wall" (a tall stack of 4 cabinets, the biggest woofer in the bottom one), "cab" (one 4x12 guitar cabinet), "mon" (a stage monitor wedge).
Cones throb 4 times a loop, a dust cap bulges, a ring of shock lines leaves the cone, and the cabinet shakes with the bass.
`rings(phase)` is an SVG of expanding feedback rings (viewBox 0 0 200 200, data-size 8 x 8 cells) for the speaker the guitarist stands at.

As a symbol, 🔊 draws a speaker wall, with `seed` as the variant.
"""
import math
import random

from kaomojilang.artlib import ArtSvg

TAU = 2 * math.pi
DARK, TOLEX, GRILL, METAL = "#0e0e11", "#1c1c20", "#2a2a30", "#8a8f99"


def _f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _cone(cx, cy, r, pulse, variant=0):
    """A woofer: surround, cone rings, dust cap; `pulse` -1..1 pushes the cone in and out."""
    k = 1 + 0.05 * pulse
    o = [f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="#0a0a0c" stroke="{METAL}" stroke-width="{_f(r * 0.07)}"/>',
         f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * 0.9 * k)}" fill="#202026" stroke="#050506" stroke-width="1.2"/>']
    for i in (0.72, 0.52):
        o.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * i * k)}" fill="none" stroke="#3a3a42" stroke-width="{_f(r * 0.05)}"/>')
    o.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * (0.3 + 0.04 * pulse))}" fill="#2e2e36" stroke="#050506" stroke-width="1.2"/>')
    o.append(f'<path d="M{_f(cx - r * 0.18)} {_f(cy - r * 0.1)} q{_f(r * 0.1)} {_f(-r * 0.14)} {_f(r * 0.3)} {_f(-r * 0.04)}" fill="none" stroke="#6a6a74" stroke-width="{_f(r * 0.05)}" stroke-linecap="round"/>')
    for i in range(8):                                                   # screws
        a = TAU * i / 8
        o.append(f'<circle cx="{_f(cx + math.cos(a) * r * 0.96)}" cy="{_f(cy + math.sin(a) * r * 0.96)}" r="{_f(r * 0.045)}" fill="{METAL}"/>')
    if pulse > 0.2:                                                     # the thump: shock arcs off the cone
        for j in (1, 2):
            o.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * (1 + 0.18 * j * pulse))}" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="{_f(0.35 * pulse / j)}"/>')
    return "".join(o)


def _tweeter(cx, cy, r, pulse):
    return (f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="#0a0a0c" stroke="{METAL}" stroke-width="1.4"/>'
            f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * (0.55 + 0.06 * pulse))}" fill="#b8a050" stroke="#050506" stroke-width="1"/>')


def _box(x, y, w, h, shake):
    return (f'<rect x="{_f(x + shake)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="3" fill="{TOLEX}" stroke="{DARK}" stroke-width="3"/>'
            f'<rect x="{_f(x + shake + 4)}" y="{_f(y + 4)}" width="{_f(w - 8)}" height="{_f(h - 8)}" rx="2" fill="{GRILL}" opacity="0.35"/>')


def _corners(x, y, w, h, shake):
    return "".join(f'<rect x="{_f(cx + shake - 3)}" y="{_f(cy - 3)}" width="6" height="6" fill="{METAL}" stroke="{DARK}" stroke-width="1"/>' for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)))


def stack(kind="wall", phase=0.0, variant=0):
    r = random.Random(variant * 101 + 7)
    beat = math.sin(TAU * phase * 4)                       # 4 thumps a loop
    pulse = max(-0.3, beat)
    shake = 1.6 * math.sin(TAU * phase * 8) * max(0, beat)
    o = []
    if kind == "wall":
        W, H = 200, 300
        for i in range(4):
            y = 4 + i * 74
            o.append(_box(6, y, 188, 70, shake))
            if i == 3:                                      # the biggest woofer is the bottom one, at head height of the one who leans on it
                o.append(_cone(100 + shake, y + 36, 29, pulse))
                o.append(_tweeter(34 + shake, y + 36, 8, pulse) + _tweeter(166 + shake, y + 36, 8, pulse))
            else:
                o.append(_cone(56 + shake, y + 35, 25, pulse * (1 if i % 2 else -1)) + _cone(144 + shake, y + 35, 25, -pulse * (1 if i % 2 else -1)))
            o.append(_corners(6, y, 188, 70, shake))
            o.append(f'<rect x="{_f(150 + shake)}" y="{_f(y + 60)}" width="36" height="7" rx="1.5" fill="#d0c8a8" stroke="{DARK}" stroke-width="0.8"/><text x="{_f(168 + shake)}" y="{_f(y + 66)}" font-size="5" text-anchor="middle" fill="#201810" font-family="sans-serif" font-weight="bold">LOUD {i + 1}</text>')
        o.append(f'<rect x="0" y="298" width="200" height="2" fill="{DARK}"/>')
    elif kind == "cab":
        W, H = 200, 200
        o.append(_box(6, 6, 188, 188, shake))
        for k in range(4):
            cx, cy = 56 + (k % 2) * 88 + shake, 56 + (k // 2) * 88
            o.append(_cone(cx, cy, 36, pulse * (1 if (k + k // 2) % 2 else -1)))
        o.append(_corners(6, 6, 188, 188, shake))
        o.append(f'<rect x="72" y="92" width="56" height="16" rx="2" fill="#d0c8a8" stroke="{DARK}" stroke-width="1"/><text x="100" y="104" font-size="9" text-anchor="middle" fill="#201810" font-family="sans-serif" font-weight="bold">4x12</text>')
    else:
        W, H = 200, 110
        o.append(f'<path d="M6 104 L194 104 L170 8 L30 8 Z" fill="{TOLEX}" stroke="{DARK}" stroke-width="3"/>')
        o.append(_cone(100 + shake, 62, 34, pulse) + _tweeter(100, 22, 8, pulse))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" data-size="{ {"wall": "6,9", "cab": "6,6", "mon": "6,3.3"}[kind] }">' + "".join(o) + "</svg>"


def rings(phase=0.0):
    """Feedback: rings and jagged lightning flinching out from the speaker face."""
    o = []
    for k in range(5):
        u = (phase + k / 5) % 1.0
        o.append(f'<circle cx="100" cy="100" r="{_f(14 + 82 * u)}" fill="none" stroke="#ffffff" stroke-width="{_f(3.2 * (1 - u) + 0.4)}" opacity="{_f(0.75 * (1 - u))}"/>')
    for k in range(7):
        a = TAU * (k / 7 + 0.13 * math.sin(TAU * phase + k))
        pts = " ".join(f"{_f(100 + math.cos(a + 0.12 * ((i * 7 + k) % 3 - 1)) * (14 + i * 11))},{_f(100 + math.sin(a + 0.12 * ((i * 5 + k) % 3 - 1)) * (14 + i * 11))}" for i in range(8))
        o.append(f'<polyline points="{pts}" fill="none" stroke="#fff6c8" stroke-width="1.6" stroke-linejoin="round" opacity="{_f(0.4 + 0.5 * ((phase * 12 + k) % 1))}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" data-size="8,8">' + "".join(o) + "</svg>"


def generate(seed):
    return ArtSvg(stack("wall", 0.0, seed or 0), "🔊")
