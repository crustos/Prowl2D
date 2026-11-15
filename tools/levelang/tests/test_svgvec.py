"""levelang/svgvec.py: our own SVG reader (no Blender here; Blender gets what this makes)."""
import glob
import math
import pathlib
import unittest

from . import _common  # noqa: F401
from ._common import REPO
from levelang import svgvec as sv

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">%s</svg>'


def area(points):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))) / 2.0


class ColourTests(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(sv.parse_color("#fff"), (1.0, 1.0, 1.0, 1.0))
        self.assertAlmostEqual(sv.parse_color("#ff000080")[3], 128 / 255.0)
        self.assertEqual(sv.parse_color("rgb(255, 0, 0)"), (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(sv.parse_color("rgba(0,0,255,.5)"), (0.0, 0.0, 1.0, 0.5))
        self.assertEqual(sv.parse_color("none"), None)
        self.assertEqual(sv.parse_color("gold")[:3], (1.0, 215 / 255.0, 0.0))
        r, g, b, a = sv.parse_color("hsl(120, 100%, 50%)")
        self.assertAlmostEqual(g, 1.0)
        self.assertAlmostEqual(r, 0.0)
        with self.assertRaises(ValueError):
            sv.parse_color("#12")


class TransformTests(unittest.TestCase):
    def test_rotate_about_a_point(self):
        m = sv.parse_transform("rotate(90 10 10)")
        x, y = sv.apply(m, 20, 10)
        self.assertAlmostEqual(x, 10)
        self.assertAlmostEqual(y, 20)

    def test_chain_is_applied_right_to_left(self):
        m = sv.parse_transform("translate(10 0) scale(2)")
        self.assertEqual(sv.apply(m, 1, 1), (12, 2))
        self.assertAlmostEqual(sv.scale_of(m), 2)

    def test_matrix_and_skew(self):
        self.assertEqual(sv.apply(sv.parse_transform("matrix(1 0 0 1 5 6)"), 0, 0), (5, 6))
        x, y = sv.apply(sv.parse_transform("skewX(45)"), 0, 10)
        self.assertAlmostEqual(x, 10)


class PathTests(unittest.TestCase):
    def test_absolute_relative_and_shorthands(self):
        a = sv.parse_path("M10 10 H50 V50 H10 Z")
        b = sv.parse_path("m10 10 h40 v40 h-40 z")
        self.assertEqual(a, b)
        self.assertEqual(a[0][1], True)
        self.assertAlmostEqual(area(a[0][0]), 1600)

    def test_implicit_lineto_after_move(self):
        subs = sv.parse_path("M0 0 10 0 10 10")
        self.assertEqual(subs[0][0], [(0, 0), (10, 0), (10, 10)])

    def test_cubic_and_smooth_cubic_reach_their_ends(self):
        subs = sv.parse_path("M0 0 C10 0 20 10 20 20 S30 40 40 40")
        pts = subs[0][0]
        self.assertEqual(pts[-1], (40, 40))
        self.assertTrue(any(p == (20, 20) for p in pts))

    def test_quadratic_and_smooth_quadratic(self):
        subs = sv.parse_path("M0 0 Q10 10 20 0 T40 0")
        pts = subs[0][0]
        self.assertEqual(pts[-1], (40, 0))
        self.assertLess(min(p[1] for p in pts), -1)          # the reflected control point bends the second half the other way

    def test_arc_is_a_circle(self):
        subs = sv.parse_path("M0 50 A50 50 0 1 1 100 50 A50 50 0 1 1 0 50Z", step=1.0)
        pts = subs[0][0]
        self.assertAlmostEqual(area(pts), math.pi * 2500, delta=math.pi * 2500 * 0.01)
        for p in pts:
            self.assertAlmostEqual(math.dist(p, (50, 50)), 50, delta=0.01)

    def test_arc_sweep_flag(self):
        up = sv.parse_path("M0 0 A10 10 0 0 1 20 0")[0][0]
        down = sv.parse_path("M0 0 A10 10 0 0 0 20 0")[0][0]
        self.assertLess(min(p[1] for p in up), -5)
        self.assertGreater(max(p[1] for p in down), 5)

    def test_two_subpaths_and_a_command_after_close(self):
        subs = sv.parse_path("M0 0 L10 0 L10 10 Z M20 20 L30 20 L30 30 Z")
        self.assertEqual(len(subs), 2)
        subs = sv.parse_path("M0 0 L10 0 L10 10 Z L5 5")
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[1][0][0], (0, 0))

    def test_scientific_and_packed_numbers(self):
        self.assertEqual(sv.parse_path("M1e1-5L.5.5")[0][0], [(10, -5), (0.5, 0.5)])


class DocumentTests(unittest.TestCase):
    def test_viewbox_and_a_rect_with_corners(self):
        v = sv.parse('<svg viewBox="0 0 40 20"><rect x="0" y="0" width="40" height="20" rx="5" fill="#ff0000"/></svg>')
        self.assertEqual(v.viewbox, (0, 0, 40, 20))
        self.assertAlmostEqual(area(v.shapes[0].subpaths[0][0]), 800 - (4 - math.pi) * 25, delta=3)

    def test_style_overrides_attributes_and_inherits_from_groups(self):
        v = sv.parse(SVG % '<g fill="#00ff00" stroke="#000" stroke-width="3"><circle cx="50" cy="50" r="10" style="fill:#0000ff"/></g>')
        s = v.shapes[0]
        self.assertEqual(s.fill.rgba, (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(s.stroke.rgba, (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(s.stroke_width, 3)

    def test_group_opacity_multiplies_in_and_transform_scales_strokes(self):
        v = sv.parse(SVG % '<g opacity=".5" transform="scale(2)"><path d="M0 0L10 0" stroke="#fff" stroke-width="2" opacity=".5"/></g>')
        s = v.shapes[0]
        self.assertAlmostEqual(s.stroke_opacity, 0.25)
        self.assertAlmostEqual(s.stroke_width, 4)
        self.assertEqual(s.subpaths[0][0][1], (20, 0))

    def test_path_with_only_a_stroke_has_no_fill_and_nothing_visible_is_dropped(self):
        v = sv.parse(SVG % '<path d="M0 0L5 5" stroke="red" fill="none"/><path d="M0 0L5 5" fill="none"/><circle r="0" fill="red"/><rect width="5" height="5" display="none"/>')
        self.assertEqual(len(v.shapes), 1)
        self.assertIsNone(v.shapes[0].fill)

    def test_use_and_defs(self):
        v = sv.parse(SVG % '<defs><circle id="c" r="5" fill="#fff"/></defs><use href="#c" x="20" y="30"/>')
        self.assertEqual(len(v.shapes), 1)
        xs = [p[0] for p in v.shapes[0].subpaths[0][0]]
        self.assertAlmostEqual(sum(xs) / len(xs), 20, places=1)

    def test_unsupported_things_are_reported_not_fatal(self):
        v = sv.parse(SVG % '<defs><clipPath id="k"><rect width="5" height="5"/></clipPath></defs><text>hi</text><circle r="5" cx="9" cy="9" fill="red" stroke="blue" stroke-dasharray="2 2"/>')
        self.assertEqual(len(v.shapes), 1)
        self.assertTrue(any("text" in w for w in v.warnings))
        self.assertTrue(any("dasharray" in w for w in v.warnings))

    def test_not_an_svg(self):
        with self.assertRaises(ValueError):
            sv.parse("<html/>")
        with self.assertRaises(ValueError):
            sv.parse("<svg")

    def test_linear_gradient_in_box_units(self):
        v = sv.parse(SVG % '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="#0000ff"/></linearGradient></defs>'
                     '<rect x="10" y="20" width="30" height="40" fill="url(#g)"/>')
        p = v.shapes[0].fill
        self.assertEqual(p.kind, "linear")
        x0, y0, dx, dy = sv.gradient_axis(p)
        self.assertEqual((x0, y0, dx, dy), (10, 20, 0, 40))
        self.assertEqual(sv.gradient_at(p, 0.0)[:3], (1.0, 0.0, 0.0))
        self.assertEqual(sv.gradient_at(p, 1.0)[:3], (0.0, 0.0, 1.0))
        self.assertAlmostEqual(sv.gradient_at(p, 0.5)[0], 0.5)

    def test_gradient_follows_a_transform_and_href(self):
        v = sv.parse(SVG % '<defs><linearGradient id="a"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient>'
                     '<linearGradient id="g" href="#a" x1="0" y1="0" x2="1" y2="0"/></defs>'
                     '<g transform="translate(100 0)"><rect width="10" height="10" fill="url(#g)"/></g>')
        x0, y0, dx, dy = sv.gradient_axis(v.shapes[0].fill)
        self.assertEqual((x0, y0, dx, dy), (100, 0, 10, 0))

    def test_gradient_user_space(self):
        v = sv.parse(SVG % '<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="100"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>'
                     '<rect y="50" width="10" height="10" fill="url(#g)"/>')
        self.assertEqual(sv.gradient_axis(v.shapes[0].fill), (0, 0, 0, 100))


def coverage(vec, size, ss=4):
    """A binary mask of where the shapes paint, by filling and stroking with PIL at `ss` times the size (only a test: it is how this reader is checked against cairosvg)."""
    from PIL import Image, ImageDraw

    vx, vy, vw, vh = vec.viewbox
    k = size / max(vw, vh) * ss
    img = Image.new("L", (int(vw * k), int(vh * k)), 0)
    d = ImageDraw.Draw(img)
    for s in vec.shapes:
        for pts, closed in s.subpaths:
            q = [((x - vx) * k, (y - vy) * k) for x, y in pts]
            if s.fill is not None and len(q) >= 3:
                d.polygon(q, fill=255)
            if s.stroke is not None:
                w = max(1.0, s.stroke_width * k)
                path = q + ([q[0]] if closed else [])
                d.line(path, fill=255, width=int(round(w)))
                r = w / 2.0
                for x, y in (path if (s.linecap == "round" or s.linejoin == "round") else []):
                    d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return img.resize((int(vw * size / max(vw, vh)), int(vh * size / max(vw, vh))), Image.BILINEAR).point(lambda v: 255 if v > 100 else 0)


@unittest.skipUnless(glob.glob(str(REPO / "Samples" / "SlimeJumpLevelang" / "svg" / "*.svg")), "needs the sample's SVGs")
class AgainstCairoTests(unittest.TestCase):
    def test_every_sample_svg_covers_what_cairo_covers(self):
        try:
            import io
            import cairosvg
            from PIL import Image
        except Exception:
            self.skipTest("needs cairosvg")
        worst = (1.0, "")
        for f in sorted(glob.glob(str(REPO / "Samples" / "SlimeJumpLevelang" / "svg" / "*.svg"))):
            text = pathlib.Path(f).read_text(encoding="utf-8")
            vec = sv.parse(text)
            self.assertEqual(vec.warnings, [], f)
            mine = coverage(vec, 400)
            png = cairosvg.svg2png(bytestring=text.encode(), output_width=mine.width, output_height=mine.height)
            theirs = Image.open(io.BytesIO(png)).convert("RGBA").getchannel("A").point(lambda v: 255 if v > 8 else 0)
            a, b = mine.tobytes(), theirs.tobytes()
            inter = sum(1 for p, q in zip(a, b) if p and q)
            union = sum(1 for p, q in zip(a, b) if p or q)
            iou = inter / union if union else 1.0
            if iou < worst[0]:
                worst = (iou, f)
        self.assertGreater(worst[0], 0.85, worst)       # thin round-capped strokes (kelp) are the worst: the PIL stand-in for a stroke is rougher than cairo's


if __name__ == "__main__":
    unittest.main()
