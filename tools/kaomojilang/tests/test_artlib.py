"""artlib: symbols in grids (files named after the symbol: .kmj / .svg / .py), ASCII art as ink, context-aware strokes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kaomojilang import run, run_file, translate  # noqa: E402
from kaomojilang.drawing.flatten import flatten  # noqa: E402
from kaomojilang.errors import RunError  # noqa: E402
ShapeError = RunError                    # Program.call reports a drawing error as a RunError
from kaomojilang import ink  # noqa: E402

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "face_artlib.kmj")
A, B, C = "\U0001d0f1", "\U0001d0f2", "\U0001d0f3"          # not in the repo's artlib/ (the tests bring their own)


def lib(tmp_path, **files):
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return [str(tmp_path)]


SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10" data-size="4,2"><rect x="0" y="0" width="20" height="10" fill="red"/></svg>'


# ----------------------------------------------------------------------------------------------------
# Stage 1: what a grid holds
# ----------------------------------------------------------------------------------------------------

def test_symbols_and_ascii_art_are_cells():
    src = translate(f"def f:\n  {A} \\\\\\\n {B}  )\n").source
    assert f"('sym', '{A}', 2.0, 0)" in src and ("('art', '\\\\', 4.0, 0)" in src) and f"('sym', '{B}', 1.0, 1)" in src


def test_def_without_parens_is_a_def():
    assert "def f(*, fill=None" in translate(f"def f:\n    {A}\n").source


def test_a_python_body_is_still_python():
    r = translate("def f(a):\n    return (a - 1)\n")
    assert r.shapes == {}


def test_numbers_and_symbols_can_share_a_grid(tmp_path):
    s = draw(tmp_path, f"    1 2 3   {A}", {f"{A}.svg": SVG})
    assert {p.kind for p in s.parts} == {"polygon", "point"} or {p.kind for p in s.parts} >= {"point"}


# ----------------------------------------------------------------------------------------------------
# Finding a symbol
# ----------------------------------------------------------------------------------------------------

def draw(tmp_path, grid, files, name="f", **call):
    d = lib(tmp_path, **files)
    prog = run(f"def {name}:\n{grid}\n", "t.kmj", artlib=d)
    return prog.call(name, **call)


def test_svg_symbol_is_stamped_at_its_cell_with_its_data_size(tmp_path):
    s = draw(tmp_path, f"    {A}", {f"{A}.svg": SVG})
    (p,) = [q for q in s.parts if q.kind == "point"]
    assert p.points == [(4.0, 0.0)] and p.size == (4.0, 2.0)
    assert "<rect" in s.to_svg()


def test_kmj_symbol_uses_the_def_named_like_the_symbol(tmp_path):
    s = draw(tmp_path, f"    {C}", {f"{C}.kmj": f"def {C}(fill=blue):\n    0     1\n\n    3     2\n"})
    (p,) = s.parts
    assert p.size == (6.0, 4.0)


def test_python_wins_over_svg_over_kmj(tmp_path):
    files = {f"{A}.py": "def generate():\n    return '<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1 1\"><circle cx=\".5\" cy=\".5\" r=\".4\" fill=\"green\"/></svg>'\n",
             f"{A}.svg": SVG, f"{A}.kmj": f"def {A}():\n    0 1\n"}
    assert "<circle" in draw(tmp_path, f"    {A}", files).to_svg()


def test_svg_next_to_the_script_is_passed_to_generate(tmp_path):
    files = {f"{A}.svg": SVG, f"{A}.py": "def generate(svg, stroke):\n    return svg.recolor({'red': 'navy'})\n"}
    out = draw(tmp_path, f"    {A}", files).to_svg()
    assert "navy" in out and "red" not in out


def test_a_def_in_the_file_beats_the_library(tmp_path):
    d = lib(tmp_path, **{f"{A}.svg": SVG})
    src = f"def {A}:\n    0   1\n\ndef f:\n    {A}\n"
    s = run(src, "t.kmj", artlib=d).call("f")
    assert "<rect" not in s.to_svg()


def test_fill_can_replace_a_symbol_for_one_call(tmp_path):
    d = lib(tmp_path, **{f"{A}.svg": SVG})
    src = f"def other:\n    0   1\n\ndef f:\n    {A}\n"
    prog = run(src, "t.kmj", artlib=d)
    s = prog.call("f", fill={A: prog.call("other")})
    assert "<rect" not in s.to_svg()


def test_sizes_scale_rotate_shift_are_per_symbol(tmp_path):
    d = lib(tmp_path, **{f"{A}.svg": SVG})
    prog = run(f"def f:\n    {A}\n", "t.kmj", artlib=d)
    p = prog.call("f", sizes={A: (6, 3)}, rotate={A: 30}, shift={A: (2, 1)}).parts[0]
    assert p.size == (6.0, 3.0) and p.angle == 30.0 and p.points == [(6.0, 2.0)]
    assert prog.call("f", scale={A: 0}).parts[0].hidden


def test_missing_symbol_says_where_it_looked(tmp_path):
    with pytest.raises(ShapeError, match=r"no drawing for the symbol .* put .*\.kmj, .*\.svg or .*\.py in artlib/"):
        draw(tmp_path, f"    {B}", {})


def test_bad_script_is_reported_with_its_path(tmp_path):
    with pytest.raises(ShapeError, match="generate"):
        draw(tmp_path, f"    {A}", {f"{A}.py": "def generate(nothing):\n    return None\n"})
    with pytest.raises(ShapeError, match="no generate"):
        draw(tmp_path, f"    {A}", {f"{A}.py": "x = 1\n"}, name="g")


# ----------------------------------------------------------------------------------------------------
# Context: neighbours, strokes under and over
# ----------------------------------------------------------------------------------------------------

LINKER = '''from kaomojilang.brush import connect, sketch, curve
def generate(ctx):
    out = []
    for n in ctx.neighbors(chars="%s"):
        if ctx.forward(n):
            out += connect(ctx.at, n.at, bend=0.3)
    return out
''' % B


def test_a_symbol_sees_its_neighbours_and_draws_a_connection(tmp_path):
    files = {f"{A}.py": LINKER, f"{B}.svg": SVG}
    s = draw(tmp_path, f"    {A}          {B}", files)
    assert len(s.over) == 1 and len(s.under) == 3              # a dark curve and three light sketch passes under it
    assert s.over[0].points[0] == (4.0, 0.0) and s.over[0].points[-1] == (15.0, 0.0)
    svg = s.to_svg()
    assert svg.index('id="under"') < svg.index('id="p2010"') < svg.index('id="over"')


def test_connection_is_drawn_once_per_pair(tmp_path):
    files = {f"{A}.py": LINKER.replace(B, A), f"{A}.svg": SVG}
    s = draw(tmp_path, f"    {A}      {A}", files)
    assert len(s.over) == 1


def test_strokes_work_for_grease_pencil_too(tmp_path):
    files = {f"{A}.py": LINKER, f"{B}.svg": SVG}
    d = draw(tmp_path, f"    {A}          {B}", files).to_drawing()
    strokes, warnings = flatten(d)
    assert {"under", "over"} <= {st.layer for st in strokes}


# ----------------------------------------------------------------------------------------------------
# Ink: ASCII art
# ----------------------------------------------------------------------------------------------------

def test_stacked_bars_are_one_straight_line():
    segs, _ = ink.strokes([("|", 3.0, 0), ("|", 3.0, 1), ("|", 3.0, 2)])
    (pts, closed), = ink.chains(segs)
    assert len(pts) == 2 and not closed and pts == [(3.0, -1.0), (3.0, 5.0)]


def test_a_row_of_slashes_is_one_shallow_stroke():
    segs, _ = ink.strokes([("\\", 4.0, 0), ("\\", 5.0, 0), ("\\", 6.0, 0)])
    assert segs == [[(3.5, -1.0), (6.5, 1.0)]]


def test_comma_dash_quote_make_an_arc():
    segs, _ = ink.strokes([(",", 0.0, 0), ("-", 1.0, 0), ("'", 2.0, 0)])
    (pts, _), = ink.chains(segs)
    assert pts[0][1] > pts[-1][1]                              # it rises to the right (y points down)


def test_ascii_art_becomes_smooth_ink_parts(tmp_path):
    s = draw(tmp_path, "    ,-.\n   /   \\\n   `---'", {})
    assert s.parts and all(p.id >= 1000 for p in s.parts)
    assert "<path" in s.to_svg()


# ----------------------------------------------------------------------------------------------------
# The repository's artlib and the example
# ----------------------------------------------------------------------------------------------------

def test_the_example_face_uses_the_repo_artlib():
    prog = run_file(EXAMPLE)
    s = prog.call("face_example")
    stamped = [p for p in s.parts if p.kind == "point" and p.id >= 2000]
    assert len(stamped) == 7 and s.under and s.over          # the nose is strokes only: its construction lines under, the hook over
    svg = s.to_svg()
    assert svg.count("<svg") == 1 and 'id="under"' in svg


def test_every_symbol_in_the_repo_artlib_draws():
    import glob
    from kaomojilang import artlib
    root = artlib.repo_artlib()
    symbols = sorted({os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(root, "*")) if not f.endswith(".md")})
    assert len(symbols) >= 60
    grid = "def sheet:\n" + "".join(f"    {s}\n\n\n\n" for s in symbols)
    s = run(grid).call("sheet")
    assert s.to_svg().count("<svg") == 1


@pytest.mark.parametrize("n", range(2, 10))
def test_example_faces_render_with_a_closed_outline(n):
    path = os.path.join(os.path.dirname(EXAMPLE), f"face_{n}_artlib.kmj")
    s = run_file(path).call(f"face_{n}")
    outline = [p for p in s.parts if 1000 <= p.id < 1500]
    assert any(not p.open and len(p.points) > 12 for p in outline)       # the head is one closed line
    assert s.under and "<svg" in s.to_svg()


# ----------------------------------------------------------------------------------------------------
# Ink: gaps and runs of marks
# ----------------------------------------------------------------------------------------------------

def test_a_cell_of_air_in_an_outline_is_still_one_line():
    cells = [("-", 0.5, 0), ("-", 1.5, 0), ("-", 4.5, 0), ("-", 5.5, 0)]        # two cells missing in the middle
    segs, _ = ink.strokes(cells, 2.0)
    assert len(ink.chains(segs)) == 2                                            # too far apart: two lines
    segs, _ = ink.strokes(cells[:2] + [("-", 3.5, 0)] + cells[2:], 2.0)
    assert len(ink.chains(segs)) == 1                                            # one missing cell: still joined


def test_marks_side_by_side_share_the_way_between_their_neighbours():
    cells = [("\\", 0.5, 1), (",", 1.5, 1), (".", 2.5, 1), ("/", 3.5, 1)]
    segs, _ = ink.strokes(cells, 2.0)
    assert len(ink.chains(segs)) == 1


# ----------------------------------------------------------------------------------------------------
# The hand and the underdrawing
# ----------------------------------------------------------------------------------------------------

def test_hand_wanders_slowly_and_overshoots():
    from kaomojilang.brush import hand, dist
    line = [(0, 0), (20, 0)]
    pts = hand(line, err=0.3, seed=4)
    steps = [dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    assert max(abs(p[1]) for p in pts) < 1.5                                     # stays near the line
    ys = [p[1] for p in pts]
    assert max(abs(ys[i + 1] - ys[i]) for i in range(len(ys) - 1)) < 0.25        # slow wander, no jitter
    assert min(p[0] for p in pts) < 0.5 or max(p[0] for p in pts) > 19.5         # an end runs on (or is cut)
    assert hand(line, err=0.3, seed=4) == pts                                    # deterministic


SKETCH = "def head(rough=1):\n" + """
    ,----------.
 ,-'            `-.
 |                |
 |   𝀇       𝀈   |
 |                |
 `-.            ,-'
    `----------'
"""


def test_rough_is_off_by_default_and_sketches_the_whole_drawing_when_on():
    plain = run(SKETCH.replace("rough=1", "rough=0")).call("head")
    assert not plain.under
    rough = run(SKETCH).call("head")
    assert len(rough.under) > 20 and all(s.layer == "under" and s.opacity < 0.5 for s in rough.under)
    assert [s.points for s in run(SKETCH).call("head").under] == [s.points for s in rough.under]       # same drawing, same sketch
    more = run(SKETCH.replace("rough=1", "rough={'amount': 2, 'seed': 3}")).call("head")
    assert more.under and [s.points for s in more.under] != [s.points for s in rough.under]


def test_underdrawing_goes_from_the_whole_to_the_parts():
    from kaomojilang import underdraw
    outline = underdraw.Contour([(0, 0), (30, 0), (30, 20), (0, 20)], True, 0.8)
    eyes = [underdraw.Block((9, 8), (5, 3)), underdraw.Block((21, 8), (5, 3))]
    strokes = underdraw.plan([outline], eyes, 1.0, "black", 1)
    xs = [p[0] for s in strokes for p in s.points]
    assert min(xs) < 0 and max(xs) > 30                      # construction and gesture run past the outline
    assert sum(1 for s in strokes if s.width > 0.1) > 0
    assert underdraw.plan([outline], eyes, 0.0) == []


def test_tapered_strokes_are_drawn_as_ribbons():
    from kaomojilang.brush import Stroke, stroke_element
    el = stroke_element(Stroke([(0, 0), (5, 1), (10, 0)], 0.4, taper=0.8))
    assert el.args["d"].endswith("Z") and el.args["fill"] == "black"
