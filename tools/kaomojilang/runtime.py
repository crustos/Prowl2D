"""Runtime: numbered grids -> shapes -> drawsvg elements -> SVG or Grease Pencil.

Rules (see SPEC.md)
-------------------
- Numbers are grouped in runs of consecutive values (3, 4, 5 ...). The first number is the id of the part.
- 1 point -> dot (or a glyph stamped at the point), 2 points -> line,
  3+ points: odd id -> closed polygon, even id -> smooth closed curve.
- A `~` right after the last number of a run (`4~`) leaves it open: an open polyline (odd id) or an
  open smooth curve (even id), e.g. a smile.
- Position: x = column, y = row * ASPECT (text rows are taller than columns).
- Parameters fill / stroke / width / sizes / smooth / shift / rotate / scale are a value or a dict
  {part id: value, '*': default}. shift = (columns, rows), rotate = degrees (clockwise, about the part
  center), scale = factor or (sx, sy) about the part center (for a dot or a stamped drawing: its size);
  scale 0 hides the part.
- A dict passed to a parameter whose default is a dict is overlaid on that default.
- A Shape used as a `fill` value of a single point is stamped at the point: at its natural size, or
  stretched to the `sizes` of that point (a number or (width, height)).
"""

import inspect
import math
from dataclasses import dataclass, field

from . import artlib, ink as inklib, underdraw
from .brush import Stroke, stroke_element
from .drawing import draw
from .drawing.flatten import NAMED_COLORS

ASPECT = 2.0
KAPPA = 0.5522847498307936          # cubic handle length for a quarter circle
DEFAULT_WIDTH = 0.15                # stroke width, in grid columns
DEFAULT_SMOOTH = 0.5
DEFAULT_SIZE = 1.5

SIZES = {"tiny": 0.7, "small": 1.0, "medium": 1.5, "large": 2.5, "huge": 4.0}
COLORS = {name: name for name in NAMED_COLORS}
COLORS["none"] = "none"

PARAMS = ("fill", "stroke", "width", "sizes", "smooth", "shift", "rotate", "scale", "rough")


class ShapeError(Exception):
    pass


# ====================================================================================================
# Data
# ====================================================================================================

@dataclass
class Part:
    id: int
    kind: str                      # 'point' | 'line' | 'polygon' | 'smooth'
    points: list                   # [(x, y)] in grid units (y already multiplied by ASPECT)
    fill: object = None            # color, or a Shape (glyph) for points
    stroke: object = "black"
    width: float = DEFAULT_WIDTH
    smooth: float = DEFAULT_SMOOTH
    size: tuple = (DEFAULT_SIZE, DEFAULT_SIZE)     # (width, height) of a dot / stamped glyph
    angle: float = 0.0                             # rotation in degrees (stamped glyphs)
    hidden: bool = False
    open: bool = False                             # 3+ points not closed (marked with `~`)

    def extent(self):
        xs, ys = [p[0] for p in self.points], [p[1] for p in self.points]
        rx, ry = (self.size[0] / 2, self.size[1] / 2) if self.kind == "point" else (0.0, 0.0)
        return min(xs) - rx, min(ys) - ry, max(xs) + rx, max(ys) + ry


def pick(value, key, default):
    """Value of a per-part parameter: scalar, or dict {id: value, '*': default}."""
    if isinstance(value, dict):
        if key in value:
            return value[key]
        return value.get("*", default)
    return default if value is None else value


def defaults_of(fn):
    return {k: v.default for k, v in inspect.signature(fn).parameters.items() if v.default is not v.empty}


def build_shape(grid, name, params, defaults, cells=(), env=None, aspect=ASPECT):
    """`__shape__`: called by the code generated for every drawing def."""
    p = {}
    for key, value in params.items():
        default = defaults.get(key)
        p[key] = {**default, **value} if isinstance(value, dict) and isinstance(default, dict) else value

    placed, open_marks = {}, set()
    for item in grid:
        number, x, row = item[:3]
        placed[number] = (x, row * aspect)
        if len(item) > 3 and item[3]:
            open_marks.add(number)
    numbers = sorted(placed)
    runs = []
    for n in numbers:
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])

    parts = []
    for run in runs:
        pid = run[0]
        pts = [placed[n] for n in run]
        misplaced = [n for n in run[:-1] if n in open_marks]
        if misplaced:
            raise ShapeError(f"{name}: '~' on {misplaced[0]}: it can only mark the last number of a run "
                             f"(here {run[-1]})")
        is_open = run[-1] in open_marks and len(run) >= 3
        kind = "point" if len(pts) == 1 else "line" if len(pts) == 2 else "polygon" if pid % 2 else "smooth"
        fill = pick(p.get("fill"), pid, None)
        if isinstance(fill, Shape) and kind != "point":
            raise ShapeError(f"{name}: a shape can only be stamped on a single point, not on part {pid}")
        stroke = pick(p.get("stroke"), pid, "black")
        smooth = pick(p.get("smooth"), pid, DEFAULT_SMOOTH)
        size = pick(p.get("sizes"), pid, None)
        width = pick(p.get("width"), pid, DEFAULT_WIDTH)
        shift = pick(p.get("shift"), pid, (0, 0))
        rotate = pick(p.get("rotate"), pid, 0.0)
        scale = pick(p.get("scale"), pid, 1.0)
        for label, v in (("smooth", smooth), ("width", width), ("rotate", rotate)):
            if not isinstance(v, (int, float)):
                raise ShapeError(f"{name}: '{label}' of part {pid} must be a number, got {v!r}")
        hidden = isinstance(scale, (int, float)) and scale == 0
        if isinstance(scale, (int, float)):
            scale = (scale, scale)
        if not (isinstance(scale, (tuple, list)) and len(scale) == 2 and all(isinstance(v, (int, float)) for v in scale)):
            raise ShapeError(f"{name}: 'scale' of part {pid} must be a number or (sx, sy), got {scale!r}")
        if not (isinstance(shift, (tuple, list)) and len(shift) == 2 and all(isinstance(v, (int, float)) for v in shift)):
            raise ShapeError(f"{name}: 'shift' of part {pid} must be (columns, rows), got {shift!r}")
        if size is None:                                   # natural size: the stamped drawing's, or a default dot
            if isinstance(fill, Shape):
                x0, y0, x1, y1 = fill.bbox()
                size = (x1 - x0, y1 - y0)
            else:
                size = DEFAULT_SIZE
        if isinstance(size, (int, float)):
            size = (size, size)
        if not (isinstance(size, (tuple, list)) and len(size) == 2 and all(isinstance(v, (int, float)) for v in size)):
            raise ShapeError(f"{name}: 'sizes' of part {pid} must be a number or (width, height), got {size!r}")
        dx, dy = shift[0], shift[1] * aspect
        if kind == "point":
            pts = [(pts[0][0] + dx, pts[0][1] + dy)]
            size = (size[0] * scale[0], size[1] * scale[1])
        else:
            cx = sum(q[0] for q in pts) / len(pts)
            cy = sum(q[1] for q in pts) / len(pts)
            ca, sa = math.cos(math.radians(rotate)), math.sin(math.radians(rotate))
            local = [((q[0] - cx) * scale[0], (q[1] - cy) * scale[1]) for q in pts]
            pts = [(cx + u * ca - v * sa + dx, cy + u * sa + v * ca + dy) for u, v in local]
        parts.append(Part(pid, kind, pts, fill, stroke, float(width), min(1.0, max(0.0, float(smooth))),
                          (float(size[0]), float(size[1])), float(rotate) if kind == "point" else 0.0, hidden,
                          is_open))
    shape = Shape(name, parts)
    if cells or p.get("rough"):
        _add_cells(shape, cells, p, name, env, aspect)
    return shape


# ====================================================================================================
# Symbols (artlib) and ink (ASCII art)
# ====================================================================================================

class Env:
    """Where a drawing is built: the program's namespace (local `def <symbol>` first), its file (to find artlib/)."""

    def __init__(self, ns=None, filename=None, dirs=()):
        self.ns, self.filename, self.extra = ns or {}, filename, tuple(dirs)
        self._dirs = None

    def dirs(self):
        if self._dirs is None:
            self._dirs = artlib.search_dirs(self.filename, self.extra)
        return self._dirs

    def run_file(self, path):
        from .stage2 import run_file
        return run_file(path)


def _numbers(name, key, value, kind="a number"):
    if not isinstance(value, (int, float)):
        raise ShapeError(f"{name}: '{key}' must be {kind}, got {value!r}")
    return float(value)


def _pair(name, key, v, default):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v), float(v)
    if isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(q, (int, float)) for q in v):
        return float(v[0]), float(v[1])
    raise ShapeError(f"{name}: '{key}' must be a number or a pair, got {v!r}")


def _stamp(art, source):
    """Glyph (ArtGlyph / Shape) out of one thing generate() returned, or None if it is not a drawing."""
    if isinstance(art, Shape):
        return art
    a = artlib.to_art(art, source)
    return artlib.ArtGlyph(a) if a is not None else None


def _add_cells(shape, cells, p, name, env, aspect):
    env = env or Env()
    # ---- ink: ASCII art, strokes that touch become one smooth line -------------------------------------------
    ink_cells = [(c, x, row) for kind, c, x, row in cells if kind == "art"]
    ink_lines = []
    if ink_cells:
        segs, dots = inklib.strokes(ink_cells, aspect)
        stroke = pick(p.get("stroke"), "ink", "black")
        width = float(pick(p.get("width"), "ink", DEFAULT_WIDTH))
        smooth = min(1.0, max(0.0, float(pick(p.get("smooth"), "ink", 0.8))))
        for k, (pts, closed) in enumerate(inklib.chains(segs)):
            ink_lines.append(pts)
            if len(pts) == 2:
                shape.parts.append(Part(1000 + k, "line", pts, None, stroke, width, smooth))
            elif closed:
                shape.parts.append(Part(1000 + k, "smooth", pts, None, stroke, width, smooth))
            else:
                shape.parts.append(Part(1000 + k, "smooth", pts, None, stroke, width, smooth, open=True))
        for k, (x, y) in enumerate(dots):
            shape.parts.append(Part(1500 + k, "point", [(x, y)], stroke, stroke, width, smooth, (width * 2.2, width * 2.2)))

    # ---- symbols ------------------------------------------------------------------------------------------------
    syms = [(c, x, row * aspect) for kind, c, x, row in cells if kind == "sym"]
    dirs = env.dirs() if syms else ()
    plan = []                                                    # per symbol: where, how big, what to draw
    for i, (c, x, y) in enumerate(syms):
        shift = pick(p.get("shift"), c, (0, 0))
        scale = _pair(name, "scale", pick(p.get("scale"), c, 1.0), (1.0, 1.0))
        rotate = _numbers(name, "rotate", pick(p.get("rotate"), c, 0.0))
        size_param = pick(p.get("sizes"), c, None)
        fillv = pick(p.get("fill"), c, None)
        sh = _pair(name, "shift", shift, (0.0, 0.0))
        at = (x + sh[0], y + sh[1] * aspect)
        files = {}
        local = env.ns.get(f"_u{ord(c):04x}_") if env.ns else None
        if not isinstance(fillv, Shape) and local is None:
            files = artlib.find(c, dirs)
        # a box for the neighbours to see: the sizes parameter, else the natural size of what is drawn
        natural = (artlib.DEFAULT_SIZE, artlib.DEFAULT_SIZE)
        try:
            if isinstance(fillv, Shape):
                natural = fillv.natural_size()
            elif local is not None and callable(local):
                natural = local().natural_size()
            elif ".svg" in files:
                natural = artlib.load_svg(files[".svg"]).size
            elif ".kmj" in files and ".py" not in files:
                natural = artlib.load_kmj(files[".kmj"], env.run_file).natural_size()
        except artlib.ArtError as e:
            raise ShapeError(f"{name}: symbol {c!r}: {e}") from None
        base = _pair(name, "sizes", size_param, natural)
        box = (base[0] * scale[0], base[1] * scale[1])
        if not isinstance(fillv, Shape) and local is None and not files:
            raise ShapeError(f"{name}: no drawing for the symbol {c!r} (U+{ord(c):04X}): put {c}.kmj, {c}.svg or {c}.py in artlib/ "
                             f"(looked in: {', '.join(dirs) or 'no artlib folder'}), or `def {c}` in this file")
        plan.append(dict(char=c, at=at, box=box, rot=rotate, fill=fillv, local=local, files=files, hidden=(scale[0] == 0 or scale[1] == 0),
                         explicit=size_param is not None, scale=scale, index=i))
    cell_list = [(q["char"], q["at"], q["box"]) for q in plan]
    for q in plan:
        c = q["char"]
        if q["hidden"]:                                          # scale 0: kept (hidden), so a Grease Pencil layer gets an empty keyframe
            shape.parts.append(Part(2000 + 10 * q["index"], "point", [q["at"]], None, "black", DEFAULT_WIDTH, DEFAULT_SMOOTH, (0.0, 0.0), 0.0, True))
            continue
        stamps, source = [], q["files"].get(".svg") or q["files"].get(".kmj") or c
        if isinstance(q["fill"], Shape):
            stamps = [q["fill"]]
        elif q["local"] is not None:
            try:
                stamps = [q["local"]()]
            except TypeError as e:
                raise ShapeError(f"{name}: `def {c}` needs arguments, a symbol is drawn without: {e}") from None
        elif ".py" in q["files"]:
            path = q["files"][".py"]
            try:
                mod = artlib.load_script(path)
                svg = artlib.load_svg(q["files"][".svg"]) if ".svg" in q["files"] else None
                kmj = artlib.load_kmj(q["files"][".kmj"], env.run_file) if ".kmj" in q["files"] else None
                ctx = artlib.Context(c, q["index"], q["at"], q["box"], q["rot"], {
                    "fill": pick(p.get("fill"), c, None), "stroke": pick(p.get("stroke"), c, "black"), "width": pick(p.get("width"), c, DEFAULT_WIDTH),
                    "smooth": pick(p.get("smooth"), c, DEFAULT_SMOOTH)}, cell_list, ink_lines, int(abs(q["at"][0] * 1000 + q["at"][1] * 31)) + ord(c))
                avail = dict(svg=svg, kmj=kmj, ctx=ctx, **ctx.params, seed=ctx.seed)
                result = artlib.call_generate(mod, path, **avail)
                items = artlib.as_list(result)
                if result is None:                              # nothing returned: the plain file
                    items = [svg or kmj] if (svg or kmj) else []
                flat = []
                for it in items:
                    flat.extend(artlib.as_list(it) if isinstance(it, (list, tuple)) else [it])
                for it in flat:
                    if isinstance(it, Stroke):
                        (shape.under if it.layer == "under" else shape.over).append(it)
                    elif isinstance(it, artlib.ArtSvg) and it is svg and not q["explicit"]:
                        stamps.append(it)
                    else:
                        g = it if isinstance(it, Shape) else artlib.to_art(it, path)
                        if g is None:
                            raise artlib.ArtError(f"{path}: generate() returned {type(it).__name__}, expected SVG text, ArtSvg, Shape or Stroke")
                        stamps.append(g)
            except artlib.ArtError as e:
                raise ShapeError(f"{name}: symbol {c!r}: {e}") from None
        elif ".svg" in q["files"]:
            stamps = [artlib.load_svg(q["files"][".svg"])]
        elif ".kmj" in q["files"]:
            stamps = [artlib.load_kmj(q["files"][".kmj"], env.run_file)]
        for k, g in enumerate(stamps):
            glyph = g if isinstance(g, Shape) else artlib.ArtGlyph(g)
            nat = glyph.natural_size()
            w, h = (q["box"] if (q["explicit"] or len(stamps) > 1 or ".py" not in q["files"]) and q["box"] else nat)
            if not q["explicit"]:                                # natural size of this very drawing, times the scale
                w, h = nat[0] * q["scale"][0], nat[1] * q["scale"][1]
            shape.parts.append(Part(2000 + 10 * q["index"] + k, "point", [q["at"]], glyph, "black", DEFAULT_WIDTH, DEFAULT_SMOOTH, (w, h), q["rot"]))
    _underdraw(shape, p, name)


def _rough_settings(name, value):
    """`rough` is an amount (0 = off, 1 = a normal sketch, 2 = messy) or a dict {'amount', 'color', 'seed', 'width'}."""
    if value is None or value is False:
        return None
    opts = {"amount": 1.0}
    if value is True:
        pass
    elif isinstance(value, (int, float)):
        opts["amount"] = float(value)
    elif isinstance(value, dict):
        bad = [k for k in value if k not in ("amount", "color", "seed", "width")]
        if bad:
            raise ShapeError(f"{name}: unknown key {bad[0]!r} in 'rough' (amount, color, seed, width)")
        opts.update(value)
    else:
        raise ShapeError(f"{name}: 'rough' must be a number or a dict, got {value!r}")
    return opts if opts["amount"] > 0 else None


def _underdraw(shape, p, name):
    """The loose pencil sketch under the whole figure (see underdraw.py), planned from every line and feature drawn."""
    opts = _rough_settings(name, p.get("rough"))
    if opts is None:
        return
    contours, blocks, ink_color = [], [], None
    for part in shape.parts:
        if part.hidden:
            continue
        if part.kind in ("line", "polygon", "smooth") and part.id < 2000 and len(part.points) >= 2:
            closed = part.kind == "polygon" or (part.kind == "smooth" and not part.open)
            contours.append(underdraw.Contour(part.points, closed, part.smooth if part.kind != "line" else 0.0))
            if ink_color is None and isinstance(part.stroke, str) and part.stroke != "none":
                ink_color = part.stroke
        elif part.kind == "point" and part.size[0] > 0 and part.size[1] > 0 and (part.id < 1000 or part.id >= 2000):
            blocks.append(underdraw.Block(part.points[0], part.size, ""))
    seed = opts.get("seed")
    if seed is None:
        pts = [q for c in contours for q in c.points] + [b.at for b in blocks]
        seed = int(sum(abs(x) * 7 + abs(y) * 13 for x, y in pts) * 100) % (1 << 30)
    color = opts.get("color") or ink_color or "black"
    width = float(opts.get("width", 0.085))
    shape.under.extend(underdraw.plan(contours, blocks, opts["amount"], color, int(seed), width))


# ====================================================================================================
# Geometry
# ====================================================================================================

def _r(v):
    return round(v, 4)


def smooth_closed_path(points, smooth, **style):
    """Closed path through the (rounded) corners of `points`.

    Each corner is replaced by a cubic from A (a fraction t = smooth / 2 of the way toward the previous
    point) to B (toward the next one), the corner being the control polygon: smooth = 1 on a square
    gives a circle, smooth = 0 the polygon itself.
    """
    n = len(points)
    t = 0.5 * smooth
    corners = []
    for i, p in enumerate(points):
        prev, nxt = points[i - 1], points[(i + 1) % n]
        a = (p[0] + t * (prev[0] - p[0]), p[1] + t * (prev[1] - p[1]))
        b = (p[0] + t * (nxt[0] - p[0]), p[1] + t * (nxt[1] - p[1]))
        corners.append((a, p, b))
    path = draw.Path(**style)
    path.M(_r(corners[0][2][0]), _r(corners[0][2][1]))
    cur = corners[0][2]
    for a, p, b in corners[1:] + corners[:1]:
        if (_r(a[0]), _r(a[1])) != (_r(cur[0]), _r(cur[1])):
            path.L(_r(a[0]), _r(a[1]))
        c1 = (a[0] + KAPPA * (p[0] - a[0]), a[1] + KAPPA * (p[1] - a[1]))
        c2 = (b[0] + KAPPA * (p[0] - b[0]), b[1] + KAPPA * (p[1] - b[1]))
        path.C(_r(c1[0]), _r(c1[1]), _r(c2[0]), _r(c2[1]), _r(b[0]), _r(b[1]))
        cur = b
    return path.Z()


def smooth_open_path(points, smooth, **style):
    """Open path: the end points stay where they are, the corners in between are rounded as in
    `smooth_closed_path`. A corner next to a free end may use that whole end segment (fraction `smooth`
    instead of `smooth / 2`), so smooth = 1 on three points is a single smooth cubic."""
    n = len(points)
    path = draw.Path(**style)
    path.M(_r(points[0][0]), _r(points[0][1]))
    cur = points[0]

    def line_to(q):
        nonlocal cur
        if (_r(q[0]), _r(q[1])) != (_r(cur[0]), _r(cur[1])):
            path.L(_r(q[0]), _r(q[1]))
            cur = q

    for i in range(1, n - 1):
        p, prev, nxt = points[i], points[i - 1], points[i + 1]
        fa = smooth if i - 1 == 0 else 0.5 * smooth
        fb = smooth if i + 1 == n - 1 else 0.5 * smooth
        a = (p[0] + fa * (prev[0] - p[0]), p[1] + fa * (prev[1] - p[1]))
        b = (p[0] + fb * (nxt[0] - p[0]), p[1] + fb * (nxt[1] - p[1]))
        line_to(a)
        c1 = (a[0] + KAPPA * (p[0] - a[0]), a[1] + KAPPA * (p[1] - a[1]))
        c2 = (b[0] + KAPPA * (p[0] - b[0]), b[1] + KAPPA * (p[1] - b[1]))
        path.C(_r(c1[0]), _r(c1[1]), _r(c2[0]), _r(c2[1]), _r(b[0]), _r(b[1]))
        cur = b
    line_to(points[-1])
    return path


def _color(c, default="none"):
    return default if c is None else c


@dataclass
class Shape:
    name: str
    parts: list = field(default_factory=list)
    under: list = field(default_factory=list)      # Strokes drawn below every part (light rough sketch lines of artlib symbols)
    over: list = field(default_factory=list)       # Strokes drawn above the parts (connecting curves of artlib symbols)

    # ----- geometry ---------------------------------------------------------------------------------

    def bbox(self):
        ext = [p.extent() for p in self.parts if not p.hidden] + [s.bbox() for s in self.under + self.over]
        if not ext:
            return 0.0, 0.0, 1.0, 1.0
        return (min(e[0] for e in ext), min(e[1] for e in ext), max(e[2] for e in ext), max(e[3] for e in ext))

    def natural_size(self):
        x0, y0, x1, y1 = self.bbox()
        return x1 - x0, y1 - y0

    def __repr__(self):
        return f"<Shape {self.name}: {', '.join(f'{p.id}:{p.kind}' for p in self.parts)}>"

    # ----- drawsvg elements -------------------------------------------------------------------------

    def _part_elements(self, part, width_factor=1.0):
        stroke = _color(part.stroke)
        style = dict(stroke=stroke, stroke_width=_r(part.width * width_factor))
        pts = part.points
        if part.kind == "point":
            (x, y), (w, h) = pts[0], part.size
            if isinstance(part.fill, artlib.ArtGlyph):
                return [self._art_glyph(part.fill, x, y, w, h, part.angle)]
            if isinstance(part.fill, Shape):
                return [self._glyph(part.fill, x, y, w, h, width_factor, part.angle)]
            fill = part.fill if part.fill is not None else (stroke if stroke != "none" else "black")
            if abs(w - h) < 1e-9:
                return [draw.Circle(_r(x), _r(y), _r(w / 2), fill=fill, **style)]
            return [draw.Ellipse(_r(x), _r(y), _r(w / 2), _r(h / 2), fill=fill, **style)]
        if part.kind == "line":
            return [draw.Line(_r(pts[0][0]), _r(pts[0][1]), _r(pts[1][0]), _r(pts[1][1]), fill="none", **style)]
        fill = _color(part.fill)
        if part.kind == "polygon" or part.smooth <= 1e-9:
            flat = [_r(v) for p in pts for v in p]
            return [draw.Lines(*flat, close=not part.open, fill=fill, **style)]
        if part.open:
            return [smooth_open_path(pts, part.smooth, fill=fill, **style)]
        return [smooth_closed_path(pts, part.smooth, fill=fill, **style)]

    def _glyph(self, glyph, x, y, w, h, width_factor=1.0, angle=0.0):
        """Stamp `glyph` centered at (x, y), stretched to a w x h box. A flat axis (a line) is not stretched,
        and stroke widths keep their size (they are divided by the stretch)."""
        gx0, gy0, gx1, gy1 = glyph.bbox()
        gw, gh = gx1 - gx0, gy1 - gy0
        sx = w / gw if gw > 1e-9 else 1.0
        sy = h / gh if gh > 1e-9 else 1.0
        rot = f"rotate({_r(angle)}) " if angle else ""
        tr = (f"translate({_r(x)} {_r(y)}) {rot}scale({_r(sx)} {_r(sy)}) "
              f"translate({_r(-(gx0 + gx1) / 2)} {_r(-(gy0 + gy1) / 2)})")
        group = draw.Group(transform=tr)
        compensate = width_factor / (abs(sx * sy) ** 0.5)
        for part in glyph.parts:
            if part.hidden:
                continue
            for e in self._part_elements(part, compensate):
                group.append(e)
        return group

    def _art_glyph(self, glyph, x, y, w, h, angle=0.0):
        """Stamp an artlib SVG symbol centered at (x, y), stretched to a w x h box."""
        gx0, gy0, gx1, gy1 = glyph.bbox()
        gw, gh = gx1 - gx0, gy1 - gy0
        sx = w / gw if gw > 1e-9 else 1.0
        sy = h / gh if gh > 1e-9 else 1.0
        rot = f"rotate({_r(angle)}) " if angle else ""
        group = draw.Group(transform=f"translate({_r(x)} {_r(y)}) {rot}scale({_r(sx)} {_r(sy)}) translate({_r(-(gx0 + gx1) / 2)} {_r(-(gy0 + gy1) / 2)})")
        for e in glyph.elements():
            group.append(e)
        return group

    def to_drawing(self, cell=10.0, margin=1.0, bbox=None):
        """A drawsvg Drawing (cell = pixels per grid column). One top-level Group `p<id>` per part:
        they become the Grease Pencil layers."""
        x0, y0, x1, y1 = bbox or self.bbox()
        x0, y0, x1, y1 = x0 - margin, y0 - margin, x1 + margin, y1 + margin
        d = draw.Drawing((x1 - x0) * cell, (y1 - y0) * cell, origin=(x0 * cell, y0 * cell))

        def strokes(items, gid):
            if items:
                g = draw.Group(id=gid, transform=f"scale({cell})")
                for st in items:
                    g.append(stroke_element(st))
                d.append(g)
        strokes(self.under, "under")
        for part in self.parts:
            if part.hidden:
                continue
            g = draw.Group(id=f"p{part.id}", transform=f"scale({cell})")
            for e in self._part_elements(part):
                g.append(e)
            d.append(g)
        strokes(self.over, "over")
        return d

    def to_svg(self, **kw):
        return self.to_drawing(**kw).as_svg()

    def save_svg(self, path, **kw):
        self.to_drawing(**kw).save_svg(path)

    def to_grease_pencil(self, gp=None, frame=1, cell=10.0, margin=1.0, bbox=None, **kw):
        from .drawing import to_grease_pencil
        return to_grease_pencil(self.to_drawing(cell=cell, margin=margin, bbox=bbox), gp, frame=frame, **kw)


def union_bbox(shapes):
    boxes = [s.bbox() for s in shapes]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def frames_to_grease_pencil(shapes, gp=None, start=1, step=1, cell=10.0, margin=1.0, name="Kaomoji", **kw):
    """One keyframe per shape (same framing for all of them, so the picture does not jump)."""
    import bpy
    shapes = list(shapes)
    gp = gp or bpy.data.grease_pencils.new(name)
    box = union_bbox(shapes)
    numbers = [start + k * step for k in range(len(shapes))]
    for n, s in zip(numbers, shapes):
        s.to_grease_pencil(gp, frame=n, cell=cell, margin=margin, bbox=box, **kw)
    # a layer without a keyframe keeps showing its previous drawing: add empty keyframes (hidden parts)
    for layer in gp.layers:
        have = {f.frame_number for f in layer.frames}
        for n in numbers:
            if n not in have:
                layer.frames.new(n)
    return gp
