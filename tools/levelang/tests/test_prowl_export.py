"""The Level.cs exporter, checked against the real Samples/SlimeJump* files."""
import os
import re
import tempfile
import unittest

from ._common import REPO, run
from levelang.export import ExportError, level_cs_to_lvl, parse_level_cs, to_level_cs
from levelang.export.slimejump import fmt, merge_rects

SAMPLES = [REPO / "Samples" / n / "Level.cs" for n in ("SlimeJump", "SlimeJumpDestruct")]
DATA_LINE = re.compile(r"^\s+(Set[24]\(|Enemies\[)")


def export(lvl_text, layers_from=None):
    return to_level_cs(run(lvl_text), "t.lvl", layers_from)


def tiles(body_rows, defs):
    """A small .lvl: `defs` are `emoji -> attrs`, rows are lists of cells ('' = air), top row first."""
    out = ["meta(width=%d, height=%d)" % (len(body_rows[0]), len(body_rows)), ""]
    for e, a in defs.items():
        out += [f"def {e} -> {a}:", ""]
    out.append("def t():")
    out += ["".join(c or "  " for c in r).rstrip() or "·" for r in body_rows]
    return "\n".join(out + ["", "t()", ""])


class RectTests(unittest.TestCase):
    def test_merge(self):
        self.assertEqual(merge_rects({(0, 0)}), [(0, 0, 1, 1)])
        self.assertEqual(merge_rects({(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)}), [(0, 0, 3, 2)])
        self.assertEqual(merge_rects({(0, 0), (2, 0)}), [(0, 0, 1, 1), (2, 0, 1, 1)])  # a gap splits a run
        self.assertEqual(merge_rects({(0, 0), (0, 2)}), [(0, 0, 1, 1), (0, 2, 1, 1)])  # and so does a missing row
        # an L is two rects, none covering a cell twice or missing one
        got = merge_rects({(0, 0), (1, 0), (0, 1)})
        self.assertEqual(sorted(sum(([(x + i, y + j) for i in range(w) for j in range(h)] for x, y, w, h in got), [])), [(0, 0), (0, 1), (1, 0)])

    def test_float_format_matches_the_samples(self):
        self.assertEqual((fmt(64), fmt(4.575), fmt(4.3), fmt(0.5), fmt(4 + 0.3)), ("64f", "4.575f", "4.3f", "0.5f", "4.3f"))


@unittest.skipUnless(all(p.exists() for p in SAMPLES), "needs the Samples folder of the Prowl2D checkout")
class RealLevelTests(unittest.TestCase):
    def test_real_levels_round_trip(self):
        for path in SAMPLES:
            with self.subTest(sample=path.parent.name):
                orig = path.read_text(encoding="utf-8")
                text, warnings = to_level_cs(run(level_cs_to_lvl(orig)), "x.lvl", str(path))
                self.assertEqual(warnings, [])
                a, b = orig.split("\n"), text.split("\n")
                self.assertEqual(len(a), len(b))
                # everything that is not data (accessors, helpers, LayerRows incl. the game's own rules) is identical, bar the header comment
                self.assertEqual([l for l in a[1:] if not DATA_LINE.match(l)], [l for l in b[1:] if not DATA_LINE.match(l)])
                # the data is the same: same spawn/goal/bounds/entities, and the same cells covered by the same kinds of rect
                da, db = parse_level_cs(orig), parse_level_cs(text)
                for key in ("spawn", "goal", "size", "saves", "gems", "anchors", "shooters", "enemies"):
                    self.assertEqual(da[key], db[key], key)
                cover = lambda rs: {(x + i, y + j) for x, y, w, h in rs for i in range(int(w)) for j in range(int(h))}
                for key in ("walls", "climbs", "spikes", "crumbles"):
                    self.assertEqual(cover(da[key]), cover(db[key]), key)
                self.assertEqual(sorted(da["walls"]), sorted(db["walls"]))  # even the rectangles: only their order differs

    def test_default_layer_rules_are_slimejumps(self):
        orig = SAMPLES[0].read_text(encoding="utf-8")
        text, _ = to_level_cs(run(level_cs_to_lvl(orig)))
        self.assertEqual(orig[orig.index("    // Layer collision matrix"):], text[text.index("    // Layer collision matrix"):])


class SchemaTests(unittest.TestCase):
    ROWS = [
        ["🐸", "", "⚓", "", "", "🏁"],
        ["", "🟫", "", "🪱", "", ""],
        ["🧱", "🧱", "➡️", "🧱", "🧱", "🧱"],
    ]
    DEFS = {"🧱": "solid", "🟫": "crumbly", "➡️": "solid, shooter(1, 0)", "⚓": "anchor, at(0.5, 0)", "🪱": "enemy(0), at(0.5, 0.3)", "🐸": "spawn", "🏁": "goal"}

    def test_every_array(self):
        text, warnings = export(tiles(self.ROWS, self.DEFS))
        self.assertEqual(warnings, [])
        d = parse_level_cs(text)
        self.assertEqual(d["size"], (6, 3))
        self.assertEqual(d["spawn"], (0.5, 2.5))  # top row of the art is the highest y: the game's y is up
        self.assertEqual(d["goal"], (5.5, 2.5))
        self.assertEqual(d["walls"], [(0, 0, 6, 1)])  # the shooter's cell is part of the walls
        self.assertEqual(d["crumbles"], [(1, 1, 1, 1)])  # a crumbly tile is NOT a wall
        self.assertEqual(d["shooters"], [(2.5, 0.5, 1, 0)])
        self.assertEqual(d["anchors"], [(2.5, 2.0)])
        self.assertEqual(d["enemies"], [(0, 3.5, 1.3)])

    def test_counts_and_sizes_follow_the_sample_conventions(self):
        text, _ = export(tiles(self.ROWS, self.DEFS))
        self.assertIn("Gems = new float[2]; GemCount = 0;", text)  # an empty array still has one slot
        self.assertIn("Enemies = new float[3]; EnemyCount = 1;", text)
        self.assertIn("Walls = new float[4]; WallCount = 1;", text)

    def test_needs_exactly_one_spawn_and_goal(self):
        rows = [r[:] for r in self.ROWS]
        rows[1][0] = "🐸"
        with self.assertRaisesRegex(ExportError, "exactly one `spawn`"):
            export(tiles(rows, self.DEFS))
        rows = [r[:] for r in self.ROWS]
        rows[0][5] = ""
        with self.assertRaisesRegex(ExportError, "exactly one `goal`"):
            export(tiles(rows, self.DEFS))

    def test_warnings_and_bad_attributes(self):
        defs = dict(self.DEFS, **{"➡️": "shooter(1, 0)"})
        _, warnings = export(tiles(self.ROWS, defs))
        self.assertTrue(any("not `solid`" in w for w in warnings))
        with self.assertRaisesRegex(ExportError, "integer kind"):
            export(tiles(self.ROWS, dict(self.DEFS, **{"🪱": "enemy(0.5)"})))
        rows = [r[:] for r in self.ROWS]
        rows[0][5], rows[0][3] = "", "🏁"
        rows[1][5] = "🧱"
        # meta says 4 wide but the art is 6 wide: the extra cells are reported, not silently dropped
        _, warnings = export(tiles(rows, self.DEFS).replace("width=6", "width=4"))
        self.assertTrue(any("outside the 4x3 level" in w for w in warnings))

    def test_without_meta_the_bounds_are_the_level(self):
        text, _ = export("def 🧱 -> solid:\n\ndef 🐸 -> spawn:\n\ndef 🏁 -> goal:\n\nx = 5; y = 5\n🐸\n🧱\n🏁\n")
        d = parse_level_cs(text)
        self.assertEqual((d["size"], d["spawn"], d["goal"], d["walls"]), ((1, 3), (0.5, 2.5), (0.5, 0.5), [(0, 1, 1, 1)]))

    def test_converter_refuses_what_it_cannot_draw(self):
        cs = SAMPLES[0].read_text(encoding="utf-8") if SAMPLES[0].exists() else None
        if cs is None:
            self.skipTest("needs the Samples folder")
        bad = cs.replace("Set2(Gems, 1, 45.5f, 6.5f)", "Set2(Gems, 1, 45.25f, 6.5f)")
        with self.assertRaisesRegex(ExportError, "different places inside their cells"):
            level_cs_to_lvl(bad)


SAMPLE = REPO / "Samples" / "SlimeJumpLevelang"


@unittest.skipUnless((SAMPLE / "level.lvl").exists() and SAMPLES[0].exists(), "needs Samples/SlimeJumpLevelang")
class SlimeJumpLevelangSampleTests(unittest.TestCase):
    def setUp(self):
        from levelang import load_file

        self.level, _ = load_file(str(SAMPLE / "level.lvl"))
        self.generated, self.warnings = to_level_cs(self.level, "level.lvl", str(SAMPLES[0]))

    def test_level_cs_is_current(self):
        """Edit level.lvl, then regenerate: python3 tools/levelang export-cs Samples/SlimeJumpLevelang/level.lvl -o Samples/SlimeJumpLevelang/Level.cs --layers-from Samples/SlimeJump/Level.cs"""
        self.assertEqual(self.warnings, [])
        self.assertEqual((SAMPLE / "Level.cs").read_text(encoding="utf-8"), self.generated)

    def test_it_is_slimejumps_level(self):
        a, b = parse_level_cs(SAMPLES[0].read_text(encoding="utf-8")), parse_level_cs(self.generated)
        for key in ("spawn", "goal", "size", "saves", "gems", "anchors", "shooters", "enemies", "crumbles", "climbs", "spikes"):
            self.assertEqual(a[key], b[key], key)
        self.assertEqual(sorted(a["walls"]), sorted(b["walls"]))

    def test_every_tile_has_a_valid_svg(self):
        import xml.etree.ElementTree as ET

        svgs = {p.tile.name: p.tile.svg for p in self.level.placements}
        svgs.update({p.tile.name: p.tile.svg for l in self.level.layers for p in l.placements})
        self.assertTrue(svgs and all(svgs.values()), "every tile of the sample should be an SVG")
        for name, text in svgs.items():
            self.assertTrue(ET.fromstring(text).tag.endswith("svg"), name)
        used = {p.name for p in (SAMPLE / "svg").glob("*.svg")}
        self.assertEqual(len(used), len(svgs))  # no tile without a file, no file without a tile

    def test_layers_and_skin_are_only_pictures(self):
        """Parallax layers and the smooth skin change the look, never Level.cs: the generated file equals SlimeJump's data (test above), and it has no trace of them."""
        self.assertTrue(self.level.layers and self.level.skins)
        self.assertFalse(any(p.tile.has("solid") or p.tile.has("hazard") or p.tile.has("item") for l in self.level.layers for p in l.placements))

    def test_scripts_are_there(self):
        """SlimeJump's scripts, plus the drawing of the layers (Scenery, its baked data, Viewer). Only Game.cs and Cfg.cs differ from SlimeJump's: they carry the switch that turns the viewer on."""
        extra = {"Scenery.cs", "SceneryData.cs", "Viewer.cs"}
        self.assertEqual({p.name for p in SAMPLE.glob("*.cs")} - extra, {p.name for p in SAMPLES[0].parent.glob("*.cs")})
        src = SAMPLES[0].parent
        for p in SAMPLE.glob("*.cs"):
            if p.name in extra | {"Level.cs", "Game.cs", "Cfg.cs"}:
                continue
            self.assertEqual(p.read_bytes(), (src / p.name).read_bytes(), p.name)

    def test_the_viewer_switch_is_off_and_changes_nothing_else(self):
        """Cfg.Draw is false: the headless run (and its hash) is SlimeJump's. Game.cs is SlimeJump's plus three lines that only run when it is true."""
        self.assertIn("public const bool Draw = false;", (SAMPLE / "Cfg.cs").read_text(encoding="utf-8"))
        a = (SAMPLES[0].parent / "Game.cs").read_text(encoding="utf-8").splitlines()
        b = (SAMPLE / "Game.cs").read_text(encoding="utf-8").splitlines()
        added = [l.strip() for l in b if l not in a]
        self.assertEqual(sorted(added), sorted(["if (Cfg.Draw && Viewer.Init() != 0) return 3;", "if (Cfg.Draw) Viewer.Frame(frame, px, py);", "if (Cfg.Draw) Viewer.Shutdown();"]))
        self.assertEqual([l for l in a if l not in b], [])


class CliTests(unittest.TestCase):
    def test_export_cs_command(self):
        from levelang.cli import main

        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.lvl")
            with open(src, "w", encoding="utf-8") as f:
                f.write(tiles(SchemaTests.ROWS, SchemaTests.DEFS))
            self.assertEqual(main(["export-cs", src]), 0)
            with open(os.path.join(d, "Level.cs"), encoding="utf-8") as f:
                text = f.read()
            self.assertTrue(text.startswith("// GENERATED by levelang from a.lvl"))
            self.assertIn("public static uint[] LayerRows()", text)


if __name__ == "__main__":
    unittest.main()
