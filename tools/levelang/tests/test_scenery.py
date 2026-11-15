"""The game-side layers: SceneryData.cs (baked by `levelang export-scenery`) and Scenery.cs (which draws it).

No C# is compiled here (there is no dotnet in the test environment), so what is checked is what can be: the generated file is current and says what the data says, the atlas decodes to the
pictures it was made from, and a line-by-line transcription of Scenery.cs's Item() gives the vertices prowl_editor.parallax gives. A guard checks the transcription still matches the C# field order.
"""
import math
import pathlib
import re
import unittest

from . import _common  # noqa: F401  (puts the repo on sys.path)
from ._common import REPO

SAMPLE = REPO / "Samples" / "SlimeJumpLevelang"


def _ints(text, name):
    body = re.search(r"public static int\[\] %s = \{(.*?)\n    \};" % name, text, re.S).group(1)
    return [int(v) for v in re.findall(r"-?\d+", body)]


def _floats(text, name):
    body = re.search(r"public static float\[\] %s = \{(.*?)\n    \};" % name, text, re.S).group(1)
    return [float(v) for v in re.findall(r"-?\d+\.\d+", body)]


def cs_item(items, o, off, clock, tint, height):
    """Scenery.cs Item(), line by line: the vertices (x, y, u, v, r, g, b, a) of one item."""
    u0, v0, u1, v1, x, y, w, h, flip, swim_n, swim_period, bob, sway, base_up, phase, sway_phase = items[o:o + 16]
    x += off[0]
    y += off[1]
    flipped = flip > 0.5
    frac = lambda v: v - float(int(v))
    if swim_n > 0.0:
        t = frac(clock / swim_period + phase)
        x += (1.0 - abs(2.0 * t - 1.0)) * swim_n
        if t > 0.5:
            flipped = not flipped
    if bob > 0.5:
        y += math.sin(6.2831853 * frac(clock / 2.4 + phase)) * 0.22
    u_left, u_right = (u1, u0) if flipped else (u0, u1)
    n, u = 1, 0.0
    if sway >= 0.0:
        want = h * 2.0
        n = int(want)
        if float(n) < want:
            n += 1
        n = max(4, min(16, n))
        u = frac(clock / 2.4 + sway_phase)
    out = []
    lean = lambda above: sway * above * math.sin(6.2831853 * u - 0.9 * above)
    for k in range(n):
        va, vb = k / float(n), (k + 1) / float(n)
        la = lean(base_up + h * (1.0 - va)) if sway >= 0.0 else 0.0
        lb = lean(base_up + h * (1.0 - vb)) if sway >= 0.0 else 0.0
        tlx, trx, ty = x + la, x + w + la, height - (y + h * va)
        blx, brx, by = x + lb, x + w + lb, height - (y + h * vb)
        tv, bv = v0 + (v1 - v0) * va, v0 + (v1 - v0) * vb
        r, g, b, a = tint
        for px, py, pu, pv in ((tlx, ty, u_left, tv), (trx, ty, u_right, tv), (brx, by, u_right, bv),
                               (tlx, ty, u_left, tv), (brx, by, u_right, bv), (blx, by, u_left, bv)):
            out.append((px, py, pu, pv, r, g, b, a))
    return out


@unittest.skipUnless((SAMPLE / "level.lvl").exists(), "needs Samples/SlimeJumpLevelang")
class SceneryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from levelang import load_file
        from levelang.export.scenery import scenery, to_csharp

        cls.level, _ = load_file(str(SAMPLE / "level.lvl"))
        cls.data = scenery(cls.level, "level", warn=lambda m: None)
        cls.text = to_csharp(cls.data, "level.lvl")

    def test_scenery_data_is_current(self):
        """Edit level.lvl, then regenerate: python3 tools/levelang export-scenery Samples/SlimeJumpLevelang/level.lvl"""
        self.assertEqual((SAMPLE / "SceneryData.cs").read_text(encoding="utf-8"), self.text)

    def test_the_file_says_what_the_data_says(self):
        d, t = self.data, self.text
        self.assertEqual(_ints(t, "Runs"), d["runs"])
        self.assertEqual(_ints(t, "Palette"), [c for rgba in d["palette"] for c in rgba])
        from levelang.export.scenery import ITEM_FIELDS, LAYER_FIELDS

        self.assertEqual(len(_floats(t, "Items")), len(d["items"]) * len(ITEM_FIELDS))
        self.assertEqual(len(_floats(t, "Layers")), len(d["layers"]) * len(LAYER_FIELDS))
        for name, n in (("LayerCount", len(d["layers"])), ("ItemCount", len(d["items"])), ("RunCount", len(d["runs"])), ("AtlasW", d["atlas_w"]), ("AtlasH", d["atlas_h"])):
            self.assertIn("public const int %s = %d;" % (name, n), t)

    def test_atlas_roundtrips_and_is_small_enough(self):
        from levelang.export.scenery import decode

        d = self.data
        self.assertLessEqual(d["atlas_w"], 8192)
        self.assertLessEqual(d["atlas_h"], 8192)
        back = decode(d["palette"], d["runs"], d["atlas_w"], d["atlas_h"])
        self.assertEqual(back.size, d["atlas"].size)
        self.assertEqual(sum(r // 256 for r in d["runs"]), d["atlas_w"] * d["atlas_h"])
        # a palette is a loss, but air stays air, and solid ink does not vanish
        a_src, a_back = d["atlas"].getchannel("A"), back.getchannel("A")
        air_filled = sum(1 for p, q in zip(a_src.tobytes(), a_back.tobytes()) if p == 0 and q != 0)
        ink_lost = sum(1 for p, q in zip(a_src.tobytes(), a_back.tobytes()) if p >= 200 and q < 64)
        self.assertEqual(air_filled, 0)
        self.assertEqual(ink_lost, 0)

    def test_every_item_points_inside_the_atlas(self):
        for it in self.data["items"]:
            for k in ("u0", "u1", "v0", "v1"):
                self.assertTrue(0.0 <= it[k] <= 1.0, (k, it))
            self.assertLessEqual(it["u0"], it["u1"])      # equal for a picture one pixel wide (the water)
            self.assertLessEqual(it["v0"], it["v1"])
        self.assertEqual(sum(l["count"] for l in self.data["layers"]), len(self.data["items"]))
        pars = [l["parallax_x"] for l in self.data["layers"]]
        self.assertEqual(pars, sorted(pars), "layers are stored far to near")

    def test_scenery_cs_reads_the_fields_in_the_order_the_data_is_written(self):
        """The transcription above (and the C#) read item k of a record at it[o + k]; check the C# still does."""
        src = (SAMPLE / "Scenery.cs").read_text(encoding="utf-8")
        want = {0: "u0", 1: "v0", 2: "u1", 3: "v1", 4: "x", 5: "y", 6: "w", 7: "h", 8: "flipped", 9: "swimN", 10: "swimPeriod", 11: "bob", 12: "sway", 13: "baseUp", 14: "phase", 15: "swayPhase"}
        got = {k: v for k, v in want.items() if re.search(r"(?:float|bool) %s = it\[o%s\]" % (v, "" if k == 0 else r" \+ %d" % k), src)}
        self.assertEqual(got, want)
        from levelang.export.scenery import ITEM_FIELDS, LAYER_FIELDS

        self.assertEqual(len(ITEM_FIELDS), 16)
        self.assertIn("public const int ItemStride = 16;", self.text)
        for k, name in enumerate(LAYER_FIELDS):
            self.assertRegex(src, r"Layers\[lb%s\]" % ("" if k == 0 else r" \+ %d" % k))

    def test_the_c_sharp_draws_what_the_editor_draws(self):
        """A transcription of Scenery.Item against prowl_editor.parallax.item_vertices, for every item, at several clocks and camera positions."""
        from prowl_editor import parallax as par
        from levelang.export.scenery import ITEM_FIELDS, LAYER_FIELDS, build_atlas  # noqa: F401
        from levelang.export.prowl_project import to_project

        project = to_project(self.level, "level", warn=lambda m: None)
        lv = project["levels"][0]
        height = self.data["level_height"]
        flat = [it[k] for it in self.data["items"] for k in ITEM_FIELDS]
        uv = {}
        n = 0
        checked = 0
        layers = sorted(lv["layers"], key=lambda l: l["parallax"][0])
        for clock, cam in ((0.0, (0.0, 0.0)), (1.37, (12.5, 0.0)), (5.9, (30.0, 1.0))):
            n = 0
            for layer in layers:
                px, py = layer["parallax"]
                off = (cam[0] * (1.0 - px), cam[1] * (1.0 - py))
                tint = par.tint(layer)
                for item in layer["items"]:
                    rec = self.data["items"][n]
                    want = par.item_vertices(item, off, height, clock, tint)
                    got = cs_item(flat, n * 16, off, clock, tint, height)
                    self.assertEqual(len(want), len(got) * 8, (layer["name"], item["image"]))
                    for i, vert in enumerate(got):
                        for j in range(8):
                            w = want[i * 8 + j]
                            g = vert[j]
                            if j in (2, 3):             # u, v: the editor's are 0..1 of the picture, the game's are inside the atlas rectangle
                                w = (rec["u0"] + (rec["u1"] - rec["u0"]) * w) if j == 2 else (rec["v0"] + (rec["v1"] - rec["v0"]) * w)
                            self.assertAlmostEqual(w, g, places=3, msg=(layer["name"], item["image"], i, j, clock))
                    n += 1
                    checked += 1
        self.assertGreater(checked, 300)
        self.assertEqual(n, len(self.data["items"]))


if __name__ == "__main__":
    unittest.main()
