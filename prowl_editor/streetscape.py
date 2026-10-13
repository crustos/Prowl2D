"""streetscape.py: the sprites of a 1990s California street, as ASCII art, for the level text (generated.py asks for them by the name of the tile).

Everything is 16 x 16, the NeoGeo's tile, drawn from the side, as in a belt-scrolling brawler: shopfronts above, the pavement, the street along the bottom.

  window, door, shutter, awning      the front of a shop: lit, barred, boarded, tagged, rusted (each a brick wall with the thing in it, so they sit in a wall)
  motel sign, liquor sign, tv sign   neon in a box on the wall (two frames: it flickers)
  hydrant, dumpster                  on the pavement
  sidewalk                           the pavement; the top row of it is in the shadow of the wall behind it (joins: see joined_name)
  streetlamp                         a column of cells: the head, the pole, the foot of it on the pavement
  car                                an 80s sedan, three cells wide, parked in the street (a run of cells; its colour is picked for each car)

A family here is [(suffix, weight, rows(size))] like the ones in generated.py, and the three that depend on their neighbours (sidewalk, streetlamp, car) are
`COLUMNS` with a builder that makes all of their sprites and `joined_name`, which says which one a cell is. rows() is a list of rows, or a list of such lists for an
animation.
"""
import random

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# a small kit

FONT = {          # 3 x 5 letters, for the neon
    "M": ["#.#", "###", "###", "#.#", "#.#"], "O": ["###", "#.#", "#.#", "#.#", "###"], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "E": ["###", "#..", "##.", "#..", "###"], "L": ["#..", "#..", "#..", "#..", "###"], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "Q": ["###", "#.#", "#.#", "###", "..#"], "U": ["#.#", "#.#", "#.#", "#.#", "###"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
}


def text(name, palette, frames, fps=1):
    """The sprite text of `frames` (a list of rows, or a list of lists of rows for an animation), with only the palette entries it uses."""
    if frames and isinstance(frames[0], str):
        frames = [frames]
    if len(frames) > 1:
        fps = 4
    used = {c for f in frames for r in f for c in r}
    head = ["# sprite: %s" % name, "# fps: %g" % fps, "# palette: " + " ".join("%s=%s" % kv for kv in palette.items() if kv[0] in used)]
    return "\n".join(head) + "\n" + "\n\n".join("\n".join(f) for f in frames) + "\n"


def blank(size=16, ch="."):
    return [[ch] * size for _ in range(size)]


def rect(g, x0, y0, x1, y1, ch):
    """Fills x0..x1, y0..y1 (inclusive), clipped to the sprite."""
    for y in range(max(0, y0), min(len(g) - 1, y1) + 1):
        for x in range(max(0, x0), min(len(g[0]) - 1, x1) + 1):
            g[y][x] = ch


def rows(g):
    return ["".join(r) for r in g]


def _lazy():
    from . import generated        # (generated imports this module: asked for at call time)
    return generated


def wall(seed=0, size=16):
    """A plain brick wall to put things in."""
    return [list(r) for r in _lazy().brick_rows(size, seed)]


PAL = {
    # brick (as generated.BRICK_PALETTE)
    "M": "#6e5f58", "R": "#b5543c", "S": "#a24a35", "T": "#c2603f", "H": "#cf7255", "D": "#8f3f2e",
    # concrete
    "p": "#aca89f", "P": "#bdb9af", "q": "#8b877f", "k": "#66635d", "K": "#2b2623", "s": "#7a766d", "w": "#d9d6cc",
    # metal
    "i": "#5d646b", "j": "#868e96", "J": "#b3bbc2", "u": "#9a4a22", "n": "#3a3f45",
    # glass and light
    "g": "#1d2330", "G": "#2f394b", "h": "#55627a",
    "y": "#f2c14e", "Y": "#d68f2c", "O": "#f08a2e", "r": "#d62f3a", "b": "#2f6fd6", "B": "#1b3f94", "c": "#35c6d8", "m": "#ff4f9a", "e": "#2fa84f",
    "W": "#e8e4d8", "V": "#c9c4b6", "d": "#52433c", "t": "#c9a56e", "x": "#2a2c30", "A": "#4b4e53", "C": "#54575d", "a": "#44474c",
}


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# the fronts of shops

def _frame(g, x0=1, y0=1, x1=14, y1=14):
    """The dark frame of a window or door: 1 px, with a concrete sill under it."""
    rect(g, x0 - 1, y0 - 1, x1 + 1, y1 + 1, "k")
    rect(g, x0, y0, x1, y1, "g")
    rect(g, 0, 15, 15, 15, "s")


def _window(kind, seed):
    def make(size):
        rng = random.Random("window/%s/%d" % (kind, seed))
        g = wall(seed % 3)
        _frame(g)
        if kind == "warm":                                    # a liquor store: shelves of bottles in a warm light
            rect(g, 2, 2, 13, 13, "Y")
            rect(g, 2, 2, 13, 5, "y")
            for y in (6, 10):
                rect(g, 2, y, 13, y, "d")
                for x in range(2, 14):
                    if rng.random() < 0.8:
                        g[y - 1][x] = rng.choice("rrebOc")
                        if x % 3:
                            g[y - 2][x] = g[y - 1][x]
        elif kind == "dark":                                  # the sky in dark glass, with a streak
            rect(g, 2, 2, 13, 13, "G")
            for i in range(9):
                g[2 + i][11 - i] = g[3 + i][11 - i] = "h"
        elif kind == "barred":
            rect(g, 2, 2, 13, 13, "G")
            for x in (3, 6, 9, 12):
                rect(g, x, 2, x, 13, "j")
            rect(g, 2, 7, 13, 7, "i")
        elif kind == "blinds":
            for y in range(2, 14):
                rect(g, 2, y, 13, y, "V" if y % 2 == 0 else "t")
            rect(g, 6, 8, 9, 9, "g")                          # a broken slat
        elif kind == "boarded":
            for i, y in enumerate(range(2, 14, 3)):
                rect(g, 2, y, 13, y + 1, "t")
                rect(g, 2, y + 2, 13, y + 2, "d")
                g[y][3 + i % 2 * 8] = g[y][12 - i % 2 * 8] = "K"
        elif kind == "poster":                                # dark glass with flyers taped to it
            rect(g, 2, 2, 13, 13, "G")
            for x0, y0, c in ((3, 3, "W"), (8, 5, "m"), (4, 9, "y")):
                rect(g, x0, y0, x0 + 3, y0 + 4, c)
                rect(g, x0 + 1, y0 + 1, x0 + 2, y0 + 1, "K")
        else:                                                 # neon: a squiggle of pink and blue in the dark
            rect(g, 2, 2, 13, 13, "g")
            for x in range(3, 13):
                g[7 + (x // 2) % 2][x] = "m"
                g[10 - (x // 3) % 2][x] = "c"
        return rows(g)
    return make


def _tv_window(frame):
    """The blue light of a TV in a dark room, with someone sitting watching it (two frames of static)."""
    def make(size):
        rng = random.Random("tv/%d" % frame)
        g = wall(1)
        _frame(g)
        rect(g, 2, 2, 13, 13, "B")
        for y in range(2, 14):
            for x in range(2, 14):
                if rng.random() < 0.22:
                    g[y][x] = "b"
        rect(g, 6, 8, 9, 13, "g")                              # the back of a head and shoulders
        rect(g, 5, 10, 10, 13, "g")
        return rows(g)
    return make


def window_family():
    return [("", 30, _window("warm", 0)), ("dark", 25, _window("dark", 1)), ("barred", 15, _window("barred", 2)), ("blinds", 10, _window("blinds", 3)),
            ("boarded", 8, _window("boarded", 4)), ("poster", 8, _window("poster", 5)), ("neon", 8, _window("neon", 6)),
            ("tv", 12, lambda size: [_tv_window(0)(size), _tv_window(1)(size)])]


def _door(kind):
    def make(size):
        rng = random.Random("door/" + kind)
        g = wall(2)
        rect(g, 2, 0, 13, 15, "k")
        if kind == "steel":
            rect(g, 3, 1, 12, 15, "j")
            rect(g, 3, 1, 4, 15, "J")
            rect(g, 3, 12, 12, 15, "i")                        # the kick plate
            rect(g, 10, 8, 11, 9, "K")
            g[5][7] = g[5][8] = "n"                            # the peephole
        elif kind == "glass":
            rect(g, 3, 1, 12, 15, "i")
            rect(g, 4, 2, 11, 10, "Y")
            rect(g, 4, 2, 11, 5, "y")
            rect(g, 3, 11, 12, 11, "j")
            for x in (5, 6, 7, 8):
                g[8][x] = "m"                                  # a neon sign hung in it
        elif kind == "wood":
            rect(g, 3, 1, 12, 15, "d")
            for x0, y0, x1, y1 in ((4, 2, 7, 6), (8, 2, 11, 6), (4, 8, 7, 14), (8, 8, 11, 14)):
                rect(g, x0, y0, x1, y1, "u")
                rect(g, x0, y0, x1, y0, "O")
            g[9][11] = "y"
        elif kind == "boarded":
            rect(g, 3, 1, 12, 15, "d")
            for y in (2, 7, 12):
                rect(g, 2, y, 13, y + 2, "t")
                g[y][3] = g[y][12] = "K"
        else:                                                  # a gate of bars, and a dark passage behind it
            rect(g, 3, 1, 12, 15, "K")
            for x in range(4, 12, 2):
                rect(g, x, 1, x, 15, "j")
            rect(g, 3, 8, 12, 8, "i")
        rect(g, 0, 15, 15, 15, "s")
        return rows(g)
    return make


def door_family():
    return [("", 30, _door("steel")), ("glass", 25, _door("glass")), ("wood", 20, _door("wood")), ("boarded", 10, _door("boarded")), ("gate", 15, _door("gate"))]


def _shutter(kind, seed):
    def make(size):
        rng = random.Random("shutter/%s/%d" % (kind, seed))
        g = wall(seed % 3)
        light, mid, dark = {"grey": "Jjn", "green": "ejn", "cream": "WVt", "rust": "ujd"}["rust" if kind == "rusty" else "green" if kind == "green" else "cream" if kind == "cream" else "grey"]
        rect(g, 0, 0, 15, 15, mid)
        for y in range(0, 16, 3):                              # the ribs
            rect(g, 0, y, 15, y, light)
            rect(g, 0, y + 1, 15, y + 1, dark)
        rect(g, 0, 0, 15, 1, "K")                              # the box it rolls up into
        rect(g, 0, 14, 15, 15, "i")                            # the bottom bar, and the handle
        rect(g, 7, 14, 8, 14, "J")
        if kind == "dented":
            for _ in range(3):
                cx, cy = rng.randint(2, 13), rng.randint(3, 11)
                rect(g, cx, cy, cx + 2, cy + 1, dark)
                rect(g, cx, cy - 1, cx + 2, cy - 1, light)
        elif kind == "rusty":
            for x in rng.sample(range(16), 5):
                for y in range(2, rng.randint(6, 14)):
                    if rng.random() < 0.8:
                        g[y][x] = rng.choice("uud")
        elif kind == "tagged":
            _lazy()._tag_swoosh(g, rng, 16)
        elif kind == "half":                                   # rolled half up: a dark gap, the shop behind
            rect(g, 0, 5, 15, 12, "K")
            rect(g, 0, 5, 15, 5, "Y")
        elif kind == "flyers":
            for x0, y0, c in ((2, 4, "W"), (8, 6, "m"), (5, 9, "y")):
                rect(g, x0, y0, x0 + 3, y0 + 3, c)
                rect(g, x0, y0 + 1, x0 + 2, y0 + 1, "K")
        return rows(g)
    return make


def shutter_family():
    return [("", 30, _shutter("grey", 0)), ("green", 12, _shutter("green", 1)), ("cream", 12, _shutter("cream", 2)), ("dented", 12, _shutter("dented", 3)),
            ("rusty", 10, _shutter("rusty", 4)), ("tagged", 18, _shutter("tagged", 5)), ("half", 6, _shutter("half", 6)), ("flyers", 8, _shutter("flyers", 7))]


def _awning(colors, kind):
    a, b = colors

    def make(size):
        rng = random.Random("awning/%s/%s" % (a, kind))
        g = wall(0)
        for y in range(0, 11):
            for x in range(16):
                g[y][x] = a if (x // 4) % 2 == 0 else b
        rect(g, 0, 0, 15, 0, "K")
        for x in range(16):                                    # the scalloped edge, and its shadow on the wall
            g[11][x] = a if (x // 4) % 2 == 0 else b
            if x % 4 in (1, 2):
                g[12][x] = a if (x // 4) % 2 == 0 else b
            if x % 4 not in (1, 2):
                g[12][x] = "K"                                 # (a shadow under the edge)
            elif g[13][x] not in "rWbeV":
                g[13][x] = "K"
        rect(g, 0, 14, 15, 15, "d")
        if kind == "dirty":
            for _ in range(14):
                g[rng.randint(1, 11)][rng.randint(0, 15)] = rng.choice("VdVk")
        if kind == "torn":
            for x in range(5, 9):
                for y in range(8, 14):
                    if rng.random() < 0.8:
                        g[y][x] = "d"
        return rows(g)
    return make


def awning_family():
    return [("", 30, _awning(("r", "W"), "plain")), ("green", 20, _awning(("e", "W"), "plain")), ("blue", 15, _awning(("b", "W"), "plain")),
            ("dirty", 20, _awning(("r", "V"), "dirty")), ("torn", 8, _awning(("b", "V"), "torn"))]


def _sign(lines, color, dim):
    """A neon sign in a box: two lines of 3 x 5 letters, glowing, and a second frame in which one of the letters has gone out."""
    def make(size):
        frames = []
        for flick in (None, 1):
            g = blank(16, "K")
            rect(g, 0, 0, 15, 0, "j")
            rect(g, 0, 15, 15, 15, "i")
            rect(g, 0, 0, 0, 15, "i")
            rect(g, 15, 0, 15, 15, "i")
            for li, word in enumerate(lines):
                x0 = (16 - (len(word) * 4 - 1)) // 2
                for ci, ch in enumerate(word):
                    on = not (flick and li == 0 and ci == 0)
                    for y, row in enumerate(FONT[ch]):
                        for x, v in enumerate(row):
                            if v == "#":
                                g[2 + li * 7 + y][x0 + ci * 4 + x] = color if on else dim
            frames.append(rows(g))
        return frames
    return make


def sign_family(lines):
    return [("", 50, _sign(lines, "m", "d")), ("cyan", 30, _sign(lines, "c", "g")), ("amber", 20, _sign(lines, "y", "d"))]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# on the pavement

def sidewalk_grid(rng, back=False, size=16):
    g = [[rng.choice("pppP") for _ in range(size)] for _ in range(size)]
    for i in range(size):
        g[size - 1][i] = "q"                                   # the joint under the slab...
        g[i][0] = "q"                                          # ...and the one beside it
    if back:                                                   # the foot of the wall: dark, with the shade of the wall on the pavement
        rect(g, 0, 0, size - 1, 0, "K")
        rect(g, 0, 1, size - 1, 1, "k")
        rect(g, 0, 2, size - 1, 3, "s")
    return g


SIDEWALK_WEIGHTS = [45, 25, 12, 10, 8, 3]


def sidewalk_rows(shape, look, size=16):
    rng = random.Random("sidewalk/%d/%d" % (shape, look))
    g = sidewalk_grid(rng, bool(shape & 1), size)
    top = 4 if shape & 1 else 1
    if look == 2:                                              # a crack, with a weed
        x, y = rng.randint(3, 12), top
        for _ in range(12):
            g[y][x] = "k"
            x = max(1, min(14, x + rng.choice((-1, 0, 1))))
            y = min(14, y + 1)
        g[rng.randint(top, 14)][x] = "e"
    elif look == 3:                                            # a dark wet stain
        cx, cy = rng.randint(4, 11), rng.randint(top + 3, 11)
        for y in range(size - 1):
            for x in range(1, size):
                if ((x - cx) / 3.5) ** 2 + ((y - cy) / 2.2) ** 2 <= 1:
                    g[y][x] = rng.choice("sss k"[:4])
    elif look == 4:                                            # gum, a cigarette end, and a bit of paper
        for _ in range(6):
            g[rng.randint(top, 13)][rng.randint(1, 14)] = "m"
        for x, y in ((rng.randint(2, 12), rng.randint(top, 13)),):
            g[y][x] = g[y][x + 1] = "W"
        x, y = rng.randint(2, 11), rng.randint(top, 12)
        rect(g, x, y, x + 2, y + 1, "V")
    elif look == 5:                                            # a drain grate at the kerb
        rect(g, 4, 10, 11, 13, "K")
        for x in range(4, 12, 2):
            rect(g, x, 10, x, 13, "j")
    return rows(g)


def sidewalk_family(base="sidewalk", size=16):
    out = []
    for shape in range(2):
        for look in range(6):
            name = sidewalk_name(base, shape, look)
            out.append((name, SIDEWALK_WEIGHTS[look], text(name, PAL, sidewalk_rows(shape, look, size))))
    out.sort(key=lambda t: t[0] != base)
    return out


def sidewalk_name(base, shape, look):
    return base if (shape, look) == (0, 0) else "%s_%d_%d" % (base, shape, look)


def _on_sidewalk(rng, draw):
    g = sidewalk_grid(rng, False)
    draw(g, rng)
    return rows(g)


def _hydrant(body, cap):
    def make(size):
        rng = random.Random("hydrant/" + body)

        def draw(g, rng):
            rect(g, 5, 8, 10, 14, body)                        # the barrel
            rect(g, 4, 7, 11, 8, cap)                          # the cap
            rect(g, 6, 5, 9, 6, cap)
            g[4][7] = g[4][8] = cap
            rect(g, 3, 10, 4, 11, cap)                         # the nozzles
            rect(g, 11, 10, 12, 11, cap)
            rect(g, 4, 14, 11, 14, "i")                        # the base
            g[9][6] = g[10][6] = "W" if body == "r" else "V"   # a shine
            rect(g, 4, 15, 11, 15, "K")
        return _on_sidewalk(rng, draw)
    return make


def hydrant_family():
    return [("", 40, _hydrant("r", "j")), ("yellow", 25, _hydrant("y", "Y")), ("rust", 15, _hydrant("u", "d")), ("blue", 20, _hydrant("b", "c"))]


def _dumpster(body, dark, kind):
    def make(size):
        rng = random.Random("dumpster/%s/%s" % (body, kind))

        def draw(g, rng):
            rect(g, 1, 6, 14, 14, body)
            rect(g, 1, 4, 14, 6, dark)                         # the lid
            rect(g, 1, 4, 14, 4, "j")
            rect(g, 1, 14, 14, 14, "K")
            for x in range(3, 14, 3):
                rect(g, x, 8, x, 13, dark)                     # the ribs
            rect(g, 2, 15, 3, 15, "K")
            rect(g, 12, 15, 13, 15, "K")                       # wheels
            if kind == "tagged":
                _lazy()._tag_swoosh(g, rng, 16)
            elif kind == "full":
                for x in range(2, 14):
                    g[3 - rng.randint(0, 2) + (x % 2)][x] = rng.choice("WVtdr")
                rect(g, 1, 4, 14, 4, "j")
        return _on_sidewalk(rng, draw)
    return make


def dumpster_family():
    return [("", 40, _dumpster("e", "n", "plain")), ("blue", 25, _dumpster("B", "n", "plain")), ("tagged", 20, _dumpster("e", "n", "tagged")),
            ("full", 15, _dumpster("B", "n", "full"))]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# streetlamps: a column

LAMP_HEAD, LAMP_BASE = 1, 2
LAMP_WEIGHTS = [85, 15]                        # lit, flickering


def lamp_rows(shape, look, size=16):
    rng = random.Random("lamp/%d/%d" % (shape, look))
    frames = []
    for frame in range(2 if look else 1):
        g = sidewalk_grid(random.Random("lamp/%d" % shape), False) if shape & LAMP_BASE else blank()       # (a foot stands on the pavement; the rest is in front of nothing)
        rect(g, 7, 0 if not shape & LAMP_HEAD else 6, 8, 15 if not shape & LAMP_BASE else 13, "j")
        rect(g, 7, 0 if not shape & LAMP_HEAD else 6, 7, 15 if not shape & LAMP_BASE else 13, "J")
        if shape & LAMP_HEAD:
            rect(g, 7, 4, 14, 5, "j")                          # the arm
            rect(g, 11, 6, 14, 7, "n")                         # the lamp
            lit = not (look and frame)
            rect(g, 11, 7, 14, 7, "y" if lit else "d")
            if lit:
                for x, y in ((10, 8), (12, 9), (14, 9), (11, 10), (13, 10), (15, 8), (12, 11), (10, 6), (15, 6)):
                    if 0 <= y < 16 and g[y][x] == ".":
                        g[y][x] = "y"                          # a dither of light
            g[3][7] = g[3][8] = "J"
        if shape & LAMP_BASE:
            rect(g, 5, 13, 10, 14, "i")
            rect(g, 4, 15, 11, 15, "K")
        frames.append(rows(g))
    return frames


def lamp_name(base, shape, look):
    return base if (shape, look) == (LAMP_HEAD, 0) else "%s_%d_%d" % (base, shape, look)


def lamp_family(base="streetlamp", size=16):
    out = [(lamp_name(base, s, l), LAMP_WEIGHTS[l], text(lamp_name(base, s, l), PAL, lamp_rows(s, l, size))) for s in range(4) for l in range(2)]
    out.sort(key=lambda t: t[0] != base)
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# cars: a run of three cells

CARS = [          # body, dark, light, name
    ("r", "D", "O", "red"), ("e", "n", "J", "green"), ("t", "d", "W", "beige"), ("B", "n", "h", "blue"), ("W", "V", "w", "white")]
CAR_WEIGHTS = [25, 20, 25, 20, 10]


def car_art(colour, rusty=False):
    """A sedan from the side, 48 x 16, standing on asphalt."""
    rng = random.Random("car/%d" % colour)
    body, dark, light, _ = CARS[colour]
    g = [[rng.choice("AAAAaC") for _ in range(48)] for _ in range(16)]
    rect(g, 3, 14, 44, 15, "x")                                # its shadow
    rect(g, 2, 8, 45, 13, body)                                # the body, with the hood and the boot lower
    rect(g, 2, 8, 45, 8, light)
    rect(g, 2, 12, 45, 13, dark)
    rect(g, 12, 3, 34, 7, body)                                # the cabin, narrower at the roof
    for y, inset in ((2, 5), (3, 4), (4, 3), (5, 1), (6, 0)):
        rect(g, 12, y, 12 + inset, y, "A")                     # (cuts the corners of the cabin)
        rect(g, 34 - inset, y, 34, y, "A")
    rect(g, 14, 3, 31, 3, light)
    rect(g, 14, 4, 22, 6, "G")                                 # windows
    rect(g, 25, 4, 31, 6, "G")
    for x, y in ((15, 4), (16, 5), (26, 4), (27, 5)):
        g[y][x] = "h"
    rect(g, 23, 4, 23, 12, dark)                               # the door
    rect(g, 20, 9, 21, 9, "J")
    rect(g, 2, 11, 3, 11, "r")                                 # the tail light and the head light
    rect(g, 44, 10, 45, 10, "y")
    rect(g, 2, 13, 3, 13, "K")
    rect(g, 44, 13, 45, 13, "K")
    for cx in (10, 37):                                        # wheels
        for y in range(10, 16):
            for x in range(cx - 3, cx + 4):
                d = (x - cx) ** 2 + (y - 12.5) ** 2
                if d <= 9.5:
                    g[y][x] = "K" if d > 3.2 else "j"
        g[12][cx] = "J"
    if rusty:
        for _ in range(26):
            x, y = rng.randint(3, 44), rng.randint(8, 13)
            if g[y][x] == body:
                g[y][x] = rng.choice("uud")
    return g


def car_family(base="car", size=16):
    out = []
    for c in range(len(CARS)):
        art = car_art(c, rusty=(c == 2))
        for i, pos in enumerate("lmr"):
            name = car_name(base, pos, c)
            out.append((name, CAR_WEIGHTS[c], text(name, PAL, rows([r[i * 16:(i + 1) * 16] for r in art]))))
    out.sort(key=lambda t: t[0] != base)
    return out


def car_name(base, pos, colour):
    return base if (pos, colour) == ("l", 0) else "%s_%s_%d" % (base, pos, colour)


# ---------------------------------------------------------------------------------------------------------------------------------------------------

COLUMNS = {"sidewalk": sidewalk_family, "streetlamp": lamp_family, "car": car_family}


def joined_name(kind, base, x, y, up, down, left, right, above_in, hash_at):
    """The sprite of the cell (x, y) of a `kind` of tile (a key of COLUMNS): `up` and `down` cells of it above and below, `left` and `right` beside it; above_in: the
    level has a row above the top of this column; hash_at(x, y): a number that looks random and is the same every time for a cell, that picks among the looks."""
    h = hash_at(x, y)
    if kind == "sidewalk":
        look, r = 0, h % sum(SIDEWALK_WEIGHTS)
        while r >= SIDEWALK_WEIGHTS[look]:
            r -= SIDEWALK_WEIGHTS[look]
            look += 1
        return sidewalk_name(base, 1 if up == 0 and above_in else 0, look)
    if kind == "streetlamp":
        shape = (LAMP_HEAD if up == 0 else 0) | (LAMP_BASE if down == 0 else 0)
        return lamp_name(base, shape, 1 if h % 100 < LAMP_WEIGHTS[1] and shape & LAMP_HEAD else 0)
    r, colour = hash_at(x - left % 3, y) % sum(CAR_WEIGHTS), 0         # a car: three cells, its colour picked in the one that starts it
    while r >= CAR_WEIGHTS[colour]:
        r -= CAR_WEIGHTS[colour]
        colour += 1
    return car_name(base, "lmr"[left % 3], colour)
