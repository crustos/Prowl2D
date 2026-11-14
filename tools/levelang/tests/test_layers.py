"""Parallax layers, per-placement size/flip, and the smooth skin."""
import unittest

from PIL import Image

from ._common import run
from levelang.render.gif import render_gif
from levelang.render.skin import grid_loops, path_data, skin_loops, skin_mask

DEFS = """
def A -> fill.red, solid:

def B -> fill.blue, bg, size(2, 2):

"""


def area(loop):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(loop, loop[1:] + loop[:1]))) / 2


class LayerTests(unittest.TestCase):
    def test_with_layer_collects_placements_apart_from_the_world(self):
        lvl = run(DEFS + "place(A, 0, 0)\nwith layer('far', parallax=0.3, haze=('#123456', 0.5), alpha=0.8):\n    place(B, 3.5, 1.25, size=(4, 3), flip=True)\n    place(B, 9, 2)\nplace(A, 1, 0)\n")
        self.assertEqual([(p.x, p.y) for p in lvl.placements], [(0, 0), (1, 0)])  # after the with, placing is back in the world
        (far,) = lvl.layers
        self.assertEqual((far.name, far.parallax, far.parallax_y, far.over, far.alpha, far.haze), ("far", 0.3, 0.3, False, 0.8, ("#123456", 0.5)))
        self.assertEqual([(p.x, p.y, p.size, p.flip) for p in far.placements], [(3.5, 1.25, (4, 3), True), (9, 2, None, False)])
        self.assertEqual(lvl.cell(3, 1), [])  # a layer is not in the world's cells (the bot and the Level.cs exporter never see it)

    def test_same_name_is_the_same_layer_and_scopes_nest(self):
        lvl = run(DEFS + "with layer('a', parallax=0.2):\n    place(B, 0, 0)\n    with layer('b', parallax=0.6, over=True):\n        place(B, 1, 1)\n    place(B, 2, 2)\nwith layer('a'):\n    place(B, 3, 3)\n")
        a, b = lvl.layers
        self.assertEqual([p.x for p in a.placements], [0, 2, 3])
        self.assertEqual([p.x for p in b.placements], [1])
        self.assertTrue(b.over and not a.over)

    def test_tall_art_function_inside_a_layer(self):
        lvl = run(DEFS + "def row(x, y):\n    B * 3\n\nwith layer('l', parallax=1):\n    place(row, 4, 5)\n")
        self.assertEqual([(p.x, p.y) for p in lvl.layers[0].placements], [(4, 5), (5, 5), (6, 5)])

    def test_to_dict_has_layers_and_skins(self):
        d = run(DEFS + "place(A, 0, 0)\nskin(A, wobble=0.1)\nwith layer('l', parallax=0.5):\n    place(B, 1, 1, size=(2, 3))\n").to_dict()
        self.assertEqual(d["layers"][0]["placements"], [["B", 1, 1, [2, 3]]])
        self.assertEqual(d["skins"][0]["selectors"], ["A"])
        self.assertIn("B", d["tiles"])

    def test_skin_wants_tiles_or_a_known_flag(self):
        with self.assertRaises(TypeError):
            run(DEFS + "skin()\n")
        with self.assertRaises(TypeError):
            run(DEFS + "skin('wet')\n")


class SkinGeometryTests(unittest.TestCase):
    def test_loops_of_a_block_and_of_a_ring(self):
        block = {(x, y) for x in range(2, 4) for y in range(2, 4)}
        loops = grid_loops(block, 8, 8)
        self.assertEqual(len(loops), 1)
        self.assertEqual(area(loops[0]), 4)
        ring = {(x, y) for x in range(8) for y in range(8)} - {(x, y) for x in range(2, 6) for y in range(2, 6)}
        loops = sorted(grid_loops(ring, 8, 8), key=area)
        self.assertEqual([area(l) for l in loops], [16, 12 * 12])  # the hole, and the outer edge: two cells beyond the level on every side
        # (the level's edge repeats outward, so there is no outline along the picture's own border)

    def test_cutting_corners_makes_it_smaller_and_smooth(self):
        block = {(x, y) for x in range(2, 6) for y in range(2, 6)}
        sharp = skin_loops(block, 8, 8, smooth=0)
        round_ = skin_loops(block, 8, 8, smooth=3)
        self.assertEqual(area(sharp[0]), 16)
        self.assertTrue(12 < area(round_[0]) < 16)
        self.assertGreater(len(round_[0]), 30 * len(sharp[0]) // 4)

    def test_wobble_is_repeatable_and_bounded(self):
        block = {(x, y) for x in range(1, 7) for y in range(4, 8)}
        a = skin_loops(block, 8, 8, wobble=0.2, seed=3)
        self.assertEqual(a, skin_loops(block, 8, 8, wobble=0.2, seed=3))
        self.assertNotEqual(a, skin_loops(block, 8, 8, wobble=0.2, seed=4))
        flat = skin_loops(block, 8, 8, wobble=0.0, seed=3)
        for p, q in zip(a[0], flat[0]):
            self.assertLessEqual(abs(p[0] - q[0]) + abs(p[1] - q[1]), 0.2 * 2 + 1e-9)

    def test_mask_fills_inside_and_leaves_holes(self):
        ring = {(x, y) for x in range(8) for y in range(8)} - {(x, y) for x in range(2, 6) for y in range(2, 6)}
        mask = skin_mask(skin_loops(ring, 8, 8, smooth=0), (8 * 4, 8 * 4), 4)
        self.assertEqual(mask.getpixel((1, 1)), 255)   # in the ring
        self.assertEqual(mask.getpixel((16, 16)), 0)   # in the hole
        self.assertEqual(mask.getpixel((31, 31)), 255)  # at the picture's edge: still solid, nothing is rounded off there

    def test_path_data(self):
        d = path_data([[(0, 0), (1, 0), (1, 1)]], origin=(0, 0), scale=10)
        self.assertEqual(d, "M0.00 0.00 L10.00 0.00 L10.00 10.00 Z")


class RenderTests(unittest.TestCase):
    # a 4 x 2 block of A with a cell of air all round it (the green dots only make the level bigger than the block; art columns count from the def's own column, so the 4-space indent is 4 cells): the edge of the picture is not the block's edge
    LEVEL = DEFS + "def C -> fill.green, bg:\n\nlegend({'=': A})\ndef t(x, y):\n    ====\n    ====\n\nt(0, 1)\nplace(C, 3, 0)\nplace(C, 8, 3)\n"

    def render(self, extra, **kw):
        import os
        import tempfile

        lvl = run(self.LEVEL + extra)
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.gif")
            info = render_gif(lvl, out, tile_px=8, fps=4, play=False, log=lambda *a: None, **kw)
            with Image.open(out) as im:
                return info, im.convert("RGB")

    def test_a_layer_is_drawn_behind_the_world_and_in_front_for_over(self):
        # world: a green dot at cell (0, 0) and a red block elsewhere; layer pictures are blue (behind) and yellow (over)
        base = DEFS + "def C -> fill.green, bg:\n\ndef D -> fill.yellow, bg, size(2, 2):\n\nplace(C, 0, 0)\nplace(A, 3, 0)\n"
        import os
        import tempfile

        def render(extra):
            lvl = run(base + extra)
            with tempfile.TemporaryDirectory() as d:
                out = os.path.join(d, "o.gif")
                render_gif(lvl, out, tile_px=8, fps=4, play=False, log=lambda *a: None)
                with Image.open(out) as im:
                    return im.convert("RGB")

        self.assertEqual(render("").size, (32, 8))
        behind = render("with layer('b', parallax=0.5):\n    place(B, 0, 0)\n")
        self.assertEqual(behind.getpixel((12, 4)), (0, 0, 255))     # cell 1 is free: the layer shows
        self.assertEqual(behind.getpixel((4, 4)), (0, 128, 0))      # cell 0 is the world's green dot, in front of the layer
        over = render("with layer('o', parallax=1, over=True):\n    place(D, 0, 0)\n")
        self.assertEqual(over.getpixel((4, 4)), (255, 255, 0))      # an `over` layer is in front of the world

    def test_parallax_is_how_much_of_the_camera_a_layer_follows(self):
        from levelang.render.gif import layer_offset
        from levelang.runtime import Layer

        self.assertEqual(layer_offset(Layer("sky", 0), 100, 50), (0, 0))        # fixed to the screen
        self.assertEqual(layer_offset(Layer("far", 0.25), 100, 50), (25, 12.5))  # drifts slowly
        self.assertEqual(layer_offset(Layer("world", 1), 100, 50), (100, 50))     # moves with the world
        self.assertEqual(layer_offset(Layer("near", 1.5, parallax_y=0), 100, 50), (150, 0))

    def test_a_skin_hides_its_square_tiles_but_keeps_their_pictures(self):
        _, plain = self.render("")
        _, skinned = self.render("skin(A, smooth=3, corner=0.4)\n")
        self.assertEqual(plain.getpixel((8, 8)), (255, 0, 0))   # square tiles: the corner pixel of the block is solid red
        self.assertNotEqual(skinned.getpixel((8, 8)), (255, 0, 0))  # the skin cuts the corner...
        self.assertEqual(skinned.getpixel((20, 12)), (255, 0, 0))  # ...and shows the tile's own red inside

    def test_swim_takes_a_speed(self):
        from levelang.render.gif import _swim, _swim_period

        self.assertEqual(_swim(None), (6, 1.3))
        self.assertEqual(_swim(8), (8, 1.3))
        self.assertEqual(_swim((30, 2)), (30, 2))
        self.assertGreater(_swim_period((40, 1)), _swim_period((40, 2)))


if __name__ == "__main__":
    unittest.main()


class EditorProjectTests(unittest.TestCase):
    """levelang -> a Prowl2D editor project; loaded back with the editor's own model, which checks every part of it."""

    SRC = """
def 🟫 -> fill.sienna, solid:

def 🔺 -> fill.red, hazard:

def 🌿 -> fill.green, bg, sway(0.05):

def 🐟 -> fill.orange, bg, swim(4, 2):

def 🪸 -> fill.pink, bg, size(2, 2):

legend({'#': 🟫, '^': 🔺, 'w': 🌿, '.': None})
def t():
    ##########
    #........#
    #.^..w...#
    ##########

t()
place(🐟, 4, 1)
place(🪸, 6.5, 0.5, size=(3, 3))
with layer('far', parallax=0.25, haze=('#102030', 0.5), alpha=0.9):
    place(🪸, 2, 1, flip=True)
skin(🟫, wobble=0.1)
background('#80d0ff', '#001020')
"""

    def project(self, **kw):
        from levelang.export import to_project

        from prowl_editor.model import Project

        warnings = []
        data = to_project(run(self.SRC), "t", warn=warnings.append, **kw)
        return data, Project.from_json(data), warnings

    def test_it_loads_in_the_editor_and_the_grid_is_the_gameplay_tiles(self):
        data, p, _ = self.project()
        self.assertEqual(data["version"], 3)
        lv = p.levels[0]
        self.assertEqual((lv.width, lv.height), (10, 4))
        self.assertEqual(lv.get(0, 0), "🟫")
        self.assertEqual(lv.get(2, 2), "🔺")
        self.assertEqual(lv.get(5, 2), "")                        # the swaying plant is a picture, not a grid tile
        self.assertTrue(p.tiles["🟫"].solid and p.tiles["🟫"].hidden)   # covered by the skin: it collides, the image is what is drawn
        self.assertFalse(p.tiles["🔺"].hidden)
        self.assertEqual(sorted(p.tiles), ["🔺", "🟫"])

    def test_pictures_become_layers_with_the_same_positions_sizes_and_motion(self):
        _, p, _ = self.project()
        layers = {l["name"]: l for l in p.levels[0].layers}
        self.assertEqual(list(layers), ["water", "far", "decor", "skin"])          # by parallax, then the world's decoration, then the skin (over the decoration, under the grid)
        far = layers["far"]
        self.assertEqual((far["parallax"], far["alpha"], far["haze"]), ([0.25, 0.25], 0.9, ["#102030", 0.5]))
        self.assertEqual(far["items"][0]["flip"], True)
        kinds = sorted(((i["w"], i["h"], i["sway"], bool(i["swim"])) for i in layers["decor"]["items"]), key=repr)
        self.assertIn((1.0, 1.0, 0.05, False), kinds)                 # the plant sways
        self.assertIn((1.0, 1.0, None, True), kinds)                  # the fish swims
        self.assertIn((3.0, 3.0, None, False), kinds)                 # the coral is 3 cells wide (the world is whole cells: place(.., 6.5, 0.5) is cell 6, 0)
        coral = next(i for i in layers["decor"]["items"] if i["w"] == 3.0)
        self.assertEqual((coral["x"], coral["y"]), (6 - 4.0, 0.0))     # (the art starts 4 cells in: its indent, and the level's origin is its left)
        fish = next(i for i in layers["decor"]["items"] if i["swim"])
        self.assertEqual((fish["swim"], fish["x"], fish["y"]), ([4.0, 2.0], 0.0, 1.0))
        self.assertEqual(far["items"][0]["x"], 2 - 4.0)                # a layer's cells are the world's numbering, from the level's origin
        self.assertTrue(layers["water"]["parallax"] == [0.0, 1.0] and layers["skin"]["parallax"] == [1.0, 1.0])

    def test_images_are_valid_pngs_and_the_skin_covers_the_level(self):
        from prowl_editor.images import decode_rgba

        data, p, _ = self.project(ppc=16)
        self.assertEqual((p.images["skin"].width, p.images["skin"].height), (10 * 16, 4 * 16))
        w, h, rgba = decode_rgba(p.images["skin"].png)
        self.assertEqual(rgba[3], 255)                                # the wall is there at the top left...
        mid = ((2 * 16) * w + 5 * 16) * 4
        self.assertEqual(rgba[mid + 3], 0)                            # ...and the water inside is clear
        self.assertGreaterEqual(len(data["images"]), 4)

    def test_a_column_of_plants_carries_base(self):
        from levelang.export import to_project

        data = to_project(run(self.SRC.replace("place(🐟, 4, 1)", "place(🌿, 9, 1)")), "t", warn=lambda m: None)
        items = [i for l in data["levels"][0]["layers"] if l["name"] == "decor" for i in l["items"] if "sway" in i]
        self.assertEqual(sorted((i["y"], i.get("base", 0)) for i in items), [(1.0, 1.0), (2.0, 0.0)])

    def test_two_gameplay_tiles_in_one_cell_warn(self):
        from levelang.export import to_project

        warnings = []
        to_project(run(self.SRC + "place(🔺, 1, 1)\nplace(🟫, 1, 1)\n"), "t", warn=warnings.append)
        self.assertTrue(any("two gameplay tiles" in w for w in warnings))

    def test_the_empty_cell_is_never_a_tile(self):
        data, _, _ = self.project()
        self.assertNotIn(data["empty"], {t["emoji"] for t in data["tiles"]})

    def test_the_sample_reef_has_slimejumps_solid_cells_and_all_its_layers(self):
        from levelang import load_file

        from levelang.export import to_project
        from levelang.export import parse_level_cs
        from prowl_editor.model import Project

        from .test_prowl_export import SAMPLE, SAMPLES

        level, _ = load_file(str(SAMPLE / "level.lvl"))
        data = to_project(level, "reef", warn=lambda m: None)
        p = Project.from_json(data)
        lv = p.levels[0]
        solid = {(x, y) for y in range(lv.height) for x in range(lv.width) if lv.get(x, y) and p.tiles[lv.get(x, y)].solid}
        ref = parse_level_cs(SAMPLES[0].read_text(encoding="utf-8"))
        walls = {(int(x) + i, lv.height - 1 - (int(y) + j)) for x, y, w, h in ref["walls"] for i in range(int(w)) for j in range(int(h))}
        self.assertEqual(solid, walls)                                 # the physics the editor plays is SlimeJump's
        names = [l["name"] for l in lv.layers]
        for n in ("rays", "whales", "reef_far", "reef_mid", "kelp_near", "growth", "front", "skin", "water"):
            self.assertIn(n, names)
        self.assertLessEqual(len(p.images) + len(p.sprites), 63)
        self.assertEqual(sum(1 for t in p.tiles.values() if t.hidden), 2)   # sand and rock

    def test_export_project_command(self):
        import json
        import os
        import tempfile

        from levelang.cli import main

        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.lvl")
            with open(src, "w", encoding="utf-8") as f:
                f.write(self.SRC)
            self.assertEqual(main(["export-project", src, "--ppc", "8"]), 0)
            with open(os.path.join(d, "a.json"), encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["format"], "prowl2d-project")
