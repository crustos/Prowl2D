"""kaomojilang tiles: ``def 🙂 -> kmj("face.kmj", "talk", fps=6, look=(1, 0)), size(2, 2):``.

kaomojilang is vendored in ``tools/kaomojilang`` (see its VENDORED.md); the SVG path is pure Python and needs no Blender.
"""
from __future__ import annotations

import importlib
import os
import sys

_TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def kaomojilang():
    """The kaomojilang package (``tools/`` is put on sys.path to find it)."""
    if _TOOLS not in sys.path:
        sys.path.append(_TOOLS)
    return importlib.import_module("kaomojilang")


def render(path: str, target: str | None = None, args: tuple = (), kwargs: dict | None = None,
           cell: float = 10, margin: float = 1) -> list[str]:
    """The SVG frames of ``target`` in a .kmj file: a shape def called with ``args``/``kwargs`` (1 frame), a Shape (1 frame)
    or a list of Shapes (one frame each, on a shared canvas). With no target, the file's last variable is used."""
    k = kaomojilang()
    prog = k.run_file(path)
    rt = importlib.import_module("kaomojilang.runtime")
    if target is None:
        names = list(prog.variables())
        if not names:
            raise ValueError(f"{path}: no variable to draw; name a shape: kmj({path!r}, 'name')")
        target = names[-1]
    obj = prog.call(target, *args, **(kwargs or {})) if (args or kwargs or target in prog.shape_names) else prog[target]
    shapes = list(obj) if isinstance(obj, (list, tuple)) else [obj]
    if not shapes or not all(isinstance(s, rt.Shape) for s in shapes):
        raise ValueError(f"{path}: {target!r} is not a shape, a list of shapes, or a shape def")
    bbox = rt.union_bbox(shapes)
    return [s.to_svg(cell=cell, margin=margin, bbox=bbox) for s in shapes]


class LazyFrames:
    """The frames of an animated kaomojilang drawing, drawn when asked for: frame k is the drawing at ``t = k / fps`` seconds
    (its ``@keyframes`` / layer ``animation`` run on the time of the scene). All frames share one canvas, the union of the drawing
    sampled along the whole time (or the ``bbox`` given)."""

    def __init__(self, path, target, args, kwargs, fps, seconds, cell=10, margin=1, bbox=None, speed=1.0):
        k = kaomojilang()
        self.rt = importlib.import_module("kaomojilang.runtime")
        self.prog = k.run_file(path)
        if target is None or not (args or kwargs or target in self.prog.shape_names):
            raise ValueError(f"{path}: an animated kmj tile needs a shape def: kmj({path!r}, 'name', seconds=..)")
        self.target, self.args, self.kwargs = target, tuple(args), dict(kwargs)
        self.fps, self.n, self.cell, self.margin = float(fps), max(1, int(round(seconds * fps))), cell, margin
        self.speed = float(speed)
        self._cache = {}
        step = max(1, self.n // 120)
        self.bbox = tuple(bbox) if bbox else self.rt.union_bbox([self.shape(i) for i in sorted({*range(0, self.n, step), self.n - 1})])

    def shape(self, i):
        return self.prog.call(self.target, *self.args, t=i / self.fps * self.speed, **self.kwargs)

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self[j] for j in range(*i.indices(self.n))]
        i = range(self.n)[i]
        if i not in self._cache:
            if len(self._cache) > 8:
                self._cache.pop(next(iter(self._cache)))
            self._cache[i] = self.shape(i).to_svg(cell=self.cell, margin=self.margin, bbox=self.bbox)
        return self._cache[i]

    def __iter__(self):
        return (self[i] for i in range(self.n))
