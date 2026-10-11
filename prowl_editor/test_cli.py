"""Tests of prowl.py's command line: plugins, the Blender import, and opening the editor on imported data (no display needed; the Blender tests use a fake
`blender` program, and one test uses a real Blender when there is one):   python3 -m unittest prowl_editor.test_cli     (or: python3 prowl.py --selftest)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

from . import blender_import, plugins
from .blender_import import BlenderError, Options
from .model import Project, ProjectError
from .test_core import make_png, rgba_rows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROWL = os.path.join(ROOT, "prowl.py")
LINUX = sys.platform.startswith("linux")
POSIX = os.name == "posix"
try:
    import PyQt5  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class TempDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(text))
        return path


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# plugins

class PluginLoading(TempDir):
    def setUp(self):
        super().setUp()
        before = set(sys.modules), list(sys.path)
        self.addCleanup(lambda: [sys.modules.pop(m) for m in set(sys.modules) - before[0] if m.startswith(("prowl_plugin_", "helper_for_"))])
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), before[1]))
        self.prowl = plugins.Prowl(ROOT)

    def load(self, *paths):
        return plugins.load_plugins(list(paths), self.prowl)

    def test_register_gets_the_interface_and_what_it_adds_is_kept(self):
        path = self.write("tool.py", """
            def register(prowl):
                prowl.add_argument("--stars", type=int, default=3, help="how many")
                prowl.add_importer(".STAR", lambda project, path, args: "imported " + path)
                prowl.on_project(lambda project, args: project.touch())
                prowl.on_gui(lambda studio, main, windows, args: None)
        """)
        self.load(path)
        self.assertEqual(self.prowl.plugins, ["tool"])
        import argparse
        ap = argparse.ArgumentParser()
        self.prowl.apply_arguments(ap)
        self.assertEqual(ap.parse_args(["--stars", "5"]).stars, 5)
        self.assertEqual(self.prowl.extensions(), [".star"])                                  # extensions are case-insensitive
        self.assertEqual(self.prowl.run_importer("A/b.Star", Project("p"), None), "imported A/b.Star")
        self.assertIsNone(self.prowl.importer_for("b.blend"))
        p = Project("p")
        revision = p.revision
        self.prowl.run_project_hooks(p, None)
        self.assertGreater(p.revision, revision)

    def test_a_plugin_without_register_is_just_run(self):
        path = self.write("plain.py", "import builtins\nbuiltins._prowl_plain_ran = True\n")
        self.addCleanup(lambda: delattr(__import__("builtins"), "_prowl_plain_ran"))
        self.load(path)
        self.assertTrue(__import__("builtins")._prowl_plain_ran)

    def test_a_folder_loads_its_py_files_in_order_and_skips_underscored_ones(self):
        for name in ("b.py", "a.py", "_private.py", "notes.txt"):
            self.write("plugs/" + name, "")
        self.load(os.path.join(self.dir, "plugs"))
        self.assertEqual(self.prowl.plugins, ["a", "b"])

    def test_a_plugin_can_import_the_modules_next_to_it(self):
        self.write("pk/helper_for_plugin.py", "VALUE = 41\n")
        path = self.write("pk/uses_helper.py", "import helper_for_plugin\ndef register(prowl):\n    prowl.on_project(lambda p, a: p.touch())\n    prowl.value = helper_for_plugin.VALUE + 1\n")
        self.load(path)
        self.assertEqual(self.prowl.value, 42)

    def test_bad_plugin_paths_are_refused_with_a_message(self):
        os.makedirs(os.path.join(self.dir, "empty"))
        self.write("notes.txt", "")
        for given, words in (("nothere.py", "does not exist"), ("notes.txt", "not a .py file"), ("empty", "no .py files")):
            with self.assertRaises(plugins.PluginError) as cm:
                self.load(os.path.join(self.dir, given))
            self.assertIn(words, str(cm.exception))

    def test_a_plugin_that_fails_to_load_is_named_and_flagged_as_a_bug(self):
        for name, body in (("syntax.py", "def register(prowl:\n"), ("raises.py", "def register(prowl):\n    raise KeyError('oops')\n")):
            with self.assertRaises(plugins.PluginError) as cm:
                self.load(self.write(name, body))
            self.assertIn(name, str(cm.exception))
            self.assertTrue(cm.exception.unexpected)
            self.assertIsNotNone(cm.exception.__cause__)

    def test_a_projecterror_from_a_plugin_is_a_plain_message_not_a_bug(self):
        path = self.write("polite.py", """
            from prowl_editor.model import ProjectError
            def register(prowl):
                def hook(project, args):
                    raise ProjectError("the file is not a level")
                prowl.on_project(hook)
        """)
        self.load(path)
        with self.assertRaises(plugins.PluginError) as cm:
            self.prowl.run_project_hooks(Project("p"), None)
        self.assertEqual(str(cm.exception), "plugin polite: the file is not a level")
        self.assertFalse(cm.exception.unexpected)

    def test_a_hook_that_crashes_is_blamed_on_its_plugin(self):
        self.load(self.write("crashy.py", "def register(prowl):\n    prowl.on_gui(lambda *a: 1 / 0)\n"))
        with self.assertRaises(plugins.PluginError) as cm:
            self.prowl.run_gui_hooks(None, None, {}, None)
        self.assertIn("plugin crashy", str(cm.exception))
        self.assertIn("ZeroDivisionError", str(cm.exception))
        self.assertTrue(cm.exception.unexpected)

    def test_importers_cannot_take_json_or_py_or_an_extension_that_is_taken(self):
        self.prowl.add_importer(".dat", print)
        for ext in (".json", ".py", ".dat"):
            with self.assertRaises(plugins.PluginError):
                self.prowl.add_importer(ext, print)

    def test_an_option_that_clashes_with_another_is_reported(self):
        self.load(self.write("clash.py", "def register(prowl):\n    prowl.add_argument('--output')\n"))
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--output")
        with self.assertRaises(plugins.PluginError) as cm:
            self.prowl.apply_arguments(ap)
        self.assertIn("plugin clash", str(cm.exception))
        self.assertIn("--output", str(cm.exception))

    def test_the_same_file_name_twice_is_refused(self):
        self.load(self.write("one/same.py", ""))
        with self.assertRaises(plugins.PluginError):
            self.load(self.write("two/same.py", ""))

    def test_builtin_errors_are_not_blamed_on_a_plugin(self):
        def fails(project, path, args):
            raise ProjectError("Blender was not found")
        self.prowl.add_importer(".thing", fails)
        with self.assertRaises(ProjectError) as cm:
            self.prowl.run_importer("a.thing", Project("p"), None)
        self.assertEqual(str(cm.exception), "Blender was not found")

    def test_import_result_summarizes_itself(self):
        r = plugins.ImportResult(sprites=[1, 2], levels=[3], notes=["n"])
        self.assertEqual((r.summary(), r.notes), ("2 sprites, 1 level", ["n"]))


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Blender: PNGs to sprites

def png_file(path, w, h, pixel):
    rows = [b"".join(bytes(pixel(x, y)) for x in range(w)) for y in range(h)]
    with open(path, "wb") as f:
        f.write(make_png(w, h, rows))


CLEAR = (0, 0, 0, 0)


class BlenderConversion(TempDir):
    def render_folder(self, sprites, notes=()):
        """A folder like the one the Blender script writes: sprites = [(name, w, h, pixel function)]."""
        entries = []
        for i, (name, w, h, pixel) in enumerate(sprites):
            png_file(os.path.join(self.dir, "sprite_%d.png" % i), w, h, pixel)
            entries.append({"name": name, "file": "sprite_%d.png" % i, "width": w, "height": h, "scale": 16.0})
        return {"sprites": entries, "notes": list(notes)}

    def add(self, project, manifest, colors=32):
        report = blender_import.BlenderReport()
        blender_import.add_rendered(project, self.dir, manifest, colors, 1.0, report)
        return project, report

    def test_crop_to_alpha_keeps_the_opaque_rectangle(self):
        rgba = b"".join(bytes((9, 9, 9, 255) if (x, y) in ((2, 1), (3, 3)) else CLEAR) for y in range(5) for x in range(6))
        w, h, out = blender_import.crop_to_alpha(6, 5, rgba)
        self.assertEqual((w, h), (2, 3))
        self.assertEqual([out[i + 3] for i in range(0, len(out), 4)], [255, 0, 0, 0, 0, 255])
        self.assertIsNone(blender_import.crop_to_alpha(2, 2, bytes(16)))

    def test_a_render_becomes_a_cropped_sprite_with_its_colours_in_the_palette(self):
        manifest = self.render_folder([("Hero", 8, 8, lambda x, y: (200, 30, 30, 255) if 2 <= x < 6 and 1 <= y < 7 else CLEAR),
                                       ("Coin", 6, 6, lambda x, y: (30, 30, 200, 255) if 2 <= x < 4 and 2 <= y < 4 else CLEAR)], notes=["'Lights' has nothing to render (skipped)"])
        p, report = self.add(Project("p"), manifest)
        self.assertEqual([(s.name, s.width, s.height) for s in p.sprites], [("Hero", 4, 6), ("Coin", 2, 2)])
        self.assertEqual(report.sprites, p.sprites)
        self.assertEqual(report.notes, ["'Lights' has nothing to render (skipped)"])
        coin = p.sprite("Coin")
        self.assertTrue(all(i != 0 for i in coin.frames[0]))
        self.assertEqual(p.palette.entries[coin.frames[0][0]].rgb, (30, 30, 200))
        self.assertTrue(p.palette.entries[coin.frames[0][0]].name.startswith("blender #"))
        self.assertTrue(p.dirty)

    def test_a_transparent_render_is_skipped_with_a_note(self):
        manifest = self.render_folder([("Ghost", 4, 4, lambda x, y: CLEAR), ("Box", 3, 3, lambda x, y: (1, 2, 3, 255))])
        p, report = self.add(Project("p"), manifest)
        self.assertEqual([s.name for s in p.sprites], ["Box"])
        self.assertTrue(any("'Ghost' rendered nothing visible" in n for n in report.notes))

    def test_colours_are_folded_to_the_limit_across_all_sprites(self):
        manifest = self.render_folder([("A", 8, 8, lambda x, y: (x * 30, y * 30, 100, 255)), ("B", 8, 8, lambda x, y: (100, x * 30, y * 30, 255))])
        p, report = self.add(Project("p"), manifest, colors=4)
        used = {i for s in p.sprites for i in s.frames[0]}
        self.assertEqual(len(used), 4)
        self.assertTrue(any("folded into 4" in n for n in report.notes))
        _, again = self.add(Project("q"), manifest, colors=0)                    # 0: no limit
        self.assertFalse(any("folded" in n for n in again.notes))

    def test_a_render_bigger_than_a_sprite_can_be_is_scaled_down_with_a_note(self):
        manifest = self.render_folder([("Wall", 300, 20, lambda x, y: (5, 5, 5, 255))])
        p, report = self.add(Project("p"), manifest)
        self.assertEqual((p.sprites[0].width, p.sprites[0].height), (256, 17))
        self.assertTrue(any("scaled to 256x17" in n for n in report.notes))

    def test_importing_twice_keeps_both_with_unique_names(self):
        manifest = self.render_folder([("Rock", 3, 3, lambda x, y: (9, 9, 9, 255))])
        p, _ = self.add(Project("p"), manifest)
        self.add(p, manifest)
        self.assertEqual([s.name for s in p.sprites], ["Rock", "Rock 2"])

    def test_reduce_colors_leaves_few_colours_alone(self):
        p = blender_import.ui.Pending("x", "x")
        p.frames.append((2, 1, bytes((1, 2, 3, 255, 4, 5, 6, 255))))
        self.assertEqual(blender_import.reduce_colors([p], 8), 2)
        self.assertEqual(p.frames[0][2], bytes((1, 2, 3, 255, 4, 5, 6, 255)))


class BlenderFrames(BlenderConversion):
    """Animation: a sprite with several renders is a sprite with several frames."""
    def frames_folder(self, name, pixels, fps=12.0, solid=False):
        """pixels: one function per frame (x, y) -> RGBA, each frame 8x8."""
        files = []
        for k, pixel in enumerate(pixels):
            files.append("%s_%d.png" % (name, k))
            png_file(os.path.join(self.dir, files[-1]), 8, 8, pixel)
        return {"name": name, "file": files[0], "files": files, "width": 8, "height": 8, "scale": 8.0, "solid": solid, "fps": fps}

    def add_items(self, *items, colors=32):
        project, report = Project("p"), blender_import.BlenderReport()
        blender_import.add_rendered(project, self.dir, {"sprites": list(items), "notes": []}, colors, 1.0, report)
        return project, report

    def block(self, x0, y0, x1, y1, rgb=(200, 40, 40, 255)):
        return lambda x, y: rgb if x0 <= x <= x1 and y0 <= y <= y1 else CLEAR

    def test_frames_share_one_crop_so_the_animation_stays_aligned(self):
        item = self.frames_folder("walk", [self.block(1, 2, 2, 3), self.block(4, 2, 5, 3)])
        p, _ = self.add_items(item)
        s = p.sprite("walk")
        self.assertEqual((s.width, s.height, len(s.frames)), (5, 2, 2))             # columns 1..5: both blocks fit, each where it was
        index = lambda frame: [i for i in range(5) if s.get(frame, i, 0)]
        self.assertEqual((index(0), index(1)), ([0, 1], [3, 4]))
        self.assertEqual(s.fps, 12.0)

    def test_a_sprite_that_never_moves_keeps_one_frame(self):
        item = self.frames_folder("rock", [self.block(2, 2, 4, 4)] * 3)
        p, _ = self.add_items(item)
        self.assertEqual(len(p.sprite("rock").frames), 1)

    def test_frames_of_different_sizes_are_skipped_with_a_note(self):
        item = self.frames_folder("bad", [self.block(1, 1, 2, 2)] * 2)
        png_file(os.path.join(self.dir, item["files"][1]), 6, 6, lambda x, y: (1, 2, 3, 255))
        p, report = self.add_items(item)
        self.assertEqual(p.sprites, [])
        self.assertTrue(any("not all the same size" in n for n in report.notes))

    def test_a_frame_with_nothing_in_it_is_still_a_frame_of_the_animation(self):
        item = self.frames_folder("blink", [self.block(1, 1, 3, 3), lambda x, y: CLEAR, self.block(1, 1, 3, 3)])
        p, _ = self.add_items(item)
        s = p.sprite("blink")
        self.assertEqual(len(s.frames), 3)
        self.assertFalse(any(s.frames[1]))

    def test_the_same_colours_are_shared_by_all_frames(self):
        item = self.frames_folder("pulse", [self.block(1, 1, 3, 3, (200, 0, 0, 255)), self.block(1, 1, 3, 3, (0, 0, 200, 255))])
        p, _ = self.add_items(item)
        a, b = p.sprite("pulse").frames
        self.assertEqual({p.palette.entries[i].rgb for i in set(a) - {0}} | {p.palette.entries[i].rgb for i in set(b) - {0}}, {(200, 0, 0), (0, 0, 200)})


class BlenderLevels(BlenderConversion):
    """Levels: the manifest's tiles (the collection instances of a Level_* collection, in Blender units) snapped to a grid of cells."""
    def library(self):
        return self.render_folder([("grass", 4, 4, lambda x, y: (20, 160, 20, 255)), ("coin", 4, 4, lambda x, y: (250, 200, 20, 255))])

    def level(self, tiles, cell=1.0, name="Level_1"):
        manifest = self.library()
        manifest["sprites"][0]["solid"] = True
        manifest["levels"] = [{"name": name, "tiles": [{"sprite": s, "x": x, "y": y} for s, x, y in tiles]}]
        project, report = Project("p"), blender_import.BlenderReport()
        blender_import.add_rendered(project, self.dir, manifest, 32, cell, report)
        return project, report

    def rows(self, project, level):
        return [[level.get(x, y) for x in range(level.width)] for y in range(level.height)]

    def test_tiles_are_put_on_the_grid_with_up_at_the_top(self):
        p, report = self.level([("grass", 0, 0), ("grass", 1, 0), ("grass", 2, 0), ("coin", 1, 1), ("coin", 2, 2)])
        level = p.level("Level_1")
        self.assertEqual((level.width, level.height), (3, 3))
        grass = next(g for g, t in p.tiles.items() if t.name == "grass")
        coin = next(g for g, t in p.tiles.items() if t.name == "coin")
        self.assertEqual(self.rows(p, level), [["", "", coin], ["", coin, ""], [grass, grass, grass]])
        self.assertEqual(report.levels, [level])

    def test_a_solid_collection_makes_a_solid_tile_and_the_tile_shows_its_sprite(self):
        p, _ = self.level([("grass", 0, 0), ("coin", 1, 0)])
        tiles = {t.name: t for t in p.tiles.values()}
        self.assertTrue(tiles["grass"].solid)
        self.assertFalse(tiles["coin"].solid)
        self.assertEqual(p.sprite_for_tile(tiles["coin"]), p.sprite("coin"))

    def test_the_cell_size_sets_the_grid_and_negative_places_work(self):
        p, _ = self.level([("grass", -2, 0), ("grass", 0, 0), ("coin", 2, -2)], cell=2.0)
        level = p.level("Level_1")
        self.assertEqual((level.width, level.height), (3, 2))
        self.assertEqual(sum(1 for c in level.cells if c), 3)

    def test_tiles_off_the_grid_or_on_top_of_each_other_are_reported(self):
        p, report = self.level([("grass", 0, 0), ("coin", 1.4, 0), ("grass", 3, 0), ("coin", 3, 0.1)])
        self.assertTrue(any("1 tile was not on the grid" in n for n in report.notes))
        self.assertTrue(any("1 tile was hidden behind another tile" in n for n in report.notes))

    def test_a_tile_of_a_collection_that_made_no_sprite_is_skipped_with_a_note(self):
        p, report = self.level([("grass", 0, 0), ("ghost", 1, 0)])
        self.assertTrue(any("'ghost' made no sprite" in n for n in report.notes))
        self.assertEqual(p.level("Level_1").width, 1)

    def test_a_level_too_big_or_with_a_bad_cell_is_refused_cleanly(self):
        p, report = self.level([("grass", 0, 0), ("grass", 600, 0)])
        self.assertEqual(p.levels, [])
        self.assertTrue(any("bigger than a level can be" in n for n in report.notes))
        for cell in (0, -1, float("nan")):
            with self.assertRaises(BlenderError):
                self.level([("grass", 0, 0)], cell=cell)

    def test_a_second_import_points_its_level_at_the_new_sprite_names(self):
        manifest = self.library()
        manifest["levels"] = [{"name": "Level_1", "tiles": [{"sprite": "grass", "x": 0, "y": 0}]}]
        project = Project("p")
        blender_import.add_rendered(project, self.dir, manifest, 32, 1.0, blender_import.BlenderReport())
        report = blender_import.BlenderReport()
        blender_import.add_rendered(project, self.dir, manifest, 32, 1.0, report)
        self.assertEqual([s.name for s in project.sprites], ["grass", "coin", "grass 2", "coin 2"])
        self.assertEqual([l.name for l in project.levels], ["Level_1", "Level_1 2"])
        second = project.level("Level_1 2")
        self.assertEqual(project.tiles[second.get(0, 0)].sprite, "grass 2")
        self.assertIn("1 level", report.summary())


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Blender: running it (a fake program stands in for it)

FAKE_BLENDER = '''#!{python}
import json, os, struct, sys, zlib
argv = sys.argv[1:]
with open(os.environ["FAKE_BLENDER_LOG"], "w") as f:
    json.dump(argv, f)
mode = os.environ.get("FAKE_BLENDER_MODE", "ok")
if mode == "fail":
    print("Blender 9.9 starting")
    print("Error: the scene is broken")
    sys.exit(3)
rest = argv[argv.index("--") + 1:]
out = rest[rest.index("--out") + 1]
os.makedirs(out, exist_ok=True)
if mode == "silent":
    sys.exit(0)

def png(w, h, pixel):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\\0" + b"".join(bytes(pixel(x, y)) for x in range(w)) for y in range(h))
    return b"\\x89PNG\\r\\n\\x1a\\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

sprites, notes = [], ["'Lights' has nothing to render (skipped)"]
if mode != "empty":
    for i, (name, w, h, pixel) in enumerate((("Hero", 8, 8, lambda x, y: (200, 30, 30, 255) if 2 <= x < 6 and 1 <= y < 7 else (0, 0, 0, 0)),
                                             ("Coin", 6, 6, lambda x, y: (30, 30, 200, 255) if 2 <= x < 4 and 2 <= y < 4 else (0, 0, 0, 0)))):
        with open(os.path.join(out, "sprite_%d.png" % i), "wb") as f:
            f.write(png(w, h, pixel))
        sprites.append({{"name": name, "file": "sprite_%d.png" % i, "width": w, "height": h, "scale": 16.0}})
with open(os.path.join(out, "manifest.json"), "w") as f:
    json.dump({{"sprites": sprites, "notes": notes, "blender": "9.9"}}, f)
print("prowl: rendered something")
print("lots of other Blender chatter")
'''


class FakeBlender(TempDir):
    """A temp folder with a fake `blender` executable; self.run_log() is the command line it was started with."""
    def setUp(self):
        super().setUp()
        if not POSIX:
            self.skipTest("the fake Blender is a script with a shebang line")
        self.blender = self.write("blender", FAKE_BLENDER.format(python=sys.executable))
        os.chmod(self.blender, 0o755)
        self.log = os.path.join(self.dir, "argv.json")
        env = mock.patch.dict(os.environ, {"BLENDER": self.blender, "FAKE_BLENDER_LOG": self.log, "FAKE_BLENDER_MODE": "ok"})
        env.start()
        self.addCleanup(env.stop)
        self.blend = self.write("scene.blend", "not really a blend file")
        self.script = self.write("make.py", "")

    def run_log(self):
        with open(self.log) as f:
            return json.load(f)


class BlenderRun(FakeBlender):
    def test_a_blend_file_is_rendered_into_sprites_and_blender_gets_the_right_command_line(self):
        said = []
        p = Project("p")
        report = blender_import.import_blend(p, self.blend, Options(), said.append)
        self.assertEqual([(s.name, s.width, s.height) for s in p.sprites], [("Hero", 4, 6), ("Coin", 2, 2)])
        self.assertEqual(said, ["rendered something"])                                        # only the "prowl:" lines are progress
        self.assertEqual(report.notes, ["'Lights' has nothing to render (skipped)"])
        argv = self.run_log()
        self.assertEqual(argv[:4], ["--background", "--factory-startup", "--python-exit-code", "1"])
        self.assertEqual(argv[4], os.path.abspath(self.blend))                                # the file comes before the scripts that use it
        self.assertEqual(argv[5:7], ["--python", blender_import.HELPER])
        self.assertNotIn("--python-expr", argv)
        rest = argv[argv.index("--") + 1:]
        self.assertEqual(rest[rest.index("--view") + 1], "front")
        self.assertEqual(rest[rest.index("--size") + 1], "32.0")
        self.assertNotIn("--ppu", rest)
        self.assertNotIn("--collections", rest)

    def test_a_script_runs_in_an_empty_scene_before_the_renderer(self):
        blender_import.import_blend_script(Project("p"), self.script, Options())
        argv = self.run_log()
        self.assertEqual(argv[4], "--python-expr")
        self.assertIn("use_empty=True", argv[5])
        self.assertEqual(argv[6:10], ["--python", os.path.abspath(self.script), "--python", blender_import.HELPER])

    def test_the_options_reach_the_renderer(self):
        blender_import.import_blend(Project("p"), self.blend, Options(view="top", ppu=16, engine="eevee", samples=4, collections=["Hero", "Co*"]))
        rest = self.run_log()
        rest = rest[rest.index("--") + 1:]
        self.assertEqual(rest[rest.index("--view") + 1], "top")
        self.assertEqual(rest[rest.index("--ppu") + 1], "16.0")
        self.assertNotIn("--size", rest)
        self.assertEqual(rest[rest.index("--engine") + 1], "eevee")
        self.assertEqual(rest[rest.index("--samples") + 1], "4")
        self.assertEqual(rest[rest.index("--collections") + 1:], ["Hero", "Co*"])

    def test_a_frame_range_reaches_the_renderer(self):
        blender_import.import_blend(Project("p"), self.blend, Options(frames="2:9"))
        rest = self.run_log()
        self.assertEqual(rest[rest.index("--frames") + 1], "2:9")
        blender_import.import_blend(Project("p"), self.blend, Options())
        self.assertNotIn("--frames", self.run_log())

    def test_the_temporary_render_folder_is_removed_and_a_kept_one_is_not(self):
        blender_import.import_blend(Project("p"), self.blend, Options())
        argv = self.run_log()
        self.assertFalse(os.path.exists(argv[argv.index("--out") + 1]))
        keep = os.path.join(self.dir, "kept", "renders")
        blender_import.import_blend(Project("p"), self.blend, Options(keep=keep))
        self.assertTrue(os.path.isfile(os.path.join(keep, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(keep, "sprite_0.png")))

    def test_a_kept_folders_old_manifest_is_never_mistaken_for_this_runs(self):
        keep = os.path.join(self.dir, "kept")
        blender_import.import_blend(Project("p"), self.blend, Options(keep=keep))
        with mock.patch.dict(os.environ, {"FAKE_BLENDER_MODE": "silent"}):
            with self.assertRaises(BlenderError):
                blender_import.import_blend(Project("p"), self.blend, Options(keep=keep))

    def test_blender_failing_shows_its_exit_code_and_what_it_printed(self):
        with mock.patch.dict(os.environ, {"FAKE_BLENDER_MODE": "fail"}):
            with self.assertRaises(BlenderError) as cm:
                blender_import.import_blend(Project("p"), self.blend, Options())
        self.assertIn("exit code 3", str(cm.exception))
        self.assertIn("the scene is broken", str(cm.exception))

    def test_blender_ending_without_a_render_list_is_explained(self):
        with mock.patch.dict(os.environ, {"FAKE_BLENDER_MODE": "silent"}):
            with self.assertRaises(BlenderError) as cm:
                blender_import.import_blend_script(Project("p"), self.script, Options())
        self.assertIn("ended without rendering", str(cm.exception))

    def test_no_sprites_is_an_error_that_carries_the_notes(self):
        p = Project("p")
        with mock.patch.dict(os.environ, {"FAKE_BLENDER_MODE": "empty"}):
            with self.assertRaises(BlenderError) as cm:
                blender_import.import_blend(p, self.blend, Options())
        self.assertIn("no sprites came out of", str(cm.exception))
        self.assertIn("'Lights' has nothing to render", str(cm.exception))
        self.assertEqual(p.sprites, [])

    def test_missing_files_are_reported(self):
        for fn in (blender_import.import_blend, blender_import.import_blend_script):
            with self.assertRaises(BlenderError) as cm:
                fn(Project("p"), os.path.join(self.dir, "nothere"), Options())
            self.assertIn("does not exist", str(cm.exception))


class FindBlender(FakeBlender):
    def test_an_explicit_path_wins_over_the_environment(self):
        other = self.write("other_blender", "")
        os.chmod(other, 0o755)
        self.assertEqual(blender_import.find_blender(other), other)
        self.assertEqual(blender_import.find_blender(), self.blender)                          # $BLENDER

    def test_a_path_that_is_not_a_program_is_an_error_naming_the_option(self):
        with self.assertRaises(BlenderError) as cm:
            blender_import.find_blender(os.path.join(self.dir, "nothere"))
        self.assertIn("--blender", str(cm.exception))
        with mock.patch.dict(os.environ, {"BLENDER": os.path.join(self.dir, "nothere")}):
            with self.assertRaises(BlenderError) as cm:
                blender_import.find_blender()
        self.assertIn("$BLENDER", str(cm.exception))

    def test_the_path_is_searched_and_nothing_found_says_what_to_do(self):
        with mock.patch.dict(os.environ, {"BLENDER": ""}):
            with mock.patch("shutil.which", return_value="/somewhere/blender"):
                self.assertEqual(blender_import.find_blender(), "/somewhere/blender")
            with mock.patch("shutil.which", return_value=None), mock.patch.object(blender_import, "_executable", return_value=None):
                with self.assertRaises(BlenderError) as cm:
                    blender_import.find_blender()
        self.assertIn("--blender PATH", str(cm.exception))

    def test_a_macos_app_bundle_means_the_program_inside_it(self):
        app = os.path.join(self.dir, "Blender.app")
        inner = self.write("Blender.app/Contents/MacOS/Blender", "")
        self.assertEqual(blender_import._executable(app), inner)


@unittest.skipUnless(shutil.which("blender") or os.environ.get("BLENDER"), "no Blender installed (put it on the PATH or set BLENDER)")
class RealBlender(TempDir):
    SCRIPT = """
        import bpy
        for name, x in (("Brick", 0), ("Ball", 3)):
            c = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(c)
            (bpy.ops.mesh.primitive_cube_add if name == "Brick" else bpy.ops.mesh.primitive_uv_sphere_add)(location=(x, 0, 0))
            o = bpy.context.active_object
            for old in list(o.users_collection):
                old.objects.unlink(o)
            c.objects.link(o)
    """

    def test_a_script_that_builds_two_collections_gives_two_sprites_of_one_scale(self):
        p = Project("p")
        report = blender_import.import_blend_script(p, self.write("make.py", self.SCRIPT), Options(size=16, samples=1))
        self.assertEqual([s.name for s in p.sprites], ["Brick", "Ball"])
        self.assertEqual(report.sprites, p.sprites)
        for s in p.sprites:
            self.assertTrue(10 <= s.width <= 16 and 10 <= s.height <= 16, (s.name, s.width, s.height))
            self.assertTrue(any(s.frames[0]))

    LEVEL_SCRIPT = """
        import bpy
        def collection(name):
            c = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(c)
            return c
        brick = collection("brick")
        brick["solid"] = True
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        o = bpy.context.active_object
        for old in list(o.users_collection):
            old.objects.unlink(o)
        brick.objects.link(o)
        level = collection("Level_1")
        for x in range(4):
            e = bpy.data.objects.new("tile", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = brick
            e.location = (x, 0, 0)
            level.objects.link(e)
    """

    ANIM_SCRIPT = """
        import bpy
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 3
        c = bpy.data.collections.new("walker")
        bpy.context.scene.collection.children.link(c)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        o = bpy.context.active_object
        for old in list(o.users_collection):
            old.objects.unlink(o)
        c.objects.link(o)
        for frame, x in ((1, 0), (3, 2)):
            o.location = (x, 0, 0)
            o.keyframe_insert("location", frame=frame)
    """

    def test_an_animated_collection_becomes_a_sprite_with_frames_that_move(self):
        p = Project("p")
        blender_import.import_blend_script(p, self.write("anim.py", self.ANIM_SCRIPT), Options(ppu=8, samples=1, frames="all"))
        s = p.sprite("walker")
        self.assertEqual(len(s.frames), 3)
        self.assertGreater(s.width, s.height)                                                  # the box that holds the whole walk
        first = [x for x in range(s.width) if s.get(0, x, s.height // 2)]
        last = [x for x in range(s.width) if s.get(2, x, s.height // 2)]
        self.assertLess(min(first), min(last))

    def test_a_level_collection_of_instances_becomes_a_level_of_solid_tiles(self):
        p = Project("p")
        report = blender_import.import_blend_script(p, self.write("lvl.py", self.LEVEL_SCRIPT), Options(ppu=8, samples=1))
        self.assertEqual([s.name for s in p.sprites], ["brick"])                                # the level itself is not a sprite
        level = p.level("Level_1")
        self.assertEqual((level.width, level.height), (4, 1))
        self.assertTrue(all(p.tiles[c].solid for c in level.cells))
        self.assertEqual(report.levels, [level])

    HEAD_SCRIPT = """
        import prowl_blender as pb
        pb.new_scene(frames=3, fps=6)
        face = pb.head("%s", name="face")
        for f in pb.frames():
            face.mouth(f.i / 2.0)
            face.look(x=f.i - 1)
            face.blink(1.0 if f.i == 2 else 0.0)
    """

    def test_code_builds_and_animates_a_head_with_layers_framed_alike(self):
        p = Project("p")
        script = self.write("head.py", self.HEAD_SCRIPT % "cat")
        blender_import.import_blend_script(p, script, Options(ppu=24, samples=1))
        self.assertEqual([s.name for s in p.sprites], ["face", "face_head", "face_mouth", "face_eyes"])
        sizes = {(s.width, s.height) for s in p.sprites}
        self.assertEqual(len(sizes), 1, "the layers are the size of the whole head")
        self.assertEqual({len(s.frames) for s in p.sprites}, {3})
        self.assertEqual({s.fps for s in p.sprites}, {6.0})
        eyes = p.sprite("face_eyes")
        self.assertNotEqual(eyes.frames[0], eyes.frames[2], "the pupils and the lids move")

    def test_every_kind_of_head_builds_with_the_same_parts(self):
        script = self.write("kinds.py", """
            import prowl_blender as pb
            pb.new_scene()
            for kind in pb.head_kinds():
                face = pb.head(kind, name=kind)
                assert {"skin", "pupil", "eye", "lid_upper", "lip_lower"} <= set(face.parts), (kind, sorted(face.parts))
                assert ("teeth_upper" in face.parts) == (kind in ("monkey", "gorilla")), kind
            assert len(pb.head_kinds()) == 8
            assert pb.head("\U0001F431", name="emoji").kind == "cat"
        """)
        p = Project("p")
        blender_import.import_blend_script(p, script, Options(ppu=8, samples=1, collections=["monkey"]))
        self.assertIn("monkey", [s.name for s in p.sprites])


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# the command line itself

class CommandLine(TempDir):
    def prowl(self, *args, display=False, extra_env=None):
        env = dict(os.environ)
        for name in ("DISPLAY", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM", "BLENDER"):
            env.pop(name, None)
        if display:
            env["QT_QPA_PLATFORM"] = "offscreen"
        env.update(extra_env or {})
        return subprocess.run([sys.executable, PROWL] + list(args), capture_output=True, text=True, cwd=self.dir, env=env, timeout=120)

    def art(self):
        sprites = self.write("hero.txt", "# sprite: hero\n..RR..\n.RRRR.\nRRRRRR\n")
        levels = self.write("lvl.txt", "⬛⬛⬛⬛\n⬛⬛🧱⬛\n🧱🧱🧱🧱\n")
        return sprites, levels

    def test_no_gui_import_ascii_writes_the_project_and_exits(self):
        sprites, levels = self.art()
        out = os.path.join(self.dir, "out.json")
        r = self.prowl("--no-gui", "--import-ascii", out, "--sprites", sprites, "--levels", levels)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = Project.load(out)
        self.assertEqual(([s.name for s in p.sprites], [l.name for l in p.levels], p.name), (["hero"], ["lvl"], "out"))

    @unittest.skipUnless(LINUX, "needs a Linux machine with no display")
    def test_without_a_display_import_ascii_still_writes_the_file(self):
        sprites, _ = self.art()
        out = os.path.join(self.dir, "out.json")
        r = self.prowl("--import-ascii", out, "--sprites", sprites)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("cannot open here", r.stdout)
        self.assertEqual([s.name for s in Project.load(out).sprites], ["hero"])

    @unittest.skipUnless(LINUX, "needs a Linux machine with no display")
    def test_an_import_that_could_be_neither_shown_nor_saved_is_refused_up_front(self):
        sprites, _ = self.art()
        r = self.prowl("--import-ascii", "--sprites", sprites)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--output", r.stderr)

    def test_a_py_file_is_pointed_to_the_option_it_belongs_to(self):
        r = self.prowl("gen.py", "--no-gui")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--plugin gen.py", r.stderr)
        self.assertIn("--blend-script gen.py", r.stderr)

    def test_a_file_name_taken_as_the_frame_range_is_explained(self):
        r = self.prowl("--blend-frames", "scene.blend", "--no-gui")
        self.assertEqual(r.returncode, 2)
        self.assertIn("put the files first", r.stderr)

    def test_two_projects_are_refused(self):
        r = self.prowl("a.json", "b.json", "--no-gui")
        self.assertEqual(r.returncode, 1)
        self.assertIn("only one project", r.stderr)

    def test_a_plugin_adds_a_file_type_and_an_option_and_they_work_from_the_command_line(self):
        plugin = self.write("pal.py", """
            from prowl_editor.model import Sprite
            from prowl_editor.plugins import ImportResult

            def register(prowl):
                prowl.add_argument("--pal-width", type=int, default=2)
                prowl.add_importer(".pal", import_pal)

            def import_pal(project, path, args):
                made = []
                for line in open(path):
                    name, hexcolour = line.split()
                    index = project.palette.add(project.palette.first_free_key(), name, tuple(int(hexcolour[i:i + 2], 16) for i in (0, 2, 4)))
                    s = Sprite(name, args.pal_width, 1)
                    s.frames = [bytearray([index] * args.pal_width)]
                    made.append(project.add_sprite(s))
                return ImportResult(sprites=made)
        """)
        pal = self.write("c.pal", "sky 3377dd\ngrass 33aa44\n")
        out = os.path.join(self.dir, "pal.json")
        r = self.prowl("--plugin", plugin, pal, "--pal-width", "3", "--no-gui", "-o", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2 sprites, 0 levels", r.stdout)
        self.assertEqual([(s.name, s.width) for s in Project.load(out).sprites], [("sky", 3), ("grass", 3)])
        help_text = self.prowl("--plugin", plugin, "--help").stdout
        self.assertIn("--pal-width", help_text)
        self.assertIn(".pal", help_text)

    def test_a_plugin_that_has_a_bug_stops_with_its_name_and_traceback(self):
        plugin = self.write("buggy.py", "def register(prowl):\n    prowl.on_project(lambda p, a: 1 / 0)\n")
        r = self.prowl("--plugin", plugin, "--no-gui")
        self.assertEqual(r.returncode, 1)
        self.assertIn("plugin buggy", r.stderr)
        self.assertIn("ZeroDivisionError", r.stderr)
        self.assertIn("Traceback", r.stderr)

    @unittest.skipUnless(POSIX, "the fake Blender is a script with a shebang line")
    def test_a_blend_file_given_to_prowl_becomes_sprites_in_a_new_project(self):
        fake = self.write("blender", FAKE_BLENDER.format(python=sys.executable))
        os.chmod(fake, 0o755)
        blend = self.write("level one.blend", "x")
        out = os.path.join(self.dir, "blend.json")
        env = {"BLENDER": fake, "FAKE_BLENDER_LOG": os.path.join(self.dir, "argv.json")}
        r = self.prowl(blend, "--no-gui", "-o", out, "--blend-view", "top", "--blend-size", "8", extra_env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = Project.load(out)
        self.assertEqual(([s.name for s in p.sprites], p.name), (["Hero", "Coin"], "blend"))
        self.assertEqual(p.levels, [])                                                          # not imported into the demo project
        with open(env["FAKE_BLENDER_LOG"]) as f:
            rest = json.load(f)
        rest = rest[rest.index("--") + 1:]
        self.assertEqual((rest[rest.index("--view") + 1], rest[rest.index("--size") + 1]), ("top", "8.0"))
        self.assertIn("note: 'Lights' has nothing to render", r.stdout)

    @unittest.skipUnless(POSIX, "the fake Blender is a script with a shebang line")
    def test_blend_script_and_blend_collections_are_passed_on(self):
        fake = self.write("blender", FAKE_BLENDER.format(python=sys.executable))
        os.chmod(fake, 0o755)
        script = self.write("make.py", "")
        env = {"BLENDER": fake, "FAKE_BLENDER_LOG": os.path.join(self.dir, "argv.json")}
        r = self.prowl("--blend-script", script, "--blend-collections", "Hero,Coin", "--blend-collections", "Rock", "--no-gui", "-o", os.path.join(self.dir, "o.json"), extra_env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(env["FAKE_BLENDER_LOG"]) as f:
            argv = json.load(f)
        self.assertEqual(argv[argv.index("--collections") + 1:], ["Hero", "Coin", "Rock"])
        self.assertIn(os.path.abspath(script), argv)

    @unittest.skipUnless(HAVE_QT, "PyQt5 is not installed")
    def test_the_editor_opens_on_what_was_imported_with_it_selected(self):
        """The point of the change: --import-ascii does not just write the file, the editor shows the data."""
        sprites, levels = self.art()
        probe = os.path.join(self.dir, "probe.json")
        plugin = self.write("probe.py", """
            import json, os

            def register(prowl):
                def gui(studio, main, windows, args):
                    with open(os.environ["PROBE_OUT"], "w") as f:
                        json.dump({"project": studio.project.name, "sprites": [s.name for s in studio.project.sprites], "levels": [l.name for l in studio.project.levels],
                                   "sprite": studio.sprite.name, "level": studio.level.name, "listed": [main.sprites.count(), main.levels.count()]}, f)
                prowl.on_gui(gui)
        """)
        out = os.path.join(self.dir, "out.json")
        r = self.prowl("--plugin", plugin, "--import-ascii", out, "--sprites", sprites, "--levels", levels, "--quit-after", "0.5", display=True, extra_env={"PROBE_OUT": probe})
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(probe) as f:
            seen = json.load(f)
        self.assertEqual(seen, {"project": "out", "sprites": ["hero"], "levels": ["lvl"], "sprite": "hero", "level": "lvl", "listed": [1, 1]})
        self.assertTrue(os.path.isfile(out))                                                    # and it is saved too

    @unittest.skipUnless(HAVE_QT, "PyQt5 is not installed")
    def test_the_editor_opens_on_a_project_with_sprites_and_no_levels(self):
        """What a Blender import makes: sprites only. The editor must cope."""
        p = Project("only_sprites")
        from .model import Sprite
        p.add_sprite(Sprite("lone", 3, 3))
        path = os.path.join(self.dir, "only.json")
        p.save(path)
        r = self.prowl(path, "--quit-after", "0.5", display=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.prowl("--screenshots", os.path.join(self.dir, "shots"), path, display=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
