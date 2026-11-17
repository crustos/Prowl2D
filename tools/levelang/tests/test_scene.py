"""Cutscenes: the scene() timeline, its GIF, its Cutscene.cs, and Samples/SlimeJumpLoveStory."""
import os
import tempfile
import unittest

from PIL import Image

from ._common import REPO, run
from levelang import load_file
from levelang.export import to_cutscene_cs
from levelang.render.scene import render_scene

SAMPLE = REPO / "Samples" / "SlimeJumpLoveStory"

SRC = '''
def A -> fill.red:

def B -> fill.blue:

def H -> fill.pink:

def S -> fill.green, solid:

for cx in range(12):
    place(S, cx, 6)
place(S, 0, 0)
scene("t", seconds=4, fps=8, view=(8, 6))
actor("a", {"idle": A, "alt": B}, 1, 4)
actor("b", A, 9, 4, flip=True)
move("a", 1, 3, 5, 4, ease="linear", hop=2)
move("a", 3, 4, 2, 4, ease="linear")
pose("a", 2, "alt")
emote("a", 1, H, seconds=1)
cam(0, 4, 3)
cam(2, 8, 3, zoom=2)
fade(0, 1, 1, 0)
fade(3, 4, 0, 1, "white")
card(0, "Title", "sub", seconds=1)
line(2, "Hi", who="A")
'''


class SceneTimelineTests(unittest.TestCase):
    def setUp(self):
        self.sc = run(SRC).scene

    def test_position_and_hop(self):
        a = self.sc.actors["a"]
        self.assertEqual(a.position(0), (1, 4))
        self.assertEqual(a.position(2), (3, 2))            # half way, at the top of a 2 cell hop
        self.assertEqual(a.position(3), (5, 4))
        self.assertEqual(a.position(3.5), (3.5, 4))
        self.assertEqual(a.position(9), (2, 4))

    def test_facing_and_pose(self):
        a, b = self.sc.actors["a"], self.sc.actors["b"]
        self.assertFalse(a.facing_flip(2))
        self.assertTrue(a.facing_flip(3.5))                 # walked left
        self.assertTrue(b.facing_flip(0))
        self.assertEqual((a.pose(1), a.pose(2)), ("idle", "alt"))

    def test_camera_and_fade(self):
        self.assertEqual(self.sc.camera(0), (4, 3, 1))
        self.assertEqual(self.sc.camera(2), (8, 3, 2))
        self.assertEqual(self.sc.camera(1)[2], 1.5)        # in-out is half way at the middle
        self.assertEqual(self.sc.camera(5), (8, 3, 2))
        self.assertEqual(self.sc.fade(0)[0], 1)
        self.assertEqual(self.sc.fade(2), (0, "black"))
        self.assertEqual(self.sc.fade(3.5), (0.5, "white"))

    def test_mistakes_are_reported_in_plain_words(self):
        with self.assertRaisesRegex(Exception, "scene"):
            run('def A -> fill.red:\n\nactor("a", A, 0, 0)\n')
        base = SRC.split("move(")[0]
        for tail, msg in [('move("zz", 0, 1, 1, 1)', "no actor"), ('move("a", 2, 1, 1, 1)', "after it starts"),
                          ('move("a", 0, 2, 1, 1)\nmove("a", 1, 3, 1, 1)', "time order"), ('pose("a", 1, "nope")', "no pose"),
                          ('cam(0, 1, 1, ease="bounce")', "ease must be")]:
            with self.subTest(tail=tail), self.assertRaisesRegex(Exception, msg):
                run(base + tail + "\n")

    def test_scene_is_in_the_json(self):
        d = self.sc.to_dict()
        self.assertEqual(d["seconds"], 4)
        self.assertEqual(len(d["actors"]["a"]["moves"]), 2)


MV = SRC.replace('scene("t", seconds=4, fps=8, view=(8, 6))', 'scene("t", seconds=4, fps=8, view=(8, 6), bpm=120)') + '''
actor("big", {"idle": A, "alt": B}, 20, 4, size=(10, 7))
hide("b", 0)
show("b", beat(4))
warp("b", beat(2), 3, 4)
dance("a", beat(8), beat(10), ["idle", "alt"], every=1, hop=1)
face("a", 3, left=False)
cut(beat(5), 7, 3, 2)
punch(beat(1), 0.1, 0.5)
shake(1, 2, 0.5)
'''


class MusicVideoTests(unittest.TestCase):
    def setUp(self):
        self.sc = run(MV).scene

    def test_beat_clock(self):
        self.assertEqual(self.sc.bpm, 120)
        self.assertEqual(self.sc.beat(4), 2.0)

    def test_cut_is_a_step(self):
        self.assertEqual(self.sc.base_camera(2.4), (8, 3, 2))        # the last key is at 2.0; the cut came at beat 5 = 2.5
        before = self.sc.base_camera(2.49)
        after = self.sc.base_camera(2.5)
        self.assertEqual(after, (7, 3, 2))
        self.assertNotEqual(before, after)

    def test_warp_show_hide_size_face(self):
        b = self.sc.actors["b"]
        self.assertFalse(b.visible(0))
        self.assertFalse(b.visible(1.9))
        self.assertTrue(b.visible(2.0))
        self.assertEqual(b.position(0.9), (9, 4))                    # not yet
        self.assertEqual(b.position(1.0), (3, 4))                    # the jump, at beat 2
        self.assertFalse(b.facing_flip(1.0) is False)                # a warp does not turn it: b started mirrored
        self.assertEqual(self.sc.actors["big"].size, (10, 7))
        self.assertFalse(self.sc.actors["a"].facing_flip(3.5))       # face(left=False) after it walked left

    def test_dance_is_poses_and_hops_on_the_beat(self):
        a = self.sc.actors["a"]
        self.assertEqual((a.pose(3.99), a.pose(4.0), a.pose(4.5)), ("alt", "idle", "alt"))
        y_mid = a.position(4.25)[1]
        self.assertLess(y_mid, a.position(4.0)[1])                   # up in the middle of a hop
        self.assertEqual(a.position(4.5)[1], a.position(4.0)[1])

    def test_punch_and_shake_move_the_camera(self):
        self.assertGreater(self.sc.punch(0.5), 1.0)
        self.assertEqual(self.sc.punch(2.0), 1.0)
        self.assertNotEqual(self.sc.camera(1.3)[:2], self.sc.base_camera(1.3)[:2])
        self.assertEqual(self.sc.camera(0.1)[:2], self.sc.base_camera(0.1)[:2])

    def test_export_has_the_music_video_functions_and_no_float_math(self):
        cs = to_cutscene_cs(run(MV))
        for needle in ("public static bool Visible(int a, float t)", "public static float Punch(float t)", "public static float ShakeX(float t)", "public static float CamZoom(float t)",
                       "if (k == 4)"):
            self.assertIn(needle, cs)
        self.assertNotIn("Math.", cs)
        self.assertIn("if (t >= 1f) return 3f;", cs)                 # the warp: a jump at its time, no Seg


class SceneRenderAndExportTests(unittest.TestCase):
    def test_gif_has_the_frames_and_size_of_the_view(self):
        lvl = run(SRC)
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "s.gif")
            info = render_scene(lvl, out, tile_px=10)
            self.assertEqual((info["frames"], info["size"]), (32, (80, 60)))
            g = Image.open(out)                    # identical neighbouring frames are merged by the encoder
            self.addCleanup(g.close)
            self.assertLessEqual(g.n_frames, 32)
            g.seek(0)
            first = g.convert("RGB").getpixel((40, 30))
            g.seek(g.n_frames - 1)
            self.assertNotEqual(first, g.convert("RGB").getpixel((40, 30)))   # the fade to white is over it

    def test_export_is_if_chains_and_matches_the_python_numbers(self):
        cs = to_cutscene_cs(run(SRC), "t.lvl")
        for bad in ("switch", "new float[", "{ 0", "List<"):
            self.assertNotIn(bad, cs)
        self.assertIn("public const float Seconds = 4f;", cs)
        self.assertIn("if (t >= 3f) return 5f;", cs)                              # the end of the long move, latest first
        self.assertIn("Hop(1f, 3f, t, 0, 2f)", cs)
        self.assertIn('return "white";', cs)
        self.assertLess(cs.index("if (t >= 3f) return 5f;"), cs.index("if (t >= 1f) return Seg(1f, 3f, 1f, 5f"))

    def test_no_scene_cannot_be_exported(self):
        with self.assertRaises(ValueError):
            to_cutscene_cs(run("def A -> fill.red, solid:\n\nplace(A, 0, 0)\n"))


class LoveStorySampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.level, _ = load_file(str(SAMPLE / "intro.lvl"), 1)

    def test_cutscene_cs_is_up_to_date(self):
        """Regenerate: python3 tools/levelang export-scene Samples/SlimeJumpLoveStory/intro.lvl -o Samples/SlimeJumpLoveStory/Cutscene.cs"""
        self.assertEqual((SAMPLE / "Cutscene.cs").read_text(encoding="utf-8"), to_cutscene_cs(self.level, "intro.lvl"))

    def test_the_story_fits_the_timeline(self):
        sc = self.level.scene
        self.assertEqual((sc.seconds, sc.bpm), (48, 120))
        self.assertEqual({"slime", "gelly", "croak", "bride", "limo", "slime_cu", "gelly_cu", "croak_cu", "bride_cu"} - set(sc.actors), set())
        caps = sorted(sc.captions, key=lambda c: c["t"])
        for c in caps:
            self.assertTrue(0 <= c["t"] and c["t"] + c["seconds"] <= sc.seconds, f"{c['text']!r} runs past the end of the scene")
        for a, b in zip(caps, caps[1:]):
            self.assertLessEqual(a["t"] + a["seconds"], b["t"] + 1e-9, f"{a['text']!r} is still up when {b['text']!r} starts")
        self.assertEqual(sc.fade(0)[0], 1)                    # opens from black
        self.assertEqual(sc.fade(sc.seconds)[0], 1)           # and ends on white, into the game

    def test_the_cuts_are_on_the_beat(self):
        sc = self.level.scene
        beat = 60.0 / sc.bpm
        cuts = [c for c in sc.cams if c[4] == "cut"]
        self.assertGreater(len(cuts), 40)                     # a music video: many shots
        for c in cuts:
            self.assertAlmostEqual(c[0] / (beat / 2), round(c[0] / (beat / 2)), places=6, msg=f"a cut at {c[0]}s is off the half beat")

    def test_every_close_up_is_in_its_room_with_a_face(self):
        sc = self.level.scene
        for cu, (x0, x1) in {"slime_cu": (128, 160), "gelly_cu": (160, 192), "croak_cu": (192, 224), "bride_cu": (256, 288)}.items():
            a = sc.actors[cu]
            self.assertTrue(x0 <= a.x and a.x + a.size[0] <= x1, f"{cu} spills out of its room")
            self.assertGreater(a.size[0], 15)

    def test_actors_stay_on_the_stage(self):
        x0, y0, x1, y1 = self.level.bounds()
        sc = self.level.scene
        for a in sc.actors.values():
            for i in range(int(sc.seconds * 4)):
                x, y = a.position(i / 4)
                self.assertTrue(x0 <= x <= x1 + 1 and y0 <= y <= y1 + 1, f"{a.name} is off the stage at {i / 4}s: {x}, {y}")

    def test_game_plays_the_cutscene_and_the_sample_is_complete(self):
        game = (SAMPLE / "Game.cs").read_text(encoding="utf-8")
        self.assertIn("Cutscene.Seconds", game)
        self.assertLess(game.index("PlayCutscene();"), game.index("Scripts.Init();"))
        for f in ("Level.cs", "Story.cs", "Cutscene.cs", "level.lvl", "intro.lvl", "intro.gif", "README.md"):
            self.assertTrue((SAMPLE / f).exists(), f)


if __name__ == "__main__":
    unittest.main()
