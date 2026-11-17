"""say() / title(): the story lines of a level, their Story.cs and their place in the preview GIF."""
import os
import tempfile
import unittest

from ._common import run
from levelang.export import to_story_cs

SRC = '''
def A -> fill.red, solid:

def S -> fill.green, spawn:

def G -> fill.gold, goal:

place(S, 0, 0)
place(A, 3, 1)
place(G, 9, 0)
say(5, "Second, with a \\"quote\\"", who="Gelly")
title(0, "Chapter 1", "The start")
say(2, "First line", who="Slime")
'''


class StoryTests(unittest.TestCase):
    def test_lines_are_collected(self):
        lvl = run(SRC)
        self.assertEqual([c["kind"] for c in lvl.captions], ["say", "title", "say"])
        self.assertEqual(lvl.to_dict()["captions"][0]["who"], "Gelly")

    def test_story_cs_is_sorted_and_escaped(self):
        cs = to_story_cs(run(SRC), "x.lvl")
        self.assertIn("public const int Count = 3;", cs)
        self.assertLess(cs.index("== Chapter 1: The start =="), cs.index("Slime: First line"))
        self.assertLess(cs.index("Slime: First line"), cs.index('Gelly: Second, with a \\"quote\\"'))
        self.assertIn("if (i == 2) return 5f;", cs)
        self.assertNotIn("switch", cs)          # the C build's subset: if chains

    def test_no_story_gives_an_empty_class(self):
        cs = to_story_cs(run("def A -> fill.red, solid:\n\nplace(A, 0, 0)\n"))
        self.assertIn("Count = 0;", cs)

    def test_the_gif_waits_for_every_line(self):
        try:
            import cairosvg  # noqa: F401
        except Exception:
            self.skipTest("cairosvg missing")
        from levelang.render.gif import render_gif
        lvl = run(SRC)
        with tempfile.TemporaryDirectory() as d:
            quiet = run(SRC.replace("say(", "(lambda *a, **k: None)(").replace("title(", "(lambda *a, **k: None)("))
            a = render_gif(quiet, os.path.join(d, "a.gif"), fps=4, tile_px=8, log=lambda *a: None)
            b = render_gif(lvl, os.path.join(d, "b.gif"), fps=4, tile_px=8, log=lambda *a: None)
        self.assertGreaterEqual(b["seconds"] - a["seconds"], 3.5 + 3.5 + 4.5 - 0.5)   # the bot stays for each line


if __name__ == "__main__":
    unittest.main()
