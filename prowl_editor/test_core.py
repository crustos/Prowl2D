"""Tests of the model and the text formats (no Qt, no engine):  python3 -m unittest prowl_editor.test_core   (or: python3 prowl.py --selftest)"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from . import fx
from .fxdefs import BY_ID, EFFECTS, PARAM_FLOATS
from .asciiart import (emoji_for_name, export_level, export_levels, export_sprite, export_sprites, import_levels, import_sprites, level_from_text,
                       level_to_text, natural_name, parse_level_text, scan_sprite_text, split_graphemes)
from .demo import make_demo_project
from . import languages, scriptbuild
from .model import Level, Palette, Project, ProjectError, ScriptFile, Sprite, TileDef, parse_color


def snapshot(project):
    """Everything about a project's sprites that matters to a viewer: each frame's pixels as RGBA, so key letters and index order may differ."""
    return {s.name: (s.width, s.height, s.fps, [s.rgba(project.palette, i) for i in range(len(s.frames))]) for s in project.sprites}


class Graphemes(unittest.TestCase):
    def test_emoji_sequences_are_one_cell(self):
        text = "\U0001f9f1\U0001fa99\U0001f468‍\U0001f469‍\U0001f467\U0001f1fa\U0001f1f8❤️#️⃣A"
        self.assertEqual(len(split_graphemes(text)), 7)

    def test_skin_tone_is_part_of_the_emoji(self):
        self.assertEqual(split_graphemes("\U0001f44d\U0001f3fd\U0001f44d"), ["\U0001f44d\U0001f3fd", "\U0001f44d"])

    def test_natural_names(self):
        self.assertEqual(natural_name("\U0001f9f1"), "brick")
        self.assertEqual(natural_name("\U0001f333"), "deciduous tree")
        self.assertEqual(natural_name("\U0001f1fa\U0001f1f8"), "flag us")
        self.assertEqual(emoji_for_name("Brick"), "\U0001f9f1")
        self.assertIsNone(emoji_for_name("no such emoji name"))


class Palette_(unittest.TestCase):
    def test_transparent_is_index_zero_and_keys_are_unique(self):
        p = Palette()
        self.assertEqual(p.key_of(0), ".")
        self.assertIsNone(p.rgba(0)[3] or None)
        with self.assertRaises(ProjectError):
            p.add("K", "again", (1, 2, 3))
        with self.assertRaises(ProjectError):
            p.add(" ", "bad", (1, 2, 3))
        with self.assertRaises(ProjectError):
            p.add("ab", "bad", (1, 2, 3))
        self.assertEqual(p.add("#", "hash", (1, 2, 3)), len(p) - 1)       # '#' is an ordinary key: ASCII art uses it a lot

    def test_recolouring_an_index_changes_every_frame_that_uses_it(self):
        """The blink: eye pixels use one index, and one colour change turns them all."""
        p = Project("t")
        eye = p.palette.add("E", "eye", (255, 255, 255))
        s = Sprite("face", 4, 2)
        s.frames = [bytearray([eye, 0, 0, eye, 0, 0, 0, 0]), bytearray([0, eye, 0, 0, 0, 0, eye, 0])]
        p.add_sprite(s)
        before = [s.rgba(p.palette, i) for i in range(2)]
        p.palette.set_color(eye, (10, 20, 30))
        after = [s.rgba(p.palette, i) for i in range(2)]
        for b, a in zip(before, after):
            self.assertEqual(len(b), len(a))
            self.assertNotEqual(b, a)
            self.assertEqual(sorted(set(a[i:i + 4] for i in range(0, len(a), 4))), sorted([bytes((10, 20, 30, 255)), bytes((0, 0, 0, 0))]))

    def test_removing_and_moving_entries_keeps_every_pixel_colour(self):
        p = make_demo_project()
        want = snapshot(p)
        p.move_palette_entry(3, 9)
        p.move_palette_entry(9, 2)
        self.assertEqual(snapshot(p), want)
        victim = p.palette.index_of("T")
        used_before = {n for s in p.sprites for f in s.frames for n in f}
        p.remove_palette_entry(victim)
        # the pixels of the removed colour are transparent now, and nothing else changed colour
        grass = p.sprite("grass")
        self.assertIn(0, grass.frames[0])
        self.assertEqual(p.sprite("brick").rgba(p.palette, 0), want["brick"][3][0])
        self.assertTrue(victim in used_before)


class SpriteText(unittest.TestCase):
    def test_export_then_import_is_lossless(self):
        a = make_demo_project()
        text = export_sprites(a)
        b = Project("b")
        b.palette = Palette(with_defaults=False)               # an empty palette: the header alone must bring the colours back
        import_sprites(text, b)
        self.assertEqual(snapshot(a), snapshot(b))
        self.assertEqual([s.name for s in a.sprites], [s.name for s in b.sprites])

    def test_frames_are_blank_line_separated_and_fps_survives(self):
        p = make_demo_project()
        coin = p.sprite("coin")
        self.assertEqual(len(coin.frames), 4)
        text = export_sprite(coin, p.palette)
        self.assertEqual(text.count("\n\n"), 3)
        q = Project("q")
        import_sprites(text, q)
        self.assertEqual(q.sprite("coin").fps, 6.0)
        self.assertEqual(len(q.sprite("coin").frames), 4)

    def test_plain_ascii_art_imports_with_a_mapping(self):
        art = "..##..\n.#@@#.\n..##..\n"
        p = Project("p")
        blocks, unknown = scan_sprite_text(art, p.palette)
        self.assertEqual(sorted(unknown), ["#", "@"])
        sprites, added = import_sprites(art, p, {"#": (200, 0, 0), "@": None})
        s = sprites[0]
        self.assertEqual((s.width, s.height), (6, 3))
        self.assertEqual(s.get(0, 2, 0), p.palette.index_of("#"))
        self.assertEqual(s.get(0, 2, 1), 0)                               # '@' was mapped to transparent
        self.assertEqual(p.palette.entries[p.palette.index_of("#")].rgb, (200, 0, 0))
        self.assertEqual(added, ["#"])
        self.assertIsNone(p.palette.index_of("@"))                        # and a transparent choice adds nothing to the palette

    def test_a_space_is_transparent_and_ragged_rows_are_padded(self):
        p = Project("p")
        (s,), _ = import_sprites("R  R\nRR\nR", p)
        self.assertEqual((s.width, s.height), (4, 3))
        self.assertEqual(s.rows(p.palette, 0), ["R..R", "RR..", "R..."])

    def test_importing_never_recolours_the_existing_palette(self):
        p = Project("p")
        yellow = p.palette.entries[p.palette.index_of("Y")].rgb
        (s,), added = import_sprites("# sprite: x\n# palette: Y=#0000ff\nYY\n", p)
        self.assertEqual(p.palette.entries[p.palette.index_of("Y")].rgb, yellow)     # the project's Y is still its Y
        self.assertEqual(len(added), 1)                                              # the file's blue Y is a new entry under a free key
        self.assertEqual(s.rgba(p.palette, 0)[:4], bytes((0, 0, 255, 255)))

    def test_header_lines_need_their_keyword(self):
        # a row that merely starts with '#' is art, not a header
        p = Project("p")
        (s,), added = import_sprites("# #\n#  \n", p)
        self.assertEqual((s.width, s.height), (3, 2))
        self.assertEqual(added, ["#"])

    def test_errors_say_where(self):
        with self.assertRaises(ProjectError) as e:
            import_sprites("# palette: K=notacolour\nKK\n", Project("p"))
        self.assertIn("line 1", str(e.exception))
        with self.assertRaises(ProjectError):
            import_sprites("\n\n", Project("p"))


class LevelText(unittest.TestCase):
    def test_demo_level_round_trips_through_text(self):
        a = make_demo_project()
        text = export_levels(a)
        b = Project("b")
        b.sprites = [s for s in a.sprites]
        import_levels(text, b)
        la, lb = a.levels[0], b.levels[0]
        self.assertEqual((la.width, la.height, la.cells), (lb.width, lb.height, lb.cells))
        self.assertEqual({k: (t.name, t.solid) for k, t in a.tiles.items()}, {k: (t.name, t.solid) for k, t in b.tiles.items()})

    def test_legend_and_header_are_readable(self):
        a = make_demo_project()
        lines = export_level(a.levels[0], a).splitlines()
        self.assertEqual(lines[0], "# level: first steps")
        self.assertIn("# \U0001f9f1 = brick (solid)", lines)
        self.assertIn("# \U0001fa99 = coin", lines)
        self.assertTrue(all(len(split_graphemes(l)) == 24 for l in lines if not l.startswith("#")))

    def test_tiles_take_their_sprite_by_name(self):
        p = make_demo_project()
        self.assertEqual(p.sprite_for_tile(p.tiles["\U0001f9f1"]).name, "brick")
        # an emoji whose natural name is a sprite's name needs no mapping at all
        q = Project("q")
        import_sprites("# sprite: brick\nRR\nRR\n", q)
        import_levels("\U0001f9f1\U0001f9f1\n", q)
        self.assertEqual(q.tiles["\U0001f9f1"].name, "brick")
        self.assertEqual(q.sprite_for_tile(q.tiles["\U0001f9f1"]).name, "brick")

    def test_a_brick_tile_with_no_sprite_gets_a_generated_one(self):
        p = Project("p")
        import_levels("\U0001f9f1\U0001f9f1\n", p)
        s = p.sprite("brick")
        self.assertEqual((s.width, s.height), (16, 16))
        self.assertIs(p.sprite_for_tile(p.tiles["\U0001f9f1"]), s)                    # (with no cell: the plain one)
        mortar = {s.get(0, x, 15) for x in range(16)}                      # the bottom row of the wall is one course's bed joint
        self.assertEqual(len(mortar), 1)

    def test_bricks_have_variants_picked_cell_by_cell(self):
        p = Project("p")
        import_levels("\U0001f9f1\U0001f9f1\n", p)
        t = p.tiles["\U0001f9f1"]
        names = [n for n, _ in t.variants]
        self.assertEqual(names[0], "brick")
        self.assertTrue({"brick_b", "brick_eroded", "brick_flecked", "brick_painted", "brick_missing", "brick_weep", "brick_drain", "brick_pipe",
                          "brick_dirty", "brick_soot", "brick_rust", "brick_tar", "brick_tag", "brick_throwup", "brick_sticker", "brick_poster", "brick_buffed"} <= set(names))
        self.assertEqual([s.name for s in p.sprites if not s.name.startswith("brick_g")], names)
        picks = [t.pick_variant(x, y) for y in range(100) for x in range(100)]
        self.assertEqual(picks, [t.pick_variant(x, y) for y in range(100) for x in range(100)])      # the same every time
        count = {n: picks.count(n) for n in names}
        plain = count["brick"] + count["brick_b"] + count["brick_c"]
        self.assertTrue(2000 < plain < 3500, count)                                                  # the plain ones in three shades are the most common (a third is painted over)
        self.assertTrue(0 < count["brick_missing"] < 200 and 0 < count["brick_pipe"] < 200 and count["brick_eroded"] > count["brick_missing"], count)
        self.assertEqual(p.sprite_for_tile(t, 3, 4).name, t.pick_variant(3, 4))
        self.assertGreater(len({p.sprite_for_tile(t, x, 0).name for x in range(40)}), 3)               # a row of a level is not one brick
        self.assertEqual(Project.from_json(json.loads(json.dumps(p.to_json()))).tiles["\U0001f9f1"].variants, t.variants)

    def test_brick_variants_tile_with_each_other(self):
        from .generated import family
        rows = {n: [r for r in text.splitlines() if not r.startswith("#")] for n, _, text in family("brick")}
        for n, r in rows.items():
            self.assertEqual((len(r), {len(x) for x in r}), (16, {16}), n)
            if n == "brick_downpipe":
                self.assertEqual(r[0][6:10], r[15][6:10])                                         # a pipe down the whole sprite: two of them are one pipe
                self.assertEqual(r[0][6:10], "LGGZ")
            elif n in ("brick", "brick_b", "brick_c", "brick_eroded", "brick_worn", "brick_flecked", "brick_painted", "brick_missing"):
                self.assertEqual(set(r[15]), {"M"}, n)                                            # the joints are where the plain wall has them
                self.assertEqual(r[3], "M" * 16, n)
            if "tag" in n or n in ("brick_throwup", "brick_star"):
                self.assertTrue(any(ch in "rbgypoc" for row in r for ch in row), n)               # spray paint, over the joints too

    def test_the_city_paints_over_the_bricks_in_patches_that_ignore_the_tiling(self):
        from .generated import patch_code
        p = Project("p")
        text = "\n".join("\U0001f9f1" * 40 for _ in range(10)) + "\n"
        (lv,), _ = import_levels(text, p)
        t = p.tiles["\U0001f9f1"]
        self.assertEqual(t.patches, "brick_g")
        codes = [patch_code(x, y, 0) for y in range(10) for x in range(40)]
        self.assertEqual(codes, [patch_code(x, y, 0) for y in range(10) for x in range(40)])                  # a function of the place
        painted = [c for c in codes if c != "0000"]
        self.assertTrue(80 < len(painted) < 300, len(painted))                                                  # a good part of the wall, not all of it
        self.assertTrue(any(len(set(c)) > 1 and "0" in c for c in painted))                                     # an edge falls inside a cell, on a half
        self.assertTrue(any(c in "1111 2222 3333 4444".split() for c in painted))                               # and a patch covers whole cells
        for x, y in ((x, y) for y in range(10) for x in range(40)):
            name = t.pick_variant(x, y)
            self.assertIsNotNone(p.sprite_for_tile(t, x, y), name)
            if patch_code(x, y, __import__("zlib").crc32(t.emoji.encode("utf-8"))) != "0000":
                self.assertTrue(name.startswith("brick_g"), name)
                self.assertEqual(p.sprite_for_tile(t, x, y).name, name)                                         # the sprite is there: made for this level
        self.assertEqual(Project.from_json(json.loads(json.dumps(p.to_json()))).tiles["\U0001f9f1"].patches, "brick_g")

    def test_a_street_is_drawn_for_each_cell_s_place_in_it(self):
        from .generated import GUTTER, KERB, LINE, road_name
        from .model import LevelCells
        road, wall = "\u25fc\ufe0f", "\U0001f9f1"
        p = Project("p")
        rows = ["\u2b1b" * 4, wall * 4, road * 4, road * 4, road * 4, road * 4]                    # a street four cells deep, along the bottom of the level
        (lv,), _ = import_levels("# level: r\n# empty: \u2b1b\n" + "\n".join(rows) + "\n", p)
        t = p.tiles[road]
        self.assertEqual((t.name, t.connects), ("road", "road"))
        self.assertEqual(len([s for s in p.sprites if s.name.startswith("road")]), 40)
        self.assertEqual(p.sprite_for_tile(t).name, "road")                                       # (the icon: asphalt with the line)

        def shape(level, x, y):
            n = t.pick_variant(x, y, level)
            return LINE if n == "road" else int(n.split("_")[1])
        self.assertEqual([shape(lv, 1, y) for y in range(2, 6)], [KERB, 0, LINE, 0])                # the kerb on top, the line in the lower middle, no gutter at the level's edge
        self.assertEqual(len({shape(lv, x, 4) for x in range(4)}), 1)                              # the same all the way along
        for y in range(2, 6):
            self.assertIsNotNone(p.sprite_for_tile(t, 1, y, lv))
        two = LevelCells(lv, list(lv.cells))                                                       # a street two cells deep, with the rest of the level under it
        for x in range(4):
            two.cells[4 * 4 + x] = two.cells[5 * 4 + x] = ""
        self.assertEqual([shape(two, 0, y) for y in (2, 3)], [KERB, LINE | GUTTER])                # (two cells deep: the line is in the lower; the gutter is where the street ends)
        top = LevelCells(lv, list(lv.cells))                                                       # a street that starts at the top of the level goes on up: no kerb
        for x in range(4):
            top.cells[x] = top.cells[4 + x] = road
        self.assertEqual(shape(top, 1, 0) & KERB, 0)
        self.assertEqual(Project.from_json(json.loads(json.dumps(p.to_json()))).tiles[road].connects, "road")
        self.assertEqual(road_name("road", 0, 0), "road_0_0")

    def test_a_street_scene_from_the_level_text(self):
        from .model import LevelCells
        legend = "\n".join("# %s = %s" % kv for kv in (("\U0001f533", "sidewalk"), ("\u25fc\ufe0f", "road"), ("\U0001f697", "car"), ("\U0001f4a1", "streetlamp"),
                                                       ("\U0001f9ef", "hydrant"), ("\U0001fa9f", "window"), ("\U0001f6aa", "door"), ("\U0001f512", "shutter"),
                                                       ("\U0001f3aa", "awning"), ("\U0001f3e8", "motel sign"), ("\U0001f37e", "liquor sign"), ("\U0001f4fa", "tv sign"),
                                                       ("\U0001f5d1\ufe0f", "dumpster")))
        rows = ["\U0001fa9f\U0001f6aa\U0001f512\U0001f3aa", "\U0001f3e8\U0001f37e\U0001f4fa\u2b1b", "\u2b1b\U0001f4a1\u2b1b\u2b1b", "\u2b1b\U0001f4a1\u2b1b\u2b1b", "\u2b1b\U0001f4a1\u2b1b\U0001f5d1\ufe0f", "\U0001f533\U0001f9ef\U0001f533\U0001f533",
                "\u25fc\ufe0f\u25fc\ufe0f\u25fc\ufe0f\u25fc\ufe0f", "\u25fc\ufe0f\U0001f697\U0001f697\U0001f697", "\u25fc\ufe0f\u25fc\ufe0f\u25fc\ufe0f\u25fc\ufe0f"]
        p = Project("p")
        (lv,), _ = import_levels("# level: s\n# empty: \u2b1b\n" + legend + "\n" + "\n".join(rows) + "\n", p)
        names = {s.name for s in p.sprites}
        for base in ("sidewalk", "road", "car", "streetlamp", "hydrant", "window", "door", "shutter", "awning", "motel_sign", "liquor_sign", "tv_sign", "dumpster"):
            self.assertIn(base, names)
        for tile in p.tiles.values():
            for x in range(lv.width):
                for y in range(lv.height):
                    if lv.get(x, y) == tile.emoji:
                        self.assertIsNotNone(p.sprite_for_tile(tile, x, y, lv), (tile.name, x, y))
        car, lamp, road, walk = (p.tiles[e] for e in ("\U0001f697", "\U0001f4a1", "\u25fc\ufe0f", "\U0001f533"))
        self.assertEqual([car.pick_variant(x, 7, lv).split("_")[1] for x in (1, 2, 3)], ["l", "m", "r"])           # three cells: a car
        self.assertEqual(len({car.pick_variant(x, 7, lv).split("_")[2] for x in (1, 2, 3)}), 1)                      # of one colour
        self.assertEqual([lamp.pick_variant(1, y, lv).split("_")[1] if "_" in lamp.pick_variant(1, y, lv) else "1" for y in range(2, 5)], ["1", "0", "2"])   # the head, the pole, the foot
        self.assertEqual(road.joins, [car.emoji])                                                                    # a car in the street is road to the street
        shape = lambda n: 0 if "_" not in n else int(n.split("_")[1])
        self.assertEqual([shape(road.pick_variant(2, y, lv)) & 1 for y in (6, 7, 8)], [1, 0, 0])                   # kerb on top, none under the car
        self.assertEqual(shape(walk.pick_variant(0, 5, lv)), 1)                                                      # the top row of the pavement is in the wall's shade
        self.assertEqual(Project.from_json(json.loads(json.dumps(p.to_json()))).tiles[road.emoji].joins, [car.emoji])

    def test_rocks_have_variants_too(self):
        p = Project("p")
        import_levels("\U0001faa8\U0001faa8\n", p)
        t = p.tiles["\U0001faa8"]
        names = [n for n, _ in t.variants]
        self.assertEqual((t.name, names[0]), ("rock", "rock"))
        self.assertTrue({"rock_wide", "rock_pair", "rock_pebbles", "rock_mossy", "rock_sandstone", "rock_basalt"} <= set(names))
        for n in names:
            s = p.sprite(n)
            self.assertEqual((s.width, s.height, s.get(0, 0, 0)), (16, 16, 0), n)
            self.assertTrue(any(s.get(0, x, y) for x in range(16) for y in range(8, 16)), n)
        self.assertGreater(len({t.pick_variant(x, 0) for x in range(60)}), 5)

    def test_trees_have_variants_too(self):
        p = Project("p")
        import_levels("\U0001f333\U0001f333\n", p)
        t = p.tiles["\U0001f333"]
        names = [n for n, _ in t.variants]
        self.assertEqual(names[0], "deciduous_tree")
        self.assertTrue({"deciduous_tree_pine", "deciduous_tree_birch", "deciduous_tree_apple", "deciduous_tree_autumn", "deciduous_tree_bare"} <= set(names))
        self.assertIs(p.sprite_for_tile(t), p.sprite("deciduous_tree"))
        for n in names:
            s = p.sprite(n)
            self.assertEqual((s.width, s.height), (16, 16))
            self.assertEqual(s.get(0, 0, 0), 0)                                                   # the corners are clear
            self.assertTrue(any(s.get(0, x, 15) for x in range(16)), n)                         # standing on the bottom row
        self.assertGreater(len({t.pick_variant(x, 0) for x in range(60)}), 4)

    def test_generated_bricks_are_not_made_when_the_project_has_a_sprite(self):
        p = Project("p")
        import_sprites("# sprite: brick\nRR\nRR\n", p)
        import_levels("\U0001f9f1\n", p)
        self.assertEqual([(s.name, s.width) for s in p.sprites], [("brick", 2)])
        self.assertEqual(p.tiles["\U0001f9f1"].variants, [])

    def test_generated_bricks_follow_the_legend_sprite_name(self):
        p = Project("p")
        import_levels("# \U0001f9f1 = wall (solid) -> brick\n\U0001f9f1\n", p)
        self.assertEqual(p.sprite_for_tile(p.tiles["\U0001f9f1"]).name, "brick")
        q = Project("q")
        import_levels("# \U0001f9f1 = wall (solid) -> mystery\n\U0001f9f1\n", q)       # a name nothing makes: no sprite, and no guess
        self.assertEqual(q.sprites, [])

    def test_typing_a_brick_in_the_text_pane_makes_the_sprite_too(self):
        p = Project("p")
        (lv,), _ = import_levels(".\n", p)
        self.assertEqual(p.sprites, [])
        level_from_text(lv, "\U0001f9f1.\n", p)
        self.assertIsNotNone(p.sprite("brick"))

    def test_brick_art_is_deterministic_and_tiles(self):
        from .generated import brick_rows, brick_text
        self.assertEqual(brick_rows(16, 3), brick_rows(16, 3))
        self.assertNotEqual(brick_rows(16, 3), brick_rows(16, 4))
        for rows in (brick_rows(16), brick_rows(24, 1)):
            n = len(rows)
            self.assertTrue(all(len(r) == n for r in rows))
            self.assertEqual(set(rows[-1]), {"M"})                            # a bed joint closes the tile, so it tiles downward
            for y in range(n):                                                # a head joint is never next to another across the seam
                self.assertFalse(rows[y][-1] == "M" and rows[y][0] == "M" and rows[y] != "M" * n)
        self.assertTrue(brick_text("wall", 8).startswith("# sprite: wall\n"))
        with self.assertRaises(ValueError):
            brick_rows(12)

    def test_a_face_tile_keeps_its_body_and_clip_and_round_trips(self):
        p = Project("p")
        import_levels("# \U0001f92a = zany (face) -> body_bat\n# \U0001f620 = grump (face=shake, solid) -> body_legs\n\U0001f92a\U0001f620\n", p)
        a, b = p.tiles["\U0001f92a"], p.tiles["\U0001f620"]
        self.assertEqual((a.face, a.clip, a.body, a.sprite), (True, "", "body_bat", ""))        # the sprite is made later, from the body
        self.assertEqual((b.face, b.clip, b.body, b.solid), (True, "shake", "body_legs", True))
        text = export_level(p.levels[0], p)
        self.assertIn("# \U0001f92a = zany (face) -> body_bat", text)
        self.assertIn("# \U0001f620 = grump (solid, face=shake) -> body_legs", text)
        again = Project("again")
        import_levels(text, again)
        self.assertEqual({k: (t.face, t.clip, t.body) for k, t in p.tiles.items()}, {k: (t.face, t.clip, t.body) for k, t in again.tiles.items()})
        loaded = Project.from_json(p.to_json()).tiles["\U0001f620"]
        self.assertEqual((loaded.face, loaded.clip, loaded.body), (True, "shake", "body_legs"))                  # and through the project file

    def test_a_face_tile_is_not_given_a_generated_sprite(self):
        p = Project("p")
        import_levels("# \U0001f9f1 = brick (face) -> body_x\n\U0001f9f1\n", p)
        self.assertEqual(p.sprites, [])

    def test_ascii_levels_work_even_with_hash_walls(self):
        p = Project("p")
        (lv,), new = import_levels(". . .\n# #  #\n", p)           # a row starting "# " is a row, not a comment
        self.assertEqual(lv.height, 2)
        self.assertEqual(sorted(t.emoji for t in new), ["#"])
        self.assertEqual(natural_name("#"), "number sign")

    def test_ragged_rows_are_padded_with_empty(self):
        p = Project("p")
        (lv,), _ = import_levels("# empty: .\n#..#\n#\n", p)
        self.assertEqual((lv.width, lv.height), (4, 2))
        self.assertEqual(lv.get(3, 1), "")

    def test_two_levels_in_one_file(self):
        p = Project("p")
        made, _ = import_levels("# level: a\n\U0001f9f1\n# level: b\n\U0001fa99\U0001fa99\n", p)
        self.assertEqual([l.name for l in made], ["a", "b"])
        self.assertEqual(made[1].width, 2)

    def test_text_pane_edit(self):
        p = make_demo_project()
        lv = p.levels[0]
        text = level_to_text(lv, p)
        self.assertEqual(len(text.splitlines()), lv.height)
        new_tiles = level_from_text(lv, text.replace("\U0001fa99", "\U0001f333", 1), p)
        self.assertEqual([t.name for t in new_tiles], ["deciduous tree"])
        self.assertEqual(level_to_text(lv, p).count("\U0001f333"), 1)

    def test_resize_and_fill(self):
        lv = Level("l", 4, 3)
        lv.flood_fill(0, 0, "X")
        self.assertEqual(lv.cells.count("X"), 12)
        lv.set(1, 1, "Y")
        lv.resize(2, 2)
        self.assertEqual(lv.cells, ["X", "X", "X", "Y"])

    def test_no_level_is_an_error(self):
        with self.assertRaises(ProjectError):
            parse_level_text("# level: nothing\n")


class JsonProject(unittest.TestCase):
    def test_round_trip_through_a_file(self):
        a = make_demo_project()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "demo.json")
            a.save(path)
            b = Project.load(path)
            self.assertEqual(snapshot(a), snapshot(b))
            self.assertEqual(a.levels[0].cells, b.levels[0].cells)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), b.to_json())
            self.assertFalse(b.dirty)

    def test_the_file_reads_like_the_art(self):
        data = make_demo_project().to_json()
        self.assertEqual(data["sprites"][0]["frames"][0][0], "SSSSSSSS")
        self.assertEqual(data["levels"][0]["rows"][10], "\U0001f7e9" * 24)

    def test_bad_files_say_where(self):
        good = make_demo_project().to_json()
        bad = json.loads(json.dumps(good))
        bad["sprites"][1]["frames"][0][2] = "ZZZZZZZZ"
        with self.assertRaises(ProjectError) as e:
            Project.from_json(bad)
        self.assertIn("sprites[1].frames[0]", str(e.exception))
        self.assertIn("'Z'", str(e.exception))
        bad = json.loads(json.dumps(good))
        bad["levels"][0]["rows"][0] = "\U0001f4a5" * 24
        with self.assertRaises(ProjectError) as e:
            Project.from_json(bad)
        self.assertIn("levels[0]", str(e.exception))
        with self.assertRaises(ProjectError):
            Project.from_json({"format": "something else"})
        bad = json.loads(json.dumps(good))
        bad["version"] = 99
        with self.assertRaises(ProjectError):
            Project.from_json(bad)

    def test_parse_color(self):
        self.assertEqual(parse_color("#fff"), (255, 255, 255))
        self.assertEqual(parse_color("0a0b0c"), (10, 11, 12))
        with self.assertRaises(ProjectError):
            parse_color("red")

    def test_sprite_edit_operations(self):
        s = Sprite("s", 3, 2)
        s.set(0, 1, 1, 5)
        n = s.add_frame(0, copy=True)
        self.assertEqual(s.get(n, 1, 1), 5)
        s.set(n, 0, 0, 7)
        s.resize(2, 3)
        self.assertEqual((s.width, s.height, s.get(n, 0, 0), s.get(n, 1, 1)), (2, 3, 7, 5))
        s.flood_fill(0, 0, 0, 9)
        self.assertEqual(s.get(0, 0, 0), 9)
        self.assertEqual(s.move_frame(0, 1), 1)
        s.delete_frame(0)
        self.assertEqual(len(s.frames), 1)
        s.delete_frame(0)
        self.assertEqual(len(s.frames), 1)                    # the last frame stays


class SlimeProject(unittest.TestCase):
    def test_the_sample_level_becomes_a_project_that_round_trips(self):
        from .slime_demo import make_slime_project
        from .asciiart import export_level, import_levels
        p = make_slime_project()
        lv = p.levels[0]
        self.assertEqual((lv.width, lv.height), (64, 20))
        self.assertEqual(lv.cells.count("\U0001f7eb"), 18)               # the dirt wall: 2 x 9 cells
        self.assertEqual(lv.cells.count("\U0001f4e6"), 4)                # four crates
        self.assertTrue(p.tiles["\U0001f4e6"].dynamic and p.tiles["\U0001f7eb"].diggable)
        p2 = Project.from_json(p.to_json())
        self.assertEqual(p2.levels[0].cells, lv.cells)
        self.assertTrue(p2.tiles["\U0001f7eb"].diggable and p2.tiles["\U0001f4e6"].dynamic)
        q = Project("again")                                                # the emoji text keeps the traits too
        import_levels(export_level(lv, p), q)
        self.assertTrue(q.tiles["\U0001f7eb"].diggable and q.tiles["\U0001f7eb"].solid and q.tiles["\U0001f4e6"].dynamic)
        self.assertEqual(q.levels[0].cells, lv.cells)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# the Unity importer: a Unity project is built in a temp dir (PNG files written here, so there are no binary fixtures)

def make_png(w, h, rows, ctype=6, depth=8, palette=None, trns=None, filt=0):
    """A PNG file's bytes. `rows` are the raw (unfiltered) bytes of each row, as many as `h`. filt 0 = none, 1 = Sub, 2 = Up."""
    import struct
    import zlib

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, channels * depth // 8)
    raw = bytearray()
    prev = bytes(len(rows[0]))
    for row in rows:
        if filt == 1:
            out = bytes((row[i] - (row[i - bpp] if i >= bpp else 0)) & 255 for i in range(len(row)))
        elif filt == 2:
            out = bytes((row[i] - prev[i]) & 255 for i in range(len(row)))
        else:
            out = bytes(row)
        raw += bytes([filt]) + out
        prev = row
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, 0))
    if palette:
        data += chunk(b"PLTE", b"".join(bytes(c) for c in palette))
    if trns:
        data += chunk(b"tRNS", bytes(trns))
    return data + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")


def rgba_rows(rows):
    """[[(r, g, b, a), ...], ...] -> raw row bytes of an RGBA image."""
    return [b"".join(bytes(px) for px in row) for row in rows]


RED, GREEN, BLUE, YELLOW, CLEAR = (224, 60, 60, 255), (60, 180, 75, 255), (60, 100, 224, 255), (242, 216, 59, 255), (0, 0, 0, 0)


def sheet_meta(mode, slices=(), texture_type=8, guid="0123456789abcdef0123456789abcdef", ppu=16, ids=None):
    """A .meta in the layout Unity writes. slices: [(name, x, y, w, h)], y counted from the bottom."""
    text = "fileFormatVersion: 2\nguid: %s\nTextureImporter:\n  textureType: %d\n  spriteMode: %d\n  spritePixelsToUnits: %d\n" % (guid, texture_type, mode, ppu)
    if slices:
        text += "  spriteSheet:\n    serializedVersion: 2\n    sprites:\n"
        for n, (name, x, y, w, h) in enumerate(slices):
            text += ("    - serializedVersion: 2\n      name: %s\n      rect:\n        serializedVersion: 2\n        x: %d\n        y: %d\n        width: %d\n"
                     "        height: %d\n      alignment: 0\n      pivot: {x: 0.5, y: 0.5}\n      border: {x: 0, y: 0, z: 0, w: 0}\n      outline: []\n"
                     "      internalID: %d\n" % (name, x, y, w, h, ids[n] if ids else 21300000 + 2 * n))
    return text + "  mipmapLimitGroupName: \nuserData: \n"


class UnityFiles(unittest.TestCase):
    """Helpers for the Unity tests: a temp Unity project with an Assets/Textures folder. (No tests here, so subclasses do not re-run each other's.)"""
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.tex = os.path.join(self.root, "Assets", "Textures")
        os.makedirs(self.tex)

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, name, data, meta=None):
        path = os.path.join(self.tex, name)
        with open(path, "wb") as f:
            f.write(data)
        if meta is not None:
            with open(path + ".meta", "w", encoding="utf-8") as f:
                f.write(meta)
        return path

    def rgba_png(self, rows, **kw):
        return make_png(len(rows[0]), len(rows), rgba_rows(rows), **kw)

    def colors(self, project, sprite, frame=0):
        """A sprite's frame as rows of RGBA tuples."""
        px = sprite.rgba(project.palette, frame)
        return [[tuple(px[(y * sprite.width + x) * 4:(y * sprite.width + x) * 4 + 4]) for x in range(sprite.width)] for y in range(sprite.height)]



class UnityImport(UnityFiles):
    # ---- PNG
    def test_png_colour_types_and_filters_decode_the_same_pixels(self):
        from .unity_import import decode_png
        img = [[RED, GREEN, BLUE], [YELLOW, CLEAR, RED]]
        want = b"".join(bytes(px) for row in img for px in row)
        for filt in (0, 1, 2):
            self.assertEqual(decode_png(self.rgba_png(img, filt=filt))[2], want, "RGBA, filter %d" % filt)
        rgb = make_png(2, 1, [bytes([10, 20, 30, 40, 50, 60])], ctype=2)
        self.assertEqual(decode_png(rgb), (2, 1, bytes([10, 20, 30, 255, 40, 50, 60, 255])))
        gray = make_png(2, 1, [bytes([0, 200])], ctype=0)
        self.assertEqual(decode_png(gray)[2], bytes([0, 0, 0, 255, 200, 200, 200, 255]))
        ga = make_png(1, 1, [bytes([90, 7])], ctype=4)
        self.assertEqual(decode_png(ga)[2], bytes([90, 90, 90, 7]))

    def test_indexed_png_with_transparency_and_packed_bits(self):
        from .unity_import import decode_png
        pal = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        eight = make_png(3, 1, [bytes([0, 1, 2])], ctype=3, palette=pal, trns=[0, 255])        # entry 0 is clear; the rest are opaque
        self.assertEqual(decode_png(eight)[2], bytes([255, 0, 0, 0, 0, 255, 0, 255, 0, 0, 255, 255]))
        four = make_png(3, 1, [bytes([0x01, 0x20])], ctype=3, depth=4, palette=pal)            # pixels 0, 1, 2 packed two to a byte
        self.assertEqual(decode_png(four)[2], bytes([255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255]))
        two = make_png(4, 1, [bytes([0b00011011])], ctype=3, depth=2, palette=pal + [(9, 9, 9)])
        self.assertEqual([decode_png(two)[2][i] for i in (0, 4, 8, 12)], [255, 0, 0, 9])

    def test_a_png_that_is_not_one_is_a_message(self):
        from .unity_import import UnityImportError, decode_png
        with self.assertRaises(UnityImportError):
            decode_png(b"GIF89a....", "x.png")

    # ---- single sprites
    def test_a_single_texture_is_one_sprite_with_rows_from_the_top(self):
        from .unity_import import import_unity_sprites
        custom = (10, 20, 30, 255)                                    # not in the default palette; red, green and blue are
        self.put("hero.png", self.rgba_png([[RED, custom], [BLUE, CLEAR]]), sheet_meta(1))
        p = Project("t")
        n_colors = len(p.palette)
        r = import_unity_sprites(p, self.root)
        self.assertEqual([s.name for s in p.sprites], ["hero"])
        self.assertEqual(self.colors(p, p.sprites[0]), [[RED, custom], [BLUE, CLEAR]])
        self.assertEqual(len(p.palette), n_colors + 1)                 # only the custom colour needed a new entry
        self.assertEqual(r.summary(), "1 sprite (1 frame) from 1 texture")

    def test_colours_the_palette_already_has_are_reused_not_added(self):
        from .unity_import import import_unity_sprites
        self.put("a.png", self.rgba_png([[RED, RED]]), sheet_meta(1))
        p = Project("t")
        before = len(p.palette)
        import_unity_sprites(p, self.root)
        self.assertEqual(len(p.palette), before)
        self.assertEqual(p.sprites[0].get(0, 0, 0), p.palette.index_of("R"))

    def test_a_texture_with_no_meta_is_a_single_sprite(self):
        from .unity_import import import_unity_sprites
        self.put("plain.png", self.rgba_png([[RED]]))
        p = Project("t")
        import_unity_sprites(p, self.root)
        self.assertEqual([s.name for s in p.sprites], ["plain"])

    def test_textures_that_are_not_sprites_are_skipped_with_a_note(self):
        from .unity_import import import_unity_sprites
        self.put("normal.png", self.rgba_png([[RED]]), sheet_meta(1, texture_type=1))
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        self.assertEqual(p.sprites, [])
        self.assertTrue(any("not a sprite texture" in n for n in r.notes))

    def test_two_textures_with_the_same_name_get_different_sprite_names(self):
        from .unity_import import import_unity_sprites
        os.makedirs(os.path.join(self.root, "Assets", "Other"))
        self.put("tile.png", self.rgba_png([[RED]]), sheet_meta(1))
        with open(os.path.join(self.root, "Assets", "Other", "tile.png"), "wb") as f:
            f.write(self.rgba_png([[GREEN]]))
        p = Project("t")
        import_unity_sprites(p, self.root)
        self.assertEqual(sorted(s.name for s in p.sprites), ["tile", "tile 2"])

    def test_library_and_package_folders_are_not_walked(self):
        from .unity_import import find_pngs
        for d in ("Library", "Packages"):
            os.makedirs(os.path.join(self.root, d))
            with open(os.path.join(self.root, d, "junk.png"), "wb") as f:
                f.write(b"x")
        self.put("keep.png", self.rgba_png([[RED]]))
        self.assertEqual([os.path.basename(x) for x in find_pngs(self.root)], ["keep.png"])

    # ---- sprite sheets
    def test_a_multiple_mode_sheet_is_cut_into_slices_with_y_counted_from_the_bottom(self):
        from .unity_import import import_unity_sprites
        top = [RED, RED, GREEN, GREEN]
        bottom = [BLUE, BLUE, YELLOW, YELLOW]
        meta = sheet_meta(2, [("lowleft", 0, 0, 2, 1), ("upright", 2, 1, 2, 1)])
        self.put("sheet.png", self.rgba_png([top, bottom]), meta)
        p = Project("t")
        import_unity_sprites(p, self.root)
        by = {s.name: s for s in p.sprites}
        self.assertEqual(sorted(by), ["lowleft", "upright"])
        self.assertEqual(self.colors(p, by["lowleft"]), [[BLUE, BLUE]])
        self.assertEqual(self.colors(p, by["upright"]), [[GREEN, GREEN]])

    def test_numbered_slices_of_one_size_become_the_frames_of_one_sprite(self):
        from .unity_import import group_slices, import_unity_sprites
        row = [RED, GREEN, BLUE, YELLOW]
        meta = sheet_meta(2, [("walk_1", 1, 0, 1, 1), ("walk_0", 0, 0, 1, 1), ("walk_2", 2, 0, 1, 1), ("idle", 3, 0, 1, 1)])
        self.put("hero.png", self.rgba_png([row]), meta)
        p = Project("t")
        import_unity_sprites(p, self.root)
        self.assertEqual([s.name for s in p.sprites], ["walk", "idle"])
        walk = p.sprite("walk")
        self.assertEqual([self.colors(p, walk, i)[0][0] for i in range(3)], [RED, GREEN, BLUE])          # in number order, not .meta order
        self.assertEqual(len(p.sprite("idle").frames), 1)
        # a lone numbered slice keeps its whole name, and different sizes do not mix
        lone = group_slices([{"name": "rock_3", "x": 0, "y": 0, "w": 4, "h": 4}, {"name": "rock_4", "x": 4, "y": 0, "w": 8, "h": 8}])
        self.assertEqual([n for n, _ in lone], ["rock_3", "rock_4"])

    def test_slices_named_after_their_texture_are_never_merged_into_an_animation(self):
        from .unity_import import group_slices
        sl = lambda n: {"name": n, "x": 0, "y": 0, "w": 4, "h": 4}
        self.assertEqual([n for n, _ in group_slices([sl("Hero_0"), sl("Hero_1")], "hero")], ["Hero_0", "Hero_1"])        # Unity's automatic names: tiles or frames, a scene names each
        self.assertEqual([n for n, _ in group_slices([sl("walk_0"), sl("walk_1")], "hero")], ["walk"])                       # a name somebody chose is an animation

    def test_a_slice_outside_the_texture_is_skipped_with_a_note(self):
        from .unity_import import import_unity_sprites
        self.put("s.png", self.rgba_png([[RED, GREEN]]), sheet_meta(2, [("ok", 0, 0, 1, 1), ("gone", 50, 50, 4, 4)]))
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        self.assertEqual([s.name for s in p.sprites], ["ok"])
        self.assertTrue(any("gone" in n for n in r.notes))

    # ---- limits
    def test_more_colours_than_the_palette_holds_are_merged_and_reported(self):
        from .unity_import import import_unity_sprites
        rows = [[(x * 8 % 256, y * 17 % 256, (x * 5 + y * 3) % 256, 255) for x in range(32)] for y in range(16)]
        self.assertGreater(len({px for row in rows for px in row}), 256)
        self.put("rainbow.png", self.rgba_png(rows), sheet_meta(1))
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        self.assertLessEqual(len(p.palette), 256)
        self.assertTrue(any("did not fit in the palette" in n for n in r.notes))
        self.assertEqual(p.sprites[0].frames[0].count(0), 0)                              # every pixel got a colour
        Project.from_json(p.to_json())                                                    # and the keys it made are valid, so the project saves and loads

    def test_a_texture_wider_than_a_sprite_is_scaled_down_and_reported(self):
        from .unity_import import import_unity_sprites
        self.put("wide.png", self.rgba_png([[RED] * 512] * 8), sheet_meta(1))
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        s = p.sprites[0]
        self.assertEqual((s.width, s.height), (256, 4))
        self.assertTrue(all(c == RED for row in self.colors(p, s) for c in row))
        self.assertTrue(any("512x8" in n and "256x4" in n for n in r.notes))

    def test_a_broken_png_is_reported_and_the_others_still_import(self):
        from .unity_import import import_unity_sprites
        self.put("bad.png", b"not a png at all")
        self.put("good.png", self.rgba_png([[RED]]))
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        self.assertEqual([s.name for s in p.sprites], ["good"])
        self.assertTrue(any("bad.png" in n for n in r.notes))

    def test_a_folder_with_no_textures_adds_nothing(self):
        from .unity_import import import_unity_sprites
        p = Project("t")
        r = import_unity_sprites(p, self.root)
        self.assertEqual(p.sprites, [])
        self.assertTrue(r.notes)

    def test_the_import_round_trips_through_the_project_file(self):
        from .unity_import import import_unity_sprites
        self.put("a.png", self.rgba_png([[RED, GREEN], [BLUE, YELLOW]]), sheet_meta(1))
        p = Project("t")
        import_unity_sprites(p, self.root)
        q = Project.from_json(p.to_json())
        self.assertEqual(snapshot(p), snapshot(q))


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Unity scenes -> levels

G_BRICK, G_COIN, G_SHEET = "b" * 32, "c" * 32, "d" * 32


class SceneBuilder:
    """Writes the text of a Unity scene (the YAML Unity serializes) object by object. Each add_* returns the GameObject's fileID."""
    def __init__(self):
        self.parts = ["%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n"]
        self.next = 100

    def _id(self):
        self.next += 10
        return self.next

    def add(self, name, x=0.0, y=0.0, sprite=None, order=0, scale=(1, 1), father=None, active=1, enabled=1, collider=None, trigger=0, body=None, rot_z=0.0,
            extra_components=()):
        """sprite: (guid, fileID) or None; collider: a class id (61 = box) or None; body: Rigidbody2D m_BodyType or None."""
        go, xf = self._id(), self._id()
        comps = [xf]
        extra = []
        self.sr = None
        if sprite:
            sr = self.sr = self._id()
            comps.append(sr)
            extra.append("--- !u!212 &%d\nSpriteRenderer:\n  m_GameObject: {fileID: %d}\n  m_Enabled: %d\n  m_Sprite: {fileID: %d, guid: %s, type: 3}\n  m_SortingOrder: %d\n"
                         % (sr, go, enabled, sprite[1], sprite[0], order))
        if collider:
            c = self._id()
            comps.append(c)
            extra.append("--- !u!%d &%d\nBoxCollider2D:\n  m_GameObject: {fileID: %d}\n  m_Enabled: 1\n  m_IsTrigger: %d\n" % (collider, c, go, trigger))
        if body is not None:
            b = self._id()
            comps.append(b)
            extra.append("--- !u!50 &%d\nRigidbody2D:\n  m_GameObject: {fileID: %d}\n  m_BodyType: %d\n" % (b, go, body))
        for class_id, make in extra_components:                              # make(go) -> the component's text, starting with its class name
            c = self._id()
            comps.append(c)
            extra.append("--- !u!%d &%d\n%s" % (class_id, c, make(go)))
        self.parts.append("--- !u!1 &%d\nGameObject:\n  m_Component:\n%s  m_Name: %s\n  m_IsActive: %d\n" % (go, "".join("  - component: {fileID: %d}\n" % c for c in comps), name, active))
        qz = rot_z / 2.0                                                    # a small angle's quaternion: z = sin(angle / 2)
        self.parts.append("--- !u!4 &%d\nTransform:\n  m_GameObject: {fileID: %d}\n  m_LocalRotation: {x: 0, y: 0, z: %g, w: 1}\n  m_LocalPosition: {x: %g, y: %g, z: 0}\n"
                          "  m_LocalScale: {x: %g, y: %g, z: 1}\n  m_Father: {fileID: %d}\n" % (xf, go, qz, x, y, scale[0], scale[1], father or 0))
        self.parts += extra
        self.xf = xf
        return go, xf

    def add_grid(self, name="Grid", cell=(1, 1), x=0.0, y=0.0, layout=0, father=None, scale=(1, 1)):
        """A GameObject with a Grid component (a tilemap's cell size lives there)."""
        def grid(go):
            return ("Grid:\n  m_GameObject: {fileID: %d}\n  m_Enabled: 1\n  m_CellSize: {x: %g, y: %g, z: 0}\n  m_CellGap: {x: 0, y: 0, z: 0}\n"
                    "  m_CellLayout: %d\n  m_CellSwizzle: 0\n" % (go, cell[0], cell[1], layout))
        return self.add(name, x, y, father=father, scale=scale, extra_components=[(156049354, grid)])

    def add_tilemap(self, name, tiles, sprites, father=None, x=0.0, y=0.0, scale=(1, 1), anchor=(0.5, 0.5), matrices=None, collider=False, renderer=True,
                    renderer_enabled=1, order=0, enabled=1, active=1):
        """A GameObject with a Tilemap (+ TilemapRenderer, + TilemapCollider2D). tiles: [(cell x, cell y, sprite index[, matrix index])]; sprites: [(guid, fileID) or
        None] (None is an unused slot, written {fileID: 0}); matrices: [(e00, e01, e10, e11)], identity by default."""
        def tilemap(go):
            out = ["Tilemap:\n  m_ObjectHideFlags: 0\n  m_GameObject: {fileID: %d}\n  m_Enabled: %d\n" % (go, enabled)]
            if tiles:
                out.append("  m_Tiles:\n")
                for t in tiles:
                    out.append("  - first: {x: %d, y: %d, z: 0}\n    second:\n      serializedVersion: 2\n      m_TileIndex: 0\n      m_TileSpriteIndex: %d\n"
                               "      m_TileMatrixIndex: %d\n      m_TileColorIndex: 0\n      m_TileObjectToInstantiateIndex: 65535\n      dummyAlignment: 0\n"
                               "      m_AllTileFlags: 1073741825\n" % (t[0], t[1], t[2], t[3] if len(t) > 3 else 0))
            else:
                out.append("  m_Tiles: {}\n")
            out.append("  m_AnimatedTiles: {}\n  m_TileAssetArray:\n  - m_RefCount: 1\n    m_Data: {fileID: 11400000, guid: %s, type: 2}\n  m_TileSpriteArray:\n" % ("e" * 32))
            for sp in sprites:
                out.append("  - m_RefCount: 1\n    m_Data: {fileID: %d, guid: %s, type: 3}\n" % (sp[1], sp[0]) if sp else "  - m_RefCount: 0\n    m_Data: {fileID: 0}\n")
            out.append("  m_TileMatrixArray:\n")
            for e00, e01, e10, e11 in (matrices or [(1, 0, 0, 1)]):
                out.append("  - m_RefCount: 1\n    m_Data:\n      e00: %g\n      e01: %g\n      e02: 0\n      e03: 0\n      e10: %g\n      e11: %g\n      e12: 0\n"
                           "      e13: 0\n      e20: 0\n      e21: 0\n      e22: 1\n      e23: 0\n      e30: 0\n      e31: 0\n      e32: 0\n      e33: 1\n" % (e00, e01, e10, e11))
            out.append("  m_TileColorArray:\n  - m_RefCount: 1\n    m_Data: {r: 1, g: 1, b: 1, a: 1}\n  m_TileObjectToInstantiateArray: []\n  m_AnimationFrameRate: 1\n"
                       "  m_Color: {r: 1, g: 1, b: 1, a: 1}\n  m_Origin: {x: 0, y: 0, z: 0}\n  m_Size: {x: 10, y: 10, z: 1}\n  m_TileAnchor: {x: %g, y: %g, z: 0}\n"
                       "  m_TileOrientation: 0\n" % anchor)
            return "".join(out)
        parts = [(1839735485, tilemap)]
        if renderer:
            parts.append((483693784, lambda go: "TilemapRenderer:\n  m_GameObject: {fileID: %d}\n  m_Enabled: %d\n  m_SortingOrder: %d\n" % (go, renderer_enabled, order)))
        if collider:
            parts.append((19719996, lambda go: "TilemapCollider2D:\n  m_GameObject: {fileID: %d}\n  m_Enabled: 1\n  m_IsTrigger: 0\n" % go))
        return self.add(name, x, y, father=father, scale=scale, active=active, extra_components=parts)

    def instance(self, guid, mods=(), parent=None):
        """A PrefabInstance of the prefab `guid`. mods: [(target fileID, propertyPath, value[, (objectReference fileID, guid)])]; parent: a transform fileID in this file."""
        fid = self._id()
        lines = ""
        for m in mods:
            ref = m[3] if len(m) > 3 else (0, None)
            objref = "{fileID: %d}" % ref[0] if not ref[1] else "{fileID: %d, guid: %s, type: 3}" % (ref[0], ref[1])
            lines += "    - target: {fileID: %d, guid: %s, type: 3}\n      propertyPath: %s\n      value: %s\n      objectReference: %s\n" % (m[0], guid, m[1], m[2], objref)
        self.parts.append("--- !u!1001 &%d\nPrefabInstance:\n  m_ObjectHideFlags: 0\n  serializedVersion: 2\n  m_Modification:\n    m_TransformParent: {fileID: %d}\n"
                          "    m_Modifications:\n%s    m_RemovedComponents: []\n  m_SourcePrefab: {fileID: 100100000, guid: %s, type: 3}\n" % (fid, parent or 0, lines, guid))
        return fid

    def stripped_transform(self, instance, source_fid):
        """The stand-in Unity writes for an object of a prefab instance, so that this file's own objects can be parented to it."""
        fid = self._id()
        self.parts.append("--- !u!4 &%d stripped\nTransform:\n  m_CorrespondingSourceObject: {fileID: %d, guid: x, type: 3}\n  m_PrefabInstance: {fileID: %d}\n" % (fid, source_fid, instance))
        return fid

    def raw(self, text):
        self.parts.append(text)

    def text(self):
        return "".join(self.parts)


class UnityScenes(UnityFiles):
    def setUp(self):
        super().setUp()
        self.scenes = os.path.join(self.root, "Assets", "Scenes")
        os.makedirs(self.scenes)
        self.put("brick.png", self.rgba_png([[RED] * 16] * 16), sheet_meta(1, guid=G_BRICK))                    # 16 px at 16 px per unit: one unit
        self.put("coin.png", self.rgba_png([[YELLOW] * 16] * 16), sheet_meta(1, guid=G_COIN))
        self.BRICK, self.COIN = (G_BRICK, 21300000), (G_COIN, 21300000)

    def scene(self, name, builder):
        with open(os.path.join(self.scenes, name + ".unity"), "w", encoding="utf-8") as f:
            f.write(builder.text())

    def run_import(self, **kw):
        from .unity_scene import import_unity_project
        self.project = Project("t")
        self.report = import_unity_project(self.project, self.root, **kw)
        return self.report

    def rows(self, level, project=None):
        p = project or self.project
        return ["".join(c or "." for c in [level.get(x, y) for x in range(level.width)]) for y in range(level.height)]

    def test_objects_land_on_the_grid_with_y_up_and_each_sprite_gets_a_tile(self):
        b = SceneBuilder()
        for x in range(3):
            b.add("Brick%d" % x, x, 0, self.BRICK, collider=61)
        b.add("Coin", 1, 1, self.COIN)
        self.scene("Level1", b)
        r = self.run_import()
        lv = self.project.level("Level1")
        self.assertEqual((lv.width, lv.height), (3, 2))
        brick, coin = lv.get(0, 1), lv.get(1, 0)
        self.assertEqual(self.rows(lv), [".%s." % coin, brick * 3])                    # the coin is above the bricks: Unity's y points up
        self.assertEqual((self.project.tiles[brick].sprite, self.project.tiles[brick].solid), ("brick", True))
        self.assertEqual((self.project.tiles[coin].sprite, self.project.tiles[coin].solid), ("coin", False))
        self.assertIn("1 level", r.summary())
        self.assertEqual(r.notes, [])

    def test_a_child_is_placed_by_its_parents_position_and_scale(self):
        b = SceneBuilder()
        _, parent = b.add("Parent", 5, 0, scale=(2, 2))
        b.add("Child", 1, 0, self.BRICK, father=parent)                                   # world x = 5 + 2 * 1
        b.add("Anchor", 3, 0, self.BRICK)
        self.scene("Nested", b)
        self.run_import()
        lv = self.project.level("Nested")
        self.assertEqual(lv.width, 5)                                                      # x from 3 to 7
        self.assertTrue(lv.get(0, 0) and lv.get(4, 0) and lv.get(1, 0) == "")

    def test_the_highest_sorting_order_wins_a_shared_cell_and_it_is_reported(self):
        b = SceneBuilder()
        b.add("Back", 0, 0, self.BRICK, order=0)
        b.add("Front", 0, 0, self.COIN, order=5)
        b.add("AlsoBack", 0, 0, self.BRICK, order=-1)
        self.scene("Stack", b)
        r = self.run_import()
        lv = self.project.level("Stack")
        self.assertEqual(self.project.tiles[lv.get(0, 0)].sprite, "coin")
        self.assertTrue(any("2 objects were hidden" in n for n in r.notes))

    def test_collider_trigger_and_body_decide_the_tile_traits(self):
        b = SceneBuilder()
        b.add("Wall", 0, 0, self.BRICK, collider=61, body=2)                              # static body: solid
        b.add("Crate", 1, 0, self.BRICK, collider=61, body=0)                             # dynamic body: solid and dynamic
        b.add("Zone", 2, 0, self.BRICK, collider=61, trigger=1)                           # a trigger is not solid
        b.add("Plain", 3, 0, self.BRICK)
        b.add("Lone", 4, 0, self.BRICK, body=0)                                           # a body with no collider is not solid
        self.scene("Traits", b)
        self.run_import()
        lv = self.project.level("Traits")
        traits = [(self.project.tiles[lv.get(x, 0)].solid, self.project.tiles[lv.get(x, 0)].dynamic) for x in range(5)]
        self.assertEqual(traits, [(True, False), (True, True), (False, False), (False, False), (False, False)])
        self.assertEqual(lv.get(2, 0), lv.get(3, 0))                                       # same sprite, same traits: one tile
        self.assertEqual(len({lv.get(x, 0) for x in range(5)}), 3)                         # wall / crate / plain

    def test_inactive_disabled_and_spriteless_objects_are_left_out(self):
        b = SceneBuilder()
        b.add("On", 0, 0, self.BRICK)
        b.add("Off", 1, 0, self.BRICK, active=0)
        b.add("Disabled", 2, 0, self.BRICK, enabled=0)
        _, hidden_parent = b.add("HiddenParent", 3, 0, active=0)
        b.add("UnderOff", 0, 0, self.COIN, father=hidden_parent)                            # inactive because its parent is
        self.scene("Filter", b)
        self.run_import()
        lv = self.project.level("Filter")
        self.assertEqual((lv.width, lv.height), (1, 1))
        self.assertEqual(self.project.tiles[lv.get(0, 0)].sprite, "brick")

    def test_sheet_slices_are_found_by_their_internal_id(self):
        sheet = self.rgba_png([[RED, RED, GREEN, GREEN]])
        self.put("sheet.png", sheet, sheet_meta(2, [("left", 0, 0, 2, 1), ("right", 2, 0, 2, 1)], guid=G_SHEET, ppu=2))        # slices are 2x1 px: one unit wide at 2 ppu
        b = SceneBuilder()
        b.add("L", 0, 0, (G_SHEET, 21300000))
        b.add("R", 1, 0, (G_SHEET, 21300002))
        self.scene("Sheet", b)
        self.run_import()
        lv = self.project.level("Sheet")
        self.assertEqual([self.project.tiles[lv.get(x, 0)].sprite for x in (0, 1)], ["left", "right"])

    def test_a_cell_size_can_be_chosen_and_the_default_is_the_common_sprite_size(self):
        from .unity_scene import choose_cell
        b = SceneBuilder()
        b.add("A", 0, 0, self.BRICK)
        b.add("B", 0.4, 0, self.BRICK)
        self.scene("Close", b)
        self.run_import()
        self.assertEqual(self.project.level("Close").width, 1)                             # at the default cell (the sprite's 1 unit) they share a cell
        self.run_import(cell=0.4)
        self.assertEqual(self.project.level("Close").width, 2)                             # at 0.4 they are one cell apart
        self.assertEqual(choose_cell([]), 1.0)

    def test_what_cannot_be_imported_is_counted_in_the_notes(self):
        b = SceneBuilder()
        b.add("Rotated", 0, 0, self.BRICK, rot_z=0.5)
        b.add("OffGrid", 1.4, 0, self.BRICK)
        b.add("Big", 3, 0, self.BRICK, scale=(3, 3))
        b.add("Unknown", 5, 0, ("e" * 32, 21300000))
        b.raw("--- !u!1001 &9\nPrefabInstance:\n  m_Modification: {}\n--- !u!1839735485 &10\nTilemap:\n  m_Enabled: 1\n")
        self.scene("Notes", b)
        r = self.run_import()
        text = "\n".join(r.notes)
        for what in ("1 object is rotated", "1 object was not on the grid", "1 object is not the size of a cell", "1 prefab instance uses a prefab that was not found",
                     "could not be found among the imported textures"):
            self.assertIn(what, text)

    def test_a_scene_too_big_for_a_level_is_skipped_with_a_note(self):
        b = SceneBuilder()
        b.add("A", 0, 0, self.BRICK)
        b.add("B", 600, 0, self.BRICK)
        self.scene("Huge", b)
        r = self.run_import()
        self.assertIsNone(self.project.level("Huge"))
        self.assertTrue(any("bigger than a level can be" in n for n in r.notes))
        self.run_import(cell=2000)                                                           # a big enough cell fits it: x = 600 is 0.3 cells, which rounds to cell 0
        self.assertEqual(self.project.level("Huge").width, 1)

    def test_a_binary_scene_is_refused_with_a_message(self):
        with open(os.path.join(self.scenes, "Bin.unity"), "wb") as f:
            f.write(b"UnityFS\0\0\0\0")
        r = self.run_import()
        self.assertEqual(self.project.levels, [])
        self.assertTrue(any("Force Text" in n for n in r.notes))

    def test_sprites_only_when_scenes_are_off_and_levels_survive_the_project_file_and_the_text_format(self):
        from .asciiart import export_level, import_levels
        b = SceneBuilder()
        b.add("W", 0, 0, self.BRICK, collider=61)
        b.add("C", 1, 0, self.COIN)
        self.scene("RT", b)
        self.run_import(scenes=False)
        self.assertEqual(self.project.levels, [])
        self.run_import()
        q = Project.from_json(self.project.to_json())
        self.assertEqual(q.levels[0].cells, self.project.levels[0].cells)
        again = Project("again")
        import_levels(export_level(self.project.levels[0], self.project), again)
        self.assertEqual(again.levels[0].cells, self.project.levels[0].cells)
        self.assertTrue(any(t.solid and t.sprite == "brick" for t in again.tiles.values()))

    # ---- prefab instances
    P_CRATE, P_TOWER, P_LOOP = "1" * 32, "2" * 32, "3" * 32

    def prefab(self, name, guid, builder):
        d = os.path.join(self.root, "Assets", "Prefabs")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, name + ".prefab")
        with open(path, "w", encoding="utf-8") as f:
            f.write(builder.text())
        with open(path + ".meta", "w", encoding="utf-8") as f:
            f.write("fileFormatVersion: 2\nguid: %s\nPrefabImporter:\n  userData: \n" % guid)

    def sprites_at(self, level, project=None):
        """{(x, y): sprite name} of a level's filled cells."""
        p = project or self.project
        return {(x, y): p.tiles[level.get(x, y)].sprite for y in range(level.height) for x in range(level.width) if level.get(x, y)}

    def crate_prefab(self, sprite=None, collider=61, body=0):
        b = SceneBuilder()
        go, xf = b.add("Crate", 0, 0, sprite or self.BRICK, collider=collider, body=body)
        self.prefab("Crate", self.P_CRATE, b)
        return go, xf, b.sr

    def test_prefab_instances_are_placed_by_their_overrides_and_keep_the_prefabs_traits(self):
        _, xf, _ = self.crate_prefab()
        b = SceneBuilder()
        for x in (2, 3, 4):
            b.add("Ground%d" % x, x, 0, self.BRICK)
        b.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 2), (xf, "m_LocalPosition.y", 1)])
        b.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 4), (xf, "m_LocalPosition.y", 1)])
        self.scene("Prefabs", b)
        r = self.run_import()
        lv = self.project.level("Prefabs")
        self.assertEqual((lv.width, lv.height), (3, 2))
        self.assertEqual(self.rows(lv)[0].count("."), 1)                                                      # the crates at x = 2 and 4, a gap between
        top = [self.project.tiles[lv.get(x, 0)] if lv.get(x, 0) else None for x in range(3)]
        self.assertTrue(top[0].solid and top[0].dynamic and top[2].solid and top[2].dynamic and top[1] is None)    # the prefab's collider and dynamic body came with it
        self.assertFalse(self.project.tiles[lv.get(0, 1)].solid)                                               # the plain ground bricks are not those tiles
        self.assertEqual(r.notes, [])

    def test_a_prefabs_children_follow_the_instance(self):
        b = SceneBuilder()
        _, root = b.add("Root", 0, 0)
        b.add("Brick", 1, 0, self.BRICK, father=root)
        b.add("Coin", 2, 0, self.COIN, father=root)
        self.prefab("Tower", self.P_TOWER, b)
        s = SceneBuilder()
        s.add("Anchor", 5, 0, self.BRICK)
        s.instance(self.P_TOWER, [(root, "m_LocalPosition.x", 5)])                                             # children are at 6 and 7
        self.scene("Kids", s)
        self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Kids")), {(0, 0): "brick", (1, 0): "brick", (2, 0): "coin"})

    def test_prefabs_that_contain_prefabs_and_overrides_that_reach_into_them(self):
        _, crate_xf, _ = self.crate_prefab(collider=None, body=None)
        b = SceneBuilder()
        b.instance(self.P_CRATE, [(crate_xf, "m_LocalPosition.y", 1)])                                          # the tower holds a crate, one up...
        b.add("Top", 0, 2, self.COIN)                                                                           # ...and a coin two up
        self.prefab("Tower", self.P_TOWER, b)
        s = SceneBuilder()
        s.add("Anchor", 0, 0, self.BRICK)
        s.instance(self.P_TOWER, [(crate_xf, "m_LocalPosition.x", 3)])                                          # the scene moves the nested crate across
        self.scene("Nest", s)
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Nest")), {(0, 0): "coin", (3, 1): "brick", (0, 2): "brick"})
        self.assertEqual(r.notes, [])

    def test_an_override_can_change_the_sprite_and_switch_an_object_off(self):
        go, xf, sr = self.crate_prefab(collider=None, body=None)
        s = SceneBuilder()
        s.add("Anchor", 0, 0, self.BRICK)
        s.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 1), (sr, "m_Sprite", 0, (21300000, G_COIN))])      # a coin, not a brick
        s.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 2), (go, "m_IsActive", 0)])                         # switched off: not placed
        self.scene("Over", s)
        self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Over")), {(0, 0): "brick", (1, 0): "coin"})

    def test_an_instance_under_a_scene_object_is_offset_by_that_object(self):
        _, xf, _ = self.crate_prefab(collider=None, body=None)
        s = SceneBuilder()
        _, mover = s.add("Mover", 10, 0, self.BRICK)
        s.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 1)], parent=mover)                                   # world x = 10 + 1
        self.scene("Under", s)
        self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Under")), {(0, 0): "brick", (1, 0): "brick"})

    def test_a_scene_object_parented_to_an_object_inside_a_prefab_instance(self):
        _, xf, _ = self.crate_prefab(collider=None, body=None)
        s = SceneBuilder()
        inst = s.instance(self.P_CRATE, [(xf, "m_LocalPosition.x", 5)])
        stand_in = s.stripped_transform(inst, xf)                                                               # how the scene names the crate's transform
        s.add("Coin", 1, 0, self.COIN, father=stand_in)                                                         # world x = 5 + 1
        self.scene("Child", s)
        self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Child")), {(0, 0): "brick", (1, 0): "coin"})

    def test_missing_prefabs_loops_and_unplaceable_overrides_are_reported_not_fatal(self):
        loop = SceneBuilder()
        loop.add("Brick", 0, 0, self.BRICK)
        loop.instance(self.P_LOOP)                                                                              # a prefab that contains itself
        self.prefab("Loop", self.P_LOOP, loop)
        _, xf, _ = self.crate_prefab(collider=None, body=None)
        s = SceneBuilder()
        s.add("Anchor", 0, 0, self.COIN)
        s.instance(self.P_LOOP, [(xf, "m_LocalPosition.x", 1)])
        s.instance("9" * 32)                                                                                    # no such prefab
        s.instance(self.P_CRATE, [(987654, "m_LocalPosition.x", 4)])                                            # names an object the prefab does not have
        self.scene("Bad", s)
        r = self.run_import()                                                                                   # (returning at all means the loop did not spin)
        text = "\n".join(r.notes)
        self.assertIn("1 prefab instance uses a prefab that was not found", text)
        self.assertIn("nested in a loop", text)
        self.assertIn("1 prefab override names an object", text)
        self.assertIsNotNone(self.project.level("Bad"))

    def test_prefab_files_are_not_scenes_and_a_scene_without_prefabs_still_imports(self):
        self.crate_prefab()
        self.assertEqual(self.run_import().levels, [])                                                          # a prefab alone makes no level
        s = SceneBuilder()
        s.add("A", 0, 0, self.BRICK)
        self.scene("Plain", s)
        self.assertEqual(len(self.run_import().levels), 1)

    # ---- tilemaps (blocks written the way Unity serializes them: `first:`/`second:` tiles indexing a sprite array whose unused slots are {fileID: 0})
    def tilemap_scene(self, name, **kw):
        """A scene with a Grid and, under it, a Tilemap of `tiles` (kw: tiles, sprites, ... for add_tilemap; grid_cell, grid_x, grid_y for the Grid)."""
        b = SceneBuilder()
        _, grid = b.add_grid(cell=kw.pop("grid_cell", (1, 1)), x=kw.pop("grid_x", 0), y=kw.pop("grid_y", 0), layout=kw.pop("layout", 0))
        b.add_tilemap("Tiles", father=grid, **kw)
        self.scene(name, b)
        return b

    def test_a_tilemap_becomes_tiles_with_the_collider_deciding_solid(self):
        self.tilemap_scene("Floor", tiles=[(x, 0, 0) for x in range(4)], sprites=[self.BRICK], collider=True)
        r = self.run_import()
        lv = self.project.level("Floor")
        self.assertEqual((lv.width, lv.height), (4, 1))
        self.assertEqual(set(self.sprites_at(lv).values()), {"brick"})
        self.assertTrue(all(self.project.tiles[lv.get(x, 0)].solid for x in range(4)))
        self.assertEqual(r.notes, [])
        self.tilemap_scene("Soft", tiles=[(0, 0, 0)], sprites=[self.BRICK], collider=False)
        self.run_import()
        self.assertFalse(self.project.tiles[self.project.level("Soft").get(0, 0)].solid)

    def test_cells_can_be_negative_and_y_points_up(self):
        self.tilemap_scene("Neg", tiles=[(-2, -1, 0), (-1, -1, 0), (0, -1, 0), (0, 0, 1)], sprites=[self.BRICK, self.COIN])
        self.run_import()
        lv = self.project.level("Neg")
        self.assertEqual(self.sprites_at(lv), {(2, 0): "coin", (0, 1): "brick", (1, 1): "brick", (2, 1): "brick"})

    def test_the_sprite_index_picks_from_the_array_and_an_empty_slot_is_counted(self):
        self.tilemap_scene("Slots", tiles=[(0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 9)], sprites=[self.BRICK, None, self.COIN])     # slot 1 is {fileID: 0}; 9 is out of range
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Slots")), {(0, 0): "brick", (2, 0): "coin"})
        self.assertTrue(any("2 tiles have no sprite and were skipped" in n for n in r.notes))

    def test_sliced_sprites_are_found_by_their_64_bit_internal_ids(self):
        ids = [-7963366471572989131, 5027406166034386782]                                    # what Unity writes for sprites cut in the sprite editor
        sheet = self.rgba_png([[RED, RED, GREEN, GREEN]] * 2)
        self.put("big.png", sheet, sheet_meta(2, [("left", 0, 0, 2, 2), ("right", 2, 0, 2, 2)], guid=G_SHEET, ppu=2, ids=ids))
        self.tilemap_scene("Sheet64", tiles=[(0, 0, 0), (1, 0, 1)], sprites=[(G_SHEET, ids[0]), (G_SHEET, ids[1])])
        self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Sheet64")), {(0, 0): "left", (1, 0): "right"})

    def test_a_sprite_that_was_not_imported_is_reported(self):
        self.tilemap_scene("Gone", tiles=[(0, 0, 0), (1, 0, 1)], sprites=[self.BRICK, ("e" * 32, 21300000)])
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Gone")), {(0, 0): "brick"})
        self.assertTrue(any("could not be found among the imported textures" in n for n in r.notes))

    def test_the_tilemaps_transform_and_scale_carry_its_tiles(self):
        self.tilemap_scene("Moved", tiles=[(0, 0, 0), (1, 0, 0)], sprites=[self.BRICK], x=10, y=5, grid_x=100)                     # both are offsets: one level, 2 wide
        self.run_import()
        self.assertEqual(self.project.level("Moved").width, 2)
        b = SceneBuilder()
        _, grid = b.add_grid(scale=(2, 2))                                                   # a Grid scaled 2x: cells are 2 world units, so sprites are half a cell
        b.add_tilemap("Tiles", [(0, 0, 0), (1, 0, 0)], [self.BRICK], father=grid)
        self.scene("Scaled", b)
        r = self.run_import()
        self.assertEqual(self.project.level("Scaled").width, 2)
        self.assertEqual(r.notes, [])                                                        # the scale makes the 1-unit sprites 2 units: exactly the 2-unit cell

    def test_sprites_centred_in_a_tiles_cell_share_it_and_others_are_reported_off_grid(self):
        b = SceneBuilder()
        _, grid = b.add_grid()
        b.add_tilemap("Tiles", [(0, 0, 0), (1, 0, 0)], [self.BRICK], father=grid, x=10, y=5, order=0)           # cell 0 is centred at (10.5, 5.5)
        b.add("Coin", 10.5, 5.5, self.COIN, order=5)                                           # in that cell, drawn above the tile
        b.add("Stray", 13, 5, self.BRICK)                                                     # on a cell's corner, not in one
        self.scene("Phase", b)
        r = self.run_import()
        lv = self.project.level("Phase")
        sprites = self.sprites_at(lv)
        self.assertEqual(sprites[(0, 0)], "coin")                                              # the coin took the tile's cell
        self.assertEqual(sprites[(1, 0)], "brick")
        text = "\n".join(r.notes)
        self.assertIn("1 object was hidden behind another sprite", text)
        self.assertIn("1 object was not on the grid", text)

    def test_the_grids_cell_size_sets_the_level_grid(self):
        self.tilemap_scene("Fine", tiles=[(0, 0, 0), (1, 0, 0), (2, 0, 0)], sprites=[self.BRICK], grid_cell=(0.5, 0.5))                # a 1-unit sprite on a half-unit grid
        r = self.run_import()
        lv = self.project.level("Fine")
        self.assertEqual(lv.width, 3)                                                          # a tile is a cell, whatever its sprite's size
        self.assertTrue(any("not the size of a cell" in n for n in r.notes))

    def test_off_and_disabled_tilemaps_place_nothing(self):
        self.tilemap_scene("Off", tiles=[(0, 0, 0)], sprites=[self.BRICK], renderer_enabled=0)
        self.assertEqual(self.run_import().levels, [])
        self.tilemap_scene("Inactive", tiles=[(0, 0, 0)], sprites=[self.BRICK], active=0)
        self.run_import()
        self.assertIsNone(self.project.level("Inactive"))

    def test_an_empty_tilemap_is_harmless(self):
        b = SceneBuilder()
        _, grid = b.add_grid()
        b.add_tilemap("Empty", [], [], father=grid)                                           # `m_Tiles: {}`
        b.add("Brick", 0, 0, self.BRICK)
        self.scene("Blank", b)
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Blank")), {(0, 0): "brick"})

    def test_flipped_tiles_and_isometric_grids_are_reported(self):
        self.tilemap_scene("Flip", tiles=[(0, 0, 0, 0), (1, 0, 0, 1)], sprites=[self.BRICK], matrices=[(1, 0, 0, 1), (-1, 0, 0, 1)])
        r = self.run_import()
        self.assertTrue(any("1 tile is rotated or flipped" in n for n in r.notes))
        self.tilemap_scene("Iso", tiles=[(0, 0, 0)], sprites=[self.BRICK], layout=2)
        r = self.run_import()
        self.assertTrue(any("1 tilemap is on an isometric or hexagonal grid" in n for n in r.notes))

    def test_a_tilemap_inside_a_prefab_is_placed_by_the_instance(self):
        pb = SceneBuilder()
        _, grid = pb.add_grid()
        pb.add_tilemap("Tiles", [(0, 0, 0), (1, 0, 0)], [self.BRICK], father=grid)
        self.prefab("Room", self.P_TOWER, pb)
        s = SceneBuilder()
        s.instance(self.P_TOWER, [(grid, "m_LocalPosition.x", 5)])                           # the room's grid is moved to x = 5: tile 0 is centred at 5.5
        s.add("Coin", 5.5, 0.5, self.COIN, order=3)                                          # on that tile's cell
        self.scene("Rooms", s)
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Rooms")), {(0, 0): "coin", (1, 0): "brick"})

    def test_an_auto_named_tileset_keeps_each_tile_its_own_sprite(self):
        ids = [11, 22]
        self.put("tiles.png", self.rgba_png([[RED, RED, GREEN, GREEN]] * 2), sheet_meta(2, [("tiles_0", 0, 0, 2, 2), ("tiles_1", 2, 0, 2, 2)], guid=G_SHEET, ppu=2, ids=ids))
        self.tilemap_scene("Set", tiles=[(0, 0, 0), (1, 0, 1)], sprites=[(G_SHEET, 11), (G_SHEET, 22)])
        r = self.run_import()
        lv = self.project.level("Set")
        self.assertEqual(self.sprites_at(lv), {(0, 0): "tiles_0", (1, 0): "tiles_1"})                          # not both "tiles": grass and dirt stay different tiles
        self.assertNotEqual(lv.get(0, 0), lv.get(1, 0))
        self.assertEqual(r.notes, [])

    def test_a_later_frame_of_a_hand_named_animation_is_reported(self):
        ids = [31, 32]
        self.put("hero.png", self.rgba_png([[RED, RED, GREEN, GREEN]] * 2), sheet_meta(2, [("walk_0", 0, 0, 2, 2), ("walk_1", 2, 0, 2, 2)], guid=G_SHEET, ppu=2, ids=ids))
        s = SceneBuilder()
        s.add("A", 0, 0, (G_SHEET, 31))                                                                        # frame 0: fine
        s.add("B", 1, 0, (G_SHEET, 32))                                                                        # frame 1: the level can only show frame 0
        self.scene("Walk", s)
        r = self.run_import()
        self.assertEqual(self.sprites_at(self.project.level("Walk")), {(0, 0): "walk", (1, 0): "walk"})
        self.assertTrue(any("1 object or tile shows a later frame of an animated sprite" in n for n in r.notes))
        self.assertEqual(len(self.project.sprite("walk").frames), 2)

    def test_importing_again_reuses_the_tiles(self):
        from .unity_scene import import_unity_scenes
        b = SceneBuilder()
        b.add("W", 0, 0, self.BRICK, collider=61)
        self.scene("Twice", b)
        self.run_import()
        n_tiles = len(self.project.tiles)
        import_unity_scenes(self.project, self.root, self.report)
        self.assertEqual(len(self.project.tiles), n_tiles)
        self.assertEqual([l.name for l in self.project.levels], ["Twice", "Twice 2"])


class Effects(unittest.TestCase):
    """The effect registry as Python sees it (fxdefs.py is generated from src/native/gfx2d/fx/*.fx) and how values are packed for gfx_effect."""

    def test_registry_is_consistent(self):
        self.assertTrue(EFFECTS)
        self.assertEqual(len({e["id"] for e in EFFECTS.values()}), len(EFFECTS))
        for name, e in EFFECTS.items():
            self.assertEqual(BY_ID[e["id"]], name)
            for p in e["params"]:
                self.assertLessEqual(p["offset"] + p["size"], PARAM_FLOATS)
                self.assertEqual(len(p["default"]), p["size"])
                if p["type"] == "color":
                    self.assertEqual(p["offset"] % 4, 0, "a color is read as one vec4 on the GPU")
                else:
                    self.assertTrue(p["min"] <= p["default"][0] <= p["max"])

    def test_defaults_when_nothing_is_given(self):
        eid, floats = fx.pack("tint")
        self.assertEqual(eid, EFFECTS["tint"]["id"])
        self.assertEqual(len(floats), PARAM_FLOATS)
        self.assertEqual(floats[:5], [1.0, 0.5, 0.1, 1.0, 0.5])      # the colour, then the amount: what tint.fx says
        self.assertEqual(fx.defaults("bright_contrast"), {"brightness": 0.0, "contrast": 0.0})

    def test_values_land_where_the_registry_says(self):
        _, floats = fx.pack("bright_contrast", {"contrast": 0.25})
        self.assertEqual(floats[:2], [0.0, 0.25])
        _, floats = fx.pack("tint", {"color": (0.2, 0.4, 0.6), "amount": 1.0})
        self.assertEqual(floats[:5], [0.2, 0.4, 0.6, 1.0, 1.0])        # three numbers: alpha 1

    def test_values_are_brought_into_range(self):
        _, floats = fx.pack("bright_contrast", {"brightness": 9, "contrast": -9})
        self.assertEqual(floats[:2], [1.0, -1.0])
        _, floats = fx.pack("tint", {"color": (2, -1, 0.5, 7)})
        self.assertEqual(floats[:4], [1.0, 0.0, 0.5, 1.0])

    def test_refusals(self):
        with self.assertRaises(KeyError):
            fx.pack("no_such_effect")
        with self.assertRaises(KeyError):
            fx.pack("tint", {"hue": 1})
        with self.assertRaises(ValueError):
            fx.pack("tint", {"amount": float("nan")})
        with self.assertRaises(ValueError):
            fx.pack("tint", {"color": (1, 2)})

    def test_int_bool_and_enum_parameters(self):
        demo = {"id": 200, "title": "Demo", "group": "", "nparams": 3, "params": [
            {"name": "steps", "type": "int", "label": "Steps", "offset": 0, "size": 1, "min": 1.0, "max": 8.0, "default": [4.0]},
            {"name": "flip", "type": "bool", "label": "Flip", "offset": 1, "size": 1, "min": 0.0, "max": 1.0, "default": [0.0]},
            {"name": "mode", "type": "enum", "label": "Mode", "offset": 2, "size": 1, "min": 0.0, "max": 2.0, "default": [0.0], "options": ["Add", "Mul", "Screen"]}]}
        with mock.patch.dict(EFFECTS, {"demo": demo}):
            _, floats = fx.pack("demo", {"steps": 2.6, "flip": True, "mode": "Screen"})
            self.assertEqual(floats[:3], [3.0, 1.0, 2.0])               # an int is rounded, a bool is 0 or 1, an enum may be named by its label
            _, floats = fx.pack("demo", {"steps": 99, "mode": 1})
            self.assertEqual(floats[:3], [8.0, 0.0, 1.0])
            with self.assertRaises(ValueError):
                fx.pack("demo", {"mode": "Divide"})


if __name__ == "__main__":
    unittest.main()


class LevelEffects(unittest.TestCase):
    def project(self):
        from .model import Level, Project
        p = Project("fx")
        lv = p.add_level(Level("a", 3, 2))
        lv.effects = [{"effect": "blend", "values": {"mode": 12, "color": [0.1, 0.2, 0.3, 0.4], "opacity": 0.5}, "enabled": False},
                      {"effect": "levels", "values": {"gamma": 2.0}, "enabled": True}]
        p.add_level(Level("b", 2, 2))
        return p

    def test_effects_survive_the_json_round_trip_and_a_level_without_any_writes_none(self):
        from .model import Project
        p = self.project()
        data = p.to_json()
        self.assertNotIn("effects", data["levels"][1])
        back = Project.from_json(json.loads(json.dumps(data)))
        self.assertEqual(back.levels[0].effects, p.levels[0].effects)
        self.assertEqual(back.levels[1].effects, [])

    def test_a_project_with_a_bad_effect_is_refused_with_the_place(self):
        from .model import Project, ProjectError
        good = self.project().to_json()
        for what, edit in (("an unknown effect", lambda e: e.update(effect="nope")),
                           ("an unknown parameter", lambda e: e.update(values={"nope": 1})),
                           ("a value that is not a number", lambda e: e.update(values={"gamma": "x"})),
                           ("effects that are not a list", None)):
            data = json.loads(json.dumps(good))
            if edit:
                edit(data["levels"][0]["effects"][1])
            else:
                data["levels"][0]["effects"] = {}
            with self.assertRaises(ProjectError, msg=what) as cm:
                Project.from_json(data)
            self.assertIn("levels[0]", str(cm.exception), what)


class ViewportEffects(unittest.TestCase):
    """The viewport hands the level's enabled effects to the engine in order (the engine is a recorder here, so no library is needed)."""

    def test_enabled_effects_are_queued_in_order_and_bad_entries_skipped(self):
        from .engine import Viewport
        from .model import Level, Project
        calls = []

        class Recorder:
            def effect(self, name, values=None):
                from .fx import pack
                pack(name, values)
                calls.append((name, values))

        lv = Level("l", 2, 2)
        lv.effects = [{"effect": "tint", "values": {"amount": 0.3}, "enabled": True},
                      {"effect": "blend", "values": {}, "enabled": False},
                      {"effect": "gone", "values": {}, "enabled": True},
                      {"effect": "levels", "values": {"gamma": 2.0}}]
        vp = Viewport(Recorder(), Project())
        vp._apply_effects(lv)
        vp._apply_effects(None)
        self.assertEqual(calls, [("tint", {"amount": 0.3}), ("levels", {"gamma": 2.0})])


class LevelLights(unittest.TestCase):
    def level(self):
        from .model import Level
        lv = Level("l", 10, 6)
        from . import lights as L
        lv.lights = [L.new_light("point", 2, 1), L.new_light("spot", 8, 4)]
        lv.lights[1]["enabled"] = False
        return lv

    def test_lights_and_lighting_round_trip_and_a_plain_level_writes_neither(self):
        from .model import Level, Project
        p = Project("p")
        lv = p.add_level(self.level())
        lv.lighting["glow"] = 0.4
        p.add_level(Level("plain", 2, 2))
        data = json.loads(json.dumps(p.to_json()))
        self.assertNotIn("lights", data["levels"][1])
        self.assertNotIn("lighting", data["levels"][1])
        back = Project.from_json(data)
        self.assertEqual(back.levels[0].lights, lv.lights)
        self.assertEqual(back.levels[0].lighting, lv.lighting)
        self.assertEqual(back.levels[1].lights, [])

    def test_bad_lights_are_refused_with_the_place_and_numbers_are_brought_into_range(self):
        from .model import Project, ProjectError
        p = Project("p")
        p.add_level(self.level())
        good = p.to_json()
        for what, edit in (("an unknown kind", lambda d: d["lights"][0].update(kind="laser")), ("a NaN", lambda d: d["lights"][0].update(x=float("nan"))),
                           ("a color of two numbers", lambda d: d["lights"][0].update(color=[1, 1])), ("lights not a list", lambda d: d.update(lights={}))):
            data = json.loads(json.dumps(good, allow_nan=True))
            edit(data["levels"][0])
            with self.assertRaises(ProjectError, msg=what) as cm:
                Project.from_json(data)
            self.assertIn("levels[0]", str(cm.exception), what)
        data = json.loads(json.dumps(good))
        data["levels"][0]["lights"][0]["intensity"] = 99
        self.assertEqual(Project.from_json(data).levels[0].lights[0]["intensity"], 4.0)

    def test_the_effect_values_follow_the_camera(self):
        from . import lights as L
        from .fx import pack
        lv = self.level()
        lv.lights[1]["enabled"] = True
        # a camera on the level's middle (5, 3) that sees 3 cells up and down and is 5/3 as wide as high
        v = L.effect_values(lv, 5.0, 3.0, 3.0, 5.0 / 3.0)
        self.assertAlmostEqual(v["l0x"], (2 - 5) / (2 * 3 * 5 / 3) + 0.5)       # 3 cells left of the middle: 0.2
        self.assertAlmostEqual(v["l0y"], 0.5 - ((6 - 1) - 3) / 6.0)              # the level's row 1 is 2 cells above the middle: y 1/6 from the top
        self.assertAlmostEqual(v["l0r"], 4 / 6.0)
        self.assertEqual((v["l0t"], v["l1t"]), (0, 1))
        self.assertEqual(pack("scene_lights", v)[0], 16)
        panned = L.effect_values(lv, 6.0, 3.0, 3.0, 5.0 / 3.0)                   # the camera moved right: the light moves left on the screen
        self.assertLess(panned["l0x"], v["l0x"])
        lv.lights[1]["enabled"] = False
        self.assertNotIn("l1x", L.effect_values(lv, 5.0, 3.0, 3.0, 5.0 / 3.0))
        lv.lights[0]["enabled"] = False
        self.assertIsNone(L.effect_values(lv, 5.0, 3.0, 3.0, 5.0 / 3.0))
        lv.lights[0]["enabled"] = True
        lv.lighting["enabled"] = False
        self.assertIsNone(L.effect_values(lv, 5.0, 3.0, 3.0, 5.0 / 3.0))

    def test_the_viewport_hands_the_lights_to_the_engine_before_the_effects(self):
        from .engine import Viewport
        from .model import Project
        calls = []

        class Recorder:
            def effect(self, name, values=None):
                from .fx import pack
                pack(name, values)
                calls.append(name)

        lv = self.level()
        lv.effects = [{"effect": "tint", "values": {}, "enabled": True}]
        vp = Viewport(Recorder(), Project())
        vp._apply_lights(lv)
        vp._apply_effects(lv)
        self.assertEqual(calls, ["scene_lights", "tint"])



class ScriptLanguages(unittest.TestCase):
    """A script is a file in one language (languages.py): its template, which classes in it are scripts, what the project file says, and what the build does with it."""

    def test_the_languages_and_their_files(self):
        self.assertEqual(list(languages.LANGUAGES), ["csharp", "cpp", "rust", "rpython"])
        self.assertEqual([l.ext for l in languages.LANGUAGES.values()], [".cs", ".cpp", ".rs", ".py"])
        self.assertEqual([l.name for l in languages.LANGUAGES.values()], ["C#", "C++", "Rust", "RPython"])
        self.assertEqual(languages.DEFAULT, "csharp")
        self.assertEqual(languages.by_extension("Spinner.RS").id, "rust")
        self.assertIsNone(languages.by_extension("Spinner.txt"))
        with self.assertRaises(languages.UnknownLanguage) as e:
            languages.get("cobol")
        self.assertIn("csharp, cpp, rust, rpython", str(e.exception))
        with self.assertRaises(ValueError):                                          # (UnknownLanguage is a ValueError)
            ScriptFile("A", "", "cobol")

    def test_each_template_is_a_script_with_its_class_and_only_it(self):
        for lang in languages.LANGUAGES.values():
            text = lang.new_text("Spinner")
            self.assertEqual(lang.classes(text), ["Spinner"], lang.id)
            self.assertEqual(ScriptFile("Spinner", text, lang.id).classes(), ["Spinner"], lang.id)
            self.assertNotIn("%(name)s", text, lang.id)

    def test_a_class_is_a_script_only_with_the_marker_and_not_inside_a_comment(self):
        plain = {"csharp": "class A { }", "cpp": "class A { };", "rust": "struct A { node: i32 }", "rpython": "class A(object):\n    pass\n"}
        commented = {"csharp": "// [Script, MaxInstances(4)]\nclass A { }",
                     "cpp": "// PROWL_SCRIPT(4)\nclass A { };\n/* PROWL_SCRIPT(4)\nclass B { }; */",
                     "rust": "// #[script(max_instances = 4)]\nstruct A { node: i32 }\n/* #[script]\nstruct B {} */",
                     "rpython": "# @script(max_instances=4)\nclass A(object):\n    pass\n"}
        for lang in languages.LANGUAGES.values():
            self.assertEqual(lang.classes(plain[lang.id]), [], lang.id)
            self.assertEqual(lang.classes(commented[lang.id]), [], lang.id)

    def test_markers_in_the_shapes_people_write(self):
        cpp = languages.get("cpp")
        self.assertEqual(cpp.classes("PROWL_SCRIPT(4) struct S { int node; };\nPROWL_SCRIPT( 8 )\nclass T {\n    int node;\n};\nclass Plain { };"), ["S", "T"])
        rust = languages.get("rust")
        self.assertEqual(rust.classes("#[derive(Clone)]\n#[script(max_instances = 4)]\n#[allow(dead_code)]\npub struct S { node: i32 }\n"
                                      "#[script]\nstruct T { node: i32 }\nstruct Plain { node: i32 }"), ["S", "T"])
        rpy = languages.get("rpython")
        self.assertEqual(rpy.classes("@script(max_instances=4)\nclass S(object):\n    pass\n\n@script\n@other(1)\nclass T(S):\n    pass\n\nclass Plain(object):\n    pass\n"),
                         ["S", "T"])
        cs = languages.get("csharp")
        self.assertEqual(cs.classes("[Script, MaxInstances(2)]\npublic sealed class S { }\n[Script]\n[Other]\nclass T { }\nclass Plain { }"), ["S", "T"])

    def test_the_project_file_says_the_language_only_when_it_is_not_csharp(self):
        p = Project("langs")
        for lang in languages.LANGUAGES.values():
            p.scripts.append(ScriptFile("S_" + lang.id, lang.new_text("S_" + lang.id), lang.id))
        data = p.to_json()
        self.assertEqual([item.get("language") for item in data["scripts"]], [None, "cpp", "rust", "rpython"])
        self.assertEqual(data["version"], 2)
        back = Project.from_json(json.loads(json.dumps(data)))
        self.assertEqual([(f.name, f.language, f.text) for f in back.scripts], [(f.name, f.language, f.text) for f in p.scripts])
        self.assertEqual(back.script_classes(), {"S_csharp": "S_csharp", "S_cpp": "S_cpp", "S_rust": "S_rust", "S_rpython": "S_rpython"})

    def test_a_project_of_csharp_scripts_is_still_version_1_and_an_old_file_loads_as_csharp(self):
        p = Project("old")
        p.scripts.append(ScriptFile("A", languages.CSHARP.new_text("A")))
        data = p.to_json()
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["scripts"], [{"name": "A", "text": languages.CSHARP.new_text("A")}])      # no "language" key: what an editor without languages wrote
        back = Project.from_json(data)
        self.assertEqual(back.scripts[0].language, "csharp")
        self.assertEqual(Project().to_json()["version"], 1)

    def test_an_unknown_language_is_refused_with_its_place(self):
        data = Project("x").to_json()
        data["version"] = 2
        data["scripts"] = [{"name": "A", "text": ""}, {"name": "B", "text": "", "language": "cobol"}]
        with self.assertRaises(ProjectError) as e:
            Project.from_json(data)
        self.assertIn("scripts[1]", str(e.exception))
        self.assertIn("cobol", str(e.exception))
        data["version"] = 3
        with self.assertRaises(ProjectError):
            Project.from_json(data)

    def test_the_build_writes_each_script_under_its_languages_extension(self):
        p = Project("mixed")
        for lang in languages.LANGUAGES.values():
            p.scripts.append(ScriptFile("S_" + lang.id, lang.new_text("S_" + lang.id), lang.id))
        with tempfile.TemporaryDirectory() as d:
            b = scriptbuild.Builder(d)
            b.prepare(p)
            self.assertEqual(sorted(os.listdir(os.path.join(d, "src"))), ["S_cpp.cpp", "S_csharp.cs", "S_rpython.py", "S_rust.rs"])
            with open(os.path.join(d, "src", "S_rust.rs"), encoding="utf-8") as f:
                self.assertEqual(f.read(), languages.get("rust").new_text("S_rust"))

    def test_what_the_tool_says_is_what_the_build_result_holds_in_the_order_it_said_it(self):
        p = Project("mixed")
        p.scripts.append(ScriptFile("S_cpp", languages.get("cpp").new_text("S_cpp"), "cpp"))
        said = "S_cpp.cpp(8,1): warning PROWL0001: C++ scripts are not built yet: S_cpp will not run\n"
        with tempfile.TemporaryDirectory() as d:
            b = scriptbuild.Builder(d)
            cmd, lib = b.prepare(p)
            open(lib, "w").close()
            with open(lib + ".scripts.json", "w") as f:
                json.dump([{"id": 0, "name": "S_csharp", "language": "csharp"}], f)
            r = b.finish(lib, 0, said)                                                  # a build that worked: the library, its numbers, the warning
            self.assertTrue(r.ok)
            self.assertEqual(r.scripts, {"S_csharp": 0})
            self.assertEqual([(d_.script, d_.line, d_.severity, d_.code) for d_ in r.diagnostics], [("S_cpp", 8, "warning", "PROWL0001")])
            cmd, lib2 = b.prepare(p)                                                    # one that failed: the error and the warning, as said
            r = b.finish(lib2, 1, said + "S_csharp.cs(3,5): error CS1002: ; expected\n")
            self.assertFalse(r.ok)
            self.assertEqual([(d_.severity, d_.script) for d_ in r.diagnostics], [("warning", "S_cpp"), ("error", "S_csharp")])
            cmd, lib3 = b.prepare(p)                                                    # a failure that said no error still says that it failed, first
            r = b.finish(lib3, 1, said)
            self.assertEqual([d_.severity for d_ in r.diagnostics], ["error", "warning"])
            self.assertIn("the build failed", r.diagnostics[0].message)
            cmd, lib4 = b.prepare(p)                                                    # and one that said nothing at all
            r = b.finish(lib4, 1, "")
            self.assertEqual([d_.severity for d_ in r.diagnostics], ["error"])

    def test_a_project_of_csharp_only_writes_just_its_files(self):
        p = Project("cs")
        p.scripts.append(ScriptFile("A", languages.CSHARP.new_text("A")))
        with tempfile.TemporaryDirectory() as d:
            scriptbuild.Builder(d).prepare(p)
            self.assertEqual(os.listdir(os.path.join(d, "src")), ["A.cs"])


# What each front end really says, captured from tools/cpprust.py, shivyc (Rust) and tools/py2c.py on scripts with a mistake in them (paths as the build gives them: the file name alone).
CPPRUST_PLACED = "cpprust: syn.cpp:4: cannot parse member 'void f(' in class A\n"
CPPRUST_PLACE_LESS = "cpprust: class C: `virtual` inheritance is not in the C++ subset. Use a base with no data members (any number of those may be inherited).\n"
CRUST_PARSER = "\x1b[1mshivyc: \x1b[31merror:\x1b[0m crust: syn.rs: line 5: unexpected ';' in expression\n"
SHIVYC_ON_RUST = "\x1b[1mundef.rs:5:16: \x1b[31merror:\x1b[0m use of undeclared identifier 'nothere'\n      self->x = (nothere + 1);\n  \x1b[33m               -------\x1b[0m\n"
PY2C_SYNTAX = "  runtime -> pyout/shivyc_rt.{h,c}\n  SYNTAX ERROR in syn.py: invalid syntax (syn.py, line 6)\nTranspiled 0/1 files into pyout\n"
GCC_ON_GENERATED = ("undef.c: In function 'D_f':\nundef.c:5:38: error: 'nothere' undeclared (first use in this function)\n"
                    "    5 | static void D_f(D *this) { this->x = nothere + 1; }\nundef.c:5:38: note: each undeclared identifier is reported only once for each function it appears in\n")


class ScriptDiagnostics(unittest.TestCase):
    """Each language's tool says its errors its own way; the problems list reads them all (scriptbuild.parse_diagnostics)."""

    def parsed(self, text):
        return [(d.script, d.line, d.col, d.severity, d.code, d.message) for d in scriptbuild.parse_diagnostics(text)]

    def test_cpp(self):
        self.assertEqual(self.parsed(CPPRUST_PLACED), [("syn", 4, 1, "error", "", "cannot parse member 'void f(' in class A")])
        (d,) = scriptbuild.parse_diagnostics(CPPRUST_PLACE_LESS)                       # (it names no file and line: an error with no place, not a lost one)
        self.assertEqual((d.script, d.line, d.severity), ("", 0, "error"))
        self.assertIn("`virtual` inheritance", d.message)

    def test_rust_in_both_of_the_shapes_shivyc_says_it_and_without_its_colour_codes(self):
        self.assertEqual(self.parsed(CRUST_PARSER), [("syn", 5, 1, "error", "", "unexpected ';' in expression")])
        self.assertEqual(self.parsed(SHIVYC_ON_RUST), [("undef", 5, 1, "error", "", "use of undeclared identifier 'nothere'")])     # (the source and the ^^^^ it shows are not diagnostics)

    def test_rpython(self):
        self.assertEqual(self.parsed(PY2C_SYNTAX), [("syn", 6, 1, "error", "", "invalid syntax")])

    def test_the_c_compiler_on_generated_c_has_no_place_because_that_line_is_not_the_scripts(self):
        (d,) = scriptbuild.parse_diagnostics(GCC_ON_GENERATED)
        self.assertEqual((d.script, d.line, d.severity), ("", 0, "error"))
        self.assertIn("'nothere' undeclared", d.message)
        self.assertIn("generated C, undef.c line 5", d.message)                        # (where it was said, so that it can be looked for)

    def test_the_tools_own_lines_and_the_csharp_translators_are_as_they_were(self):
        self.assertEqual(self.parsed("Other_cpp.cpp(8,1): warning PROWL0001: C++ scripts are not built yet: Other_cpp will not run\n"),
                         [("Other_cpp", 8, 1, "warning", "PROWL0001", "C++ scripts are not built yet: Other_cpp will not run")])
        self.assertEqual(self.parsed("NoCap.rs(2,1): error GEN0001: script NoCap needs #[script(max_instances = N)] with N an integer literal\n"),
                         [("NoCap", 2, 1, "error", "GEN0001", "script NoCap needs #[script(max_instances = N)] with N an integer literal")])
        self.assertEqual(self.parsed("Teleporter.cs(10,9): error CS1002: ; expected\n"), [("Teleporter", 10, 9, "error", "CS1002", "; expected")])
        self.assertEqual(self.parsed("$ python3 tools/ccsharp/ccs2c.py x\n== translating\n"), [])                         # (not diagnostics)

    def test_a_whole_build_output_is_read_in_the_order_it_was_said(self):
        out = ("Other_cpp.cpp(8,1): warning PROWL0001: C++ scripts are not built yet: Other_cpp will not run\n== translating Native/Engine2D/Engine.cs\n" + CPPRUST_PLACED + CRUST_PARSER
               + PY2C_SYNTAX + GCC_ON_GENERATED)
        self.assertEqual([(d.severity, d.script, d.line) for d in scriptbuild.parse_diagnostics(out)],
                         [("warning", "Other_cpp", 8), ("error", "syn", 4), ("error", "syn", 5), ("error", "syn", 6), ("error", "", 0)])

    def test_a_diagnostic_reads_well_with_and_without_a_code_and_a_place(self):
        d = scriptbuild.Diagnostic
        self.assertEqual(str(d("A", 4, 1, "error", "", "bad")), "A:4: error: bad")
        self.assertEqual(str(d("A", 4, 1, "warning", "PROWL0001", "note")), "A:4: warning PROWL0001: note")
        self.assertEqual(str(d("A", 0, 0, "error", "GEN0001", "no line")), "A: error GEN0001: no line")
        self.assertEqual(str(d("", 0, 0, "error", "", "no place")), "error: no place")


def load_script_langs():
    """tools/script_langs.py (tools is not a package)."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "script_langs.py")
    spec = importlib.util.spec_from_file_location("script_langs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SL = load_script_langs()


def load_script_native():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "script_native.py")
    spec = importlib.util.spec_from_file_location("script_native", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SN = load_script_native()
TOOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "prowl2d_so.py")


class ScriptGlue(unittest.TestCase):
    """What the build generates for the scripts that are not C# (tools/script_native.py): the C# proxy, the bindings, the headers and the glue, as text (a real build runs in test_gui)."""
    API = [("int", "NewNode", []), ("void", "SetPos", [("int", "node"), ("float", "x"), ("float", "y")]), ("float", "NodeX", [("int", "node")]),
           ("int", "KeyDown", [("int", "key")]), ("void", "Step", [("float", "dt")]), ("int", "Init", [("int", "w"), ("int", "h")])]
    SCRIPT = {"name": "Mover", "language": "cpp", "capacity": 8, "callbacks": ["Update", "OnCollisionBegin2D", "OnTriggerEnter2D"], "line": 3, "where": "/x/Mover.cpp:3"}

    def test_the_proxy_is_a_csharp_script_with_the_capacity_and_a_call_per_callback(self):
        cs = SN.proxy_cs(self.SCRIPT)
        self.assertIn("[Script, MaxInstances(8)]\nclass Mover", cs)
        self.assertIn("public Component Self;", cs)
        self.assertIn("public void Update() { P2DNative_Mover.Update(Self.Slot, Self.Node.Index); }", cs)
        self.assertIn("public void OnCollisionBegin2D(Collision2D hit)", cs)
        self.assertIn("P2DNative_Mover.OnCollisionBegin2D(Self.Slot, Self.Node.Index, other, hit.X, hit.Y, hit.NX, hit.NY, hit.Impulse);", cs)
        self.assertIn("public void OnTriggerEnter2D(Collider2D other)", cs)
        self.assertIn("public void Reset() { P2DNative_Mover.Reset(Self.Slot); }", cs)               # (a recycled slot starts again)
        self.assertNotIn("FixedUpdate", cs)                                                          # (only the script's own callbacks, so the scene does not call what is not there)
        self.assertTrue(gen_scripts_accepts(cs))

    def test_bindings_and_prototypes_agree(self):
        b, h = SN.bindings_cs([self.SCRIPT]), SN.glue_prototypes([self.SCRIPT])
        for proto in ("void p2dn_Mover_Reset(int slot);", "void p2dn_Mover_Update(int slot, int node);",
                      "void p2dn_Mover_OnCollisionBegin2D(int slot, int node, int other, float x, float y, float nx, float ny, float impulse);",
                      "void p2dn_Mover_OnTriggerEnter2D(int slot, int node, int other);"):
            self.assertIn(proto, h)
        self.assertIn('[Crust.Cpp("p2dn_Mover_Update({0}, {1})")] public static extern void Update(int slot, int node);', b)
        self.assertIn('[Crust.Cpp("p2dn_Mover_OnTriggerEnter2D({0}, {1}, {2})")] public static extern void OnTriggerEnter2D(int slot, int node, int other);', b)
        self.assertIn('[Crust.CppInclude("\\"p2d_native.h\\"")]', b)

    def test_a_script_is_given_the_engines_calls_and_not_the_hosts(self):
        h = SN.engine_header(self.API)
        self.assertIn("static inline void SetPos(int node, float x, float y) { p2d_set_pos(node, x, y); }", h)
        self.assertIn("static inline float NodeX(int node) { return p2d_node_x(node); }", h)
        self.assertIn("#define PROWL_SCRIPT(n)", h)
        self.assertIn("HitNY()", h)
        rs, py = SN.rust_prelude(self.API), SN.rpython_prelude(self.API)
        self.assertIn("fn set_pos(node: i32, x: f32, y: f32) { p2d_set_pos(node, x, y); }", rs)
        self.assertIn("fn node_x(node: i32) -> f32 { return p2d_node_x(node); }", rs)
        self.assertIn("def set_pos(node: int, x: float, y: float):\n    _p2d.p2d_set_pos(node, x, y)", py)
        self.assertIn("_p2d.p2d_node_x.restype = ctypes.c_float", py)
        for text in (h, rs, py):
            for host in ("Step", "Init", "p2d_step", "p2d_init", "def step", "fn step", "fn init"):
                self.assertNotIn(host, text)                                                          # (the frame and the process are the host's)

    def test_the_glue_keeps_the_instances_in_a_pool_and_sets_the_node_before_each_call(self):
        g = SN.c_glue(self.SCRIPT, lambda cb, inst, args: "%s.%s(%s)" % (inst, cb, ", ".join(args)))
        self.assertIn("static Mover p2d_pool_Mover[8];", g)
        self.assertIn("void p2dn_Mover_Reset(int slot) { p2d_pool_Mover[slot] = p2d_zero_Mover; }", g)
        self.assertIn("void p2dn_Mover_Update(int slot, int node) { p2d_pool_Mover[slot].node = node; p2d_pool_Mover[slot].Update(); }", g)
        self.assertIn("p2d_hit[3] = ny;", g)
        self.assertIn("p2d_pool_Mover[slot].OnTriggerEnter2D(other);", g)
        self.assertNotIn("p2d_hit[0] = x;", g.split("p2dn_Mover_OnTriggerEnter2D")[1])              # (only a collision has a point)
        g = SN.c_glue(self.SCRIPT, lambda cb, inst, args: "X", init="Mover___init__")               # (RPython: __init__ before the first call, and again after a reset)
        self.assertIn("if (!p2d_live_Mover[slot]) { Mover___init__(&p2d_pool_Mover[slot]); p2d_live_Mover[slot] = 1; }", g)
        self.assertIn("p2d_live_Mover[slot] = 0;", g)
        self.assertEqual(SN.glue_names(self.SCRIPT), ["p2dn_Mover_Reset", "p2dn_Mover_Update", "p2dn_Mover_OnCollisionBegin2D", "p2dn_Mover_OnTriggerEnter2D"])

    def test_the_marker_lines_of_an_rpython_script_are_commented_out_where_they_stand(self):
        text = "from prowl import script\n\n\n@script(max_instances=4)\nclass A:\n    pass\n"
        out = SN._MARKER_LINES.sub(lambda m: m.group(1) + "# " + m.group(2), text)
        self.assertEqual(out.split("\n"), ["# from prowl import script", "", "", "# @script(max_instances=4)", "class A:", "    pass", ""])


def gen_scripts_accepts(cs_text):
    """True if the C# script generator (tools/ccsharp/gen_scripts.py) accepts `cs_text` as a script file."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "ccsharp"))
    import gen_scripts
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "P.cs")
        with open(path, "w") as f:
            f.write(cs_text)
        _ns, scripts = gen_scripts.scan_file(path)
    return [(sc["name"], sc["capacity"], [c[0] for c in sc["callbacks"]], sc["reset"]) for sc in scripts] == [("Mover", 8, ["Update", "OnCollisionBegin2D", "OnTriggerEnter2D"], True)]


class ScriptScan(unittest.TestCase):
    """What the build reads from C++, Rust and RPython scripts (tools/script_langs.py): the marker, the capacity, the callbacks, and the mistakes that would make a script silently never run."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return path

    def scan(self, name, text):
        return SL.scan_file(self.write(name, text))

    def refused(self, name, text, line, *words):
        with self.assertRaises(SL.GenError) as e:
            self.scan(name, text)
        msg = str(e.exception)
        self.assertTrue(msg.startswith("%s:%d:" % (os.path.join(self.dir.name, name), line)), msg)
        for w in words:
            self.assertIn(w, msg)

    def test_each_template_is_one_script_of_16_with_an_update_at_its_markers_line(self):
        for lang in languages.LANGUAGES.values():
            if lang.id == "csharp":
                continue
            text = lang.new_text("Spinner")
            (sc,) = self.scan("Spinner" + lang.ext, text)
            marker = {"cpp": "PROWL_SCRIPT(16)", "rust": "#[script(max_instances = 16)]", "rpython": "@script(max_instances=16)"}[lang.id]
            self.assertEqual((sc["name"], sc["language"], sc["capacity"], sc["callbacks"]), ("Spinner", lang.id, 16, ["Update"]), lang.id)
            self.assertEqual(text.split("\n")[sc["line"] - 1], marker, lang.id)

    def test_the_editor_and_the_build_agree_on_which_classes_are_scripts(self):
        samples = {"cpp": "PROWL_SCRIPT(4) struct S { int node; };\nPROWL_SCRIPT( 8 )\nclass T {\n    int node;\n};\nclass Plain { };\n// PROWL_SCRIPT(1)\nclass Hidden { };\n#define PROWL_SCRIPT(n)\n",
                   "rust": "#[derive(Clone)]\n#[script(max_instances = 4)]\n#[allow(dead_code)]\npub struct S { node: i32 }\n#[script(max_instances = 2)]\nstruct T { node: i32 }\n"
                           "struct Plain { node: i32 }\n// #[script(max_instances = 1)]\nstruct Hidden { }\n",
                   "rpython": "@script(max_instances=4)\nclass S(object):\n    def __init__(self):\n        self.node: int = 0\n\n@script(2)\n@other(1)\nclass T(S):\n    def __init__(self):\n        self.node: int = 0\n\nclass Plain(object):\n    pass\n"
                              "# @script(max_instances=1)\nclass Hidden(object):\n    pass\n"}
        for lang_id, text in samples.items():
            lang = languages.get(lang_id)
            built = [sc["name"] for sc in self.scan("Many" + lang.ext, text)]
            self.assertEqual(built, ["S", "T"], lang_id)
            self.assertEqual(lang.classes(text), built, lang_id)
        for lang in languages.LANGUAGES.values():                                       # and on the templates, which is what a new script is
            if lang.id != "csharp":
                self.assertEqual(lang.classes(lang.new_text("Z")), [sc["name"] for sc in self.scan("Z" + lang.ext, lang.new_text("Z"))])

    def test_every_callback_is_found_in_each_languages_own_spelling(self):
        cpp = "".join("    void %s(%s) { }\n" % (c, "" if c in SL.LIFECYCLE else "int other") for c in SL.CALLBACKS)
        rust = "".join("    fn %s(&mut self%s) { }\n" % (SL.SNAKE[c], "" if c in SL.LIFECYCLE else ", other: i32") for c in SL.CALLBACKS)
        rpy = "".join("    def %s(self%s):\n        pass\n" % (SL.SNAKE[c], "" if c in SL.LIFECYCLE else ", other: int") for c in SL.CALLBACKS)
        (a,) = self.scan("A.cpp", "PROWL_SCRIPT(1)\nclass A {\npublic:\n    int node;\n%s};\n" % cpp)
        (b,) = self.scan("B.rs", "#[script(max_instances = 1)]\nstruct B { node: i32 }\nimpl B {\n%s}\n" % rust)
        (c,) = self.scan("C.py", "@script(max_instances=1)\nclass C(object):\n    def __init__(self):\n        self.node: int = 0\n%s" % rpy)
        for sc in (a, b, c):
            self.assertEqual(sc["callbacks"], SL.CALLBACKS, sc["language"])
        for lang_id in ("cpp", "rust", "rpython"):                                      # the templates name them all, in the same spelling
            text = languages.get(lang_id).new_text("Z")
            for cb in SL.CALLBACKS:
                self.assertIn(SL.spelling(lang_id, cb), text, (lang_id, cb))

    def test_a_callback_is_found_wherever_it_is_written_and_a_call_is_not_a_declaration(self):
        (a,) = self.scan("A.cpp", "PROWL_SCRIPT(4) class A { public: int node; void Start() { Update(); } void Update() { node = 1; } };\n")
        self.assertEqual(a["callbacks"], ["Start", "Update"])
        (b,) = self.scan("B.cpp", "PROWL_SCRIPT(4) class B { public: int node; void Start() { Update(); } };\n")
        self.assertEqual(b["callbacks"], ["Start"])                                     # (Update() is called, never declared)
        (c,) = self.scan("C.rs", "#[script(max_instances = 4)] struct C { node: i32 }\nimpl C { fn start(&mut self) { fn update(x: i32) -> i32 { x } } }\n")
        self.assertEqual(c["callbacks"], ["Start"])                                     # (a function inside a method is not the script's)
        (d,) = self.scan("D.py", "@script(max_instances=4)\nclass D(object):\n    def __init__(self):\n        self.node: int = 0\n    def start(self):\n        def update(x):\n            return x\n")
        self.assertEqual(d["callbacks"], ["Start"])

    def test_a_struct_script_is_public_and_a_class_script_must_say_so(self):
        (a,) = self.scan("A.cpp", "PROWL_SCRIPT(4) struct A { int node; void Update() { } };\n")
        self.assertEqual(a["callbacks"], ["Update"])
        self.refused("B.cpp", "PROWL_SCRIPT(4)\nclass B {\n    int node;\n    void Update() { }\n};\n", 4, "Update is not public")

    def test_a_script_that_is_wrong_is_an_error_at_its_line(self):
        self.refused("A.cpp", "// a\nPROWL_SCRIPT()\nclass A { };\n", 2, "script A needs PROWL_SCRIPT(N)", "integer literal")
        self.refused("A.cpp", "PROWL_SCRIPT(0)\nclass A { };\n", 1, "at least 1")
        self.refused("A.cpp", "PROWL_SCRIPT(MAX)\nclass A { };\n", 1, "integer literal")
        self.refused("A.cpp", "int x;\nPROWL_SCRIPT(4)\nint y;\n", 2, "directly before a class")
        self.refused("A.cpp", "PROWL_SCRIPT(4)\nclass A {\npublic:\n    int Update() { return 1; }\n};\n", 4, "Update must return void")
        self.refused("A.cpp", "PROWL_SCRIPT(4)\nclass A {\npublic:\n    void Update(int dt) { }\n};\n", 4, "Update takes no parameters")
        self.refused("A.rs", "#[script]\nstruct A { node: i32 }\n", 1, "script A needs #[script(max_instances = N)]")
        self.refused("A.rs", "#[script(max_instances = four)]\nstruct A { node: i32 }\n", 1, "integer literal")
        self.refused("A.rs", "#[script(max_instances = 4)]\nfn f() { }\n", 1, "directly before a struct")
        self.refused("A.rs", "#[script(max_instances = 4)]\nstruct A { node: i32 }\nimpl A {\n    fn update(self) { }\n}\n", 4, "update must take `&mut self`")
        self.refused("A.rs", "#[script(max_instances = 4)]\nstruct A { node: i32 }\nimpl A {\n    fn start(&mut self, x: i32) { }\n}\n", 4, "start takes no parameters")
        self.refused("A.py", "@script\nclass A(object):\n    pass\n", 1, "script A needs @script(max_instances=N)")
        self.refused("A.py", "@script(max_instances=0)\nclass A(object):\n    pass\n", 1, "at least 1")
        self.refused("A.py", "@script(max_instances=4)\ndef f():\n    pass\n", 1, "directly before a class")
        self.refused("A.py", "@script(max_instances=4)\nclass A(object):\n    x = 1\n\n    def update():\n        pass\n", 5, "update must take `self`")
        self.refused("A.py", "@script(max_instances=4)\nclass A(object):\n    def start(self, x):\n        pass\n", 3, "start takes no parameters")

    def test_comments_and_strings_do_not_make_scripts_or_hide_them(self):
        (a,) = self.scan("A.py", "# @script(max_instances=9)\ns = \"\"\"\n@script(max_instances=8)\nclass Fake(object):\n\"\"\"\n@script(max_instances=3)\nclass A(object):\n    def __init__(self):\n        self.node: int = 0\n")
        self.assertEqual((a["name"], a["capacity"], a["line"]), ("A", 3, 6))
        (b,) = self.scan("B.rs", "/* #[script(max_instances = 9)]\nstruct Fake { } */\nlet s = \"#[script(max_instances = 8)] struct Fake\";\n#[script(max_instances = 3)]\nstruct B { node: i32 }\n")
        self.assertEqual((b["name"], b["capacity"], b["line"]), ("B", 3, 4))
        self.assertEqual(self.scan("C.cpp", "/* PROWL_SCRIPT(9)\nclass Fake { }; */\nconst char *s = \"PROWL_SCRIPT(8) class Fake {\";\n"), [])

    def test_a_folder_gives_every_files_scripts_and_every_files_error_and_skips_csharp(self):
        self.write("Good.cpp", languages.get("cpp").new_text("Good"))
        self.write("Nothing.cs", "class Nothing { }")
        self.write("Plain.py", "x = 1\n")                                              # (a .py that is no script: a module)
        self.write("NoCap.rs", "#[script]\nstruct NoCap { node: i32 }\n")
        self.write("NoSelf.py", "@script(max_instances=4)\nclass NoSelf(object):\n    def update():\n        pass\n")
        scripts, errors = SL.scan_folder(self.dir.name)
        self.assertEqual([s_["name"] for s_ in scripts], ["Good"])
        self.assertEqual(errors, ["NoCap.rs(1,1): error GEN0001: script NoCap needs #[script(max_instances = N)] with N an integer literal",
                                  "NoSelf.py(3,1): error GEN0001: script NoSelf: update must take `self`, or it would never be called"])
        self.assertEqual([d_.script for d_ in scriptbuild.parse_diagnostics("\n".join(errors))], ["NoCap", "NoSelf"])      # (and the problems list reads them)

    def test_scripts_of_a_language_that_is_not_built_are_warned_about_at_their_marker(self):
        was = SL.BUILT
        SL.BUILT = ("csharp",)                                                         # (every language is built now: a build that cannot build one is what is tested)
        self.addCleanup(setattr, SL, "BUILT", was)
        self.write("A.cpp", languages.get("cpp").new_text("A"))
        self.write("B.rs", languages.get("rust").new_text("B"))
        scripts, _ = SL.scan_folder(self.dir.name)
        a_line = languages.get("cpp").new_text("A").split("\n").index("PROWL_SCRIPT(16)") + 1
        b_line = languages.get("rust").new_text("B").split("\n").index("#[script(max_instances = 16)]") + 1
        self.assertEqual(SL.unbuilt_notes(scripts), ["A.cpp(%d,1): warning PROWL0001: C++ scripts are not built yet: A will not run" % a_line,
                                                     "B.rs(%d,1): warning PROWL0001: Rust scripts are not built yet: B will not run" % b_line])

    def test_every_language_is_built_and_each_has_a_builder(self):
        self.assertEqual(SL.BUILT, ("csharp", "cpp", "rust", "rpython"))
        self.assertEqual(sorted(SN.BUILDERS), ["cpp", "rpython", "rust"])
        self.write("A.cpp", languages.get("cpp").new_text("A"))
        scripts, _ = SL.scan_folder(self.dir.name)
        self.assertEqual(SL.unbuilt_notes(scripts), [])

    def test_a_script_needs_the_field_the_engine_sets(self):
        self.refused("A.cpp", "PROWL_SCRIPT(4)\nclass A {\npublic:\n    int x;\n};\n", 1, "needs a member `int node;`")
        self.refused("A.rs", "#[script(max_instances = 4)]\nstruct A { x: i32 }\n", 1, "needs a field `node: i32`")
        self.refused("A.py", "@script(max_instances=4)\nclass A:\n    def __init__(self):\n        self.node = 0\n", 1, "needs `self.node: int = 0`")

    def test_a_collision_or_trigger_callback_takes_the_other_nodes_handle(self):
        self.refused("A.cpp", "PROWL_SCRIPT(4)\nclass A {\npublic:\n    int node;\n    void OnTriggerEnter2D(float other) { }\n};\n", 5, "takes the other node's handle")
        self.refused("A.rs", "#[script(max_instances = 4)]\nstruct A { node: i32 }\nimpl A {\n    fn on_collision_begin_2d(&mut self) { }\n}\n", 4, "takes the other node's handle")
        self.refused("A.py", "@script(max_instances=4)\nclass A:\n    def __init__(self):\n        self.node: int = 0\n    def on_trigger_enter_2d(self, other):\n        pass\n", 5, "takes the other node's handle")

    def run_tool(self, folder):
        """The tool on a folder of scripts, as far as it goes without translating anything (--no-sdl: the check for libSDL2 is not what is tested)."""
        with tempfile.TemporaryDirectory() as work:
            r = subprocess.run([sys.executable, TOOL, "--no-sdl", "--scripts", folder, "--work", os.path.join(work, "w"), "-o", os.path.join(work, "x.so")], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_the_tool_stops_on_a_script_that_is_wrong_with_all_the_errors_and_on_one_name_used_twice(self):
        self.write("NoCap.rs", "#[script]\nstruct NoCap { node: i32 }\n")
        self.write("NoSelf.py", "@script(max_instances=4)\nclass NoSelf(object):\n    def update():\n        pass\n")
        code, out = self.run_tool(self.dir.name)
        self.assertEqual(code, 1)
        self.assertIn("NoCap.rs(1,1): error GEN0001", out)
        self.assertIn("NoSelf.py(3,1): error GEN0001", out)                              # (both: one file's mistake does not hide another's)
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        for name, lang in (("Same.cpp", "cpp"), ("Other.rs", "rust")):
            with open(os.path.join(other.name, name), "w") as f:
                f.write(languages.get(lang).new_text("Same"))
        code, out = self.run_tool(other.name)
        self.assertEqual(code, 1)
        self.assertIn("error GEN0002: two scripts are called Same (Other.rs and Same.cpp)", out)                    # (across languages)


class EmojiFaces(unittest.TestCase):
    """emoji_faces.py without Blender: the parts around the render (the render itself is run by prowl.py --import-ascii with Blender and blender.py)."""

    def body_project(self):
        p = Project("p")
        import_sprites("# sprite: body\n# palette: @=#ff00ff P=#6b4a8f\n"
                       "P....P\n"
                       "P.@@.P\n"
                       "P.@@.P\n\n"
                       "PP..PP\n"
                       "P.@@.P\n"
                       "P.@@.P\n", p)
        return p

    def test_emoji_codes_are_blender_py_file_names(self):
        from .emoji_faces import emoji_code
        self.assertEqual(emoji_code("\U0001f92a"), "1f92a")
        self.assertEqual(emoji_code("☠️"), "2620")                         # the variation selector is not part of the name

    def test_the_generator_is_found_by_path_or_environment_or_not_at_all(self):
        from .emoji_faces import FaceError, find_generator
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        with open(os.path.join(d.name, "blender.py"), "w") as f:
            f.write("")
        self.assertEqual(find_generator(d.name), os.path.join(d.name, "blender.py"))                               # a folder
        self.assertEqual(find_generator(os.path.join(d.name, "blender.py")), os.path.join(d.name, "blender.py"))   # or the file
        with mock.patch.dict(os.environ, {"EMOJI_GEN": d.name}):
            self.assertEqual(find_generator(), os.path.join(d.name, "blender.py"))
        with self.assertRaises(FaceError) as e:
            find_generator(os.path.join(d.name, "nothere"))
        self.assertIn("--emoji-gen", str(e.exception))
        with mock.patch.dict(os.environ, {"EMOJI_GEN": ""}), mock.patch("os.path.isfile", return_value=False):
            with self.assertRaises(FaceError) as e:
                find_generator()
        self.assertIn("git clone", str(e.exception))

    def test_a_body_says_where_the_head_goes_in_every_frame(self):
        from .emoji_faces import marker_boxes
        p = self.body_project()
        boxes, marks = marker_boxes(p, p.sprite("body"))
        self.assertEqual(boxes, [(2, 1, 2, 2), (2, 1, 2, 2)])
        import_sprites("# sprite: bare\nPP\nPP\n", p)
        from .emoji_faces import FaceError
        with self.assertRaises(FaceError):
            marker_boxes(p, p.sprite("bare"))

    def test_the_head_replaces_the_square_and_stands_on_its_floor(self):
        from .emoji_faces import compose
        p = self.body_project()
        red = p.palette.add("r", "red", (200, 0, 0))
        head = Sprite("head", 2, 1)                              # 2 wide, 1 high: smaller than the 2x2 square, so it is centred and on the floor
        head.frames = [bytearray([red, red]), bytearray([0, red])]
        out = compose(p, "out", p.sprite("body"), head, 4)
        self.assertEqual((out.width, out.height, len(out.frames)), (6, 3, 4))
        marks = [i for i, e in enumerate(p.palette.entries) if e.rgb == (255, 0, 255)]
        self.assertTrue(all(v not in marks for f in out.frames for v in f))                               # no '@' is left: the square is the head, or empty
        self.assertEqual([out.get(0, x, 2) for x in (2, 3)], [red, red])                                    # the head's row is the floor of the square
        self.assertEqual([out.get(0, x, 1) for x in (2, 3)], [0, 0])
        self.assertEqual([out.get(1, x, 2) for x in (2, 3)], [red, red])                                    # frames 0 and 1 of 4: head frame 0 (0 * 2 // 4, 1 * 2 // 4)
        self.assertEqual([out.get(2, x, 2) for x in (2, 3)], [0, red])                                      # frame 2 is the head's second frame
        body = p.sprite("body")
        self.assertEqual([out.get(i, 1, 0) for i in range(4)], [body.get(0, 1, 0), body.get(1, 1, 0), body.get(0, 1, 0), body.get(1, 1, 0)])      # the body's frames go round

    def test_a_face_without_a_body_is_an_error_that_says_so(self):
        from .emoji_faces import FaceError, make_face_sprites
        p = Project("p")
        import_levels("# \U0001f92a = zany (face) -> body_missing\n\U0001f92a\n", p)
        with self.assertRaises(FaceError) as e:
            make_face_sprites(p)
        self.assertIn("body_missing", str(e.exception))

    def test_a_face_that_has_its_sprite_is_not_made_again(self):
        from .emoji_faces import make_face_sprites
        p = self.body_project()
        import_levels("# \U0001f92a = zany (face) -> body\n\U0001f92a\n", p)
        p.tiles["\U0001f92a"].sprite = "body"                    # (as after a first run, or from a saved project)
        with mock.patch("prowl_editor.emoji_faces.find_generator", side_effect=AssertionError("must not run")):
            self.assertEqual(make_face_sprites(p), [])


class SlimeJumpFacesAssets(unittest.TestCase):
    """The files of Samples/SlimeJumpFaces and tools/slime_faces that need no Blender: the bodies, the level, and that the level and Level.cs agree."""
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def tool(self, name):
        spec = importlib.util.spec_from_file_location("slime_faces_" + name, os.path.join(self.ROOT, "tools", "slime_faces", name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def read(self, *path):
        with open(os.path.join(self.ROOT, *path), encoding="utf-8") as f:
            return f.read()

    def test_the_bodies_file_is_what_make_bodies_writes(self):
        from . import asciiart
        self.assertEqual(self.tool("make_bodies").text(), self.read("tools", "slime_faces", "bodies.txt"))          # (so the art can be changed in one place)
        blocks = asciiart.parse_sprite_text(self.read("tools", "slime_faces", "bodies.txt"))
        self.assertEqual([b.name for b in blocks], ["body_spring", "body_jet", "body_spider", "body_golem"])
        for b in blocks:
            self.assertEqual(len(b.frames), 4, b.name)
            self.assertEqual(b.header_colors["@"], (255, 0, 255), b.name)                                         # the colour emoji_faces.py looks for
            for rows in b.frames:
                self.assertEqual({len(r) for r in rows}, {len(b.frames[0][0])}, b.name)                           # every frame is the same size
                self.assertEqual(len(rows), len(b.frames[0]), b.name)
                cells = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "@"]
                xs, ys = [x for x, _ in cells], [y for _, y in cells]
                self.assertEqual((max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(cells)), (32, 32, 1024), b.name)      # a full 32 x 32 square: the head

    def test_the_level_is_the_shaft_with_four_faces_that_have_bodies(self):
        from . import asciiart
        (block,) = asciiart.parse_level_text(self.read("Samples", "SlimeJumpFaces", "level.txt"))
        self.assertEqual((len(block.rows), {len(r) for r in block.rows}, block.empty), (96, {18}, "⬛"))
        bodies = {b.name for b in asciiart.parse_sprite_text(self.read("tools", "slime_faces", "bodies.txt"))}
        faces = {g: traits for g, (_, _, traits) in block.legend.items() if any(t.startswith("face") for t in traits)}
        self.assertEqual(sorted(faces), sorted(["\U0001f92a", "\U0001f620", "\U0001f631", "\U0001f92f"]))
        for g in faces:
            self.assertIn(block.legend[g][1], bodies)                                                              # `-> body` is one of the bodies
        project = Project("p")
        import_levels(self.read("Samples", "SlimeJumpFaces", "level.txt"), project)
        self.assertEqual([t.emoji for t in project.tiles.values() if t.face], list(faces))

    def test_level_txt_and_level_cs_agree_and_the_check_notices_when_they_do_not(self):
        build = self.tool("build")
        self.assertEqual(build.check(), ["\U0001f92a", "\U0001f620", "\U0001f631", "\U0001f92f"])                   # kind 2 first, as Level.EnemyKind says
        lines = self.read("Samples", "SlimeJumpFaces", "level.txt").split("\n")
        row = next(i for i, l in enumerate(lines) if l.startswith("\U0001f9f1") and "\U0001f92a" in l)             # the row of the zany face (a level row, not the legend)
        col = lines[row].index("\U0001f92a")                                                                       # (every emoji of this level is one character)
        moved = list(lines)
        moved[row] = lines[row].replace("\U0001f92a", "⬛")
        moved[row + 3] = lines[row + 3][:col] + "\U0001f92a" + lines[row + 3][col + 1:]                           # three cells lower: not where the game puts it
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = os.path.join(d.name, "level.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(moved))
        build.LEVEL = path
        with self.assertRaises(SystemExit) as e:                                                                   # the zany face is gone from where the game puts it
            build.check()
        self.assertIn("enemy 0", str(e.exception))


@unittest.skipUnless(os.environ.get("BLENDER") and os.path.isfile(os.path.join(os.environ.get("EMOJI_GEN", ""), "blender.py")),
                     "needs Blender ($BLENDER) and the emoji generator ($EMOJI_GEN: the folder of its blender.py)")
class EmojiFacesWithBlender(unittest.TestCase):
    """The whole chain: prowl.py --import-ascii runs blender.py (which runs Blender), renders the Grease Pencil head with Cycles and puts it on an ASCII body."""
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_a_face_in_a_level_becomes_a_sprite_on_its_body(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        level = os.path.join(d.name, "faces.txt")
        with open(level, "w", encoding="utf-8") as f:
            f.write("# level: one\n# empty: ⬛\n# \U0001f92a = zany (face=blink) -> body_spring\n⬛\U0001f92a\n")
        out = os.path.join(d.name, "out.json")
        run = subprocess.run([sys.executable, os.path.join(self.ROOT, "prowl.py"), "--import-ascii", out, "--sprites", os.path.join(self.ROOT, "tools", "slime_faces", "bodies.txt"),
                              "--levels", level, "--no-gui"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
        self.assertEqual(run.returncode, 0, run.stdout)
        p = Project.load(out)
        tile = p.tiles["\U0001f92a"]
        sprite = p.sprite(tile.sprite)
        body = p.sprite("body_spring")
        self.assertEqual((tile.sprite, (sprite.width, sprite.height, len(sprite.frames))), ("zany", (body.width, body.height, 8)))
        marks = {i for i, e in enumerate(p.palette.entries) if e.rgb == (255, 0, 255)}
        self.assertTrue(all(v not in marks for f in sprite.frames for v in f))                              # the head is where the magenta square was
        top = [sprite.get(0, x, y) for y in range(0, 28) for x in range(4, 36)]
        self.assertGreater(sum(1 for v in top if v), 300)                                                  # and it is drawn: hundreds of opaque pixels over the spring
        self.assertTrue(all(len({v for v in f if v}) > 5 for f in sprite.frames))                        # in colours, not a silhouette


class ClassicalPimpAssets(unittest.TestCase):
    """The files of Samples/ClassicalPimp and tools/classic_pimp that need no game: the street, the characters, the HUD."""
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def tool(self, name):
        folder = os.path.join(self.ROOT, "tools", "classic_pimp")
        sys.path.insert(0, folder)                                              # (make_characters imports puppet from beside it)
        try:
            spec = importlib.util.spec_from_file_location("classic_pimp_" + name, os.path.join(folder, name + ".py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(folder)
        return module

    def read(self, *path):
        with open(os.path.join(self.ROOT, *path), encoding="utf-8") as f:
            return f.read()

    def test_the_files_are_what_the_tools_write(self):
        self.assertEqual("\n".join(self.tool("make_level").build()) + "\n", "".join(l + "\n" for l in self.read("Samples", "ClassicalPimp", "level.txt").splitlines() if not l.startswith("#")))
        self.assertEqual(self.tool("make_characters").text(), self.read("tools", "classic_pimp", "characters.txt"))
        self.assertEqual(self.tool("make_hud").text(), self.read("tools", "classic_pimp", "hud.txt"))
        self.assertEqual(self.tool("make_butterfly").text(), self.read("tools", "classic_pimp", "butterfly.txt"))

    def test_the_spin_kick_and_the_launched_hoes(self):
        from . import asciiart
        blocks = {b.name: b for b in asciiart.parse_sprite_text(self.read("tools", "classic_pimp", "characters.txt"))}
        self.assertEqual(len(blocks["pimp_spinkick"].frames), 8)
        self.assertEqual(len(blocks["pimp_confused"].frames), 3)
        for look in ("red", "blue", "green", "yellow", "pink"):                                   # Shared.Looks = 5, in this order
            self.assertEqual(len(blocks["hoe_%s_launch" % look].frames), 4, look)
            for anim in ("idle", "walk", "hit", "fall"):
                self.assertIn("hoe_%s_%s" % (look, anim), blocks)

    def test_the_butterfly_scenes_fit_their_window(self):
        from . import asciiart
        blocks = asciiart.parse_sprite_text(self.read("tools", "classic_pimp", "butterfly.txt"))
        got = {b.name: (len(b.frames), len(b.frames[0][0]), len(b.frames[0])) for b in blocks}
        self.assertEqual(got, {"butterfly_family": (8, 96, 56), "butterfly_dogs": (8, 96, 56), "butterfly_rain": (8, 96, 56), "butterfly_static": (4, 96, 56)})

    def test_the_game_logic_plays_through_in_c_and_on_dotnet(self):
        """Samples/ClassicalPimp/*.cs is the game: a bot plays the street, and the C build and .NET must print the same (needs dotnet, CCSharp and the native library)."""
        import shutil
        import subprocess
        if not shutil.which("dotnet") or not os.path.exists(os.path.join(self.ROOT, "..", "CCSharp")) or not os.path.exists(os.path.join(self.ROOT, "Libraries", "linux-x64", "native", "libprowl_box2d.so")):
            self.skipTest("the C# to C toolchain is not here (python3 build.py deps --ccsharp; python3 build.py native)")
        r = subprocess.run([sys.executable, os.path.join(self.ROOT, "build.py"), "player", "Samples/ClassicalPimp", "--verify", "--run"], cwd=self.ROOT, capture_output=True, text=True, timeout=900)
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
        self.assertIn("verify    ok", r.stdout)
        self.assertIn("won=1", r.stdout)
        self.assertIn("boss dead=1", r.stdout)
        self.assertRegex(r.stdout, r"launches=[1-9]\d* palette swaps=[1-9]\d* confused=[1-9]")

    def test_the_level_is_four_screens_of_a_street(self):
        from . import asciiart
        block, = asciiart.parse_level_text(self.read("Samples", "ClassicalPimp", "level.txt"))
        self.assertEqual((len(block.rows[0]), len(block.rows)), (76, 14))                                         # 4 screens of 19 x 14 cells of 16 pixels: 304 x 224
        self.assertTrue(all(len(r) == 76 for r in block.rows))
        self.assertEqual(set(block.rows[13]), {"\u25fc\ufe0f"})                                                   # the street along the bottom, four rows deep
        self.assertEqual({row[0] for row in block.rows[10:]}, {"\u25fc\ufe0f"})

    def test_the_characters_stand_on_one_line_and_only_the_hoes_shimmer(self):
        from . import asciiart
        blocks = {b.name: b for b in asciiart.parse_sprite_text(self.read("tools", "classic_pimp", "characters.txt"))}
        self.assertEqual({len(b.frames) for n, b in blocks.items() if n.endswith("_idle")}, {4})
        self.assertEqual(len(blocks["pimp_walk"].frames), 6)
        self.assertEqual(len(blocks["pimp_slap"].frames), 5)
        for name, b in blocks.items():
            for frame in b.frames:
                self.assertEqual((len(frame), {len(r) for r in frame}), (100, {96}), name)
            if "fall" not in name and "launch" not in name:                                                      # (a hoe blasted off the screen is in the air)
                for frame in b.frames:
                    low = max(y for y, r in enumerate(frame) if set(r) - {"."})
                    self.assertTrue(94 <= low <= 99, (name, low))                                                  # the feet are on the floor line in every frame
        light = lambda frame: sum(r.count("c") + r.count("w") + r.count("C") for r in frame)
        for name in ("pimp_idle", "pimp_walk"):
            self.assertEqual([light(f) for f in blocks[name].frames], [0] * len(blocks[name].frames), name)       # the Classical Pimp is solid
        self.assertEqual([light(f) > 0 for f in blocks["pimp_slap"].frames], [False, True, True, False, False])     # but the slap is a measurement: the burst
        idle = blocks["hoe_red_idle"].frames
        self.assertTrue(all(light(f) > 20 for f in idle))                                                          # a Probability Hoe's edges shimmer...
        self.assertEqual(len({tuple(f) for f in idle}), 4)                                                         # ...differently in every frame
        self.assertEqual(light(blocks["hoe_red_fall"].frames[-1]), 0)                                              # until she is measured: down, she is solid
        self.assertEqual(blocks["hoe_red_idle"].frames[0].__len__(), blocks["hoe_blue_idle"].frames[0].__len__())
        self.assertNotEqual(blocks["hoe_red_idle"].header_colors["d"], blocks["hoe_blue_idle"].header_colors["d"])  # one body, three looks: only the palette differs

    def test_the_hud_sprites_fit(self):
        from . import asciiart
        for b in asciiart.parse_sprite_text(self.read("tools", "classic_pimp", "hud.txt")):
            self.assertTrue(len(b.frames[0]) <= 256 and max(len(r) for r in b.frames[0]) <= 256, b.name)
        names = [b.name for b in asciiart.parse_sprite_text(self.read("tools", "classic_pimp", "hud.txt"))]
        self.assertEqual(names, ["hud_portrait", "hud_bar_frame", "hud_bar_fill", "hud_butterfly_frame", "hud_corner_tl", "hud_corner_tr", "hud_corner_bl", "hud_corner_br"])
