"""The Blender export: the scene description (plain Python, always tested) and the .blend it makes (tested when the `bpy` module is installed: `pip install bpy`)."""
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest

from . import _common  # noqa: F401
from ._common import REPO
from levelang.export import blender_scene as bs
from levelang.runtime import Level, Skin, Tile

try:
    import importlib.util

    HAVE_BPY = importlib.util.find_spec("bpy") is not None
except Exception:
    HAVE_BPY = False

SAMPLE = REPO / "Samples" / "SlimeJumpLevelang" / "level.lvl"
IMPORT = os.path.join(os.path.dirname(bs.__file__), "blender_import.py")


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2.0


def pairs(flat):
    return list(zip(flat[0::2], flat[1::2]))


def toy(background=("#102030", "#304050")):
    """A 12 x 5 level: a floor, a bot to spawn, a goal, a gem, a swimming fish, a bobbing jelly and a swaying kelp."""
    lv = Level()

    def tile(name, glyph, fill=None, flags=(), anim=None, size=None, svg=None):
        t = Tile(name, glyph)
        t.fill, t.flags, t.svg = fill, set(flags), svg
        if anim:
            t.anim = anim
        if size:
            t.size = size
        return t

    ground = tile("ground", "G", "#336699", {"solid"})
    kelp_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 20"><path d="M5 20 C2 14 8 8 5 0" stroke="#22aa44" stroke-width="2" fill="none"/></svg>'
    for x in range(12):
        lv.add(ground, x, 4)
    lv.add(tile("spawn", "S", "#ffcc00", {"spawn"}), 1, 3)
    lv.add(tile("goal", "X", "#00ff00", {"goal"}), 10, 3)
    lv.add(tile("gem", "D", "#ff00ff", {"item"}), 5, 3)
    lv.add(tile("fish", "F", "#ff8800", anim={"swim": (4, 1.3)}), 3, 0)
    lv.add(tile("jelly", "J", "#aa00aa", anim={"bob": None}), 8, 1)
    lv.add(tile("kelp", "K", svg=kelp_svg, anim={"sway": None}, size=(1, 2)), 6, 2)
    lv.background = background
    return lv


class ClipTests(unittest.TestCase):
    SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]

    def test_half_plane(self):
        top = bs.clip_half_plane(self.SQUARE, 0, 0, 0, 10, 0.5)          # t = y / 10 >= .5: the lower half
        self.assertAlmostEqual(poly_area(top), 50)
        self.assertAlmostEqual(poly_area(bs.clip_half_plane(self.SQUARE, 0, 0, 0, 10, 0.0)), 100)
        self.assertEqual(bs.clip_half_plane(self.SQUARE, 0, 0, 0, 10, 2.0), [])

    def test_disc(self):
        inside = bs.clip_disc(self.SQUARE, 5, 5, 2)
        self.assertAlmostEqual(poly_area(inside), math.pi * 4, delta=0.3)
        self.assertEqual(bs.clip_disc(self.SQUARE, 50, 50, 1), [])


class StrokeTests(unittest.TestCase):
    def sprites(self, tile, size=None, veil=bs.NO_VEIL):
        return bs.Sprites(warn=lambda m: None).get(tile, size, veil)[0]

    def svg_tile(self, body, size=(2, 1)):
        t = Tile("t", "T")
        t.svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10">%s</svg>' % body
        t.size = size
        return t

    def test_viewbox_is_fitted_into_the_tiles_box(self):
        (s,) = self.sprites(self.svg_tile('<rect width="20" height="10" fill="#ff0000"/>', (4, 4)))     # a 2:1 picture in a 4 x 4 box: scaled evenly, centred
        xs, ys = s["p"][0::2], s["p"][1::2]
        self.assertEqual((min(xs), max(xs)), (0.0, 4.0))
        self.assertEqual((min(ys), max(ys)), (1.0, 3.0))

    def test_fill_and_line_are_separate_strokes_so_an_open_path_is_not_closed_by_its_line(self):
        st = self.sprites(self.svg_tile('<path d="M0 0 L10 0 L10 10" fill="#00f" stroke="#fff" stroke-width="1"/>'))
        fill = [s for s in st if s["fill"] is not None]
        line = [s for s in st if s["line"] is not None]
        self.assertEqual((len(fill), len(line)), (1, 1))
        self.assertTrue(fill[0]["closed"] and not line[0]["closed"])
        self.assertAlmostEqual(line[0]["w"], 0.1)                      # 1 unit of a 20 unit wide picture in 2 cells

    def test_opaque_gradient_is_overlapping_bands_that_reach_the_end(self):
        t = self.svg_tile('<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>'
                          '<rect width="20" height="10" fill="url(#g)"/>')
        st = self.sprites(t)
        self.assertEqual(len(st), bs.GRADIENT_STEPS)
        areas = [poly_area(pairs(s["p"])) for s in st]
        self.assertAlmostEqual(areas[0], 2.0)                           # the first band is the whole shape
        self.assertTrue(all(a > b for a, b in zip(areas, areas[1:])))
        shades = [s["fill"][0] for s in st]
        self.assertEqual(shades, sorted(shades))                        # dark to light, in drawing order
        self.assertEqual(len({s["g"] for s in st}), bs.GRADIENT_STEPS)

    def test_translucent_gradient_is_bands_that_do_not_overlap(self):
        t = self.svg_tile('<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient></defs>'
                          '<rect width="20" height="10" fill="url(#g)"/>')
        st = self.sprites(t)
        self.assertAlmostEqual(sum(poly_area(pairs(s["p"])) for s in st), 2.0, places=5)
        self.assertEqual(sorted(s["fo"] for s in st), [s["fo"] for s in sorted(st, key=lambda s: s["fo"])])
        self.assertLess(st[0]["fo"], st[-1]["fo"])

    def test_radial_gradient_bands_and_a_ring_hole(self):
        t = self.svg_tile('<defs><radialGradient id="g"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient></defs><circle cx="10" cy="5" r="5" fill="url(#g)"/>')
        st = self.sprites(t)
        self.assertGreaterEqual(len(st), bs.GRADIENT_STEPS)
        self.assertLess(st[0]["fill"][0], st[-1]["fill"][0])            # dark outside first, light in the middle last

    def test_veil_mixes_toward_the_haze_and_fades(self):
        veil = bs.Veil(("#0000ff", 0.5), 0.5)
        (s,) = self.sprites(self.svg_tile('<rect width="20" height="10" fill="#ff0000"/>'), veil=veil)
        self.assertEqual(tuple(round(c, 3) for c in s["fill"]), (0.5, 0.0, 0.5))
        self.assertAlmostEqual(s["fo"], 0.5)
        (s,) = self.sprites(self.svg_tile('<path d="M0 0L5 5" stroke="#ff0000" stroke-width="1"/>'), veil=veil)
        self.assertAlmostEqual(s["lo"], 0.5)

    def test_fill_tile_and_placeholder(self):
        t = Tile("f", "F")
        t.fill = "#00ff00"
        (s,) = self.sprites(t, (2, 3))
        self.assertEqual(s["fill"], (0.0, 1.0, 0.0))
        self.assertAlmostEqual(poly_area(pairs(s["p"])), 6.0)
        e = Tile("e", "🐠")                                              # nothing to draw it with: a placeholder, and one warning
        msgs = []
        st = bs.Sprites(warn=msgs.append)
        st.get(e)
        st.get(e, (2, 2))
        self.assertEqual(len(msgs), 1)

    def test_stamp_moves_mirrors_and_renumbers(self):
        t = self.svg_tile('<rect width="10" height="10" fill="#f00"/>')
        st, w, h = bs.Sprites(warn=lambda m: None).get(t)
        g = bs.Groups()
        a = bs.stamp(st, 3, 4, w, False, g)
        b = bs.stamp(st, 3, 4, w, True, g)
        self.assertEqual(min(a[0]["p"][0::2]), 3.0)
        self.assertEqual(min(b[0]["p"][0::2]), 4.0)                      # the picture fills the left half of its 2 wide box; mirrored it fills the right half
        self.assertNotEqual(a[0]["g"], b[0]["g"])
        self.assertEqual(st[0]["g"], 1)                                  # the cached sprite is not touched


class SceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.level = toy()
        cls.scene = bs.build(cls.level, warn=lambda m: None)

    def test_it_is_plain_json(self):
        s = self.scene
        again = json.loads(json.dumps(s))
        self.assertEqual(again["cells"], {"x0": 0, "y0": 0, "cols": 12, "rows": 5})
        self.assertEqual(s["version"], bs.VERSION)

    def test_timeline_is_the_previews(self):
        s = self.scene
        bot, cam = s["bot"], s["camera"]
        self.assertEqual(bot["keys"][0][1:3], [1.5, 3.5])                 # the spawn cell's centre
        self.assertAlmostEqual(bot["keys"][-1][1], 10.5, delta=0.05)      # the goal cell's centre
        self.assertEqual(len(bot["keys"]), len(cam))
        self.assertEqual(len(cam), int(s["duration"] * s["fps"]) + 1)
        vw, vh = s["view"]
        for t, cx, cy in cam:
            self.assertGreaterEqual(cx, vw / 2.0 - 1e-6)
            self.assertLessEqual(cx, 12 - vw / 2.0 + 1e-6)
            self.assertGreaterEqual(cy, vh / 2.0 - 1e-6)
        self.assertTrue(any(k[3] for k in bot["keys"]) is False)          # it only walks right here

    def test_the_gem_vanishes_when_the_bot_reaches_it(self):
        (gem,) = [o for o in self.scene["objects"] if o["name"].startswith("gem")]
        xs = [(t, x) for t, x, y, f in self.scene["bot"]["keys"]]
        reach = next(t for t, x in xs if x >= 5.5 - 1e-6)
        self.assertAlmostEqual(gem["hide_at"], reach, delta=0.1)

    def test_animations(self):
        by = {o["name"].split("_")[0]: o for o in self.scene["objects"]}
        self.assertEqual(by["fish"]["anim"]["swim"]["n"], 4)
        self.assertAlmostEqual(by["fish"]["anim"]["swim"]["period"] / 2.4, round(by["fish"]["anim"]["swim"]["period"] / 2.4), places=6)   # a whole number of sway periods: it loops
        self.assertEqual(by["jelly"]["anim"]["bob"]["amp"], 0.22)
        self.assertIn("sway", by["kelp"]["anim"])
        sp = self.scene["sprites"][by["kelp"]["sprite"]]
        self.assertEqual(sp["sway"]["poses"], bs.SWAY_POSES)
        self.assertEqual(by["gem"]["anim"]["bob"]["period"], 1.2)

    def test_draw_order_is_unique_and_the_bot_is_in_front_of_the_world(self):
        s = self.scene
        depths = [o["depth"] for o in s["objects"]] + [o["depth"] for o in s["statics"]] + [s["bot"]["depth"]]
        self.assertEqual(len(depths), len(set(depths)))
        world = [o["depth"] for o in s["statics"]]
        self.assertTrue(s["bot"]["depth"] > max(world))

    def test_sprite_boxes(self):
        for key, sp in self.scene["sprites"].items():
            for st in sp["strokes"]:
                for x, y in pairs(st["p"]):
                    self.assertTrue(-0.2 <= x <= sp["w"] + 0.2 and -0.2 <= y <= sp["h"] + 0.2, (key, x, y))

    def test_no_bot_means_a_still_camera(self):
        s = bs.build(toy(), play=False, warn=lambda m: None)
        self.assertIsNone(s["bot"])
        self.assertGreaterEqual(s["duration"], 4.8)
        self.assertEqual(len({(c[1], c[2]) for c in s["camera"]}), 1)

    def test_empty_level(self):
        with self.assertRaises(ValueError):
            bs.build(Level())

    def test_layers_sit_far_to_near_with_the_front_ones_after_the_bot(self):
        lv = toy()
        far, near, front = Tile("far", "a"), Tile("near", "b"), Tile("front", "c")
        for t in (far, near, front):
            t.fill = "#ffffff"
        from levelang.runtime import Layer, Placed

        for name, par, over, tile in (("near", 0.6, False, near), ("front", 1.4, True, front), ("far", 0.1, False, far)):
            L = Layer(name, par, over=over, alpha=0.5, haze=("#000000", 0.5))
            L.placements.append(Placed(tile, 2.5, 1.5, 0))
            lv.layers.append(L)
        s = bs.build(lv, warn=lambda m: None)
        d = {o["name"]: o["depth"] for o in s["statics"]}
        self.assertLess(d["layer_far"], d["layer_near"])
        self.assertLess(d["layer_near"], d["world_front"] if "world_front" in d else s["bot"]["depth"])
        self.assertGreater(d["layer_front"], s["bot"]["depth"])
        self.assertEqual([l["name"] for l in s["layers"]], ["far", "near", "front"])
        self.assertEqual([o["parent"] for o in s["statics"] if o["name"].startswith("layer_")], ["layer:far", "layer:near", "layer:front"])
        st = [l for o in s["statics"] if o["name"] == "layer_far" for l in o["layers"]][0]["strokes"][0]
        self.assertAlmostEqual(st["fo"], 0.5)                             # the layer's alpha
        self.assertEqual(tuple(round(c, 2) for c in st["fill"]), (0.5, 0.5, 0.5))   # mixed halfway to the black haze

    def test_skin_art_is_masked_by_its_shape(self):
        lv = toy()
        lv.skins.append(Skin(selectors=("solid",), corner=0.3, smooth=2, outline="#000000"))
        s = bs.build(lv, warn=lambda m: None)
        (sk,) = [o for o in s["statics"] if o["name"] == "skin_0"]
        names = {l["name"]: l for l in sk["layers"]}
        self.assertEqual(list(names), ["shape", "art", "outline"])
        self.assertEqual(names["art"]["mask"], "shape")
        self.assertTrue(names["shape"]["strokes"])
        self.assertTrue(all(st["g"] == names["shape"]["strokes"][0]["g"] for st in names["shape"]["strokes"]))   # one fill group: an inner loop is a hole
        self.assertFalse(any(o["name"].startswith("ground") for o in s["objects"]))


@unittest.skipUnless(SAMPLE.exists(), "needs Samples/SlimeJumpLevelang")
class SampleSceneTests(unittest.TestCase):
    def test_the_sample_builds_with_no_warnings(self):
        from levelang import load_file

        lv, _ = load_file(str(SAMPLE))
        msgs = []
        s = bs.build(lv, warn=msgs.append)
        self.assertEqual(msgs, [])
        self.assertGreater(len(s["objects"]), 50)
        self.assertEqual([l["name"] for l in s["layers"]], sorted([l["name"] for l in s["layers"]], key=lambda n: next(x["parallax"][0] for x in s["layers"] if x["name"] == n)))
        self.assertTrue(any(o["name"].startswith("skin_") for o in s["statics"]))
        self.assertTrue(s["bot"] and s["bot"]["keys"][-1][1] > s["bot"]["keys"][0][1] + 20)


class RunnerTests(unittest.TestCase):
    def test_no_blender_is_a_clear_error(self):
        from levelang.export import blender as bl

        with self.assertRaises(bl.BlenderError):
            bl.find_blender("/definitely/not/blender")
        old = (bl.find_blender, bl.have_bpy)
        bl.find_blender, bl.have_bpy = (lambda e=None: None), (lambda: False)
        try:
            with self.assertRaises(bl.BlenderError) as cm:
                bl.export_blender(toy(), "/tmp/never.blend")
            self.assertIn("Blender not found", str(cm.exception))
        finally:
            bl.find_blender, bl.have_bpy = old

    def test_default_output_is_in_tmp(self):
        from levelang.export import blender as bl

        if os.name == "posix":
            self.assertEqual(bl.DEFAULT_OUT, "/tmp/levelang-preview.blend")

    def test_a_blender_that_fails_is_reported_with_its_output(self):
        from levelang.export import blender as bl

        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "blender")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'Blender 4.3.0'; exit 0; fi\necho 'boom: bad thing' >&2\nexit 1\n")
            os.chmod(fake, 0o755)
            with self.assertRaises(bl.BlenderError) as cm:
                bl.export_blender(toy(), os.path.join(d, "x.blend"), blender=fake)
            self.assertIn("boom: bad thing", str(cm.exception))

    def test_an_old_blender_is_refused(self):
        from levelang.export import blender as bl

        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "blender")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\necho 'Blender 3.6.1'\n")
            os.chmod(fake, 0o755)
            with self.assertRaises(bl.BlenderError) as cm:
                bl.export_blender(toy(), os.path.join(d, "x.blend"), blender=fake)
            self.assertIn("too old", str(cm.exception))


@unittest.skipUnless(HAVE_BPY, "needs the bpy module: pip install bpy")
class BlendTests(unittest.TestCase):
    """Build the toy level into a .blend (in a child process, which is what the real thing does too) and look at what is in it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.scene = bs.build(toy(), warn=lambda m: None)
        cls.scene_path = os.path.join(cls.tmp.name, "scene.json")
        with open(cls.scene_path, "w") as f:
            json.dump(cls.scene, f)
        cls.blend = os.path.join(cls.tmp.name, "toy.blend")
        cls.run_import(cls.scene_path, cls.blend, ("--res", "120x50", "--video", "png"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def run_import(scene_path, out, extra=()):
        r = subprocess.run([sys.executable, IMPORT, "--", scene_path, out, *extra], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            raise AssertionError(r.stdout[-1500:] + r.stderr[-1500:])

    def open(self):
        import bpy

        bpy.ops.wm.open_mainfile(filepath=self.blend)
        return bpy.context.scene

    def at(self, sc, frame):
        import bpy

        sc.frame_set(frame)
        bpy.context.view_layer.update()

    def test_what_is_in_the_file(self):
        import bpy

        sc = self.open()
        names = {o.name for o in bpy.data.objects}
        for n in ("levelang_camera", "levelang_backdrop", "levelang_bot", "world_front"):
            self.assertIn(n, names)
        self.assertEqual(sc.camera.name, "levelang_camera")
        self.assertEqual(sc.camera.data.type, "ORTHO")
        self.assertEqual(sc.render.fps, 24)
        self.assertEqual((sc.render.resolution_x, sc.render.resolution_y), (120, 50))
        self.assertEqual(sc.frame_end, int(round(self.scene["duration"] * 24)) + 1)
        self.assertEqual(sc.view_settings.view_transform, "Standard")
        kinds = {o.type for o in bpy.data.objects}
        self.assertIn("GREASEPENCIL", kinds)

    def test_swim_bob_and_gem(self):
        import bpy

        sc = self.open()
        by = {o["name"].split("_")[0]: o for o in self.scene["objects"]}
        fish, jelly, gem = by["fish"], by["jelly"], by["gem"]
        for f in (1, 13, 30, 60, 79):
            self.at(sc, f)
            t = (f - 1) / 24.0
            s = fish["anim"]["swim"]
            w = (t / s["period"] + s["phase"]) % 1.0
            self.assertAlmostEqual(bpy.data.objects[fish["name"]].matrix_world.translation.x, fish["x"] + fish["w"] / 2 + (1 - abs(2 * w - 1)) * s["n"], places=4)
            self.assertEqual(bpy.data.objects[fish["name"]].matrix_world.to_scale().x < 0, w > 0.5)
            b = jelly["anim"]["bob"]
            ez = -(jelly["y"] + jelly["h"] / 2) - b["amp"] * math.sin(2 * math.pi * ((t / b["period"] + b["phase"]) % 1.0))
            self.assertAlmostEqual(bpy.data.objects[jelly["name"]].matrix_world.translation.z, ez, delta=0.02)    # keyed eight times a period and eased
            self.assertEqual(bpy.data.objects[gem["name"]].hide_render, t >= gem["hide_at"] - 1e-6)

    def test_the_bot_and_the_camera_follow_their_keys(self):
        import bpy

        sc = self.open()
        bot, cam = self.scene["bot"], self.scene["camera"]
        for f in (1, 20, 41, 80):
            self.at(sc, f)
            t, x, y, left = bot["keys"][f - 1]
            loc = bpy.data.objects["levelang_bot"].matrix_world.translation
            self.assertAlmostEqual(loc.x, x, places=4)
            self.assertAlmostEqual(loc.z, -y, places=4)
            c = bpy.data.objects["levelang_camera"].matrix_world.translation
            self.assertAlmostEqual(c.x, cam[f - 1][1], places=4)
            self.assertAlmostEqual(c.z, -cam[f - 1][2], places=4)
        self.assertAlmostEqual(bpy.data.objects["levelang_bot"].scale.x, self.scene["bot"]["size"], places=5)

    def test_kelp_sways_in_a_loop_with_its_own_phase(self):
        import bpy

        sc = self.open()
        (kelp,) = [o for o in self.scene["objects"] if o["name"].startswith("kelp")]
        ob = bpy.data.objects[kelp["name"]]
        n = self.scene["sprites"][kelp["sprite"]]["sway"]["poses"]
        self.assertEqual(len(ob.data.layers[0].frames), n)
        xs = []
        for f in (1, 4, 9, 20, 33, 50):
            self.at(sc, f)
            e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            xs.append(round(max(((p.position[0], p.position[2]) for p in e.data.layers[0].current_frame().drawing.strokes[0].points), key=lambda q: q[1])[0], 3))
        self.assertGreater(len(set(xs)), 3)                                # it moves
        self.assertTrue(all(abs(x) < 0.5 for x in xs))                    # and stays near its foot

    def test_parallax_rig_follows_the_camera_by_a_driver(self):
        import bpy

        lv = toy()
        t = Tile("deep", "d")
        t.fill = "#ffffff"
        from levelang.runtime import Layer, Placed

        L = Layer("deep", 0.25)
        L.placements.append(Placed(t, 1.0, 1.0, 0))
        lv.layers.append(L)
        scene = bs.build(lv, warn=lambda m: None)
        sp, out = os.path.join(self.tmp.name, "p.json"), os.path.join(self.tmp.name, "p.blend")
        with open(sp, "w") as f:
            json.dump(scene, f)
        self.run_import(sp, out, ("--video", "png"))
        bpy.ops.wm.open_mainfile(filepath=out)
        sc = bpy.context.scene
        rig = bpy.data.objects["parallax/deep"]
        cam = bpy.data.objects["levelang_camera"]
        hw, hh = scene["view"][0] / 2.0, scene["view"][1] / 2.0
        for x, z in ((6.0, -2.5), (9.0, -4.0)):
            cam.location.x, cam.location.z = x, z
            bpy.context.view_layer.update()
            self.assertAlmostEqual(rig.matrix_world.translation.x, (x - hw) * 0.75, places=4)
            self.assertAlmostEqual(rig.matrix_world.translation.z, (z + hh) * 0.75, places=4)
        self.assertEqual(sc.camera.name, "levelang_camera")

    def render(self, blend, frame, size=(120, 50)):
        import bpy
        from PIL import Image

        bpy.ops.wm.open_mainfile(filepath=blend)
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y = size
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = os.path.join(self.tmp.name, "frame.png")
        sc.eevee.taa_render_samples = 4
        sc.frame_set(frame)
        bpy.ops.render.render(write_still=True)
        return Image.open(sc.render.filepath).convert("RGB")

    def test_colours_come_out_as_written_and_the_sky_is_a_gradient(self):
        """A render of the toy level: the floor is the SVG's colour exactly (not tone-mapped), the sky runs from the top colour to the bottom one."""
        img = self.render(self.blend, 1)
        w, h = img.size                                                      # 12 x 5 cells on 120 x 50 pixels: 10 pixels a cell
        floor = img.getpixel((60, h - 5))
        self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(floor, (0x33, 0x66, 0x99))), floor)
        top, low = img.getpixel((5, 2)), img.getpixel((5, 37))
        self.assertTrue(all(abs(a - b) <= 6 for a, b in zip(top, (0x10, 0x20, 0x30))), top)
        self.assertGreater(low[2], top[2] + 10)                              # lighter towards the bottom colour
        bot = img.getpixel((15, 35))                                         # the bot starts on the floor at cell 1: a yellow box
        self.assertTrue(bot[0] > 200 and bot[1] > 150 and bot[2] < 60, bot)

    def test_a_hole_in_a_shape_and_art_masked_by_a_skin(self):
        """A ring (two loops in one fill group) shows the sky through its middle; the skin's art does not paint outside the skin's shape."""
        lv = Level()
        ring = Tile("ring", "R")
        ring.svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30"><path d="M0 0H30V30H0Z M10 10V20H20V10Z" fill="#ff0000" fill-rule="evenodd"/></svg>'
        ring.size = (3, 3)
        ring.anim = {}
        rock = Tile("rock", "r")
        rock.fill, rock.flags = "#00aa00", {"solid"}
        rock.svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect x="-50" y="-50" width="110" height="110" fill="#00aa00"/></svg>'   # art that overflows its cell
        lv.add(ring, 0, 0)
        lv.add(rock, 5, 2)
        lv.add(rock, 6, 2)
        lv.skins.append(Skin(selectors=("solid",), corner=0.5, smooth=3, outline=None))
        lv.background = ("#0000ff", "#0000ff")
        lv.meta = {"width": 8, "height": 3}
        scene = bs.build(lv, play=False, view=(8, 3), warn=lambda m: None)
        sp, out = os.path.join(self.tmp.name, "h.json"), os.path.join(self.tmp.name, "h.blend")
        with open(sp, "w") as f:
            json.dump(scene, f)
        self.run_import(sp, out, ("--video", "png"))
        img = self.render(out, 1, (160, 60))                                 # 8 x 3 cells (the level's height is 3) -> 20 pixels a cell
        px = lambda cx, cy: img.getpixel((int(cx * 20), int(cy * 20)))
        ring_edge, ring_mid = px(0.5, 1.5), px(1.5, 1.5)
        self.assertTrue(ring_edge[0] > 200 and ring_edge[2] < 60, ring_edge)  # the red ring
        self.assertTrue(ring_mid[2] > 200 and ring_mid[0] < 60, ring_mid)     # the sky shows through the hole
        inside = px(5.5, 2.5)
        self.assertTrue(inside[1] > 120 and inside[0] < 60, inside)           # the rock, in the skin
        outside = px(5.5, 0.5)
        self.assertTrue(outside[2] > 200 and outside[1] < 60, outside)         # the overflowing art is cut off at the skin's shape


if __name__ == "__main__":
    unittest.main()
