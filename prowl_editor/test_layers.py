"""Images, parallax layers and hidden tiles: the model (JSON, checks, undo) and parallax.py's plan. No engine and no display needed."""
import base64
import json
import unittest

from . import parallax
from .images import Image, ImageError, decode_rgba, encode_png, png_size
from .model import Level, Project, ProjectError, Sprite, TileDef, clean_layers

RED = encode_png(bytes([255, 0, 0, 255, 0, 255, 0, 128] * 2), 2, 2)       # 2 x 2: red, half-transparent green; twice


def item(**kw):
    d = {"image": "a", "x": 0, "y": 0, "w": 2, "h": 1}
    d.update(kw)
    return d


def layer(items, **kw):
    d = {"name": "l", "parallax": [0.5, 0.5], "items": items}
    d.update(kw)
    return d


class ImageTests(unittest.TestCase):
    def test_png_round_trip(self):
        self.assertEqual(png_size(RED), (2, 2))
        w, h, rgba = decode_rgba(RED)
        self.assertEqual((w, h), (2, 2))
        self.assertEqual(rgba[:8], bytes([255, 0, 0, 255, 0, 255, 0, 128]))

    def test_not_a_png(self):
        for bad in (b"", b"GIF89a" + bytes(40), RED[:20]):
            with self.assertRaises(ImageError):
                png_size(bad)
        with self.assertRaises(ImageError):
            encode_png(bytes(3), 2, 2)

    def test_json(self):
        img = Image("a", RED)
        self.assertEqual(Image.from_json(img.to_json(), "x").png, RED)
        with self.assertRaises(ImageError):
            Image.from_json({"name": "a", "png": "!!!"}, "x")


class LayerCheckTests(unittest.TestCase):
    IMAGES = {"a": Image("a", RED)}

    def test_defaults_and_ranges(self):
        (l,) = clean_layers([layer([item()], parallax=0.3)], self.IMAGES, "levels[0]")
        self.assertEqual((l["parallax"], l["over"], l["alpha"], l["haze"]), ([0.3, 0.3], False, 1.0, None))
        self.assertEqual(l["items"][0], {"image": "a", "x": 0.0, "y": 0.0, "w": 2.0, "h": 1.0, "flip": False, "sway": None, "bob": False, "swim": None, "base": 0.0})

    def test_what_it_refuses_says_where(self):
        for bad, text in ((layer([item(image="nope")]), "no image named"), (layer([item(w=0)]), "items[0].w"), (layer([item(swim=[3])]), "swim"),
                          (layer([], haze=["#zzz", 0.5]), "haze"), (layer([], haze=["#112233", 2]), "haze amount"), (layer([], alpha=1.5), "alpha"),
                          (layer([], parallax=[1]), "parallax"), (layer([item(x="a")]), "items[0].x"), ({"parallax": 1}, "name")):
            with self.assertRaises(ProjectError) as cm:
                clean_layers([bad], self.IMAGES, "levels[2]")
            self.assertIn(text, str(cm.exception))
            self.assertIn("levels[2].layers[0]", str(cm.exception))


class ProjectTests(unittest.TestCase):
    def project(self):
        p = Project("t")
        p.images["a"] = Image("a", RED)
        p.tiles["🟫"] = TileDef("🟫", "ground", "", True, hidden=True)
        lv = Level("L", 4, 2)
        lv.set(0, 1, "🟫")
        lv.layers = clean_layers([layer([item(swim=[4, 1], sway=0.05, bob=True)], haze=["#0d3b6e", 0.4], over=True, alpha=0.8)], p.images, "L")
        p.levels.append(lv)
        return p

    def test_round_trip_and_version(self):
        p = self.project()
        data = json.loads(json.dumps(p.to_json()))
        self.assertEqual(data["version"], 3)
        self.assertEqual(data["images"][0]["png"], base64.b64encode(RED).decode())
        q = Project.from_json(data)
        self.assertEqual(q.levels[0].layers, p.levels[0].layers)
        self.assertEqual(q.images["a"].png, RED)
        self.assertTrue(q.tiles["🟫"].hidden)
        self.assertEqual(q.to_json(), data)

    def test_a_project_without_them_is_still_version_one_and_has_no_new_keys(self):
        p = Project("t")
        p.tiles["🟫"] = TileDef("🟫", "ground", "", True)
        p.levels.append(Level("L", 2, 2))
        data = p.to_json()
        self.assertEqual(data["version"], 1)
        self.assertNotIn("images", data)
        self.assertNotIn("layers", data["levels"][0])
        self.assertNotIn("hidden", data["tiles"][0])

    def test_a_layer_naming_a_missing_image_is_refused_on_load(self):
        data = self.project().to_json()
        data["images"] = []
        with self.assertRaises(ProjectError):
            Project.from_json(data)

    def test_a_newer_version_than_this_editor_is_still_refused(self):
        data = self.project().to_json()
        data["version"] = 4
        with self.assertRaises(ProjectError):
            Project.from_json(data)


class PlanTests(unittest.TestCase):
    def level(self, *layers, height=10):
        lv = Level("L", 20, height)
        lv.layers = [dict(layer(it, **kw), over=kw.get("over", False)) for it, kw in layers]
        for l in lv.layers:
            l["alpha"], l["haze"] = l.get("alpha", 1.0), l.get("haze")
            for i in l["items"]:
                i.setdefault("flip", False), i.setdefault("sway", None), i.setdefault("bob", False), i.setdefault("swim", None)
        return lv

    def xs(self, verts):
        return [verts[i] for i in range(0, len(verts), 8)]

    def ys(self, verts):
        return [verts[i + 1] for i in range(0, len(verts), 8)]

    def test_a_quad_is_two_triangles_y_up(self):
        lv = self.level(([item(x=3, y=2, w=4, h=2)], {"parallax": [1, 1]}))
        (behind, over), = [parallax.plan(lv, 0, 0, 0)]
        self.assertEqual(over, [])
        name, v = behind[0]
        self.assertEqual((name, len(v) // 8), ("a", 6))
        self.assertEqual((min(self.xs(v)), max(self.xs(v))), (3, 7))
        self.assertEqual((min(self.ys(v)), max(self.ys(v))), (10 - 2 - 2, 10 - 2))   # y down 2..4 in a level 10 high: y up 6..8
        # u, v: the first vertex is the top left of the picture
        self.assertEqual((v[2], v[3]), (0.0, 0.0))

    def test_parallax_moves_a_layer_by_its_share_of_the_camera(self):
        for par, shift in ((0.0, 100.0), (0.25, 75.0), (1.0, 0.0), (1.5, -50.0)):
            lv = self.level(([item(x=5)], {"parallax": [par, par]}))
            v = parallax.plan(lv, 100.0, 40.0, 0)[0][0][1]
            self.assertAlmostEqual(min(self.xs(v)), 5 + shift)
        lv = self.level(([item(y=0, h=1)], {"parallax": [1, 0.5]}))
        v = parallax.plan(lv, 0, 8.0, 0)[0][0][1]
        self.assertAlmostEqual(max(self.ys(v)), 10 - (0 + 4.0))      # moved down 8 * (1 - 0.5)

    def test_far_to_near_and_over_apart(self):
        lv = self.level(([item(image="a")], {"parallax": [0.9, 0.9]}), ([item(image="b")], {"parallax": [0.1, 0.1]}),
                        ([item(image="c")], {"parallax": [0.5, 0.5]}), ([item(image="d")], {"parallax": [1.4, 1.4], "over": True}))
        behind, over = parallax.plan(lv, 0, 0, 0)
        self.assertEqual([b[0] for b in behind], ["b", "c", "a"])
        self.assertEqual([o[0] for o in over], ["d"])

    def test_same_picture_shares_a_batch(self):
        lv = self.level(([item(x=0), item(x=3), item(x=6, image="b")], {}))
        behind, _ = parallax.plan(lv, 0, 0, 0)
        self.assertEqual([(n, len(v) // 8) for n, v in behind], [("a", 12), ("b", 6)])

    def test_tint_is_haze_and_alpha(self):
        self.assertEqual(parallax.tint({"alpha": 0.5}), (1.0, 1.0, 1.0, 0.5))
        r, g, b, a = parallax.tint({"haze": ["#000000", 0.4], "alpha": 1.0})
        self.assertAlmostEqual(r, 0.6)
        lv = self.level(([item()], {"haze": ["#000000", 1.0], "alpha": 0.25}))
        v = parallax.plan(lv, 0, 0, 0)[0][0][1]
        self.assertEqual(tuple(v[4:8]), (0.0, 0.0, 0.0, 0.25))

    def test_flip_swaps_u(self):
        v = parallax.plan(self.level(([item(flip=True)], {})), 0, 0, 0)[0][0][1]
        self.assertEqual((v[2], v[10]), (1.0, 0.0))

    def test_swim_goes_there_and_back_and_turns_over(self):
        it = item(swim=[10, 1.0], x=0)
        period = parallax.swim_period(it["swim"])
        self.assertEqual(period, 2.4 * round(20 / 2.4))
        seen = []
        for k in range(0, 21):
            clock = period * k / 20.0
            dx, _, flipped = parallax.motion(dict(it, x=0, y=0), clock)
            seen.append((round(dx, 2), flipped))
        dxs = [d for d, _ in seen]
        self.assertAlmostEqual(max(dxs), 10.0, places=1)
        self.assertAlmostEqual(min(dxs), 0.0, places=1)
        self.assertEqual({f for d, f in seen[:10]}, {False})        # swimming out it faces the way it was drawn; coming back it is turned over
        self.assertEqual({f for d, f in seen[12:20]}, {True})

    def test_bob_is_a_fifth_of_a_cell(self):
        ys = [parallax.motion(item(bob=True), t / 10.0)[1] for t in range(0, 24)]
        self.assertAlmostEqual(max(ys), 0.22, places=2)
        self.assertAlmostEqual(min(ys), -0.22, places=2)

    def test_sway_cuts_strips_and_leans_the_top_more(self):
        it = item(x=0, y=0, w=1, h=10, sway=0.03)
        n = parallax.strips(10)
        self.assertEqual(n, 16)
        v = parallax.item_vertices(it, (0, 0), 10, 0.6, (1, 1, 1, 1))
        self.assertEqual(len(v) // 8, 6 * n)
        # the foot (the lowest line, v = 1) does not lean; the top (v = 0) leans by amp * 10 * sin(...)
        bottoms = [self.xs(v)[i] for i in range(len(v) // 8) if abs(v[i * 8 + 3] - 1.0) < 1e-6]
        self.assertTrue(bottoms and all(x in (0.0, 1.0) for x in bottoms))
        tops = [v[i * 8] for i in range(len(v) // 8) if v[i * 8 + 3] == 0.0]
        self.assertGreater(abs(tops[0]), 0.0)
        self.assertLessEqual(abs(tops[0]), 0.03 * 10 + 1e-9)
        self.assertAlmostEqual(tops[1] - tops[0], 1.0)             # a strip keeps its width

    def test_a_column_of_plants_leans_as_one(self):
        # two 1-cell plants, one on the other: the upper one starts leaning where the lower one stopped
        low = parallax.item_vertices(item(x=0, y=1, w=1, h=1, sway=0.05), (0, 0), 10, 0.6, (1, 1, 1, 1))
        high = parallax.item_vertices(item(x=0, y=0, w=1, h=1, sway=0.05, base=1), (0, 0), 10, 0.6, (1, 1, 1, 1))
        lean = lambda v, vv: [v[i * 8] for i in range(len(v) // 8) if v[i * 8 + 3] == vv and v[i * 8 + 2] == 0.0][0]      # x of a left corner at v
        self.assertAlmostEqual(lean(high, 1.0), lean(low, 0.0))        # the lower one's top is the upper one's foot

    def test_still_when_not_animating(self):
        it = item(swim=[10, 1.0], bob=True, sway=0.05)
        a = parallax.item_vertices(it, (0, 0), 10, 1.7, (1, 1, 1, 1), animate=False)
        b = parallax.item_vertices(it, (0, 0), 10, 5.2, (1, 1, 1, 1), animate=False)
        self.assertEqual(list(a), list(b))
        self.assertEqual(len(a) // 8, 6)

    def test_chunks_are_whole_triangles(self):
        import array
        v = array.array("f", [0.0] * (8 * 100))
        pieces = list(parallax.chunks(v, most=30))
        self.assertEqual([len(p) // 8 for p in pieces], [30, 30, 30, 10])


class FakeLib:
    """Records the renderer calls the viewport makes (the real library needs the translated engine, which needs a .NET SDK to build)."""

    def __init__(self):
        self.calls, self.next_texture = [], 1

    def gfx_texture(self, w, h, filt, ptr):
        self.calls.append(("texture", w, h, filt))
        self.next_texture += 1
        return self.next_texture - 1

    def gfx_triangles(self, ptr, count, tex):
        self.calls.append(("triangles", count, tex))
        return count

    def gfx_draw(self, ptr, n):
        self.calls.append(("draw", n))

    def __getattr__(self, name):
        if name.startswith("gfx_"):
            return lambda *a: self.calls.append((name[4:],) + tuple(a)) or 0
        raise AttributeError(name)


class FakeEngine:
    started = True

    def __init__(self):
        self.lib = FakeLib()

    def effect(self, *a):
        pass


class ViewportDrawTests(unittest.TestCase):
    def viewport(self, hidden=False):
        from .engine import Viewport

        p = Project("t")
        p.images["a"] = Image("a", RED)
        p.images["b"] = Image("b", RED)
        idx = p.palette.add("r", "red", (255, 0, 0))
        spr = p.add_sprite(Sprite("ground", 1, 1))
        spr.set(0, 0, 0, idx)
        p.tiles["🟫"] = TileDef("🟫", "ground", "ground", True, hidden=hidden)
        lv = Level("L", 4, 2)
        lv.set(0, 1, "🟫")
        lv.layers = clean_layers([layer([item(image="a")], parallax=0.2), layer([item(image="b")], parallax=1.4, over=True)], p.images, "L")
        p.levels.append(lv)
        vp = Viewport(FakeEngine(), p, 400, 200)
        vp.level = lv
        vp.cx, vp.cy, vp.half = 2.0, 1.0, 1.0
        return vp

    def test_layers_are_drawn_behind_and_over_the_tiles_with_smooth_textures(self):
        vp = self.viewport()
        vp._draw()
        calls = vp.engine.lib.calls
        tri = [c for c in calls if c[0] == "triangles"]
        self.assertEqual([c[1] for c in tri], [6, 6, 6])                 # behind layer, the one tile, the over layer
        tex = [c for c in calls if c[0] == "texture"]
        self.assertEqual(sorted(t[3] for t in tex), [0, 1, 1])           # the sprite is nearest, both images linear
        self.assertEqual(tri[1][2], 1)                                   # (the tile's sprite was uploaded first: it is texture 1)
        self.assertNotEqual(tri[0][2], tri[2][2])
        self.assertLess(calls.index(tri[0]), calls.index(tri[1]))
        self.assertLess(calls.index(tri[1]), calls.index(tri[2]))

    def test_a_hidden_tile_is_not_drawn(self):
        vp = self.viewport(hidden=True)
        vp._draw()
        tri = [c for c in vp.engine.lib.calls if c[0] == "triangles"]
        self.assertEqual([c[1] for c in tri], [6, 6])                    # the two layers only

    def test_a_missing_image_or_a_full_texture_table_skips_the_item_and_carries_on(self):
        vp = self.viewport()
        vp.engine.lib.gfx_texture = lambda *a: 0
        vp._draw()
        self.assertEqual([c for c in vp.engine.lib.calls if c[0] == "triangles"], [])


class TilePanelTests(unittest.TestCase):
    def test_editing_a_tile_keeps_hidden(self):
        from .gui import Studio

        p = Project("t")
        p.tiles["🟫"] = TileDef("🟫", "ground", "", True, hidden=True)
        s = Studio(p)
        s.edit_tile("🟫", "🟫", "ground", "", True, False, False, True)
        self.assertTrue(s.project.tiles["🟫"].hidden)
        s.edit_tile("🟫", "🟫", "ground", "", True, False, False, False)
        self.assertFalse(s.project.tiles["🟫"].hidden)


if __name__ == "__main__":
    unittest.main()
