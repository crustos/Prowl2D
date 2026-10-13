"""generated.py: sprites that make themselves, as ASCII art.

A level written in emoji can use a tile (🧱, 🌳) that has no sprite yet. For the tiles that are never quite the same twice, asciiart.import_levels asks this module
for a *family* of sprites: a brick wall is mostly plain brick in three shades, sometimes weathered or flecked with paint, and rarely has a brick missing, a weep hole
or a pipe in it; a tree is an oak, a broad one, a tall one, a pine, one with apples or blossom or autumn leaves, a birch, a sapling, a dead one. Each is an ordinary sprite
(the sprite ASCII format of prowl.py --import-ascii, with a header palette) that can be opened and painted over in the editor, and the tile gets `variants`: the
sprites and how often each is picked (model.TileDef.pick_variant picks one for each cell of a level, the same one every time). Only made when the project has no
sprite for the tile.

    family("brick")        -> [("brick", 360, text), ("brick_b", 220, text), ... ("brick_pipe", 5, text)]      (name, weight, sprite text)
    sprite_text("brick")   -> the text of the first

The bricks all have the same joints, and nothing in them crosses the edge of the sprite except the pipe that goes down the whole of it, so every variant tiles with every
other, up, down and sideways. The art depends only on its arguments (`seed` picks the shades), so the same level always makes the same sprites.
"""
import math
import random

from . import streetscape

BRICK_PALETTE = {
    "M": "#6e5f58",      # the mortar
    "R": "#b5543c",      # the bricks, three shades
    "S": "#a24a35",
    "T": "#c2603f",
    "H": "#cf7255",      # the lit top edge of a brick
    "D": "#8f3f2e",      # a dark speckle
}
COURSE = 4               # a course of bricks is 3 rows of brick and 1 of mortar (under it)


def brick_rows(size=16, seed=0):
    """The rows of a wall of bricks in running bond (every other course is shifted by half a brick), `size` x `size`, that tiles: put two side by side, or one on
    top of another, and the joints carry on. `size` is a multiple of 8 (the bricks are half a tile wide)."""
    if size < 8 or size % 8:
        raise ValueError("a brick wall is a multiple of 8 pixels (got %d)" % size)
    rng = random.Random("brick/%d/%d" % (size, seed))
    brick_w = size // 2
    shift = brick_w // 2
    courses = size // COURSE
    shades = [[rng.choice("RRST") for _ in range(2)] for _ in range(courses)]
    speck = {}                                           # (course, brick) -> (x, y) of a dark pixel inside it
    for c in range(courses):
        for k in range(2):
            if rng.random() < 0.6:
                speck[(c, k)] = (rng.randrange(1, brick_w - 2), rng.randrange(1, COURSE - 2))
    rows = []
    for y in range(size):
        c, ry = divmod(y, COURSE)
        row = []
        for x in range(size):
            u = (x + (c % 2) * shift) % size             # x along the course, counted from where its first brick starts
            k, rx = divmod(u, brick_w)
            if ry == COURSE - 1 or rx == brick_w - 1:    # the bed joint under a course, the head joint at the end of a brick
                row.append("M")
            elif ry == 0:
                row.append("H")
            elif speck.get((c, k)) == (rx, ry):
                row.append("D")
            else:
                row.append(shades[c][k])
        rows.append("".join(row))
    return rows


def brick_text(name="brick", size=16, seed=0):
    return _text(name, BRICK_PALETTE, brick_rows(size, seed))

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# brick variants: each takes the grid of a plain wall (a list of lists of characters) and changes it, keeping the joints where they were

BRICK_PALETTE.update({
    "E": "#7b3828",      # eroded brick, darker and rougher
    "K": "#2b2320",      # a hole: the dark inside of the wall
    "N": "#3d322d",      # ...its lighter side
    "W": "#e8e4d8",      # white paint
    "V": "#c9c4b6",      # ...in shade
    "G": "#8c959c",      # a pipe
    "L": "#bcc4ca",      # ...lit
    "Z": "#59626a",      # ...in shade
    "a": "#a04836", "e": "#92402f", "f": "#aa523d", "h": "#b96450",      # grimy brick: R S T H, with dust and soot in them
    "1": "#c0654b", "2": "#b45d44", "3": "#cb7256", "4": "#d68566",      # sun-bleached brick, the same four
    "d": "#52433c",      # soot and dirt
    "t": "#26211f",      # tar
    "u": "#9a4a22",      # rust
    "w": "#a8957c",      # the beige of paint that buffs graffiti out
    "k": "#141013",      # the black of a tag's outline
    "r": "#d62f3a", "b": "#2f6fd6", "g": "#2fa84f", "y": "#f0c93a", "p": "#8a3fd0", "o": "#f08a2e", "c": "#35c6d8",      # spray paint
})
SPRAY = "rbgypoc"
DIRTY = {"R": "a", "S": "e", "T": "f", "H": "h", "M": "d"}
BLEACHED = {"R": "1", "S": "2", "T": "3", "H": "4"}


def _pixels(size):
    """[(x, y, course, brick, rx, ry)] of the pixels inside a brick (not the joints). rx, ry count from the brick's top left corner."""
    brick_w, shift = size // 2, size // 4
    out = []
    for y in range(size):
        c, ry = divmod(y, COURSE)
        for x in range(size):
            k, rx = divmod((x + (c % 2) * shift) % size, brick_w)
            if ry < COURSE - 1 and rx < brick_w - 1:
                out.append((x, y, c, k, rx, ry))
    return out


def _whole_bricks(size):
    """[(course, brick)] of the bricks that are in one piece in the sprite (a brick of a shifted course that wraps round the edge is not)."""
    return [(c, k) for c in range(size // COURSE) for k in range(2) if c % 2 == 0 or k == 1]


def _eroded(g, rng, size, heavy):
    brick_w = size // 2
    for x, y, c, k, rx, ry in _pixels(size):
        corner = rx in (0, brick_w - 2) and ry in (0, COURSE - 2)
        if corner and rng.random() < (0.55 if heavy else 0.3):
            g[y][x] = rng.choice("MMD")                       # a chipped corner, down to the mortar
        elif heavy and (rx in (0, brick_w - 2) or ry == COURSE - 2) and rng.random() < 0.35:
            g[y][x] = "E"                                     # crumbling edges
    pits = _pixels(size)
    for x, y, *_ in rng.sample(pits, 9 if heavy else 4):
        g[y][x] = rng.choice("EED")
    return g


def _paint(g, rng, size, keep):
    """White paint over the bricks; `keep(x, y)` says where it has gone and the brick shows."""
    for x, y, c, k, rx, ry in _pixels(size):
        if not keep(x, y):
            g[y][x] = "V" if ry == COURSE - 2 or rng.random() < 0.22 else "W"
    return g


def _flaking(g, rng, size):
    blobs = [(rng.randrange(size), rng.randrange(size), rng.uniform(1.8, 3.6)) for _ in range(4)]
    gone = lambda x, y: any((x - bx) ** 2 + (y - by) ** 2 < r * r for bx, by, r in blobs) or rng.random() < 0.08
    return _paint(g, rng, size, gone)


def _flecked(g, rng, size):
    pix = {(x, y) for x, y, *_ in _pixels(size)}
    for _ in range(6):
        x, y = rng.choice(sorted(pix))
        for p in ((x, y), rng.choice(((x + 1, y), (x, y + 1)))):
            if p in pix:
                g[p[1]][p[0]] = "W"
    return g


def _missing(g, rng, size):
    brick_w = size // 2
    c, k = rng.choice([b for b in _whole_bricks(size) if 0 < b[0] < size // COURSE - 1])
    for x, y, cc, kk, rx, ry in _pixels(size):
        if (cc, kk) == (c, k):
            g[y][x] = "K" if ry == 0 or rx == 0 else "N"
    return g


def _weep(g, rng, size):
    """An open head joint: a weep hole, the slot where water leaves the wall."""
    c = rng.choice([c for c in range(1, size // COURSE - 1) if c % 2 == 0])
    for ry in range(COURSE - 1):
        g[c * COURSE + ry][size // 2 - 1] = "K"
    return g


def _disc(size, cx, cy, r):
    return [(x, y) for y in range(size) for x in range(size) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r]


def _drain(g, rng, size):
    for x, y in _disc(size, size / 2, size / 2, 3.6):
        g[y][x] = "M"
    for x, y in _disc(size, size / 2, size / 2, 2.6):
        g[y][x] = "K" if y < size // 2 + 1 else "N"
    return g


def _pipe(g, rng, size):
    """The end of a pipe that comes out of the wall."""
    cx = cy = size / 2
    for x, y in _disc(size, cx, cy, 4.4):
        g[y][x] = "Z"
    for x, y in _disc(size, cx, cy, 3.6):
        g[y][x] = "L" if (x + y) < size - 2 else "G"
    for x, y in _disc(size, cx, cy, 2.0):
        g[y][x] = "K"
    return g


def _downpipe(g, rng, size):
    """A pipe down the whole of the sprite (so two of them one over the other are one pipe), with two brackets."""
    x0 = size // 2 - 2
    for y in range(size):
        for i, ch in enumerate("LGGZ"):
            g[y][x0 + i] = ch
    for y in (3, 11):
        for x in range(x0 - 1, x0 + 5):
            g[y][x] = "G"
            g[y + 1][x] = "Z"
    return g


def _recolor(g, table, chance=1.0, rng=None, only=None):
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch in table and (chance >= 1.0 or rng.random() < chance) and (only is None or only(x, y)):
                row[x] = table[ch]
    return g


def _dirty(g, rng, size):
    """The whole wall grimy: darker bricks, dust in the joints, and pits of soot."""
    _recolor(g, DIRTY, 0.7, rng)
    for x, y, *_ in rng.sample(_pixels(size), 14):
        g[y][x] = rng.choice("dde")
    return g


def _soot(g, rng, size):
    """Black streaks running down from the top where rain carries the soot, over a grimy wall."""
    _recolor(g, DIRTY, 0.5, rng)
    for x in rng.sample(range(size), 5):
        for y in range(rng.randint(5, 13)):
            if rng.random() < 0.85 - y * 0.03:
                g[y][x] = "d" if g[y][x] in "Md" else rng.choice("de")
    return g


def _bleached(g, rng, size):
    """Brick faded by years of valley sun: paler, with a few bricks that kept their colour."""
    _recolor(g, BLEACHED, 0.9, rng)
    for x, y, *_ in rng.sample(_pixels(size), 8):
        g[y][x] = rng.choice("VMD")
    return g


def _stained(g, rng, size):
    """White salt (efflorescence) and damp coming out of the bricks, thicker toward the bottom."""
    for x, y, *_ in _pixels(size):
        if rng.random() < 0.05 + 0.5 * (y / size) ** 3:
            g[y][x] = "V" if rng.random() < 0.6 else "W"
    return _recolor(g, DIRTY, 0.3, rng)


def _rust(g, rng, size):
    """Rust running down from a bolt or a nail."""
    x = rng.randint(4, size - 5)
    g[1][x] = "Z"
    g[2][x] = "G"
    for y in range(3, size - rng.randint(0, 4)):
        if g[y][x] != "M" or rng.random() < 0.5:
            g[y][x] = "u"
        if rng.random() < 0.35:
            x = max(1, min(size - 2, x + rng.choice((-1, 1))))
        if rng.random() < 0.4:
            g[y][x + rng.choice((-1, 1))] = "u" if rng.random() < 0.6 else "d"
    return g


def _blob(g, rng, size, cx, cy, rx, ry, ch):
    pts = []
    for y in range(size):
        for x in range(size):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1.0 + rng.uniform(-0.35, 0.35):
                g[y][x] = ch
                pts.append((x, y))
    return pts


def _tar(g, rng, size):
    """A patch of tar over a crack, with a shine on it."""
    pts = _blob(g, rng, size, rng.randint(6, 10), rng.randint(6, 10), rng.uniform(2.2, 3.4), rng.uniform(1.6, 2.6), "t")
    for x, y in rng.sample(pts, min(len(pts), 3)):
        g[y][x] = "d"
    return g


def _stamp(g, art, x0, y0, colors, outline=None):
    """Draws `art` (rows; '.' leaves the wall) at x0, y0 in the sprite; `colors` maps an art character to a wall character. The black outline
    goes round it first, if `outline` is on, so that it reads as a tag and not as a stain."""
    size = len(g)
    mine = {(x0 + i, y0 + j): colors.get(ch, ch) for j, row in enumerate(art) for i, ch in enumerate(row) if ch != "."}
    ring = {(x + dx, y + dy) for x, y in mine for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(mine) if outline else set()
    for (x, y), ch in [(p, "k") for p in ring] + list(mine.items()):
        if 0 <= x < size and 0 <= y < size:
            g[y][x] = ch
    return mine


def _drips(g, rng, size, painted, col, count=2):
    low = sorted((p for p in painted if painted[p] == col), key=lambda p: -p[1])[:8]
    for x, y in rng.sample(low, min(count, len(low))):
        for dy in range(1, rng.randint(2, 4)):
            if y + dy < size:
                g[y + dy][x] = col


def _tag_swoosh(g, rng, size):
    """A tagger's signature: one fast line of spray with a shadow and drips."""
    col = rng.choice(SPRAY)
    ys = [rng.randint(8, 11), rng.randint(3, 6), rng.randint(8, 12), rng.randint(3, 6), rng.randint(7, 10)]
    pts = [(1 + 3 * i, y) for i, y in enumerate(ys)]
    art = [["."] * size for _ in range(size)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            art[y0 + (y1 - y0) * i // n][x0 + (x1 - x0) * i // n] = col
    for y in range(size):                                                       # a second pass, a pixel lower: the stroke is two thick
        for x in range(size):
            if art[y][x] == col and y + 1 < size and art[y + 1][x] == ".":
                art[y + 1][x] = col
                break
    painted = _stamp(g, ["".join(r) for r in art], 0, 0, {}, outline=True)
    _drips(g, rng, size, painted, col)
    return g


GLYPH_O = ["..####..", ".######.", "##....##", "##....##", "##....##", "##....##", ".######.", "..####.."]
GLYPH_X = ["##....##", "###..###", ".######.", "..####..", "..####..", ".######.", "###..###", "##....##"]
GLYPH_K = ["##...##", "##..##.", "##.##..", "####...", "##.##..", "##..##.", "##...##", "##...##"]


def _tag_bubble(g, rng, size):
    """Throw-up: two fat bubble letters, filled, with a black outline and a white shine."""
    a, b = rng.sample(SPRAY, 2)
    first, second = rng.choice(((GLYPH_O, GLYPH_X), (GLYPH_K, GLYPH_O), (GLYPH_X, GLYPH_K)))
    painted = {}
    painted.update(_stamp(g, first, 0, 4, {"#": a}, outline=True))
    painted.update(_stamp(g, second, 8, 4, {"#": b}, outline=True))
    for x, y in ((2, 6), (10, 6)):
        g[y][x] = "W"
    _drips(g, rng, size, painted, a, 1)
    _drips(g, rng, size, painted, b, 1)
    return g


def _small(art):
    def make(g, rng, size):
        col = rng.choice(SPRAY)
        w, h = len(art[0]), len(art)
        painted = _stamp(g, art, rng.randint(1, size - w - 1), rng.randint(1, size - h - 4), {"#": col}, outline=True)
        _drips(g, rng, size, painted, col, 1)
        return g
    return make


STAR = ["...#...", "..###..", "#######", ".#####.", "..###..", ".##.##.", "##...##"]
HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
CROWN = ["#.#.#.#", "#######", "#######", ".#####."]
ARROW = ["...#....", "...##...", "########", "...##...", "...#...."]


def _eyes(g, rng, size):
    """A pair of watching eyes: a sticker artist's mark."""
    eye = [".WWW.", "WWKWW", ".WWW."]
    _stamp(g, eye, 2, 6, {}, outline=True)
    _stamp(g, eye, 9, 6, {}, outline=True)
    return g


def _sticker(g, rng, size):
    col, col2 = rng.sample(SPRAY, 2)
    w, h = rng.randint(7, 9), rng.randint(5, 7)
    x0, y0 = rng.randint(1, size - w - 1), rng.randint(1, size - h - 1)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            g[y][x] = "W" if edge else col if (x + y) % 3 else col2
    for _ in range(3):
        g[rng.randint(y0 + 1, y0 + h - 2)][rng.randint(x0 + 1, x0 + w - 2)] = "k"
    g[y0][x0 + w - 1] = "V"                                                     # a peeling corner
    return g


def _poster(g, rng, size):
    """A wheatpaste poster, torn and weathered, with its lines of print."""
    x0, y0, w, h = rng.randint(2, 4), 1, rng.randint(8, 10), 13
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            torn = (y > y0 + h - 3 and rng.random() < 0.5) or (x == x0 + w - 1 and rng.random() < 0.4)
            if not torn:
                g[y][x] = "V" if rng.random() < 0.3 else "W"
    for y in range(y0 + 2, y0 + h - 3, 2):
        for x in range(x0 + 1, x0 + w - 1 - rng.randint(0, 3)):
            if rng.random() < 0.8:
                g[y][x] = "k" if y < y0 + 5 else "Z"
    for x, y in ((x0, y0), (x0 + w - 1, y0)):
        g[y][x] = "G"                                                           # staples
    return g


def _buffed(g, rng, size):
    """Graffiti the city painted over in the wrong beige: a clean patch that matches nothing, with a ghost of the tag showing through."""
    x0, y0, w, h = rng.randint(1, 3), rng.randint(2, 5), rng.randint(9, 12), rng.randint(6, 8)
    col = rng.choice(SPRAY)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if (x in (x0, x0 + w - 1) and y in (y0, y0 + h - 1)) or rng.random() < 0.05:
                continue
            g[y][x] = "w"
    for _ in range(4):
        g[rng.randint(y0 + 1, y0 + h - 2)][rng.randint(x0 + 1, x0 + w - 2)] = col
    for x in range(x0 + 1, x0 + w - 1):                                         # a roller's edge
        if rng.random() < 0.5:
            g[y0 + h][x] = "w"
    return g


def _variant(base_seed, change=None, *args):
    def make(size):
        rng = random.Random("brick-variant/%s/%d" % (getattr(change, "__name__", "plain"), base_seed))
        g = [list(r) for r in brick_rows(size, base_seed)]
        return ["".join(r) for r in (change(g, rng, size, *args) if change else g)]
    return make


BRICK_VARIANTS = [         # (suffix, weight, rows(size)): the first is the sprite that has the tile's name
    ("", 190, _variant(0)),
    ("b", 130, _variant(1)),
    ("c", 130, _variant(2)),
    ("dirty", 100, _variant(13, _dirty)),
    ("dirty_b", 70, _variant(14, _dirty)),
    ("soot", 60, _variant(15, _soot)),
    ("bleached", 50, _variant(16, _bleached)),
    ("stained", 40, _variant(17, _stained)),
    ("rust", 25, _variant(18, _rust)),
    ("tar", 20, _variant(19, _tar)),
    ("eroded", 40, _variant(3, _eroded, False)),
    ("worn", 25, _variant(4, _eroded, True)),
    ("flecked", 30, _variant(5, _flecked)),
    ("flaking", 20, _variant(6, _flaking)),
    ("painted", 10, _variant(7, lambda g, rng, size: _paint(g, rng, size, lambda x, y: False))),
    ("buffed", 25, _variant(20, _buffed)),
    ("tag", 22, _variant(21, _tag_swoosh)),
    ("tag_b", 14, _variant(22, _tag_swoosh)),
    ("throwup", 14, _variant(23, _tag_bubble)),
    ("star", 8, _variant(24, _small(STAR))),
    ("heart", 6, _variant(25, _small(HEART))),
    ("crown", 5, _variant(26, _small(CROWN))),
    ("arrow", 6, _variant(27, _small(ARROW))),
    ("eyes", 6, _variant(28, _eyes)),
    ("sticker", 12, _variant(29, _sticker)),
    ("poster", 10, _variant(30, _poster)),
    ("missing", 5, _variant(8, _missing)),
    ("weep", 6, _variant(9, _weep)),
    ("drain", 5, _variant(10, _drain)),
    ("pipe", 4, _variant(11, _pipe)),
    ("downpipe", 4, _variant(12, _downpipe)),
]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# paint-over patches: the city paints the graffiti out, in whatever grey the truck had, again and again. These break the tiling rule on purpose: a patch is a
# rectangle of a grey, from a few cells to a good part of the wall, with edges that fall anywhere on a half cell, painted over the bricks and over the patches
# before it. Where the patches are is a function of the position in the level (patch_code), so the same level always has the same walls.

GREYS = [      # (main, dark, light): cool, warm, pale and dark grey paint, each with the shade of the joints showing through and of the roller's streaks
    (("j", "#9b9da0"), ("m", "#70737a"), ("5", "#b4b6b8")),
    (("q", "#aaa69c"), ("n", "#7f7b72"), ("6", "#c0bcb2")),
    (("s", "#c4c6c4"), ("x", "#8f9290"), ("7", "#d8dad8")),
    (("v", "#6c7276"), ("z", "#4a5054"), ("8", "#80888d")),
]
PATCH_LAYERS = ((16, 0.20), (10, 0.25), (6, 0.25))      # (the lattice cell in half cells, the chance that it has a patch), oldest first: a later layer paints over


def _hash(*vals):
    h = 2166136261
    for v in vals:
        h = ((h ^ (v & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 0x5BD1E995) & 0xFFFFFFFF
    return h ^ (h >> 15)


def _grey_at(hx, hy, salt):
    """Which grey (1..4, 0 for none) paints the half cell (hx, hy) of the level: each layer is a lattice with at most one rectangle in each of its cells."""
    grey = 0
    for layer, (size, chance) in enumerate(PATCH_LAYERS):
        cx, cy = hx // size, hy // size
        h = _hash(salt, layer, cx, cy)
        if (h % 1000) / 1000.0 >= chance:
            continue
        w, t = size // 2 + (h >> 10) % (size // 2 + 1), size // 2 + (h >> 14) % (size // 2 + 1)
        ox, oy = (h >> 18) % (size - w + 1), (h >> 22) % (size - t + 1)
        if ox <= hx % size < ox + w and oy <= hy % size < oy + t:
            grey = 1 + _hash(h, 7) % len(GREYS)
    return grey


def patch_code(x, y, salt=0):
    """The paint over the cell (x, y): four digits, the grey (1..4) over its top left, top right, bottom left and bottom right quarter, 0 for bare brick;
    '0000' where nothing was painted."""
    return "".join(str(_grey_at(2 * x + i, 2 * y + j, salt)) for j in (0, 1) for i in (0, 1))


def patch_text(code, name, size=16):
    """The sprite of a cell painted as `code` says (patch_code): bricks, with a grey over each quarter that has one. The joints show through the paint, a few
    bricks show where the roller missed, and the paint is streaked. Every cell's quarters meet the next one's on a straight line, so a patch runs on over cells."""
    rng = random.Random("patch/" + code)
    g = [list(r) for r in brick_rows(size, int(code, 5) % 3)]
    half = size // 2
    for y in range(size):
        for x in range(size):
            grey = int(code[(y // half) * 2 + x // half])
            if not grey:
                continue
            main, dark, light = GREYS[grey - 1]
            ch = g[y][x]
            r = rng.random()
            if r < 0.010:
                continue                                                         # the roller missed: the brick shows
            if r < 0.013:
                g[y][x] = rng.choice("rbgypoc")                                  # the tag, still there under the paint
            elif ch == "M":
                g[y][x] = dark[0] if r < 0.5 else main[0]                        # the joints are only a trace under the paint
            elif (x * 7 + grey * 3) % 5 == 0 and r < 0.22 or (y * 5 + grey) % 7 == 0 and r < 0.15:
                g[y][x] = light[0]                                               # the roller's streaks
            else:
                g[y][x] = dark[0] if r > 0.985 else main[0]
    palette = {k: v for grey in GREYS for k, v in grey}
    return _text(name, {**BRICK_PALETTE, **palette}, ["".join(r) for r in g])



# ---------------------------------------------------------------------------------------------------------------------------------------------------
# trees: 16 x 16, standing on the bottom row, in front of nothing ('.')

TREE_PALETTE = {
    "B": "#6b4a2f",      # trunk
    "O": "#432d1c",      # ...in shade, and the marks on a birch
    "F": "#3f8f3a",      # leaves
    "J": "#28622b",      # ...in shade
    "Q": "#6db84f",      # ...lit
    "A": "#d6362f",      # an apple
    "P": "#f4a9c8",      # blossom
    "C": "#d8719f",      # ...in shade
    "U": "#d9822b",      # autumn leaves
    "X": "#e8bd3b",      # ...yellow
    "Y": "#a85a1d",      # ...in shade
    "I": "#e9e6da",      # a birch's trunk
}


def _tree(size, seed, kind):
    rng = random.Random("tree/%s/%d" % (kind, seed))
    g = [["."] * size for _ in range(size)]
    s = size / 16.0
    leaves = {"mid": "F", "light": "Q", "dark": "J"}
    if kind == "blossom":
        leaves = {"mid": "P", "light": "P", "dark": "C"}
    crown, trunk, trunk_ch, mark = [], (7, 8, 10), "B", None
    if kind in ("oak", "apple", "blossom", "autumn"):
        crown = _disc(size, 8 * s, 6 * s, 5.6 * s)
    elif kind == "broad":
        crown = sorted(set(_disc(size, 5 * s, 7.4 * s, 4.2 * s) + _disc(size, 11 * s, 7.4 * s, 4.2 * s) + _disc(size, 8 * s, 5 * s, 4.8 * s)))
        trunk = (7, 8, 11)
    elif kind == "tall":
        crown = [(x, y) for x, y in _disc(size, 8 * s, 6.2 * s, 6.2 * s) if abs(x + 0.5 - 8 * s) <= 3.8 * s]
        trunk = (7, 8, 12)
    elif kind == "birch":
        crown = [(x, y) for x, y in _disc(size, 8 * s, 5.6 * s, 5.4 * s) if abs(x + 0.5 - 8 * s) <= 4.2 * s]
        trunk, trunk_ch, mark = (7, 8, 10), "I", "O"
        leaves = {"mid": "Q", "light": "Q", "dark": "F"}
    elif kind == "sapling":
        crown = _disc(size, 8 * s, 10 * s, 3.1 * s)
        trunk = (7, 8, 12)
    for x, y in crown:
        dx, dy = (x + 0.5) / s - 8, (y + 0.5) / s - 6
        shade = leaves["dark"] if (dx + dy > 3.2 or rng.random() < 0.12) else leaves["light"] if (dx + dy < -3.6 or rng.random() < 0.12) else leaves["mid"]
        if kind == "autumn":
            shade = rng.choice("UUXY") if shade == "F" else {"J": "Y", "Q": "X"}[shade]
        g[y][x] = shade
    if kind == "apple":
        for x, y in rng.sample(sorted(crown), 5):
            g[y][x] = "A"
    if kind == "pine":
        for y in range(int(13 * s)):
            half = (1.0 + (y // 4) * 1.8 + (y % 4) * 0.55) * s                 # three tiers, each wider than the one above
            for x in range(size):
                d = x + 0.5 - 8 * s
                if abs(d) <= half:
                    g[y][x] = "Q" if d < -half * 0.45 else "J" if d > half * 0.3 or y % 4 == 3 else "F"
        trunk = (7, 8, 13)
    if kind == "bare":
        for x, y in ((7, 8), (6, 7), (5, 6), (4, 5), (3, 5), (8, 8), (9, 7), (10, 6), (11, 5), (12, 5), (7, 7), (7, 6), (8, 5), (8, 4), (7, 3), (6, 5), (10, 5)):
            g[int(y * s)][int(x * s)] = "B"
        trunk = (7, 8, 9)
    x0, x1, top = trunk
    for y in range(int(top * s), size):
        for x in range(int(x0 * s), int((x1 + 1) * s)):
            g[y][x] = trunk_ch if x < int(x1 * s) or trunk_ch == "I" and rng.random() < 0.7 else "O"
            if mark and rng.random() < 0.18:
                g[y][x] = mark
    for x in (int(x0 * s) - 1, int((x1 + 1) * s)):                 # the roots
        g[size - 1][x] = "B"
    return ["".join(r) for r in g]


def _tree_variant(kind, seed):
    return lambda size: _tree(size, seed, kind)


TREE_VARIANTS = [
    ("", 300, _tree_variant("oak", 0)),
    ("broad", 240, _tree_variant("broad", 1)),
    ("tall", 150, _tree_variant("tall", 2)),
    ("pine", 90, _tree_variant("pine", 3)),
    ("birch", 80, _tree_variant("birch", 4)),
    ("apple", 60, _tree_variant("apple", 5)),
    ("autumn", 60, _tree_variant("autumn", 6)),
    ("blossom", 50, _tree_variant("blossom", 7)),
    ("sapling", 40, _tree_variant("sapling", 8)),
    ("bare", 20, _tree_variant("bare", 9)),
]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# roads: the street of a side-scrolling brawler (Final Fight): a band across the bottom of the screen, a few cells thick, that goes on to the left and the right, with
# a kerb along its top, and a dashed yellow line down the middle of it, low on the screen. A ◼️ is a piece of the street, not a whole one: a column of them is the street
# a few cells deep, and each is drawn for its place in it. In a band n cells deep (counting down from the kerb: up = 0, 1, 2...) the top cell has the kerb, the bottom
# cell the gutter if something other than the level's edge is under it, and the cell where up == n // 2 has the line: the middle cell, and the lower of the middle two.
# Each of the 8 shapes has 5 looks: plain twice, cracked with weeds, patched, and a pothole or an oil stain.

ROAD_PALETTE = {
    "A": "#4b4e53", "B": "#44474c", "C": "#54575d",         # asphalt, three shades
    "x": "#2a2c30",         # a crack, a pothole, the shadow of the kerb
    "o": "#2f3138",         # oil
    "a": "#3b3e43",         # a patch of newer asphalt
    "p": "#aca89f", "q": "#8b877f", "k": "#66635d",         # the pavement, its joints, the kerb's face
    "y": "#d6b43a", "Y": "#b4962f",                         # the line, faded
    "g": "#5f8238",         # weeds in the cracks
}
ROAD_WEIGHTS = [50, 25, 12, 8, 5]           # how often each look is used
KERB, GUTTER, LINE = 1, 2, 4                # the parts of a shape
STRAIGHT = LINE                             # the shape that is the road's own sprite (named just `road`): asphalt with the line


def road_name(base, shape, look):
    """The name of the sprite of a road cell: `road` for the middle of the street, plain, else road_SHAPE_LOOK (the shape's number, 0 to 7)."""
    return base if (shape, look) == (STRAIGHT, 0) else "%s_%d_%d" % (base, shape, look)


def road_shape(up, down, kerb_above, kerb_below):
    """The shape of the road cell that has `up` road cells above it and `down` below it in the street; kerb_above says that what is above the street is not the level's
    edge (it has a kerb), and kerb_below the same for the bottom (it has a gutter)."""
    n = up + 1 + down
    return (KERB if up == 0 and kerb_above else 0) | (GUTTER if down == 0 and kerb_below else 0) | (LINE if up == n // 2 else 0)


def road_rows(shape, look, size=16):
    rng = random.Random("road/%d/%d" % (shape, look))
    g = [[rng.choice("AAAABC") for _ in range(size)] for _ in range(size)]
    if shape & KERB:
        for x in range(size):
            g[0][x] = g[1][x] = "q" if x % 8 == 0 else "p"                  # the pavement's edge, in slabs
            g[2][x] = "k"                                                    # the kerb's face
            g[3][x] = "x"                                                    # its shadow on the asphalt
            if rng.random() < 0.4:
                g[4][x] = "B"
        for x in rng.sample(range(size), 3):
            g[1][x] = "q"                                                    # a stain on the slab
    if shape & GUTTER:
        for x in range(size):
            g[size - 2][x] = "q" if x % 8 else "k"
            g[size - 1][x] = "k"
    if shape & LINE:
        for x in range(size):
            if x % 16 < 10:                                                  # long dashes: ten on and six off, the same in every cell, so they run on
                for y in (size // 2 - 1, size // 2):
                    g[y][x] = "Y" if rng.random() < 0.18 else "y"
    free = [(x, y) for y in range(size) for x in range(size) if g[y][x] in "ABC"]
    if look == 2:                                                            # cracked, with weeds in the crack
        x, y = rng.randint(3, size - 4), rng.randint(5, size - 6)
        for _ in range(12):
            if g[y][x] in "ABC":
                g[y][x] = "x"
            x = max(0, min(size - 1, x + rng.choice((-1, 0, 1, 1))))
            y = max(0, min(size - 1, y + rng.choice((-1, 0, 1))))
        for _ in range(2):
            wx, wy = rng.choice(free)
            if g[wy][wx] in "ABC":
                g[wy][wx] = "g"
    elif look == 3:                                                          # a patch of newer asphalt, a rectangle with a ragged edge
        w, h = rng.randint(5, 9), rng.randint(3, 6)
        x0, y0 = rng.randint(1, size - w - 1), rng.randint(5, size - h - 3)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if g[y][x] in "ABC" and rng.random() < 0.93:
                    g[y][x] = "a"
    elif look == 4:                                                          # a pothole with a broken rim, or an oil stain
        cx, cy = rng.randint(4, size - 5), rng.randint(6, size - 6)
        for y in range(size):
            for x in range(size):
                d = ((x + 0.5 - cx) / 3.2) ** 2 + ((y + 0.5 - cy) / 1.8) ** 2
                if g[y][x] in "ABCa":
                    if d <= 1.0:
                        g[y][x] = "x" if shape % 2 else "o"
                    elif d <= 1.7 and shape % 2 and rng.random() < 0.5:
                        g[y][x] = "B"
    return ["".join(r) for r in g]


def road_family(base="road", size=16):
    out = []
    for shape in range(8):
        for look in range(5):
            name = road_name(base, shape, look)
            out.append((name, ROAD_WEIGHTS[look], _text(name, ROAD_PALETTE, road_rows(shape, look, size))))
    out.sort(key=lambda t: t[0] != base)                                    # the sprite that has the tile's name first
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# rocks: 16 x 16, on the bottom row, in front of nothing

ROCK_PALETTE = {
    "W": "#dfe2e4", "l": "#b7bbbf", "m": "#8b9096", "d": "#5f6369", "k": "#34373c",           # grey stone, light to dark, and its outline
    "G": "#7da35a", "H": "#4f7a3b",                                                           # moss
    "s": "#cdaa72", "S": "#a38150", "T": "#7d5f38",                                           # sandstone
    "n": "#4e4e58", "N": "#2e2e36", "V": "#6b6b78",                                           # basalt
}
ROCK_SETS = {"grey": "Wlmdk", "sand": "WsSTk", "basalt": "VnnNk"}


def _rock(g, rng, cx, cy, rx, ry, tones="Wlmdk", lumpy=0.18, angular=False):
    """A lump of stone centred at (cx, cy), lit from the top left, with a dark outline."""
    size = len(g)
    n = 9
    radii = [1.0 + rng.uniform(-lumpy, lumpy) * (2 if angular else 1) for _ in range(n)]
    body = []
    for y in range(size):
        for x in range(size):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            ang = (math.atan2(dy, dx) % (2 * math.pi)) / (2 * math.pi) * n
            r = radii[int(ang) % n] * (1 - frac(ang)) + radii[(int(ang) + 1) % n] * frac(ang) if not angular else radii[int(ang) % n]
            if dx * dx + dy * dy <= r * r:
                body.append((x, y, dx, dy))
    cells = {(x, y) for x, y, *_ in body}
    for x, y, dx, dy in body:
        edge = any((x + a, y + b) not in cells for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        light = -(dx * 0.6 + dy * 0.8) + rng.uniform(-0.18, 0.18)
        tone = tones[0] if light > 0.75 else tones[1] if light > 0.15 else tones[2] if light > -0.45 else tones[3]
        g[y][x] = tones[4] if edge and (dx + dy > -0.3 or rng.random() < 0.5) else tone
    return cells


def frac(v):
    return v - int(v)


def _rock_grid(size=16):
    return [["."] * size for _ in range(size)]


def _rocks(kind, seed, size=16):
    rng = random.Random("rock/%s/%d" % (kind, seed))
    g = _rock_grid(size)
    s = size / 16.0
    tones = ROCK_SETS["sand" if kind == "sandstone" else "basalt" if kind == "basalt" else "grey"]
    if kind in ("boulder", "mossy", "cracked", "sandstone", "basalt"):
        cells = _rock(g, rng, 8 * s, 10 * s, 6.3 * s, 5.2 * s, tones)
    elif kind == "wide":
        cells = _rock(g, rng, 8 * s, 11.5 * s, 7 * s, 3.8 * s, tones)
    elif kind == "pair":
        _rock(g, rng, 5 * s, 11 * s, 4.3 * s, 4 * s, tones)
        cells = _rock(g, rng, 11.5 * s, 12.2 * s, 3.5 * s, 2.8 * s, tones)
    elif kind == "three":
        _rock(g, rng, 4.5 * s, 12 * s, 3.3 * s, 3 * s, tones)
        _rock(g, rng, 10 * s, 11 * s, 4 * s, 3.8 * s, tones)
        cells = _rock(g, rng, 13 * s, 13.6 * s, 2.2 * s, 1.8 * s, tones)
    elif kind == "tall":
        cells = _rock(g, rng, 8 * s, 8.5 * s, 4.4 * s, 7 * s, tones, lumpy=0.22, angular=True)
    elif kind == "slab":
        cells = _rock(g, rng, 8 * s, 12.6 * s, 7.4 * s, 2.6 * s, tones, lumpy=0.12)
    elif kind == "rubble":
        for cx, cy, r in ((4, 13.2, 2.4), (8, 13, 2.8), (12, 13.3, 2.4), (6, 10.2, 2.4), (10, 10.4, 2.4), (8, 7.6, 2.2)):
            _rock(g, rng, cx * s, cy * s, r * s, r * 0.85 * s, tones)
        cells = {(x, y) for y in range(size) for x in range(size) if g[y][x] != "."}
    else:                                                              # pebbles
        cells = set()
        for _ in range(7):
            cx, cy = rng.randint(2, size - 3), rng.randint(9, size - 2)
            cells |= _rock(g, rng, cx + 0.5, cy + 0.5, rng.choice((1.1, 1.5, 1.9)) * s, rng.choice((0.9, 1.2)) * s, tones, lumpy=0.05)
    if kind == "mossy":
        for x, y in sorted(cells):
            if y < 9 * s and rng.random() < 0.5 - (y / size) * 0.4 and g[y][x] != "k":
                g[y][x] = rng.choice("GGH")
    if kind == "cracked":
        x, y = rng.randint(6, 10), 6
        for _ in range(8):
            if (x, y) in cells:
                g[y][x] = "k"
            x += rng.choice((-1, 0, 0, 1))
            y += 1
    if kind == "sandstone":
        for y in range(5, size, 3):                                    # layers
            for x in range(size):
                if (x, y) in cells and g[y][x] not in "k":
                    g[y][x] = "T" if rng.random() < 0.7 else g[y][x]
    return ["".join(r) for r in g]


def _rock_variant(kind, seed):
    return lambda size: _rocks(kind, seed, size)


ROCK_VARIANTS = [
    ("", 300, _rock_variant("boulder", 0)),
    ("wide", 200, _rock_variant("wide", 1)),
    ("pair", 150, _rock_variant("pair", 2)),
    ("three", 100, _rock_variant("three", 3)),
    ("pebbles", 120, _rock_variant("pebbles", 4)),
    ("tall", 80, _rock_variant("tall", 5)),
    ("slab", 60, _rock_variant("slab", 6)),
    ("rubble", 60, _rock_variant("rubble", 7)),
    ("mossy", 80, _rock_variant("mossy", 8)),
    ("cracked", 50, _rock_variant("cracked", 9)),
    ("sandstone", 60, _rock_variant("sandstone", 10)),
    ("basalt", 40, _rock_variant("basalt", 11)),
]


# ---------------------------------------------------------------------------------------------------------------------------------------------------

# a tile's sprite name (see model.slug) -> (palette, variants); the first variant is the sprite with that name, the rest are named NAME_SUFFIX
FAMILIES = {
    "brick": (BRICK_PALETTE, BRICK_VARIANTS),
    "deciduous_tree": (TREE_PALETTE, TREE_VARIANTS),
    "tree": (TREE_PALETTE, TREE_VARIANTS),
    "rock": (ROCK_PALETTE, ROCK_VARIANTS),
    "stone": (ROCK_PALETTE, ROCK_VARIANTS),
    "boulder": (ROCK_PALETTE, ROCK_VARIANTS),
}
FAMILIES.update({
    "window": (streetscape.PAL, streetscape.window_family()),
    "door": (streetscape.PAL, streetscape.door_family()),
    "shutter": (streetscape.PAL, streetscape.shutter_family()),
    "awning": (streetscape.PAL, streetscape.awning_family()),
    "motel_sign": (streetscape.PAL, streetscape.sign_family(["MO", "TEL"])),
    "liquor_sign": (streetscape.PAL, streetscape.sign_family(["LIQ", "UOR"])),
    "tv_sign": (streetscape.PAL, streetscape.sign_family(["TV"])),
    "hydrant": (streetscape.PAL, streetscape.hydrant_family()),
    "dumpster": (streetscape.PAL, streetscape.dumpster_family()),
})
# families whose sprite depends on the cells around it (a cell is drawn for its place in a column of them, or a run): key -> the function that makes all of them
CONNECTS = {"road": road_family, **streetscape.COLUMNS}


GROUPS = {          # kind of tile -> the kinds that stand in it and count as it, for its sake: a car in the street does not give the road a kerb in front of it
    "road": {"car"},
    "sidewalk": {"streetlamp", "hydrant", "dumpster"},
}


def connects_for(key, base):
    """What TileDef.connects holds for the family `key` whose first sprite is named `base`: just the name when it starts with the key, else 'key:name'."""
    return base if base == key or base.startswith(key + "_") else "%s:%s" % (key, base)


def split_connects(connects):
    """(the family's key, the name of its first sprite) from TileDef.connects."""
    if ":" in connects:
        key, base = connects.split(":", 1)
        return key, base
    for k in CONNECTS:
        if connects == k or connects.startswith(k + "_"):
            return k, connects
    return "road", connects


def joined_name(kind, base, x, y, up, down, left, right, above_in, below_in, hash_at):
    """The sprite that draws the cell (x, y) of a tile of `kind`, from the cells of its kind around it (see TileDef.pick_variant)."""
    if kind == "road":
        r, look = hash_at(x, y) % sum(ROAD_WEIGHTS), 0
        while r >= ROAD_WEIGHTS[look]:
            r -= ROAD_WEIGHTS[look]
            look += 1
        return road_name(base, road_shape(up, down, above_in, below_in), look)
    return streetscape.joined_name(kind, base, x, y, up, down, left, right, above_in, hash_at)


def _text(name, palette, rows):
    """The sprite text: `rows` is a list of rows, or a list of lists of rows (the frames of an animation, 4 a second)."""
    if rows and not isinstance(rows[0], str):
        return streetscape.text(name, palette, rows)
    head = ["# sprite: %s" % name, "# fps: 1", "# palette: " + " ".join("%s=%s" % kv for kv in palette.items() if any(kv[0] in r for r in rows))]
    return "\n".join(head + list(rows)) + "\n"


def family(key, name=None, size=16):
    """[(sprite name, weight, ASCII art text)] for the generated tile `key` (a slug such as 'brick'), the first named `name` (default `key`) and the others NAME_SUFFIX;
    or None when nothing makes sprites for `key`."""
    if key in CONNECTS:
        return CONNECTS[key](name or key, size)
    if key not in FAMILIES:
        return None
    palette, variants = FAMILIES[key]
    name = name or key
    return [(name + "_" + suffix if suffix else name, weight, _text(name + "_" + suffix if suffix else name, palette, make(size))) for suffix, weight, make in variants]


PATCHES = {"brick": "_g"}        # a family with paint-over patches: the sprites of a cell are NAME + this + the digits of patch_code


def sprite_text(key, name=None):
    """The ASCII art of the first (the most common) generated sprite for `key`, named `name` (default `key`), or None when nothing makes one."""
    fam = family(key, name)
    return fam[0][2] if fam else None
