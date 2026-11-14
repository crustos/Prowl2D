import ast
import tempfile
import unittest

from ._common import EX, Runtime, cells, compile_level, run, transform, translate, xy
from levelang.emoji import cluster_width, ident_for, scan_cluster


class EmojiTests(unittest.TestCase):
    def test_clusters_and_names(self):
        self.assertEqual(scan_cluster("⛰️x", 0), 2)  # base + VS16 is one cluster
        self.assertEqual(scan_cluster("🧑‍🚀!", 0), 3)  # ZWJ sequence
        self.assertEqual(scan_cluster("a", 0), 0)
        self.assertEqual(ident_for("⛰️"), "tile_MOUNTAIN")
        self.assertEqual(ident_for("⛰"), "tile_MOUNTAIN")
        self.assertEqual((cluster_width("🧱"), cluster_width("☁️")), (2, 2))

    def test_emoji_in_strings_and_comments_untouched(self):
        t = translate('s = "🧱"  # 🧱\n🧱\n')
        self.assertIn('"🧱"', t.python)
        self.assertIn("# 🧱", t.python)
        self.assertIn("tile_BRICK", t.python.splitlines()[1])


class ParserTests(unittest.TestCase):
    def test_line_count_preserved_and_valid_python(self):
        for name in ("section", "mario", "underwater"):
            src = (EX / f"{name}.lvl").read_text(encoding="utf-8")
            t = translate(src)
            self.assertEqual(t.python.count("\n"), src.count("\n"), name)
            compile(t.python, name, "exec")

    def test_nbsp_is_a_space(self):
        lv = run("def f():\n    🧱 🪨\n\nf()\n")
        self.assertEqual(cells(lv), [("tile_BRICK", 2, 0), ("tile_ROCK", 3, 0)])

    def test_art_columns_use_cells_two_spaces_per_tile(self):
        # 🧱 = 2 cells (tile 0) | 2 spaces = 1 empty tile | 🧱 at cell 4 (tile 2) | 4 spaces = 2 tiles | 🧱 at cell 10 (tile 5)
        self.assertEqual(xy(run("def f():\n🧱  🧱    🧱\n\nf(y=3)\n")), [(0, 3), (2, 3), (5, 3)])

    def test_ascii_art_is_one_cell_per_tile(self):
        self.assertEqual(xy(run("legend({'#': 🧱, '.': None})\ndef f():\n#.#\n\nf()\n")), [(0, 0), (2, 0)])

    def test_spacer_keeps_an_empty_row_alive(self):
        self.assertEqual(xy(run("def f():\n🧱\n·\n🧱\n\nf()\n")), [(0, 0), (0, 2)])

    def test_anchor_position_width_and_call(self):
        calls = []
        tr = translate("def f(a, b):\n🧱a( )🧱\n\n")
        ns = Runtime(1).namespace(tr, "t")
        exec(compile(transform(ast.parse(tr.python), tr.tiles), "t", "exec"), ns)
        ns["f"](lambda x, y, w: calls.append((x, y, w)), None, x=10, y=5)
        self.assertEqual(calls, [(11, 5, 2)])  # `a( )` is 4 cells = 2 tiles wide, one tile after the brick

    def test_arrow_def_pattern_and_attrs(self):
        t = run("def 🟦 -> fill.blue, stroke.white, solid:\n~ ~\n ~ \n\n🟦\n").placements[0].tile
        self.assertEqual((t.fill, t.stroke, t.pattern), ("blue", "white", ["~ ~", " ~"]))
        self.assertTrue(t.has("solid"))

    def test_arrow_def_svg_inline(self):
        t = run('def 🪸 -> svg, sway:\n<svg viewBox="0 0 1 1">\n<rect width="1" height="1"/>\n</svg>\n\n🪸\n').placements[0].tile
        self.assertTrue(t.svg.strip().startswith("<svg") and t.svg.strip().endswith("</svg>"))
        self.assertIn("sway", t.anim)

    def test_valued_attributes_land_in_params(self):
        t = run("def 🔫 -> solid, shooter(1, 0), enemy(1), at(0.5, 0.25):\n\n🔫\n").placements[0].tile
        self.assertEqual(t.params, {"shooter": (1, 0), "enemy": 1, "at": (0.5, 0.25)})


class TransformerTests(unittest.TestCase):
    def test_statement_emits_row_and_moves_down(self):
        lv = run("x = 3; y = 2\n🧱*4\n🪨\n")
        self.assertEqual(cells(lv), [("tile_BRICK", 3, 2), ("tile_BRICK", 4, 2), ("tile_BRICK", 5, 2), ("tile_BRICK", 6, 2), ("tile_ROCK", 3, 3)])

    def test_or_is_random_per_tile_and_seeded(self):
        src = "(🧱 or 🪨 or None)*200\n"
        a, b = run(src, 5), run(src, 5)
        self.assertEqual(cells(a), cells(b))
        self.assertEqual({p.tile.name for p in a.placements}, {"tile_BRICK", "tile_ROCK"})
        self.assertTrue(100 < len(a.placements) < 160)

    def test_tile_times_float_is_a_chance(self):
        self.assertTrue(60 < len(run("(🪙*0.25)*400\n").placements) < 140)

    def test_plain_python_untouched(self):
        self.assertEqual(len(run("a = 0 or 5\nb = [1] * 3\nassert a == 5 and b == [1, 1, 1]\n🧱\n").placements), 1)

    def test_if_chance_and_tile_functions(self):
        lv = run("def ⛰️(x, y):\n    if 🟩 * 0.5:\n        🟫\n        🟫\n⛰️*100\n")
        self.assertTrue(60 < len(lv.placements) < 140)

    def test_emitting_function_gets_cursor_params(self):
        self.assertEqual(xy(run("def row():\n    🧱*3\nrow(x=1, y=4)\n")), [(1, 4), (2, 4), (3, 4)])


class ExampleTests(unittest.TestCase):
    def test_uploaded_examples_run(self):
        lv = run((EX / "mario.lvl").read_text(encoding="utf-8") + "\nM(30, 0)\n")
        self.assertLessEqual({"tile_CLOUD", "tile_BRICK", "tile_EVERGREEN_TREE"}, {p.tile.name for p in lv.placements})
        self.assertGreater(len(run((EX / "section.lvl").read_text(encoding="utf-8") + "\nsection_start(None, None, y=3)\n").placements), 100)

    def test_underwater_is_playable(self):
        from levelang import bot

        path = EX / "underwater.lvl"
        lv, _ = compile_level(path.read_text(encoding="utf-8"), str(path), seed=7)
        plan = bot.plan(lv)
        self.assertEqual(plan.notes, [])
        self.assertEqual(plan.points[-1], plan.goal)
        self.assertEqual(len(plan.collects), len(lv.find("item")))
        blocked = {(p.x, p.y) for p in lv.placements if p.tile.has("solid") or p.tile.has("hazard")}
        self.assertFalse(set(plan.points) & blocked)

    def test_gif_renders(self):
        try:
            import cairosvg  # noqa: F401
        except Exception:
            self.skipTest("cairosvg not installed")
        from levelang.render import render_gif

        path = EX / "underwater.lvl"
        lv, _ = compile_level(path.read_text(encoding="utf-8"), str(path), seed=7)
        with tempfile.TemporaryDirectory() as d:
            info = render_gif(lv, d + "/o.gif", fps=8, speed=30)
            self.assertTrue(info["reached_goal"])


if __name__ == "__main__":
    unittest.main()
