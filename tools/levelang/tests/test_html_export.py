"""export-html: scenes as ONE self-contained page (camera, bubbles, scene switches)."""
import json
import os
import re
import tempfile
import unittest

from ._common import REPO, run
from levelang.export import to_html

BASE = '''
def S -> fill.green, solid:

def A -> fill.red:

for cx in range(12):
    place(S, cx, 6)
place(S, 0, 0)
'''


def lvl(name, extra="", nxt=None):
    n = f', next="{nxt}"' if nxt else ""
    return run(BASE + f'scene("{name}", seconds=4, fps=8, view=(8, 6){n})\nactor("pip", A, 1, 5)\nmove("pip", 1, 3, 6, 5, hop=1)\ncam(0, 4, 3)\n' + extra)


def page(levels, **kw):
    return to_html(levels, warn=lambda m: None, **kw)


def show_of(html):
    return json.loads(re.search(r'<script id="show" type="application/json">(.*?)</script>', html, re.S).group(1).replace("<\\/", "</"))


class HtmlExportTests(unittest.TestCase):
    def test_one_file_with_everything_inline(self):
        h = page([lvl("one", 'line(1, "Hello", who="Pip")\ncard(0, "Title", "sub")\nfade(0, 1, 1, 0)')])
        self.assertTrue(h.startswith("<!DOCTYPE html>"))
        self.assertNotRegex(h, r'(?:src|href)="(?!#|data:)')       # nothing is fetched
        d = show_of(h)["scenes"][0]
        self.assertEqual(d["name"], "one")
        self.assertEqual(d["captions"][0]["who"], "Pip")
        self.assertEqual(d["actors"][0]["moves"][0][:2], [1.0, 3.0])
        self.assertIn("function render", h)

    def test_next_and_order(self):
        h = page([lvl("one", nxt="two"), lvl("two")])
        s = show_of(h)["scenes"]
        self.assertEqual([x["name"] for x in s], ["one", "two"])
        self.assertEqual(s[0]["next"], "two")
        self.assertIsNone(s[1]["next"])

    def test_scene_next_in_dict(self):
        self.assertEqual(lvl("one", nxt="x").scene.to_dict()["next"], "x")
        self.assertNotIn("next", lvl("one").scene.to_dict())

    def test_errors(self):
        with self.assertRaisesRegex(ValueError, "next='nope'"):
            page([lvl("one", nxt="nope")])
        with self.assertRaisesRegex(ValueError, "two scenes are called"):
            page([lvl("one"), lvl("one")])
        with self.assertRaisesRegex(ValueError, "no scene"):
            page([run(BASE)])
        with self.assertRaisesRegex(ValueError, "names no scene"):
            page([lvl("one")], audio={"zzz": __file__})

    def test_audio_is_embedded(self):
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"ID3fake")
        try:
            h = page([lvl("one")], audio={"one": f.name})
        finally:
            os.unlink(f.name)
        self.assertIn("data:audio/mpeg;base64,", h)
        self.assertEqual(show_of(h)["audio"], {"one": 0})

    def test_unsupported_fx_warns(self):
        msgs = []
        to_html([lvl("one", 'fx(1, 2, "posterize")')], warn=msgs.append)
        self.assertTrue(any("posterize" in m for m in msgs))

    def test_script_closing_tag_in_text_is_escaped(self):
        h = page([lvl("one", 'line(1, "a</script>b", who="Pip")')])
        self.assertEqual(show_of(h)["scenes"][0]["captions"][0]["text"], "a</script>b")
        self.assertEqual(h.count("</script>"), 3)     # the data, the director, the player

    def test_sample_intro(self):
        sample = REPO / "Samples" / "SlimeJumpLoveStory"
        from levelang import load_file
        if not (sample / "intro.lvl").exists():
            self.skipTest("sample missing")
        cwd = os.getcwd()
        os.chdir(sample)
        try:
            h = page([load_file("intro.lvl")[0]])
        finally:
            os.chdir(cwd)
        self.assertIn('class="lay"', h)
        self.assertGreater(len(show_of(h)["scenes"][0]["captions"]), 5)


if __name__ == "__main__":
    unittest.main()


class ChaosTests(unittest.TestCase):
    SRC = BASE + '''
def P -> fill.red:

def Q -> svgs("x_*.svg", fps=4):

scene("c", seconds=4, view=(8, 6))
actor("pip", A, 1, 5)
chaos(shots=[(4, 3, 0.8)], singer=(3, 4), band={"guitar": A}, pit=(2, 9, 6), crowd=[A], lights=[(2, 1)], floor=6, rate=2.0)
'''

    def test_chaos_in_the_page(self):
        sc = run(self.SRC.replace('def Q -> svgs("x_*.svg", fps=4):\n', "")).scene
        self.assertEqual(sc.chaos["rate"], 2.0)
        h = page([run(self.SRC.replace('def Q -> svgs("x_*.svg", fps=4):\n', ""))])
        ch = show_of(h)["scenes"][0]["chaos"]
        self.assertEqual(ch["pit"], [2, 9, 6])               # (the stage starts at 0, 0)
        self.assertEqual(len(ch["crowd"]), 1)
        self.assertIn("guitar", ch["band"])
        self.assertIn("window.Chaos", h)
        self.assertIn("#grid=", h)

    def test_no_chaos_without_the_call(self):
        self.assertIsNone(show_of(page([lvl("one")]))["scenes"][0]["chaos"])
