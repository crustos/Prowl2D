"""layer sections of a drawing: transparencies on the same grid, clip, per-call options."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kaomojilang import run  # noqa: E402
from kaomojilang.drawing.flatten import flatten  # noqa: E402
from kaomojilang.errors import RunError, Stage1Error  # noqa: E402

SRC = """def thing(rough=0):
    layer body
        0         2

        3         1
    layer mud(clip=body, opacity=0.5)

          10    12

          13    11
    layer drips
    20
"""


def thing(**kw):
    return run(SRC).call("thing", **kw)


def test_layers_are_parsed_and_their_parts_belong_to_them():
    s = thing()
    assert [n for n, _ in s.layers] == ["body", "mud", "drips"]
    assert dict(s.layers)["mud"] == {"clip": "body", "opacity": 0.5}
    assert {p.id: p.layer for p in s.parts} == {0: "body", 10: "mud", 20: "drips"}


def test_each_layer_is_a_transparency_on_the_same_grid_its_first_line_is_row_0():
    s = thing()
    body, mud = [p for p in s.parts if p.id in (0, 10)]
    assert body.points[0][1] == 0.0                   # row 0 of body
    assert mud.points[0][1] == 2.0                    # the mud layer starts with an empty line: its first number is on row 1


def test_clip_masks_the_layer_in_the_svg_and_options_can_be_set_per_call():
    svg = thing().to_svg()
    assert '<clipPath id="clip_mud">' in svg and 'clip-path="url(#clip_mud)"' in svg and 'opacity="0.5"' in svg
    moved = thing(layers={"mud": {"shift": (0, -3)}}).to_svg()
    assert "translate(" in moved and moved != svg
    hidden = thing(layers={"mud": {"hidden": True}}).to_svg()
    assert 'id="mud"' not in hidden and 'id="body"' in hidden


def test_layers_are_grease_pencil_layers():
    strokes, _ = flatten(thing().to_drawing())
    assert {s.layer for s in strokes} == {"body", "mud", "drips"}


def test_a_drawing_without_layers_is_unchanged():
    s = run("def sq():\n    1    2\n\n    4    3\n").call("sq")
    assert s.layers == [] and all(p.layer == "" for p in s.parts)
    assert 'id="p1"' in s.to_svg()


def test_errors_are_clear():
    with pytest.raises(Stage1Error, match="no such layer"):
        run("def a():\n    layer x(clip=nope)\n    1  2\n\n    4  3\n")
    with pytest.raises(Stage1Error, match="unknown layer option"):
        run("def a():\n    layer x(blur=2)\n    1  2\n\n    4  3\n")
    with pytest.raises(RunError, match="no layer 'zzz'"):
        thing(layers={"zzz": {}})
    with pytest.raises(RunError, match="different layers"):
        run("def a():\n    layer x\n    1  2\n    layer y\n    3  4\n").call("a")


def test_ink_is_chained_per_layer():
    s = run("def a:\n    layer x\n    ,---.\n    layer y\n    `---'\n").call("a")
    assert sorted((p.layer) for p in s.parts if 1000 <= p.id < 1500) == ["x", "y"]


def test_a_clip_is_one_path_so_overlapping_shapes_keep_their_union():
    src = """def two:
    layer a
    2    3

    5    4
    layer b
      12   13

      15   14
    layer m(clip=(a, b))
    20      22
    24      26
"""
    svg = run(src).call("two").to_svg()
    assert svg.count("<clipPath") == 1 and svg.split("<clipPath")[1].split("</clipPath>")[0].count("<path") == 1


def test_scale_pivots_on_the_origin_of_the_layer():
    src = "def a:\n    layer pool(origin=bottom)\n    2    3\n\n    5    4\n"
    box = run(src).call("a", layers={"pool": {"scale": (0.5, 0.5)}}).bbox()
    full = run(src).call("a").bbox()
    assert abs(box[3] - full[3]) < 1e-9 and box[1] > full[1]                      # shrinks toward its bottom edge
    top = run(src).call("a", layers={"pool": {"scale": (0.5, 0.5), "origin": "top"}}).bbox()
    assert abs(top[1] - full[1]) < 1e-9 and top[3] < full[3]
    with pytest.raises(RunError, match="origin"):
        run(src).call("a", layers={"pool": {"origin": "nowhere"}})
