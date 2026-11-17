"""Samples/SlimeJumpRPG: the generated files match level.lvl, and the people are real kaomojilang drawings."""
import pathlib
import unittest

from ._common import REPO
from levelang import kmj, load_file
from levelang.export import to_level_cs, to_story_cs

SAMPLE = REPO / "Samples" / "SlimeJumpRPG"
LAYERS_FROM = str(REPO / "Samples" / "SlimeJump" / "Level.cs")


class RpgSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.level, _ = load_file(str(SAMPLE / "level.lvl"), 1)

    def test_level_cs_is_up_to_date(self):
        """Regenerate: python3 tools/levelang export-cs Samples/SlimeJumpRPG/level.lvl -o Samples/SlimeJumpRPG/Level.cs --layers-from Samples/SlimeJump/Level.cs"""
        text, _ = to_level_cs(self.level, "level.lvl", LAYERS_FROM)
        self.assertEqual((SAMPLE / "Level.cs").read_text(encoding="utf-8"), text)

    def test_story_cs_is_up_to_date(self):
        """Regenerate: python3 tools/levelang export-story Samples/SlimeJumpRPG/level.lvl -o Samples/SlimeJumpRPG/Story.cs"""
        self.assertEqual((SAMPLE / "Story.cs").read_text(encoding="utf-8"), to_story_cs(self.level, "level.lvl"))

    def test_the_story_fits_the_level(self):
        goal = self.level.find("goal")[0]
        xs = [c["x"] for c in self.level.captions]
        self.assertGreater(len(xs), 20)
        self.assertTrue(all(0 <= x <= goal.x + 0.5 for x in xs), "a line after the goal is never reached")
        titles = [c["text"] for c in self.level.captions if c["kind"] == "title"]
        self.assertEqual(len(titles), len(set(titles)))
        whos = {c.get("who") for c in self.level.captions if c["kind"] == "say"}
        self.assertTrue({"Slime", "Gelly", "Sir Croak", "Ember"} <= whos)

    def test_gameplay_things(self):
        self.assertEqual(len(self.level.find("spawn")), 1)
        self.assertEqual(len(self.level.find("goal")), 1)
        self.assertGreaterEqual(len(self.level.find("item")), 8)           # hearts
        self.assertGreaterEqual(len(self.level.find("save")), 5)           # flowers
        self.assertGreaterEqual(len(self.level.find("crumbly")), 20)       # the bridge
        self.assertEqual(len(self.level.find("shooter")) if False else sum(1 for p in self.level.placements if "shooter" in p.tile.params), 1)

    def test_every_character_is_drawn_by_kaomojilang(self):
        try:
            kmj.kaomojilang()
        except Exception as e:  # pragma: no cover
            self.skipTest(str(e))
        drawn = {p.tile.name: p.tile for p in self.level.placements if p.tile.svg}
        for p in (p for l in self.level.layers for p in l.placements):
            drawn.setdefault(p.tile.name, p.tile)
        names = {"tile_LARGE_GREEN_CIRCLE", "tile_FROG_FACE", "tile_BAT", "tile_DRAGON_FACE", "tile_GIRL", "tile_BRIDE_WITH_VEIL"}
        for n in names:
            self.assertIn(n, drawn, n)
            self.assertIn("<svg", drawn[n].svg)
        animated = [t for t in drawn.values() if t.frames and len(t.frames) > 1]
        self.assertGreaterEqual(len(animated), 8)                           # slime, frog, bat, dragon, Gelly x3, hearts, flowers...

    def test_the_kmj_files_run(self):
        k = kmj.kaomojilang()
        for name, anims in {"slime": ["idle", "hop", "love", "happy", "sad", "scared"], "gelly": ["idle", "wave", "blush", "love", "bride", "bride_love", "cry"],
                            "frog": ["croak", "blink", "glare"], "bat": ["wings"], "dragon": ["glare"], "props": ["gem", "bloom", "wedding", "tree_sway"]}.items():
            prog = k.run_file(str(SAMPLE / "kmj" / f"{name}.kmj"))
            for a in anims:
                self.assertGreater(len(prog[a]), 1, f"{name}.{a}")


if __name__ == "__main__":
    unittest.main()
