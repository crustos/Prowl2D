"""blender_scene.py: a Level as a plain, JSON-able scene description for Blender's grease pencil (the part of the Blender export that needs levelang, PIL and the level; the part that
needs Blender is blender_import.py, which runs in Blender's own Python and reads this).

Everything is vector: each tile's SVG is read by our own parser (`svgvec`), scaled to the tile's size in cells, and kept as polylines with a fill and a stroke. Units are CELLS and y is
DOWN, from the level's top left corner (the importer turns that into Blender's x right, z up). The scene says:

  sprites   shared pictures of things that move: their strokes, in a box of w x h cells (origin at its top left); a swaying one says how it bends
  statics   grease pencil objects built once at the level's place (terrain, a layer's standing scenery, the smooth skin): layers of strokes, in draw order
  objects   what moves: a sprite, where it stands, how it animates, when it disappears
  layers    the parallax layers (a rig each: the importer moves it with the camera)
  bot, camera   keyframes in seconds; the same plan, speed, holds and camera clamp as the GIF preview

A stroke is {"p": [x, y, x, y, ...], "closed", "fill": [r, g, b] | None, "fo": fill opacity, "line": [r, g, b] | None, "lo": line opacity, "w": line width in cells, "cap": "round"|"flat",
"g": a fill group: strokes of one group are filled together (an inner loop is a hole)}.
"""
from __future__ import annotations

import math

from .. import bot as botmod
from .. import svgvec
from ..render.gif import ANIM_PERIOD, SWAY_AMP, _phase, _smooth, _swim, _swim_period
from ..render.skin import skin_loops
from ..render.sprites import color as css_color

VERSION = 1
SWAY_POSES = 24             # poses in one sway cycle: the importer cuts a swaying sprite into this many drawings and loops them
GRADIENT_STEPS = 8          # bands a gradient fill is cut into (grease pencil fills are one flat colour each)


# ---- colour ----------------------------------------------------------------------------------------------------------------------------------

def _rgb(c):
    r, g, b = css_color(c)[:3]
    return (r / 255.0, g / 255.0, b / 255.0)


class Veil:
    """A layer's distance: mix toward the haze colour, fade by alpha (what the preview's `_veil` does to a picture, here to each colour)."""

    def __init__(self, haze=None, alpha=1.0):
        self.haze = (_rgb(haze[0]), float(haze[1])) if haze else None
        self.alpha = float(alpha)

    def key(self):
        return (self.haze, self.alpha) if (self.haze or self.alpha < 1.0) else None

    def __call__(self, rgb):
        if not self.haze:
            return rgb
        h, amt = self.haze
        return tuple(c + (hc - c) * amt for c, hc in zip(rgb, h))


NO_VEIL = Veil()


# ---- polygons ----------------------------------------------------------------------------------------------------------------------------------

def _clip(poly, inside, cut):
    """Sutherland-Hodgman against one edge of a convex clipper: `inside(p)` and `cut(a, b)` (where the segment ab crosses the edge)."""
    out = []
    for i, cur in enumerate(poly):
        prev = poly[i - 1]
        a, b = inside(prev), inside(cur)
        if b:
            if not a:
                out.append(cut(prev, cur))
            out.append(cur)
        elif a:
            out.append(cut(prev, cur))
    return out


def clip_half_plane(poly, x0, y0, dx, dy, t0):
    """The part of `poly` where t = ((x - x0) dx + (y - y0) dy) / (dx² + dy²) >= t0."""
    n = dx * dx + dy * dy
    f = lambda p: ((p[0] - x0) * dx + (p[1] - y0) * dy) / n - t0

    def cut(a, b):
        fa, fb = f(a), f(b)
        k = fa / (fa - fb) if fa != fb else 0.0
        return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)

    return _clip(poly, lambda p: f(p) >= 0, cut)


def clip_disc(poly, cx, cy, r, sides=40):
    """The part of `poly` inside a disc (a regular polygon with `sides` sides, which is convex)."""
    ring = [(cx + r * math.cos(2 * math.pi * k / sides), cy + r * math.sin(2 * math.pi * k / sides)) for k in range(sides)]
    for i in range(sides):
        a, b = ring[i], ring[(i + 1) % sides]
        ex, ey = b[0] - a[0], b[1] - a[1]
        f = lambda p, a=a, ex=ex, ey=ey: ex * (p[1] - a[1]) - ey * (p[0] - a[0])      # positive on the inside (the ring runs clockwise on screen)

        def cut(p, q, f=f):
            fp, fq = f(p), f(q)
            k = fp / (fp - fq) if fp != fq else 0.0
            return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)

        poly = _clip(poly, lambda p, f=f: f(p) >= 0, cut)
        if len(poly) < 3:
            return []
    return poly


# ---- a vector picture -> strokes ---------------------------------------------------------------------------------------------------------------------

class Groups:
    """Fill groups: a number per filled shape that is unique within one grease pencil object."""

    def __init__(self):
        self.n = 0

    def new(self):
        self.n += 1
        return self.n


def shape_strokes(shape, tf, veil, groups, steps=GRADIENT_STEPS):
    """The strokes of one SVG shape. `tf(x, y)` takes the SVG's coordinates to cells. A filled shape's fill is a stroke of its own (cyclic, no line), its line another (so an open path
    with a fill does not get closed by its line)."""
    out = []
    sub = [([tf(x, y) for x, y in pts], closed) for pts, closed in shape.subpaths]
    scale = math.sqrt(abs(_det(tf)))
    if shape.fill is not None and shape.fill_opacity > 0:
        for rgb, alpha, polys in _fill_layers(shape, sub, steps):
            g = groups.new()
            for poly in polys:
                if len(poly) >= 3 and alpha > 0.0:
                    out.append({"p": _flat(poly), "closed": True, "fill": veil(rgb), "fo": shape.fill_opacity * alpha * veil.alpha, "line": None, "lo": 0.0, "w": 0.0, "cap": "flat", "g": g})
    if shape.stroke is not None and shape.stroke_width > 0 and shape.stroke_opacity > 0:
        rgb = shape.stroke.rgba[:3]
        a = shape.stroke.rgba[3]
        for pts, closed in sub:
            out.append({"p": _flat(pts), "closed": closed, "fill": None, "fo": 0.0, "line": veil(rgb), "lo": shape.stroke_opacity * a * veil.alpha, "w": shape.stroke_width * scale,
                        "cap": "round" if shape.linecap == "round" else "flat", "g": 0})
    return out


def _det(tf):
    (ax, ay), (bx, by), (cx, cy) = tf(0.0, 0.0), tf(1.0, 0.0), tf(0.0, 1.0)
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _flat(pts):
    return [round(v, 5) for p in pts for v in p]


def _fill_layers(shape, sub, steps):
    """[(rgb, alpha, [polygons])] drawn in order: one entry for a flat colour; for a gradient, bands. An opaque gradient is drawn as overlapping bands (each reaches to the end of the shape,
    so no seams show); one with transparent stops is cut into bands that do not overlap (overlapping would add their alphas up)."""
    fill = shape.fill
    polys = [pts for pts, _ in sub if len(pts) >= 3]
    if not polys:
        return []
    if fill.kind == "color":
        return [(fill.rgba[:3], fill.rgba[3], polys)]
    translucent = any(c[1][3] < 0.999 for c in fill.gradient["stops"])
    axis = _cell_axis(shape, sub)
    out = []
    if fill.kind == "linear":
        x0, y0, dx, dy = axis
        if dx == 0 and dy == 0:
            return [(fill.rgba[:3], fill.rgba[3], polys)]
        for k in range(steps):
            lo, hi = k / float(steps), (k + 1) / float(steps)
            cut = [clip_half_plane(p, x0, y0, dx, dy, lo) if k else p for p in polys]
            if translucent and k < steps - 1:
                cut = [clip_half_plane(c, x0, y0, -dx, -dy, -hi) if len(c) >= 3 else c for c in cut]
            c = svgvec.gradient_at(fill, (k + 0.5) / steps)
            out.append((c[:3], c[3], [q for q in cut if len(q) >= 3]))
    else:
        cx, cy, r, _ = axis
        if r <= 0:
            return [(fill.rgba[:3], fill.rgba[3], polys)]
        if not translucent:
            c = svgvec.gradient_at(fill, 1.0)
            out.append((c[:3], c[3], polys))
        for k in range(steps - 1, -1, -1):
            outer = [clip_disc(p, cx, cy, r * (k + 1) / steps) for p in polys]
            if translucent:
                inner = [clip_disc(p, cx, cy, r * k / steps) for p in polys] if k else []
                ring = [q for q in outer + inner if len(q) >= 3]       # an inner loop inside an outer one is a hole
                if k == steps - 1:
                    ring = [q for q in polys] + [q for q in inner if len(q) >= 3]
                c = svgvec.gradient_at(fill, (k + 0.5) / steps)
                out.append((c[:3], c[3], ring))
            else:
                c = svgvec.gradient_at(fill, (k + 0.5) / steps)
                out.append((c[:3], c[3], [q for q in outer if len(q) >= 3]))
    return out


def _cell_axis(shape, sub):
    """gradient_axis in the shape's output coordinates, which `shape_strokes` has already moved to cells: the axis is carried by the same linear map, so recover that map from the
    shape's subpaths (the SVG's own coordinates are in shape.subpaths)."""
    g = shape.fill.gradient
    return g["axis_cells"]


def sprite_strokes(vec, w, h, veil=NO_VEIL, steps=GRADIENT_STEPS, groups=None):
    """A parsed SVG as strokes in a box of w x h cells (origin top left). The viewBox is fitted the way `preserveAspectRatio` says by default: scaled evenly, centred."""
    groups = groups or Groups()
    vx, vy, vw, vh = vec.viewbox
    s = min(w / vw, h / vh)
    ox, oy = (w - vw * s) / 2.0, (h - vh * s) / 2.0
    tf = lambda x, y: ((x - vx) * s + ox, (y - vy) * s + oy)
    out = []
    for shape in vec.shapes:
        if shape.fill is not None and shape.fill.kind != "color":
            shape.fill.gradient["axis_cells"] = _axis_to_cells(shape, tf)
        out.extend(shape_strokes(shape, tf, veil, groups, steps))
    return out


def _axis_to_cells(shape, tf):
    ax = svgvec.gradient_axis(shape.fill)
    p0 = tf(ax[0], ax[1])
    if shape.fill.kind == "linear":
        p1 = tf(ax[0] + ax[2], ax[1] + ax[3])
        return (p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1])
    scale = math.sqrt(abs(_det(tf)))
    return (p0[0], p0[1], ax[2] * scale, None)


def placeholder_strokes(tile, w, h, groups):
    """For a tile with no SVG, fill or pattern (a bare emoji): a rounded square in a colour taken from its name, like the preview's placeholder."""
    import colorsys
    import zlib

    hue = (zlib.crc32((tile.glyph or tile.name).encode()) % 360) / 360.0
    rgb = colorsys.hsv_to_rgb(hue, 0.45, 0.85)
    m, r = min(w, h) * 0.1, min(w, h) * 0.2
    pts = []
    for cx, cy, a0 in ((w - m - r, m + r, -90), (w - m - r, h - m - r, 0), (m + r, h - m - r, 90), (m + r, m + r, 180)):
        for k in range(6):
            a = math.radians(a0 + 90.0 * k / 5.0)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return [{"p": _flat(pts), "closed": True, "fill": rgb, "fo": 1.0, "line": tuple(c / 2 for c in rgb), "lo": 1.0, "w": min(w, h) * 0.04, "cap": "round", "g": groups.new()}]


class Sprites:
    """Tile -> strokes, cached. The preview's order of preference is kept: a fill, then the SVG over it (a pattern or an emoji font cannot be vectors: those draw as the placeholder)."""

    def __init__(self, steps=GRADIENT_STEPS, warn=print):
        self.cache = {}
        self.steps = steps
        self.warn = warn
        self.warned = set()
        self.vectors = {}

    def _warn(self, key, msg):
        if key not in self.warned:
            self.warned.add(key)
            self.warn("levelang: " + msg)

    def get(self, tile, size=None, veil=NO_VEIL, groups=None):
        """(strokes, w, h). A fresh set of fill groups each time `groups` is given (a stamp needs its own); cached otherwise."""
        w, h = size or tile.size
        key = (id(tile), w, h, veil.key())
        if groups is None and key in self.cache:
            return self.cache[key], w, h
        g = groups or Groups()
        strokes = []
        drawn = False
        if tile.fill is not None:
            rgb = _rgb(tile.fill)
            strokes.append({"p": _flat([(0, 0), (w, 0), (w, h), (0, h)]), "closed": True, "fill": veil(rgb), "fo": veil.alpha, "line": None, "lo": 0.0, "w": 0.0, "cap": "flat", "g": g.new()})
            drawn = True
        if tile.pattern:
            self._warn("pattern:" + tile.name, "a text pattern (tile %s) cannot be a vector: it is left out of the Blender export" % (tile.glyph or tile.name))
        if tile.svg:
            try:
                vec = self.vectors.get(id(tile))
                if vec is None:
                    vec = self.vectors[id(tile)] = svgvec.parse(tile.svg)
                    for msg in vec.warnings:
                        self._warn("svg:%s:%s" % (tile.name, msg), "SVG of %s: %s" % (tile.glyph or tile.name, msg))
                strokes.extend(sprite_strokes(vec, w, h, veil, self.steps, g))
                drawn = True
            except Exception as e:
                self._warn("svgerr:" + tile.name, "couldn't read the SVG of %s: %s" % (tile.glyph or tile.name, e))
        if not drawn:
            if tile.glyph:
                self._warn("emoji:" + tile.name, "tile %s has no SVG: drawn as a coloured placeholder (give it `def X -> svg:` for a real picture)" % tile.glyph)
            strokes = placeholder_strokes(tile, w, h, g)
        if groups is None:
            self.cache[key] = strokes
        return strokes, w, h


def stamp(strokes, x, y, w, flip, groups):
    """The strokes of a sprite moved to (x, y) cells (mirrored left-right about its own box when `flip`), with fresh fill groups."""
    remap, out = {}, []
    for s in strokes:
        p = s["p"]
        if flip:
            q = [(w - p[i]) if i % 2 == 0 else p[i] for i in range(len(p))]
        else:
            q = list(p)
        q = [round(v + (x if i % 2 == 0 else y), 5) for i, v in enumerate(q)]
        if flip:                                    # keep the winding the same way round
            pairs = list(zip(q[0::2], q[1::2]))[::-1]
            q = [v for pt in pairs for v in pt]
        n = dict(s)
        n["p"] = q
        if s["g"]:
            if s["g"] not in remap:
                remap[s["g"]] = groups.new()
            n["g"] = remap[s["g"]]
        out.append(n)
    return out


# ---- the scene -----------------------------------------------------------------------------------------------------------------------------------

def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in rgb[:3])


def _interp(track, f):
    """track: [(x, y)] at the preview's fps; f: fractional index."""
    f = max(0.0, min(len(track) - 1.0, f))
    i = int(f)
    j = min(i + 1, len(track) - 1)
    k = f - i
    return (track[i][0] + (track[j][0] - track[i][0]) * k, track[i][1] + (track[j][1] - track[i][1]) * k)


def build(level, *, name="levelang", fps=24, view=(32, 20), speed=8.0, hold=(0.6, 1.6), bot_scale=1.6, play=True, steps=GRADIENT_STEPS, warn=print):
    """The scene description (a dict of plain numbers, lists and strings)."""
    if not level.placements:
        raise ValueError("the level is empty: nothing to export")
    x0, y0, x1, y1 = level.bounds()
    if level.meta.get("width") and level.meta.get("height"):
        x1, y1 = x0 + int(level.meta["width"]) - 1, y0 + int(level.meta["height"]) - 1
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    sprites = Sprites(steps, warn)
    notes = []

    # ---- timeline: the same plan, speed, holds, smoothing and camera clamp as the GIF preview ----
    plan = botmod.plan(level) if play else botmod.Plan()
    notes.extend(plan.notes)
    pts = plan.points
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    travel = cum[-1] / speed if len(pts) > 1 else 0.0
    h0, h1 = hold
    swims = [p.tile.anim["swim"] for p in level.placements if "swim" in p.tile.anim]
    swims += [p.tile.anim["swim"] for L in level.layers for p in L.placements if "swim" in p.tile.anim]
    total = h0 + travel + h1 if play and pts else max([4.8] + [_swim_period(v) for v in swims])
    pfps = 10                                       # the preview's fps: the smoothing window is in its frames

    def raw_pos(t):
        s = min(max(t - h0, 0.0), travel) * speed
        if len(pts) < 2:
            return (pts[0][0] + 0.5, pts[0][1] + 0.5) if pts else (0.0, 0.0)
        lo, hi = 0, len(cum) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if cum[mid] <= s else (lo, mid)
        seg = cum[hi] - cum[lo] or 1.0
        f = (s - cum[lo]) / seg
        return (pts[lo][0] + (pts[hi][0] - pts[lo][0]) * f + 0.5, pts[lo][1] + (pts[hi][1] - pts[lo][1]) * f + 0.5)

    n_prev = max(2, int(total * pfps))
    track = _smooth([raw_pos(i / pfps) for i in range(n_prev)], 3)
    track = [(bx - x0, by - y0) for bx, by in track]      # cells from the level's top left; the cell's centre
    face = []
    left_now = False
    for i, (bx, by) in enumerate(track):
        nxt = track[min(i + 2, len(track) - 1)]
        left_now = nxt[0] < bx - 0.02 or (abs(nxt[0] - bx) <= 0.02 and left_now)
        face.append(left_now)
    collect_t = {id(it): h0 + cum[idx] / speed for idx, it in plan.collects}

    # ---- classify placements the way the preview does ----
    spawns, items, dynamic, plain = [], [], [], []
    skinned = {id(sk): [] for sk in level.skins}
    for p in sorted(level.placements, key=lambda p: (p.tile.layer, p.order)):
        t = p.tile
        if t.has("spawn") and play:
            spawns.append(p)
        elif t.has("item"):
            items.append(p)
        elif t.anim:
            dynamic.append(p)
        else:
            sk = next((k for k in level.skins if k.hide and k.covers(t)), None)
            (skinned[id(sk)] if sk is not None else plain).append(p)

    statics, objects, layers_out = [], [], []
    shared = {}                                    # sprite key -> sprite dict

    def rel(p):
        return p.x - x0, p.y - y0

    def sprite_of(p, size, veil, extra=None, sway=None):
        """Register the sprite a moving placement uses (shared by every placement that looks the same and bends the same way)."""
        strokes, w, h = sprites.get(p.tile, size, veil)
        key = "%s|%gx%g|%s|%s" % (p.tile.name, w, h, repr(veil.key()), repr(sway))
        if key not in shared:
            shared[key] = {"w": w, "h": h, "strokes": strokes}
            if sway is not None:
                shared[key]["sway"] = {"amp": sway[0], "base": sway[1], "h": h, "poses": SWAY_POSES}
        return key, w, h

    def animation(p, base_below=0):
        a = {}
        tile = p.tile
        if "bob" in tile.anim:
            a["bob"] = {"amp": 0.22, "period": ANIM_PERIOD, "phase": _phase(p)}
        if "swim" in tile.anim:
            n, spd = _swim(tile.anim["swim"])
            a["swim"] = {"n": n, "period": _swim_period(tile.anim["swim"]), "phase": _phase(p)}
        if "sway" in tile.anim:
            a["sway"] = {"phase": _phase(p), "period": ANIM_PERIOD}
        return a

    def below(p):
        n = 0
        while n < 8 and any("sway" in q.tile.anim for q in level.cell(p.x, p.y + 1 + n)):
            n += 1
        return n

    def moving(p, veil, parent, depth_key, hide_at=None, item=False):
        size = p.size or p.tile.size
        sway = None
        if "sway" in p.tile.anim:
            sway = (p.tile.anim["sway"] or SWAY_AMP, below(p) if parent is None else 0)
        key, w, h = sprite_of(p, size, veil, sway=sway)
        x, y = rel(p)
        anim = animation(p)
        if item:
            anim["bob"] = {"amp": 0.12, "period": ANIM_PERIOD / 2, "phase": _phase(p)}
        o = {"name": "%s_%d" % (p.tile.name, p.order), "sprite": key, "x": x, "y": y, "w": w, "h": h, "flip": bool(p.flip), "anim": anim, "parent": parent, "depth": depth_key}
        if hide_at is not None:
            o["hide_at"] = hide_at
        objects.append(o)

    groups_for = {}

    def static_object(name, parent, depth_key, over=False):
        so = {"name": name, "parent": parent, "depth": depth_key, "layers": []}
        statics.append(so)
        return so

    def add_layer(so, lname, strokes, mask=None):
        so["layers"].append({"name": lname, "strokes": strokes, "mask": mask})

    # ---- parallax layers behind the world, far to near ----
    order = []                                      # what is drawn, in order; each entry is (depth key) -> the importer numbers them 0, 1, 2...
    seq = [0]

    def next_depth():
        seq[0] += 1
        return seq[0]

    lay_sorted = sorted(level.layers, key=lambda l: l.parallax)

    def do_layer(lay, idx):
        veil = Veil(lay.haze, lay.alpha)
        parent = "layer:%s" % lay.name
        layers_out.append({"name": lay.name, "parallax": [lay.parallax, lay.parallax_y], "over": bool(lay.over), "alpha": lay.alpha, "haze": [lay.haze[0], lay.haze[1]] if lay.haze else None})
        stat = [p for p in lay.placements if not p.tile.anim]
        dyn = [p for p in lay.placements if p.tile.anim]
        if stat:
            g = Groups()
            strokes = []
            for p in stat:
                st, w, h = sprites.get(p.tile, p.size, veil)
                strokes.extend(stamp(st, rel(p)[0], rel(p)[1], w, p.flip, g))
            so = static_object("layer_" + lay.name, parent, next_depth())
            add_layer(so, lay.name, strokes)
        for p in dyn:
            moving(p, veil, parent, next_depth())

    for lay in lay_sorted:
        if not lay.over:
            do_layer(lay, 0)

    # ---- the world: plants behind the terrain, the smooth skin, the rest ----
    def stamps_of(placed, g):
        strokes = []
        for p in placed:
            st, w, h = sprites.get(p.tile, p.size)
            strokes.extend(stamp(st, rel(p)[0], rel(p)[1], w, p.flip, g))
        return strokes

    back = [p for p in plain if p.tile.layer < 0]
    if back:
        so = static_object("world_back", None, next_depth())
        add_layer(so, "back", stamps_of(back, Groups()))
    for si, sk in enumerate(level.skins):
        placed = skinned[id(sk)]
        if not placed:
            continue
        so = static_object("skin_%d" % si, None, next_depth())
        cells = {}
        for p in placed:
            cells[(p.x - x0, p.y - y0)] = p
        loops = skin_loops(set(cells), cols, rows, sk.corner, sk.smooth, sk.wobble, sk.seed)
        g = Groups()
        base = _skin_base(sprites, placed)
        # the mask is the skin's shape; the art (the covered tiles' own pictures, and the neighbours' one cell out) shows through it
        gid = g.new()
        add_layer(so, "shape", [{"p": _flat(lp), "closed": True, "fill": base, "fo": 1.0, "line": None, "lo": 0.0, "w": 0.0, "cap": "flat", "g": gid} for lp in loops])
        art = []
        for (cx, cy), p in cells.items():
            st, w, h = sprites.get(p.tile, p.size)
            art.extend(stamp(st, cx, cy, w, p.flip, g))
        near = [(0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]
        for cy in range(rows):
            for cx in range(cols):
                if (cx, cy) in cells:
                    continue
                for dx, dy in near:
                    q = cells.get((cx + dx, cy + dy))
                    if q is not None:
                        st, w, h = sprites.get(q.tile, q.size)
                        art.extend(stamp(st, cx, cy, w, q.flip, g))
                        break
        add_layer(so, "art", art, mask="shape")
        if sk.outline:
            rgb = _rgb(sk.outline)
            add_layer(so, "outline", [{"p": _flat(lp), "closed": True, "fill": None, "fo": 0.0, "line": rgb, "lo": 1.0, "w": sk.outline_width, "cap": "round", "g": 0} for lp in loops])
    front = [p for p in plain if p.tile.layer >= 0]
    if front:
        so = static_object("world_front", None, next_depth())
        add_layer(so, "front", stamps_of(front, Groups()))

    for p in dynamic:
        moving(p, NO_VEIL, None, next_depth())
    for it in items:
        moving(it, NO_VEIL, None, next_depth(), hide_at=collect_t.get(id(it)), item=True)

    # ---- the bot ----
    bot = None
    if play and pts:
        if spawns and (spawns[0].tile.svg or spawns[0].tile.pattern or spawns[0].tile.fill):
            tile = spawns[0].tile
            st, w, h = sprites.get(tile, (1, 1))
            sk = "bot"
            shared[sk] = {"w": 1.0, "h": 1.0, "strokes": st}
        else:
            shared["bot"] = {"w": 1.0, "h": 1.0, "strokes": _default_bot()}
        keys = []
        nf = int(total * fps) + 1
        for f in range(nf):
            t = f / float(fps)
            bx, by = _interp(track, t * pfps)
            wob = math.sin(2 * math.pi * t / 1.1) * 0.06
            keys.append([round(t, 5), round(bx, 5), round(by + wob, 5), 1 if face[min(len(face) - 1, int(round(t * pfps)))] else 0])
        bot = {"sprite": "bot", "size": bot_scale, "keys": keys, "depth": next_depth()}

    for lay in lay_sorted:
        if lay.over:
            do_layer(lay, 1)

    # ---- the camera: follows the bot, clamped to the level, in cells ----
    vw, vh = min(view[0], cols), min(view[1], rows)
    cam = []
    for f in range(int(total * fps) + 1):
        t = f / float(fps)
        bx, by = _interp(track, t * pfps) if pts and play else (cols / 2.0, rows / 2.0)
        left = min(max(bx - vw / 2.0, 0.0), cols - vw)
        top = min(max(by - vh / 2.0, 0.0), rows - vh)
        cam.append([round(t, 5), round(left + vw / 2.0, 5), round(top + vh / 2.0, 5)])

    top_c, bot_c = level.background or ("#20222c", "#20222c")
    return {
        "version": VERSION, "name": name, "fps": fps, "duration": round(total, 4),
        "cells": {"x0": x0, "y0": y0, "cols": cols, "rows": rows},
        "view": [vw, vh],
        "background": [_hex(_rgb(top_c)), _hex(_rgb(bot_c))],
        "sprites": shared, "statics": statics, "objects": objects, "layers": layers_out,
        "bot": bot, "camera": cam, "sway_poses": SWAY_POSES, "notes": notes,
    }


def _skin_base(sprites, placed):
    """The colour under a skin's art: the biggest flat fill of the most common covered tile."""
    from collections import Counter

    c = Counter(p.tile for p in placed)
    tile = c.most_common(1)[0][0]
    strokes, w, h = sprites.get(tile, None)
    best, area = (0.3, 0.3, 0.3), -1.0
    for s in strokes:
        if s["fill"] is not None and len(s["p"]) >= 6:
            xs, ys = s["p"][0::2], s["p"][1::2]
            a = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if a > area:
                best, area = tuple(s["fill"]), a
    return best


def _default_bot():
    """A yellow ball with an eye, like the preview's default bot (a unit box)."""
    n = 28
    ball = [(0.5 + 0.4 * math.cos(2 * math.pi * k / n), 0.5 + 0.4 * math.sin(2 * math.pi * k / n)) for k in range(n)]
    eye = [(0.665 + 0.115 * math.cos(2 * math.pi * k / 16), 0.415 + 0.115 * math.sin(2 * math.pi * k / 16)) for k in range(16)]
    pupil = [(0.70 + 0.05 * math.cos(2 * math.pi * k / 12), 0.41 + 0.05 * math.sin(2 * math.pi * k / 12)) for k in range(12)]
    g = Groups()
    mk = lambda pts, fill, line, w: {"p": _flat(pts), "closed": True, "fill": fill, "fo": 1.0, "line": line, "lo": 1.0 if line else 0.0, "w": w, "cap": "round", "g": g.new()}
    return [mk(ball, (1.0, 0.82, 0.16), (0.47, 0.31, 0.0), 0.02), mk(eye, (1.0, 1.0, 1.0), None, 0.0), mk(pupil, (0.0, 0.0, 0.0), None, 0.0)]
