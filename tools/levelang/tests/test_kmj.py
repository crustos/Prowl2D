"""kmj tiles: shapes and animations drawn by kaomojilang (tools/kaomojilang) used as levelang tiles."""
import os
import unittest

from ._common import EX, run

try:
    from levelang import kmj
    kmj.kaomojilang()
    HAVE = True
except Exception:
    HAVE = False

K = "../../kaomojilang/examples/"


def level(extra=""):
    return run(f'def F -> kmj("{K}face_anim.kmj", "talk", fps=4), size(2, 2){extra}:\n\n'
               f'def B -> kmj("{K}bear.kmj", "bear"), size(2, 2):\n\n'
               f'def E -> kmj("{K}face_anim.kmj", "eye"), size(1, 1):\n\n'
               'place(F, 0, 0)\nplace(B, 3, 0)\nplace(E, 6, 0)\n'.replace("\\", "/"))


@unittest.skipUnless(HAVE, "tools/kaomojilang missing")
class KmjTests(unittest.TestCase):
    def setUp(self):
        os.chdir(EX)    # file names are relative to the .lvl; the test source has none, so use the examples folder

    def tiles(self):
        return {t.name: t for t in (p.tile for p in level().placements)}

    def test_a_list_of_shapes_is_an_animation(self):
        t = self.tiles()["F"]
        self.assertGreater(len(t.frames), 1)
        self.assertEqual(t.fps, 4)
        self.assertTrue(t.animated)
        self.assertEqual(t.svg, t.frames[0])
        # the frames share one canvas, so they line up when cycled
        vb = {f.split('viewBox="')[1].split('"')[0] for f in t.frames}
        self.assertEqual(len(vb), 1)

    def test_a_shape_def_is_a_single_frame(self):
        t = self.tiles()["B"]
        self.assertIn("<svg", t.svg)
        self.assertFalse(t.animated)

    def test_arguments_reach_the_shape_def(self):
        lvl = run(f'def A -> kmj("{K}face_anim.kmj", "eye"), size(1, 1):\n\n'
                  f'def B -> kmj("{K}face_anim.kmj", "eye", scale={{10: 0}}), size(1, 1):\n\n'
                  'place(A, 0, 0)\nplace(B, 2, 0)\n')
        a, b = (p.tile for p in lvl.placements)
        self.assertNotEqual(a.svg, b.svg)       # the pupil (part 10) is hidden in B

    def test_frame_follows_time(self):
        t = self.tiles()["F"]
        self.assertEqual(t.frame_svg(0), t.frames[0])
        self.assertEqual(t.frame_svg(0.25), t.frames[1])
        self.assertEqual(t.frame_svg(len(t.frames) / 4), t.frames[0])      # loops

    def test_to_dict_has_frames(self):
        d = self.tiles()["F"].to_dict()
        self.assertEqual(len(d["frames"]), len(self.tiles()["F"].frames))
        self.assertEqual(d["fps"], 4)

    def test_bad_target_is_an_error(self):
        with self.assertRaises(Exception):
            run(f'def A -> kmj("{K}bear.kmj", "nope"), size(1, 1):\n\nplace(A, 0, 0)\n')

    def test_gif_renders_animated_tiles(self):
        try:
            import cairosvg  # noqa: F401
        except Exception:
            self.skipTest("cairosvg missing")
        from levelang.render.gif import render_gif
        lvl = level()
        import tempfile
        out = os.path.join(tempfile.mkdtemp(), "k.gif")
        render_gif(lvl, out, seconds=1.0) if "seconds" in render_gif.__code__.co_varnames else render_gif(lvl, out)
        from PIL import Image
        im = Image.open(out)
        im.seek(0); a = im.convert("RGB").tobytes()
        im.seek(min(2, im.n_frames - 1)); b = im.convert("RGB").tobytes()
        self.assertNotEqual(a, b)               # the face changes between frames


@unittest.skipUnless(HAVE, "tools/kaomojilang missing")
class KmjExampleTests(unittest.TestCase):
    def test_example_level_compiles(self):
        from levelang import compile_level
        src = (EX / "kaomoji.lvl").read_text(encoding="utf-8")
        lvl = compile_level(src, str(EX / "kaomoji.lvl"), seed=1)[0]
        names = {p.tile.name: p.tile for p in lvl.placements}
        self.assertEqual(sum(1 for t in names.values() if t.frames), 5)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAVE, "tools/kaomojilang missing")
class AnimatedKmjTests(unittest.TestCase):
    """kmj("file", "shape", fps=4, seconds=4): frame k is the drawing at t = k / fps (CSS @keyframes / layer animation)."""

    SRC = ('@keyframes rise { from { shift: 0 -6 } to { shift: 0 0 } }\n'
           'def thing:\n    layer body\n         10    12\n         14    16\n'
           '    layer mud(shift=(0, -6), animation="rise 4s linear forwards")\n     20  22\n     24  26\n')

    def test_the_tile_draws_its_frames_when_asked(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "thing.kmj")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.SRC)
            lv = run(f'def M -> kmj("{path}", "thing", fps=4, seconds=4), size(2, 2):\n\nplace(M, 0, 0)\n')
            t = lv.placements[0].tile
            self.assertEqual((len(t.frames), t.fps, t.animated), (16, 4, True))
            self.assertNotEqual(t.frame_svg(0.0), t.frame_svg(3.0))                    # the mud has risen
            vb = {t.frames[i].split('viewBox="')[1].split('"')[0] for i in (0, 7, 15)}
            self.assertEqual(len(vb), 1)                                               # one canvas
            self.assertEqual(t.frame_svg(1.0), t.frames[4])

    def test_speed_stretches_the_time_of_the_animation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "thing.kmj")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.SRC)
            slow = run(f'def M -> kmj("{path}", "thing", fps=4, seconds=16, speed=0.25), size(2, 2):\n\nplace(M, 0, 0)\n').placements[0].tile
            fast = run(f'def M -> kmj("{path}", "thing", fps=4, seconds=4), size(2, 2):\n\nplace(M, 0, 0)\n').placements[0].tile
            self.assertEqual(slow.frames[12], fast.frames[3])                                                  # 3s of a 4s story, in 12s
