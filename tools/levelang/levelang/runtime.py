"""Runtime: the Level IR plus the helpers that generated code calls (``__art__``, ``__emit__`` ...)."""
from __future__ import annotations

import ast
import inspect
import os
import random
from dataclasses import dataclass
from typing import Any

from .emoji import VS15, VS16
from .parser import Translation, translate
from .transform import transform


# ----------------------------------------------------------------------------- tile attributes


class Call:
    """The arguments of an attribute call that has keywords (``kmj("face.kmj", "talk", fps=6)``)."""

    def __init__(self, args: tuple, kwargs: dict) -> None:
        self.args, self.kwargs = args, kwargs

    def __repr__(self) -> str:
        return f"Call({self.args!r}, {self.kwargs!r})"


class Attr:
    """``solid``, ``fill.blue``, ``swim(6)``, ``size(1, 3)`` all evaluate to an Attr(kind, value)."""

    def __init__(self, kind: str, value: Any = True) -> None:
        self.kind, self.value = kind, value

    def __getattr__(self, name: str) -> "Attr":
        if name.startswith("__"):
            raise AttributeError(name)
        return Attr(self.kind, name)

    def __call__(self, *args: Any, **kwargs: Any) -> "Attr":
        if kwargs or self.kind == "kmj":   # kmj("file.kmj", "shape", look=(1, 0)): keep the call as it is
            return Attr(self.kind, Call(args, kwargs))
        return Attr(self.kind, args[0] if len(args) == 1 else args)

    def __repr__(self) -> str:
        return f"Attr({self.kind}={self.value!r})"


# flags: the first seven are engine-neutral; climb/save/anchor/crumbly are the platformer ones the
# Prowl2D Level.cs exporter understands (see export/slimejump.py)
FLAGS = ("solid", "hazard", "item", "spawn", "goal", "bg", "fg", "climb", "save", "anchor", "crumbly")
ANIMS = ("sway", "bob", "swim")
# valued attributes that end up in Tile.params: enemy(kind), shooter(dx, dy), at(ax, ay) = where in its cell an entity stands
PARAM_ATTRS = ("enemy", "shooter", "at")
ATTR_NAMES = FLAGS + ANIMS + PARAM_ATTRS + ("fill", "stroke", "svg", "size", "kmj", "svgs")


class Tile:
    def __init__(self, name: str, glyph: str = "") -> None:
        self.name = name
        self.glyph = glyph
        self.fill: Any = None
        self.stroke: Any = None
        self.pattern: list[str] | None = None
        self.svg: str | None = None
        self.frames: list[str] | None = None   # kmj tiles with several frames: SVGs cycled at `fps`
        self.fps: float = 6.0
        self.size: tuple = (1, 1)
        self.flags: set[str] = set()
        self.anim: dict[str, Any] = {}  # 'sway' / 'bob' / 'swim' -> param or None
        self.params: dict[str, Any] = {}

    # tiles are combined into rows with + and *
    def __add__(self, other):
        return Row([self]) + other

    def __radd__(self, other):
        return Row([other]) + self if other is not None else Row([None, self])

    def __mul__(self, n):
        if isinstance(n, float):
            raise TypeError("tile * float is only meaningful where the level transformer can see it (a statement or `if`)")
        return Row([self] * int(n))

    __rmul__ = __mul__

    def has(self, flag: str) -> bool:
        return flag in self.flags

    @property
    def animated(self) -> bool:
        return bool(self.anim) or bool(self.frames and len(self.frames) > 1)

    def frame_svg(self, t: float | None = None) -> str | None:
        if self.frames and len(self.frames) > 1 and t is not None:
            return self.frames[int(t * self.fps) % len(self.frames)]
        return self.svg

    @property
    def layer(self) -> int:
        return -1 if "bg" in self.flags else 1 if "fg" in self.flags else 0

    def to_dict(self) -> dict:
        d = {"name": self.name, "glyph": self.glyph, "flags": sorted(self.flags)}
        for k in ("fill", "stroke", "pattern", "svg"):
            if getattr(self, k) is not None:
                d[k] = getattr(self, k)
        if self.anim:
            d["anim"] = self.anim
        if self.params:
            d["params"] = {k: list(v) if isinstance(v, tuple) else v for k, v in self.params.items()}
        if self.size != (1, 1):
            d["size"] = list(self.size)
        if self.frames and len(self.frames) > 1:
            d["frames"], d["fps"] = self.frames, self.fps
        return d

    def __repr__(self) -> str:
        return f"<Tile {self.glyph or self.name}>"


class Row(list):
    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            return Row(list(self) + list(other))
        return Row(list(self) + [other])

    def __radd__(self, other):
        return Row([other] + list(self))

    def __mul__(self, n):
        return Row(list(self) * int(n))

    __rmul__ = __mul__


@dataclass
class Anchor:
    target: Any
    width: int


@dataclass
class Placed:
    tile: Tile
    x: float          # a whole cell in the world; layers may place at fractions of a cell
    y: float
    order: int
    size: tuple | None = None   # (w, h) in cells: overrides the tile's own size (a bigger or smaller coral from the same SVG)
    flip: bool = False          # mirrored left-right


class Layer:
    """A parallax layer: free-placed scenery that lives apart from the world grid (``with layer("far", parallax=0.3): ...``).

    ``parallax`` is how much of the camera's movement the layer follows: 1 moves with the world, 0 stays on the screen, 0.3 drifts slowly (far away),
    more than 1 rushes past (foreground). A layer's coordinates are cells, like the world's, and x = 0, y = 0 line up with the world's when the camera
    is at the top left corner. ``over`` layers draw in front of the world (and the player), the others behind it.
    ``haze=(colour, amount)`` blends the layer toward a colour (distance fog under water) and ``alpha`` fades it.
    """

    def __init__(self, name: str, parallax: float = 0.5, parallax_y: float | None = None, over: bool = False,
                 alpha: float = 1.0, haze: tuple | None = None) -> None:
        self.name, self.parallax = name, float(parallax)
        self.parallax_y = self.parallax if parallax_y is None else float(parallax_y)
        self.over, self.alpha, self.haze = bool(over), float(alpha), tuple(haze) if haze else None
        self.placements: list[Placed] = []
        self._index: dict | None = None

    def add(self, tile: Tile, x: float, y: float, size=None, flip=False) -> None:
        self.placements.append(Placed(tile, x, y, len(self.placements), tuple(size) if size else None, bool(flip)))
        self._index = None

    def cell(self, x: int, y: int) -> list[Placed]:
        if self._index is None:
            self._index = {}
            for p in self.placements:
                self._index.setdefault((int(p.x), int(p.y)), []).append(p)
        return self._index.get((x, y), [])

    def to_dict(self) -> dict:
        d = {"name": self.name, "parallax": [self.parallax, self.parallax_y], "over": self.over, "alpha": self.alpha,
             "placements": [[p.tile.name, p.x, p.y] + ([list(p.size)] if p.size else []) + (["flip"] if p.flip else []) for p in self.placements]}
        if self.haze:
            d["haze"] = list(self.haze)
        return d


@dataclass
class Skin:
    """Smooth outline drawn over blocky tiles: the ``selectors`` (flag names or tiles) are the cells it covers (see render/skin.py)."""
    selectors: tuple
    corner: float = 0.28       # how much of a one-cell edge each corner cut takes (0.5 is the most)
    smooth: int = 3            # rounds of corner cutting
    wobble: float = 0.0        # cells of gentle wave along the outline, so a straight floor is not a ruler line
    outline: Any = None        # colour of a line along the outline
    outline_width: float = 0.07
    seed: int = 0
    hide: bool = True          # the blocky tiles it covers are not drawn themselves

    def covers(self, tile: Tile) -> bool:
        return any(sel is tile or (isinstance(sel, str) and sel in tile.flags) for sel in self.selectors)

    def to_dict(self) -> dict:
        return {"selectors": [s if isinstance(s, str) else s.name for s in self.selectors], "corner": self.corner, "smooth": self.smooth,
                "wobble": self.wobble, "outline": self.outline, "outline_width": self.outline_width, "seed": self.seed, "hide": self.hide}


class Level:
    def __init__(self) -> None:
        self.placements: list[Placed] = []
        self.background: tuple | None = None  # (top colour, bottom colour)
        self.legend: dict[str, Any] = {"·": None}  # "·" is a spacer: use it to keep an otherwise empty art row alive
        self.meta: dict[str, Any] = {}
        self.layers: list[Layer] = []          # parallax layers, back to front within the "behind" and the "over" groups
        self.skins: list[Skin] = []            # smooth outlines over blocky tiles
        self.captions: list[dict] = []         # the story: say() / title() lines shown when the player passes x
        self.scene = None                      # a cutscene (see scene.py)
        self._index: dict | None = None

    def add(self, tile: Tile, x: int, y: int, size=None, flip=False) -> None:
        self.placements.append(Placed(tile, int(x), int(y), len(self.placements), tuple(size) if size else None, bool(flip)))
        self._index = None

    def bounds(self) -> tuple[int, int, int, int]:
        """(x0, y0, x1, y1), inclusive."""
        if not self.placements:
            return 0, 0, 0, 0
        xs = [p.x for p in self.placements]
        ys = [p.y for p in self.placements]
        return min(xs), min(ys), max(xs), max(ys)

    def cell(self, x: int, y: int) -> list[Placed]:
        if self._index is None:
            self._index = {}
            for p in self.placements:
                self._index.setdefault((p.x, p.y), []).append(p)
        return self._index.get((x, y), [])

    def find(self, flag: str) -> list[Placed]:
        return [p for p in self.placements if flag in p.tile.flags]

    def to_dict(self) -> dict:
        """Engine-neutral dump; the future exporters (Godot, Unity, Tiled ...) start from this."""
        tiles = {p.tile.name: p.tile for p in self.placements}
        tiles.update({p.tile.name: p.tile for l in self.layers for p in l.placements})
        x0, y0, x1, y1 = self.bounds()
        return {
            "bounds": [x0, y0, x1, y1],
            "background": list(self.background) if self.background else None,
            "tiles": {k: t.to_dict() for k, t in tiles.items()},
            "placements": [[p.tile.name, p.x, p.y] for p in self.placements],
            "meta": self.meta,
            **({"layers": [l.to_dict() for l in self.layers]} if self.layers else {}),
            **({"skins": [k.to_dict() for k in self.skins]} if self.skins else {}),
            **({"captions": self.captions} if self.captions else {}),
            **({"scene": self.scene.to_dict()} if self.scene else {}),
        }


# ----------------------------------------------------------------------------- defaults for bare emoji

_SQUARES = {
    "🟥": "crimson", "🟧": "darkorange", "🟨": "gold", "🟩": "limegreen", "🟦": "royalblue",
    "🟪": "mediumpurple", "🟫": "saddlebrown", "⬛": "black", "⬜": "white",
}
_SOLID = set("🧱🪨🪵") | set(_SQUARES)
_ITEMS = set("🪙💎⭐🍄")


def _default_tile(name: str, glyph: str) -> Tile:
    """An emoji you never defined still works: it draws as the emoji, with a few sensible defaults."""
    t = Tile(name, glyph)
    g = glyph.replace(VS16, "").replace(VS15, "")
    if g in _SQUARES:
        t.fill = _SQUARES[g]
    if g in _SOLID:
        t.flags.add("solid")
    if g in _ITEMS:
        t.flags.add("item")
    return t


# ----------------------------------------------------------------------------- runtime


class Runtime:
    MAX_DEPTH = 64

    def __init__(self, seed: int | None = None, basedir: str = ".") -> None:
        self.level = Level()
        self.rng = random.Random(seed)
        self.basedir = basedir
        self._warned: set[str] = set()
        self.cur: Layer | None = None   # inside `with layer(...)`: where place() puts tiles

    # -- placement ------------------------------------------------------------------
    def place(self, obj: Any, x: float, y: float, depth: int = 0, size=None, flip: bool = False) -> None:
        if depth > self.MAX_DEPTH:
            raise RecursionError("levelang: tile functions nested too deeply")
        if obj is None:
            return
        if isinstance(obj, Tile):
            if self.cur is not None:
                self.cur.add(obj, x, y, size, flip)
            else:
                self.level.add(obj, x, y, size, flip)
        elif isinstance(obj, Row):
            for i, o in enumerate(obj):
                self.place(o, x + i, y, depth + 1, size, flip)
        elif isinstance(obj, Anchor):
            self._call_section(obj, x, y)
        elif isinstance(obj, str):
            self.place(self.level.legend.get(obj) if obj in self.level.legend else self._unknown_char(obj), x, y, depth + 1)
        elif callable(obj):  # a procedural tile: def ⛰️(x, y): ...
            obj(x, y)
        else:
            raise TypeError(f"can't place {obj!r} at ({x}, {y})")

    def _unknown_char(self, ch: str):
        if ch not in self._warned:
            self._warned.add(ch)
            print(f"levelang: warning: art character {ch!r} is not in legend(); ignored")
        return None

    def _call_section(self, a: Anchor, x: int, y: int) -> None:
        fn = a.target
        if fn is None:
            return
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            params = {}
        kw = {}
        if "x" in params:
            kw["x"] = x
        if "y" in params:
            kw["y"] = y
        if "w" in params:
            kw["w"] = a.width
        if kw:
            fn(**kw)
        else:
            fn(x, y)

    # -- helpers that generated code calls -----------------------------------------
    def __tile__(self, name, glyph, attrs=(), pattern=None, svg=None) -> Tile:
        t = Tile(name, glyph)  # an explicit definition starts blank: no guessed defaults
        t.pattern = [str(r) for r in pattern] if pattern else None
        for a in attrs:
            if not isinstance(a, Attr):
                raise TypeError(f"def {name}: {a!r} is not a tile attribute (known: {', '.join(ATTR_NAMES)})")
            k, v = a.kind, a.value
            if k in ("fill", "stroke"):
                setattr(t, k, v)
            elif k == "svg":
                if v is not True:
                    svg = self._load_svg(v)
            elif k == "kmj":
                self._kmj(t, v)
            elif k == "svgs":
                self._svgs(t, v)
            elif k in FLAGS:
                t.flags.add(k)
            elif k in ANIMS:
                t.anim[k] = None if v is True else v
            elif k == "size":
                t.size = tuple(v) if isinstance(v, (tuple, list)) else (int(v), int(v))
            else:
                t.params[k] = v
        t.svg = svg if svg is not None else t.svg
        if pattern and not t.fill:
            t.fill = "dimgray"
        return t

    def _kmj(self, t: Tile, v: Any) -> None:
        """``kmj("file.kmj", "shape-or-list", fps=6, **args)``: SVG (or frames) drawn by kaomojilang."""
        from . import kmj
        args, kw = (v.args, dict(v.kwargs)) if isinstance(v, Call) else ((v,) if isinstance(v, str) else tuple(v), {})
        if not args or not isinstance(args[0], str):
            raise TypeError(f"kmj needs a file name: kmj(\"face.kmj\", \"shape\"), got {v!r}")
        t.fps = float(kw.pop("fps", 6))
        margin = float(kw.pop("margin", 1))
        path = args[0] if os.path.isabs(args[0]) else os.path.join(self.basedir, args[0])
        target = args[1] if len(args) > 1 else None
        frames = kmj.render(path, target, args[2:], kw, margin=margin)
        t.svg, t.frames = frames[0], frames

    def _svgs(self, t: Tile, v: Any) -> None:
        """``svgs("svg/dance_*.svg", fps=8)``: the SVG files that match (in name order) are the frames of the tile (any python made them)."""
        import glob
        args, kw = (v.args, dict(v.kwargs)) if isinstance(v, Call) else ((v,) if isinstance(v, str) else tuple(v), {})
        if not args or not isinstance(args[0], str):
            raise TypeError(f"svgs needs a file pattern: svgs(\"svg/dance_*.svg\", fps=8), got {v!r}")
        t.fps = float(kw.pop("fps", 6))
        pat = args[0] if os.path.isabs(args[0]) else os.path.join(self.basedir, args[0])
        files = sorted(glob.glob(pat))
        if not files:
            raise FileNotFoundError(f"svgs({args[0]!r}): no file matches (run the script that draws them?)")
        frames = []
        for p in files:
            with open(p, encoding="utf-8") as fh:
                frames.append(fh.read())
        t.svg, t.frames = frames[0], frames

    def _load_svg(self, src: str) -> str:
        if "<svg" in src:
            return src
        path = src if os.path.isabs(src) else os.path.join(self.basedir, src)
        with open(path, encoding="utf-8") as f:
            return f.read()

    def __art__(self, x0, y0, rows) -> None:
        for r, row in enumerate(rows):
            for col, obj in row:
                self.place(obj, x0 + col, y0 + r)

    def __anchor__(self, target, width) -> Anchor:
        return Anchor(target, width)

    def __emit__(self, value, x, y) -> int:
        self.place(value, x, y)
        return y + 1

    def __rep__(self, fn, n) -> Row:
        return Row(fn() for _ in range(int(n)))

    def __pick__(self, *fns):
        return self.rng.choice(fns)()

    def __maybe__(self, fn, p):
        return fn() if self.rng.random() < p else None

    def __roll__(self, p) -> bool:
        return self.rng.random() < p

    # -- builtins exposed to level files -------------------------------------------
    def _builtins(self) -> dict:
        def seed(n):
            self.rng.seed(n)

        def background(top, bottom=None):
            self.level.background = (top, bottom or top)

        def legend(mapping=None, **kw):
            self.level.legend.update(mapping or {})
            self.level.legend.update(kw)

        def meta(**kw):
            self.level.meta.update(kw)

        def layer(name, parallax=0.5, parallax_y=None, over=False, alpha=1.0, haze=None):
            """``with layer("far", parallax=0.3, haze=("#1b6ca8", 0.5)):`` puts what is placed inside it on a parallax layer."""
            rt = self
            found = next((l for l in rt.level.layers if l.name == name), None)
            lay = found or Layer(name, parallax, parallax_y, over, alpha, haze)
            if not found:
                rt.level.layers.append(lay)

            class _Scope:
                def __enter__(self_):
                    self_.prev, rt.cur = rt.cur, lay
                    return lay

                def __exit__(self_, *exc):
                    rt.cur = self_.prev
                    return False

            return _Scope()

        def skin(*tiles, **kw):
            """``skin(🟨, 🪨, wobble=0.15)`` or ``skin("solid")``: draw those cells with a smooth outline instead of square edges."""
            if not tiles:
                raise TypeError("skin() needs the tiles (or flag names, like \"solid\") it covers")
            for t in tiles:
                if not (isinstance(t, Tile) or (isinstance(t, str) and t in FLAGS)):
                    raise TypeError(f"skin(): {t!r} is neither a tile nor a flag name ({', '.join(FLAGS)})")
            sk = Skin(tuple(tiles), **kw)
            self.level.skins.append(sk)
            return sk

        def say(x, text, who=None, seconds=3.5):
            """``say(14, "Hello!", who="Slime")``: a line of dialogue, shown (and printed by the game) when the player gets to column x."""
            self.level.captions.append({"kind": "say", "x": float(x), "text": str(text), "who": who, "seconds": float(seconds)})

        def title(x, text, sub=None, seconds=4.5):
            """``title(0, "Chapter 1", "A quiet meadow")``: a chapter card, same trigger as say()."""
            self.level.captions.append({"kind": "title", "x": float(x), "text": str(text), "sub": sub, "seconds": float(seconds)})

        from .scene import builtins as scene_builtins
        import json as _json

        def data(path):
            """``data("audio.json")``: a JSON file next to the .lvl, as python lists and dicts."""
            p = path if os.path.isabs(path) else os.path.join(self.basedir, path)
            with open(p, encoding="utf-8") as fh:
                return _json.load(fh)

        return {
            "data": data,
            **scene_builtins(self.level),
            "say": say, "title": title,
            "seed": seed, "background": background, "legend": legend, "meta": meta, "layer": layer, "skin": skin,
            "rand": self.rng.random, "randint": self.rng.randint, "choice": self.rng.choice,
            "chance": lambda p: self.rng.random() < p,
            "place": lambda obj, x, y, size=None, flip=False: self.place(obj, x, y, size=size, flip=flip),
            "level": self.level,
        }

    def namespace(self, tr: Translation, filename: str) -> dict:
        ns: dict[str, Any] = {"__name__": "__levelang__", "__file__": filename, "x": 0, "y": 0}
        for k in ("__tile__", "__art__", "__anchor__", "__emit__", "__rep__", "__pick__", "__maybe__", "__roll__"):
            ns[k] = getattr(self, k)
        for k in ATTR_NAMES:
            ns[k] = Attr(k, None if k in ("fill", "stroke") else True)
        ns.update(self._builtins())
        for name, glyph in tr.symbols.items():
            ns[name] = _default_tile(name, glyph)
        return ns


def compile_level(source: str, filename: str = "<levelang>", seed: int | None = None, basedir: str | None = None) -> tuple[Level, Translation]:
    """levelang source -> (Level, Translation). Runs the whole pipeline."""
    tr = translate(source, filename)
    tree = transform(ast.parse(tr.python, filename), tr.tiles)
    code = compile(tree, filename, "exec")
    rt = Runtime(seed, basedir or (os.path.dirname(os.path.abspath(filename)) if os.path.exists(filename) else "."))
    exec(code, rt.namespace(tr, filename))
    return rt.level, tr


def load_file(path: str, seed: int | None = None) -> tuple[Level, Translation]:
    with open(path, encoding="utf-8") as f:
        return compile_level(f.read(), path, seed)
