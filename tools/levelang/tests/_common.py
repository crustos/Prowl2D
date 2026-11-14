"""Shared helpers. Run all tests:   python3 -m unittest discover -s tools/levelang/tests -t tools/levelang"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # tools/levelang
REPO = ROOT.parent.parent  # the Prowl2D checkout
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(REPO) not in sys.path:      # the editor's model (prowl_editor) checks what the project exporter writes
    sys.path.insert(1, str(REPO))

from levelang import compile_level, translate  # noqa: E402
from levelang.runtime import Runtime  # noqa: E402
from levelang.transform import transform  # noqa: E402

EX = ROOT / "examples"


def run(src, seed=1):
    return compile_level(src, "<test>", seed=seed)[0]


def cells(level):
    return sorted((p.tile.name, p.x, p.y) for p in level.placements)


def xy(level):
    return [(x, y) for _, x, y in cells(level)]
