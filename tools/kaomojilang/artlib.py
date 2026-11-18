"""artlib: symbols of the grid language, drawn by files named after the symbol.

    artlib/<symbol>.kmj      a drawing (small, easy to read)
    artlib/<symbol>.svg      a vector file
    artlib/<symbol>.py       a script: `generate(...)` returns the art (it gets the .svg of the same name, if there is one)

A symbol is found, in this order, in: a `def <symbol>` of the .kmj file itself, the `artlib/` folder next to the .kmj
file (and its parents), `$KAOMOJI_ARTLIB`, and the `artlib/` at the root of the repository. Of the files for one
symbol the .py wins, then the .svg, then the .kmj.

generate(...) may declare any of these parameters (it gets the ones it asks for):

    svg     the ArtSvg of <symbol>.svg (None if there is no such file)
    ctx     a Context: where the symbol is, how big, the neighbours, the parameters of the figure
    kmj     the Shape of <symbol>.kmj (None if there is none)
    fill stroke width smooth seed      the parameters of the figure for this symbol

and returns what to draw (or a list of them): an ArtSvg / SVG text / Shape (stamped in the symbol's box),
`Stroke`s (drawn in figure coordinates, see brush.py), or None to draw the .svg / .kmj as it is.
"""

import inspect
import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .brush import Stroke, angle_to, dist
from .drawing import draw

DEFAULT_SIZE = 3.0                  # columns: the longer side of a stamped symbol, unless the file says (data-size)
ENV = "KAOMOJI_ARTLIB"
SUFFIXES = (".py", ".svg", ".kmj")


class ArtError(Exception):
    pass


# ====================================================================================================
# Finding the files
# ====================================================================================================

def repo_artlib():
    """`artlib/` at the root of the repository this package is vendored in (tools/kaomojilang/ -> ../../artlib)."""
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "artlib"))


def search_dirs(filename=None, extra=()):
    dirs = [d for d in extra if d]
    if filename and not filename.startswith("<"):
        here = os.path.dirname(os.path.abspath(filename))
        while True:
            cand = os.path.join(here, "artlib")
            if os.path.isdir(cand):
                dirs.append(cand)
            parent = os.path.dirname(here)
            if parent == here:
                break
            here = parent
    if os.environ.get(ENV):
        dirs.extend(p for p in os.environ[ENV].split(os.pathsep) if p)
    dirs.append(repo_artlib())
    seen, out = set(), []
    for d in dirs:
        d = os.path.abspath(d)
        if d not in seen and os.path.isdir(d):
            seen.add(d)
            out.append(d)
    return out


def find(symbol, dirs):
    """{suffix: path} of the files for `symbol` in the first folder that has any."""
    for d in dirs:
        found = {s: os.path.join(d, symbol + s) for s in SUFFIXES if os.path.isfile(os.path.join(d, symbol + s))}
        if found:
            return found
    return {}


# ====================================================================================================
# SVG -> drawsvg elements (so an .svg symbol works for SVG and Grease Pencil output alike)
# ====================================================================================================

_NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


def _style(e, inherited):
    st = dict(inherited)
    for k in ("fill", "stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity", "stroke-linecap", "stroke-linejoin"):
        if e.get(k) is not None:
            st[k] = e.get(k)
    for decl in (e.get("style") or "").split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            st[k.strip()] = v.strip()
    return st


def _kwargs(st, gradients):
    kw = {}
    for k, v in st.items():
        if v.startswith("url("):                                 # a gradient: its first colour
            v = gradients.get(v[v.find("#") + 1:v.find(")")], "none")
        kw[k.replace("-", "_")] = v
    return kw


def _floats(text):
    return [float(x) for x in _NUM.findall(text or "")]


def _convert(e, st, gradients, out):
    tag = _tag(e)
    if tag in ("defs", "linearGradient", "radialGradient", "title", "desc", "metadata", "style", "clipPath", "mask"):
        return
    st = _style(e, st)
    kw = _kwargs(st, gradients)
    tr = e.get("transform")
    target = out
    if tag == "g":
        g = draw.Group(**({"transform": tr} if tr else {}), **{k: v for k, v in kw.items() if k in ("opacity",)})
        for c in e:
            _convert(c, {k: v for k, v in st.items() if k != "opacity"}, gradients, g)
        out.append(g)
        return
    if tag == "path":
        el = draw.Path(d=e.get("d", ""), **kw)
    elif tag == "circle":
        el = draw.Circle(float(e.get("cx", 0)), float(e.get("cy", 0)), float(e.get("r", 0)), **kw)
    elif tag == "ellipse":
        el = draw.Ellipse(float(e.get("cx", 0)), float(e.get("cy", 0)), float(e.get("rx", 0)), float(e.get("ry", 0)), **kw)
    elif tag == "rect":
        rx = float(e.get("rx", e.get("ry", 0)) or 0)
        el = draw.Rectangle(float(e.get("x", 0)), float(e.get("y", 0)), float(e.get("width", 0)), float(e.get("height", 0)), rx=rx, ry=rx, **kw)
    elif tag == "line":
        el = draw.Line(float(e.get("x1", 0)), float(e.get("y1", 0)), float(e.get("x2", 0)), float(e.get("y2", 0)), **{**kw, "fill": "none"})
    elif tag in ("polyline", "polygon"):
        pts = _floats(e.get("points"))
        if len(pts) < 4:
            return
        el = draw.Lines(*pts, close=(tag == "polygon"), **kw)
    else:
        return
    if tr:
        g = draw.Group(transform=tr)
        g.append(el)
        el = g
    target.append(el)


def parse_svg(text, source="<svg>"):
    """(elements, viewbox, root attributes) of an SVG text."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ArtError(f"{source}: not valid SVG ({e})") from None
    if _tag(root) != "svg":
        raise ArtError(f"{source}: the root element is <{_tag(root)}>, not <svg>")
    vb = _floats(root.get("viewBox"))
    if len(vb) != 4:
        w, h = _floats(root.get("width"))[:1] or [100.0], _floats(root.get("height"))[:1] or [100.0]
        vb = [0.0, 0.0, w[0], h[0]]
    gradients = {}
    for g in root.iter():
        if _tag(g) in ("linearGradient", "radialGradient") and g.get("id"):
            stops = [s for s in g if _tag(s) == "stop"]
            if stops:
                gradients[g.get("id")] = stops[0].get("stop-color") or _style(stops[0], {}).get("stop-color", "none")
    holder = draw.Group()
    base = {}
    for c in root:
        _convert(c, base, gradients, holder)
    return list(holder.children), tuple(vb), dict(root.attrib)


def _parse_size(attr, vb):
    """`data-size="4"` or `"4,3"` -> (w, h) in columns; none -> DEFAULT_SIZE on the longer side."""
    w, h = vb[2], vb[3]
    nums = _floats(attr)
    if len(nums) >= 2:
        return nums[0], nums[1]
    k = (nums[0] if nums else DEFAULT_SIZE) / max(w, h, 1e-9)
    return w * k, h * k


class ArtSvg:
    """An SVG file loaded for a symbol. Edit it with `recolor`, return it from `generate()`."""

    def __init__(self, text, source="<svg>"):
        self.text = text
        self.source = source
        self.elements, self.viewbox, self.attrs = parse_svg(text, source)
        self.size = _parse_size(self.attrs.get("data-size"), self.viewbox)

    def recolor(self, mapping):
        """A new ArtSvg with colours replaced: `svg.recolor({"#ff0000": "navy", "black": "#222"})`."""
        text = self.text
        for old, new in mapping.items():
            text = re.sub(re.escape(old), new, text, flags=re.I)
        return ArtSvg(text, self.source)

    def with_attrs(self, **attrs):
        """A new ArtSvg with attributes set on the root (`data_size="4"`)."""
        text = self.text
        for k, v in attrs.items():
            k = k.replace("_", "-")
            if re.search(rf'<svg[^>]*\s{k}="', text):
                text = re.sub(rf'(<svg[^>]*\s{k}=")[^"]*"', rf'\g<1>{v}"', text, count=1)
            else:
                text = text.replace("<svg", f'<svg {k}="{v}"', 1)
        return ArtSvg(text, self.source)

    def __repr__(self):
        return f"<ArtSvg {os.path.basename(self.source)} viewBox={self.viewbox}>"


class ArtGlyph:
    """A stamped symbol drawn from SVG elements: `Shape._glyph` places it in a box."""

    def __init__(self, art: ArtSvg):
        self.art = art

    def bbox(self):
        x, y, w, h = self.art.viewbox
        return x, y, x + w, y + h

    def natural_size(self):
        return self.art.size

    def elements(self):
        return self.art.elements


# ====================================================================================================
# The context a symbol gets
# ====================================================================================================

@dataclass
class Near:
    char: str                       # the symbol of the neighbour ("" for an ink anchor)
    at: tuple                       # centre in figure coordinates
    dist: float
    angle: float                    # degrees, clockwise from +x, from this symbol to it
    index: int                      # its number among the symbols of the figure
    size: tuple = (1.0, 1.0)


@dataclass
class Context:
    char: str
    index: int
    at: tuple
    size: tuple
    angle: float
    params: dict
    cells: list = field(repr=False, default_factory=list)       # every symbol of the figure: (char, at, size)
    ink: list = field(repr=False, default_factory=list)         # the ink polylines of the figure (from the ASCII art)
    seed: int = 0

    def neighbors(self, within=None, chars=None):
        """The other symbols, nearest first: Near(char, at, dist, angle, index, size)."""
        out = []
        for i, (c, p, s) in enumerate(self.cells):
            if i == self.index:
                continue
            if chars is not None and c not in chars:
                continue
            d = dist(self.at, p)
            if within is None or d <= within:
                out.append(Near(c, p, d, angle_to(self.at, p), i, s))
        return sorted(out, key=lambda n: n.dist)

    def nearest(self, chars=None, within=None):
        n = self.neighbors(within, chars)
        return n[0] if n else None

    def nearest_ink(self):
        """(point, polyline index) of the ink closest to this symbol, or None."""
        best = None
        for k, line in enumerate(self.ink):
            for p in line:
                d = dist(self.at, p)
                if best is None or d < best[0]:
                    best = (d, p, k)
        return None if best is None else (best[1], best[2])

    def forward(self, n: Near):
        """True for the symbol of a pair that should draw the connection (so a pair is drawn once)."""
        return self.index < n.index


# ====================================================================================================
# Loading a symbol
# ====================================================================================================

_cache = {}


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def load_svg(path):
    key = ("svg", path, _mtime(path))
    if key not in _cache:
        with open(path, encoding="utf-8") as f:
            _cache[key] = ArtSvg(f.read(), path)
    return _cache[key]


def load_script(path):
    key = ("py", path, _mtime(path))
    if key not in _cache:
        import types
        mod = types.ModuleType("artlib_" + re.sub(r"\W", "_", os.path.basename(path)))
        mod.__file__ = path
        try:
            with open(path, encoding="utf-8") as f:
                exec(compile(f.read(), path, "exec"), mod.__dict__)      # (no __pycache__ is written next to the symbols)
        except Exception as e:
            raise ArtError(f"{path}: {type(e).__name__}: {e}") from None
        if not callable(getattr(mod, "generate", None)):
            raise ArtError(f"{path}: it has no generate(...) function")
        _cache[key] = mod
    return _cache[key]


def load_kmj(path, run_file):
    """The Shape of an artlib .kmj: the def named like the symbol, or the only def, or the first one."""
    key = ("kmj", path, _mtime(path))
    if key not in _cache:
        prog = run_file(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        names = prog.shape_names
        pick = stem if stem in names else names[0] if names else None
        if pick is None:
            raise ArtError(f"{path}: it draws nothing (no def with a grid)")
        _cache[key] = prog.call(pick)
    return _cache[key]


def call_generate(mod, path, **available):
    """Call generate() with the parameters it declares."""
    sig = inspect.signature(mod.generate)
    kw, extra = {}, any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values())
    for name, p in sig.parameters.items():
        if name in available:
            kw[name] = available[name]
        elif p.default is p.empty and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
            raise ArtError(f"{path}: generate({name}) is not a parameter I can give (they are: {', '.join(available)})")
    if extra:
        kw = dict(available)
    try:
        return mod.generate(**kw)
    except ArtError:
        raise
    except Exception as e:
        raise ArtError(f"{path}: generate() failed: {type(e).__name__}: {e}") from None


def as_list(result):
    if result is None:
        return []
    return list(result) if isinstance(result, (list, tuple)) else [result]


def to_art(item, source):
    """An ArtSvg out of what generate() returned (text or ArtSvg), else None."""
    if isinstance(item, ArtSvg):
        return item
    if isinstance(item, str):
        return ArtSvg(item, source)
    return None
