"""CSS animation: @keyframes, the animation property, timing functions, interpolation, layers and templates driven by t."""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kaomojilang import anim, run  # noqa: E402
from kaomojilang.errors import RunError, Stage1Error  # noqa: E402

SYM = "𝀂"


def sample(css, spec, t, style=None, kinds=None):
    kinds = kinds or {"left": "length", "opacity": "number", "transform": "transform"}
    return anim.animate(style or {"left": "0px", "opacity": "1", "transform": "none"}, anim.parse_animation(spec), anim.parse_keyframes(css), t, kinds)


KF = "@keyframes k { from { left: 0px } to { left: 100px } }"


# ---- the animation property ------------------------------------------------------------------------------------------

def test_shorthand_in_any_order():
    a, = anim.parse_animation("2s ease-in 500ms infinite alternate both k")
    assert (a.name, a.duration, a.delay, a.iterations, a.direction, a.fill, a.timing) == ("k", 2.0, 0.5, math.inf, "alternate", "both", "ease-in")
    a, b = anim.parse_animation("k 1s linear, j 3s steps(4, jump-start) 2")
    assert (b.name, b.iterations, b.timing) == ("j", 2.0, "steps(4, jump-start)")


@pytest.mark.parametrize("bad", ["1s", "k 1s paused", "k 1s nonsense word", "k 1s 2s 3s"])
def test_shorthand_errors(bad):
    with pytest.raises(anim.AnimError):
        anim.parse_animation(bad)


def test_linear_progress_delay_and_fill():
    at = lambda spec, t: sample(KF, spec, t).get("left")           # noqa: E731
    assert at("k 2s linear", 1) == "50px"
    assert at("k 2s linear", 3) is None                              # over: back to the style
    assert at("k 2s linear forwards", 3) == "100px"                  # forwards keeps the end
    assert at("k 2s linear 1s", 0.5) is None                         # waiting for the delay
    assert at("k 2s linear 1s backwards", 0.5) == "0px"              # backwards applies the first keyframe while waiting
    assert at("k 2s linear -1s", 0) == "50px"                        # a negative delay starts in the middle
    assert at("k 2s linear 2", 3) == "50px"                          # two iterations: 1s into the second
    assert at("k 2s linear 2 forwards", 9) == "100px"
    assert at("k 2s linear infinite", 5) == "50px"


def test_directions():
    at = lambda d, t: sample(KF, f"k 2s linear infinite {d}", t)["left"]       # noqa: E731
    assert at("reverse", 0.5) == "75px"
    assert at("alternate", 2.5) == "75px"                            # the second pass runs backwards
    assert at("alternate-reverse", 0.5) == "75px"
    assert at("alternate-reverse", 2.5) == "25px"


def test_percent_keyframes_and_missing_ends_come_from_the_style():
    css = "@keyframes k { 50% { opacity: 0 } }"
    assert sample(css, "k 2s linear", 0.5, style={"opacity": "1"}, kinds={"opacity": "number"}) == {"opacity": "0.5"}
    assert sample(css, "k 2s linear", 1, style={"opacity": "1"}, kinds={"opacity": "number"}) == {"opacity": "0"}
    assert sample(css, "k 2s linear", 1.5, style={"opacity": "1"}, kinds={"opacity": "number"}) == {"opacity": "0.5"}
    css = "@keyframes k { 0%, 90% { left: 0px } 100% { left: 10px } }"
    assert sample(css, "k 10s linear", 8)["left"] == "0px"


def test_timing_functions():
    ease = anim.timing_function
    assert ease("linear")(0.3) == pytest.approx(0.3)
    for name in ("ease", "ease-in", "ease-out", "ease-in-out"):
        f = ease(name)
        assert f(0) == 0 and f(1) == 1
    assert ease("ease-in")(0.5) < 0.5 < ease("ease-out")(0.5)
    assert ease("ease-in-out")(0.5) == pytest.approx(0.5, abs=1e-6)
    assert ease("cubic-bezier(0, 0, 1, 1)")(0.37) == pytest.approx(0.37, abs=1e-6)
    assert [ease("steps(4)")(x) for x in (0, 0.24, 0.26, 0.99)] == [0, 0, 0.25, 0.75]
    assert [ease("steps(2, jump-start)")(x) for x in (0.01, 0.6)] == [0.5, 1.0]
    assert ease("step-end")(0.99) == 0 and ease("step-start")(0.01) == 1
    for bad in ("cubic-bezier(2, 0, 1, 1)", "wobble", "steps(0)"):
        with pytest.raises(anim.AnimError):
            ease(bad)


def test_keyframe_timing_function_applies_to_its_interval():
    css = "@keyframes k { from { left: 0px; animation-timing-function: steps(2) } to { left: 100px } }"
    assert sample(css, "k 2s linear", 0.5)["left"] == "0px"          # the step function of the keyframe, not the linear one of the animation
    assert sample(css, "k 2s linear", 1.2)["left"] == "50px"


def test_later_animation_wins():
    css = KF + "@keyframes j { from { left: 7px } to { left: 7px } }"
    assert sample(css, "k 2s linear, j 2s linear", 1)["left"] == "7px"


# ---- values --------------------------------------------------------------------------------------------------------------

def test_transform_interpolation():
    f = anim.lerp_transform
    assert f("rotate(0deg)", "rotate(90deg)", 0.5) == "rotate(45deg)"
    assert f("none", "scale(3)", 0.5) == "scale(2, 2)"
    assert f("translateX(0px)", "translate(20px, 10px)", 0.5) == "translate(10px, 5px)"
    assert f("scaleX(1)", "scaleX(-1)", 0.5) == "scale(0, 1)"                     # a flip goes through zero, as in a browser
    mixed = anim.parse_transform(f("rotate(0deg)", "translate(10px, 0px) rotate(180deg)", 0.5))
    assert mixed[0][0] == "matrix"
    a, b, c, d, e, g = mixed[0][1]
    assert (e, g) == pytest.approx((5, 0)) and (a, b) == pytest.approx((0, 1), abs=1e-9)       # half way: 90 degrees, half the distance


def test_decompose_roundtrip():
    m = anim._matrix_of([("translate", [3, 4]), ("rotate", [30]), ("skewX", [20]), ("scale", [2, 0.5])])
    assert anim._recompose(*anim.decompose(m)) == pytest.approx(m)


def test_other_kinds():
    assert anim.interpolate("pair", "0 -62", "0 0", 0.5) == "0 -31"
    assert anim.interpolate("pair", "1", "3 5", 0.5) == "2 3"
    assert anim.interpolate("filter", "none", "blur(40px)", 0.25) == "blur(10px)"
    assert anim.interpolate("origin", "left top", "50% 50%", 0.5) == "25% 25%"
    assert anim.interpolate("angle", "0", "0.5turn", 0.5) == "90deg"
    with pytest.raises(anim.AnimError):
        anim.interpolate("length", "1em", "2px", 0.5)


def test_keyframes_errors():
    for bad in ("@keyframes k { 150% { left: 0px } }", "@keyframes k { sideways { left: 0px } }", "@keyframes k { }",
                ".a { color: red }", "@keyframes k { from { left: 0px }"):
        with pytest.raises(anim.AnimError):
            anim.parse_keyframes(bad)


# ---- layers --------------------------------------------------------------------------------------------------------------

LAYERS = """@keyframes rise {
    from { shift: 0 -6 }
    to   { shift: 0 0 }
}
@keyframes fade { from { opacity: 0 } to { opacity: 1 } }

def thing:
    layer body
         10    12
         14    16
    layer mud(shift=(0, -6), animation="rise 4s linear forwards")
     20  22
     24  26
    layer glow(opacity=0, animation="fade 2s linear 1s forwards, rise 2s")
     30  32
"""


def mud(t=None, **kw):
    return dict(run(LAYERS).call("thing", t=t, **kw).layers)


def test_layer_animation_follows_t():
    assert mud()["mud"]["shift"] == (0, -6)                          # no t: nothing is animated
    assert mud(0)["mud"]["shift"] == (0, -6)
    assert mud(2)["mud"]["shift"] == pytest.approx((0, -3))
    assert mud(9)["mud"]["shift"] == (0, 0)                          # forwards
    assert mud(2)["glow"]["opacity"] == pytest.approx(0.5)           # starts after its 1s delay: 1s into 2s


def test_layer_animation_per_call_and_wins_over_call_options():
    assert mud(1, layers={"mud": {"animation": "rise 2s linear forwards"}})["mud"]["shift"] == pytest.approx((0, -3))
    assert mud(2, layers={"mud": {"shift": (0, -99)}})["mud"]["shift"] == pytest.approx((0, -3))
    with pytest.raises(RunError, match="must be text"):
        mud(1, layers={"mud": {"animation": 3}})


def test_layer_animation_moves_the_drawing():
    p = run(LAYERS)
    a, b = p.call("thing", t=0), p.call("thing", t=4)
    assert a.bbox()[1] != b.bbox()[1]                                # the mud layer moved
    assert len(p.frames("thing", fps=4, duration=4)) == 16


def test_layer_animation_errors():
    with pytest.raises(RunError, match="no @keyframes named 'nope'"):
        run(LAYERS.replace("rise 4s", "nope 4s")).call("thing", t=1)
    with pytest.raises(RunError, match="cannot be animated"):
        run(LAYERS.replace("from { opacity: 0 }", "from { color: red }")).call("thing", t=1)
    with pytest.raises(RunError, match="'t' must be a number"):
        run(LAYERS).call("thing", t="soon")
    with pytest.raises(Stage1Error, match="never closed"):
        run("@keyframes a {\n from { left: 0px }\n")
    with pytest.raises(Stage1Error, match="percentage"):
        run("@keyframes a { 200% { left: 0px } }")


# ---- templates -----------------------------------------------------------------------------------------------------------

def tpl(src, **kw):
    return run(f"def scene(x=0):\n" + "".join(f"    {l}\n" for l in src.strip("\n").splitlines())).call("scene", **kw)


def test_template_animation_with_a_style_block_and_expressions():
    src = f'''<style>
  @keyframes slide {{ from {{ left: {{x}}px }} to {{ left: {{x+100}}px }} }}
</style>
<div style="left:{{x}}px; font-size:40px; animation: slide 2s linear forwards">{SYM}</div>'''
    xs = lambda t: tpl(src, x=10, t=t).parts[0].points[0][0] - tpl(src, x=10).parts[0].size[0] / 2           # noqa: E731
    assert xs(None) == pytest.approx(1.0)
    assert xs(1) == pytest.approx(6.0)                                # half way: 50px = 5 columns further
    assert xs(5) == pytest.approx(11.0)


def test_template_transform_animation_and_file_level_keyframes():
    src = f'''<div style="font-size:40px; animation: sway 2s linear infinite">{SYM}</div>'''
    prog = run("@keyframes sway { 0%, 100% { transform: rotate(-10deg) } 50% { transform: rotate(10deg) } }\n"
               "def scene():\n    " + src + "\n")
    lin = lambda t: prog.call("scene", t=t).parts[0].linear                                   # noqa: E731
    assert lin(0)[1] < 0 < lin(1)[1]
    assert lin(1) == pytest.approx(lin(3))                            # infinite


def test_template_blur_and_opacity_animation():
    src = f'''<style> @keyframes soft {{ from {{ filter: blur(0px); opacity: 0 }} to {{ filter: blur(40px); opacity: 1 }} }} </style>
<div style="font-size:40px; animation: soft 2s linear both">{SYM}</div>'''
    p = tpl(src, t=1).parts[0]
    assert p.opacity == pytest.approx(0.5) and p.blur[1] == pytest.approx(2.0)


def test_template_animation_errors():
    with pytest.raises(RunError, match="no @keyframes named"):
        tpl(f'<div style="animation: ghost 1s">{SYM}</div>', t=0)
    with pytest.raises(RunError, match="only @keyframes"):
        tpl(f'<style> .a {{ left: 0px }} </style><div>{SYM}</div>', t=0)
    with pytest.raises(RunError, match="same unit"):
        tpl(f'<style> @keyframes a {{ to {{ transform-origin: 0px 0px }} }} </style><div style="animation: a 1s">{SYM}</div>', t=0.5)
