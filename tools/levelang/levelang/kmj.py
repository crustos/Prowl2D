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
