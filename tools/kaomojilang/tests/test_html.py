"""HTML + CSS subset: templates in a def, symbols placed with position/left/top/font-size and transforms."""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kaomojilang import run  # noqa: E402
from kaomojilang.errors import RunError  # noqa: E402

SYM = "𝀂"          # an asymmetric symbol of artlib (the angry brow)


def draw(body, params="", **kw):
    src = f"def scene({params}):\n" + "".join(f"    {l}\n" for l in body.strip("\n").splitlines())
    return run(src).call("scene", **kw)


def part(shape, k=0):
    return [p for p in shape.parts if p.kind == "point"][k]


def test_position_size_and_units():
    s = draw(f'<div style="position:absolute; left:100px; top:50px; font-size:100px">{SYM}</div>')
    p = part(s)
    w, h = p.size
    from kaomojilang import artlib
    nat = artlib.load_svg(os.path.join(os.path.dirname(artlib.__file__), "..", "..", "artlib", f"{SYM}.svg")).size
    assert max(w, h) == pytest.approx(10.0 * max(nat) / artlib.DEFAULT_SIZE)       # font-size 100px = 10 columns for a default-size symbol
    assert p.points[0][0] == pytest.approx(10.0 + w / 2)                 # left is the left edge of the box
    assert p.points[0][1] == pytest.approx(5.0 + h / 2)


def test_expressions_and_braces():
    s = draw(f'<div style="left:{{x*2+10}}px; top:{{y}}px; font-size:50px">{SYM}</div>', "x, y", x=5, y=7)
    p = part(s)
    assert p.points[0][0] == pytest.approx(2.0 + p.size[0] / 2)
    assert p.points[0][1] == pytest.approx(0.7 + p.size[1] / 2)
    assert len(draw(f'<div>{{c}}</div>', "c", c=SYM).parts) == 1                   # content from a parameter


def test_python_lines_before_the_template():
    s = draw(f'n = x + 1\n<div style="left:{{n * 10}}px">{SYM}</div>', "x", x=4)
    assert part(s).points[0][0] - part(s).size[0] / 2 == pytest.approx(5.0)


def test_flip_rotate_scale_make_the_matrix():
    s = draw(f'<div style="transform:scaleX(-1)">{SYM}</div>')
    assert part(s).linear == pytest.approx((-1, 0, 0, 1))
    assert 'matrix(-1' in s.to_svg()
    s = draw(f'<div style="transform:rotate(90deg)">{SYM}</div>')
    assert part(s).linear == pytest.approx((0, 1, -1, 0), abs=1e-9)
    s = draw(f'<div style="transform:scale(2, 0.5)">{SYM}</div>')
    assert part(s).linear == pytest.approx((2, 0, 0, 0.5))
    x0, y0, x1, y1 = s.bbox()                                              # the box is stretched about its centre
    w, h = part(s).size
    assert (x1 - x0) == pytest.approx(2 * w) and (y1 - y0) == pytest.approx(h / 2)


def test_rotation_about_the_center_keeps_the_symbol_in_place():
    plain = part(draw(f'<div style="left:100px; top:100px; font-size:60px">{SYM}</div>'))
    turned = part(draw(f'<div style="left:100px; top:100px; font-size:60px; transform:rotate(90deg)">{SYM}</div>'))
    assert turned.points[0] == pytest.approx(plain.points[0])


def test_transform_origin_moves_the_pivot():
    base = '<div style="left:100px; top:100px; font-size:100px; transform:rotate(180deg); transform-origin:%s">' + SYM + '</div>'
    c = part(draw(base % "50% 50%")).points[0]
    tl = part(draw(base % "left top")).points[0]
    w, h = part(draw(base % "50% 50%")).size
    assert tl[0] == pytest.approx(c[0] - w) and tl[1] == pytest.approx(c[1] - h)    # turning about the corner mirrors the centre across it


def test_nested_elements_follow_the_parent():
    s = draw(f'<div style="left:100px; top:0px; transform:rotate(90deg)"><div style="left:50px; top:0px; font-size:10px">{SYM}</div></div>')
    p = part(s)
    w, h = p.size
    # the child is at (5 + w/2, h/2) in the parent's frame, which is turned by 90 degrees about the parent's own corner (10, 0)
    assert p.points[0] == pytest.approx((10 - h / 2, 5 + w / 2))
    assert p.linear == pytest.approx((0, 1, -1, 0), abs=1e-9)


def test_text_run_goes_left_to_right_and_spaces_are_skipped():
    s = draw(f'<div style="left:0px; top:0px; font-size:40px">{SYM} {SYM}</div>')
    a, b = [p for p in s.parts if p.kind == "point"]
    assert b.points[0][0] - a.points[0][0] == pytest.approx(a.size[0])


def test_opacity_hidden_and_display():
    s = draw(f'<div style="opacity:0.5">{SYM}</div><div style="display:none">{SYM}</div><div style="visibility:hidden">{SYM}</div>')
    assert len(s.parts) == 1 and part(s).opacity == 0.5
    assert 'opacity="0.5"' in s.to_svg()


def test_layers_by_attribute_and_per_call_options():
    src = f'<div layer="a" style="left:0px">{SYM}</div><div layer="b" style="left:200px">{SYM}</div>'
    s = draw(src)
    assert [n for n, _ in s.layers] == ["a", "b"]
    moved = draw(src, layers={"b": {"shift": (0, 10)}})
    assert moved.bbox()[3] > s.bbox()[3]
    with pytest.raises(RunError, match="no layer"):
        draw(src, layers={"zzz": {}})


def test_symbols_from_a_def_and_standard_params():
    src = f'''def dot:
    1

def scene():
    <div style="left:30px; font-size:50px">{SYM}</div>
'''
    s = run(src).call("scene", sizes={SYM: (1, 1)})
    assert s.parts                                                      # the standard parameters are accepted by a template


def test_grid_drawings_with_ascii_arrows_are_still_grids():
    src = "def g:\n    <--- 1\n    2\n"
    assert run(src).call("g").parts


@pytest.mark.parametrize("body, msg", [
    (f'<div style="color:red">{SYM}</div>', "not supported"),
    (f'<div style="transform:wiggle(3)">{SYM}</div>', "not supported"),
    (f'<div style="left:4em">{SYM}</div>', "length"),
    (f'<div>{SYM}', "never closed"),
    (f'{SYM}</div>', None),
    (f'<div style="left:{{__x}}px">{SYM}</div>', "reserved"),
    (f'<div style="left:{{a.b}}px">{SYM}</div>', "not allowed"),
    (f'<div style="left:{{1/0}}px">{SYM}</div>', "ZeroDivision"),
    ('<div>A</div>', "no drawing for the symbol"),
])
def test_clear_errors(body, msg):
    if msg is None:
        pytest.skip("not a template")
    with pytest.raises(RunError, match=msg):
        draw(body)


def test_fox_example_runs_with_layers():
    from kaomojilang import run_file
    path = os.path.join(os.path.dirname(__file__), "..", "examples", "fox_html.kmj")
    prog = run_file(path)
    fox = prog.call("fox")
    assert [n for n, _ in fox.layers] == ["shade", "ears", "face", "fur"]
    assert len(fox.parts) == 11 and fox.to_svg().count("matrix(") >= 6          # (the whiskers are strokes from artlib/𝀯.py, not parts)
    lifted = prog.call("fox", layers={"ears": {"shift": (0, -3)}})
    assert lifted.bbox()[1] < fox.bbox()[1]


def test_filter_blur_is_one_embedded_image_for_the_element_and_its_children():
    s = draw(f'<div style="left:0px; top:0px; filter:blur(20px); opacity:0.5"><div style="left:0px">{SYM}</div><div style="left:100px">{SYM}</div></div>')
    a, b = s.parts
    assert a.blur[0] == b.blur[0] and a.blur[1] == pytest.approx(2.0)      # 20px = 2 columns of sigma; one group
    assert a.opacity == b.opacity == 0.5                                   # the opacity of an element reaches its children
    svg = s.to_svg()
    assert svg.count("<image") == 1 and "data:image/png;base64" in svg
    x0, y0, x1, y1 = s.bbox()
    assert x0 < -5.5                                                       # the blur margin (3 sigma) is part of the box


def test_blur_is_soft_and_keeps_its_colour():
    import cairosvg
    import io
    from PIL import Image
    s = draw('<div style="left:0px; top:0px; font-size:80px; filter:blur(4px)">\U0001d00f</div>')          # a black dot
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.to_svg().encode(), output_width=200))).convert("RGBA")
    w, h = im.size
    centre, edge = im.getpixel((w // 2, h // 2)), im.getpixel((w // 2, 3))
    assert centre[3] > 200 and centre[0] < 20                              # solid black in the middle (no grey bleed from the transparent pixels)
    assert edge[3] < centre[3]                                             # and fading out


@pytest.mark.parametrize("css, msg", [("filter:blur(2em)", "length"), ("filter:sepia(1)", "not supported"), ("filter:blur(-3px)", "negative")])
def test_filter_errors(css, msg):
    with pytest.raises(RunError, match=msg):
        draw(f'<div style="{css}">{SYM}</div>')
