#!/usr/bin/env python3
"""build.py: makes the art of SlimeJumpFaces: the faces of its level asciiart, rendered with Grease Pencil and put on their ASCII art bodies.

    python3 tools/slime_faces/build.py [--emoji-gen PATH] [--blender PATH] [--no-gif]      # the project, the art and a preview gif (needs Blender)
    python3 tools/slime_faces/build.py --check                                           # only: does level.txt agree with Level.cs? (no Blender)

What it does:
  1. checks that the faces in Samples/SlimeJumpFaces/level.txt are where Level.cs puts its enemies (to within a cell: the text has one cell to a world unit), and which
     face is which enemy kind (the first is kind 2, as Level.EnemyKind says);
  2. python3 prowl.py --import-ascii Samples/SlimeJumpFaces/slimejumpfaces.json --sprites tools/slime_faces/bodies.txt --levels Samples/SlimeJumpFaces/level.txt:
     the bodies and the level become a Prowl2D project (open it in the editor), and prowl.py runs blender.py of the emoji generator (https://github.com/crustos/3d-emoji-assets-generator,
     --emoji-gen PATH or $EMOJI_GEN) to make each `face` tile's head and puts it on its body (prowl_editor/emoji_faces.py); the bricks are generated (prowl_editor/generated.py);
  3. writes tools/slime_faces/art/NAME_N.png (frame N of each face on its body), anchors.json (where the head's centre is: the enemy's position) and kinds.json (enemy
     kind -> NAME), which tools/sand_gif.py --sample SlimeJumpFaces draws over the game's run;
  4. writes Samples/SlimeJumpFaces/faces.gif: the four faces side by side.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SAMPLE = os.path.join(ROOT, "Samples", "SlimeJumpFaces")
LEVEL = os.path.join(SAMPLE, "level.txt")
LEVEL_CS = os.path.join(SAMPLE, "Level.cs")
BODIES = os.path.join(HERE, "bodies.txt")
PROJECT = os.path.join(SAMPLE, "slimejumpfaces.json")
ART = os.path.join(HERE, "art")
GIF = os.path.join(SAMPLE, "faces.gif")
TOLERANCE = 0.75                    # how far (world units) a face may be from the enemy's place in Level.cs: the text puts it at the centre of a cell

sys.path.insert(0, ROOT)


def read_level_cs():
    """(the constants of Level.cs, [(x, y) of each enemy]): enemy i is `if (i == n) return A;`, the last one `return A;`, A a number or `AirBottom(r) + c`."""
    with open(LEVEL_CS, encoding="utf-8") as f:
        text = f.read()
    const = {m.group(1): float(m.group(2)) for m in re.finditer(r"public const (?:int|float) (\w+) = (-?[\d.]+)f?;", text)}
    air_bottom = lambda r: const["Top"] - r * const["Pitch"] - const["AirHeight"]

    def value(expr):
        expr = expr.strip().rstrip("f")
        m = re.fullmatch(r"AirBottom\((\d+)\) \+ ([\d.]+)f?", expr)
        return air_bottom(int(m.group(1))) + float(m.group(2)) if m else float(expr)

    def returns(name):
        body = re.search(r"public static float %s\(int i\)\s*\{(.*?)\n    \}" % name, text, re.S).group(1)
        found = {int(i): value(v) for i, v in re.findall(r"if \(i == (\d+)\) return ([^;]+);", body)}
        found[int(const["EnemyCount"]) - 1] = value(re.findall(r"return ([^;]+);", body)[-1])        # the last enemy is the one the ifs leave over
        return found
    xs, ys = returns("EnemyX"), returns("EnemyY")
    return const, [(xs[i], ys[i]) for i in range(int(const["EnemyCount"]))]


def faces_in_level():
    """[(emoji, x, y)] of the cells of level.txt that are faces, with the cell's centre as the place (x right, y up from the bottom, one cell to a unit)."""
    from prowl_editor import asciiart
    with open(LEVEL, encoding="utf-8") as f:
        block, = asciiart.parse_level_text(f.read())
    faces = {g for g, (_, _, traits) in block.legend.items() if any(t == "face" or t.startswith("face=") for t in traits)}
    return [(g, x + 0.5, len(block.rows) - y - 0.5) for y, row in enumerate(block.rows) for x, g in enumerate(row) if g in faces], block


def check():
    """The emoji of each enemy kind, in order (kind 2 first), after checking that level.txt has a face where Level.cs has each enemy. Raises SystemExit if not."""
    const, enemies = read_level_cs()
    faces, block = faces_in_level()
    rows = len(block.rows)
    problems = []
    if (len(block.rows[0]), rows) != (int(const["Width"]), int(const["Height"])):
        problems.append("level.txt is %dx%d cells, the shaft is %gx%g units" % (len(block.rows[0]), rows, const["Width"], const["Height"]))
    order = []
    for i, (ex, ey) in enumerate(enemies):
        near = [f for f in faces if abs(f[1] - ex) <= TOLERANCE and abs(f[2] - ey) <= TOLERANCE]
        if len(near) != 1:
            problems.append("enemy %d is at (%g, %g) in Level.cs, and level.txt has %s there" % (i, ex, ey, "no face" if not near else "%d faces" % len(near)))
        else:
            order.append(near[0][0])
    if len(faces) != len(enemies):
        problems.append("level.txt has %d faces, Level.cs has %d enemies" % (len(faces), len(enemies)))
    if problems:
        raise SystemExit("level.txt and Level.cs disagree:\n  " + "\n  ".join(problems))
    print("level.txt agrees with Level.cs: %s" % ", ".join("kind %d %s at (%g, %g)" % (2 + i, g, *enemies[i]) for i, g in enumerate(order)))
    return order


def export_art(project, order):
    """The PNGs and the two json files tools/sand_gif.py reads."""
    from PIL import Image
    from prowl_editor import emoji_faces
    os.makedirs(ART, exist_ok=True)
    for name in os.listdir(ART):
        if name.endswith(".png"):
            os.remove(os.path.join(ART, name))
    anchors, kinds, frames = {}, {}, {}
    for i, emoji in enumerate(order):
        tile = project.tiles[emoji]
        sprite = project.sprite(tile.sprite)
        body = project.sprite(tile.body)
        mx, my, mw, mh = emoji_faces.marker_boxes(project, body)[0][0]
        anchors[sprite.name] = [mx + mw // 2, my + mh // 2]                # the centre of the head in the first frame: the enemy's place
        kinds[str(2 + i)] = sprite.name
        frames[sprite.name] = []
        for n in range(len(sprite.frames)):
            im = Image.frombytes("RGBA", (sprite.width, sprite.height), sprite.rgba(project.palette, n))
            im.save(os.path.join(ART, "%s_%d.png" % (sprite.name, n)))
            frames[sprite.name].append(im)
    for name, data in (("anchors.json", anchors), ("kinds.json", kinds)):
        with open(os.path.join(ART, name), "w") as f:
            json.dump(data, f, indent=1, sort_keys=True)
    print("wrote %s: %s" % (ART, ", ".join("%s %dx%d x%d" % (n, f[0].width, f[0].height, len(f)) for n, f in frames.items())))
    return frames


def write_gif(frames, scale=4, fps=8):
    from PIL import Image
    names = list(frames)
    count = max(len(f) for f in frames.values())
    gap = 8
    w = sum(frames[n][0].width for n in names) * scale + gap * (len(names) + 1)
    h = max(frames[n][0].height for n in names) * scale + 2 * gap
    out = []
    for i in range(count):
        im = Image.new("RGBA", (w, h), (36, 28, 44, 255))
        x = gap
        for n in names:
            f = frames[n][i % len(frames[n])]
            big = f.resize((f.width * scale, f.height * scale), Image.NEAREST)
            im.alpha_composite(big, (x, h - gap - big.height))                # all stand on one floor
            x += big.width + gap
        out.append(im.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    out[0].save(GIF, save_all=True, append_images=out[1:], duration=1000 // fps, loop=0, optimize=True)
    print("wrote %s (%d frames, %dx%d, %d KiB)" % (GIF, len(out), w, h, os.path.getsize(GIF) // 1024))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only check that level.txt and Level.cs agree (no Blender)")
    ap.add_argument("--emoji-gen", metavar="PATH", help="blender.py of the emoji generator, or its folder (default: $EMOJI_GEN, or next to Prowl2D)")
    ap.add_argument("--blender", metavar="PATH", help="the Blender executable (default: $BLENDER, the PATH, the usual install folders)")
    ap.add_argument("--no-gif", action="store_true", help="do not write faces.gif")
    a = ap.parse_args()
    order = check()
    if a.check:
        return 0
    cmd = [sys.executable, os.path.join(ROOT, "prowl.py"), "--import-ascii", PROJECT, "--sprites", BODIES, "--levels", LEVEL, "--no-gui"]
    cmd += ["--emoji-gen", a.emoji_gen] if a.emoji_gen else []
    cmd += ["--blender", a.blender] if a.blender else []
    if os.path.exists(PROJECT):
        os.remove(PROJECT)                                                      # a project that is there would be added to
    subprocess.run(cmd, check=True)
    from prowl_editor.model import Project
    frames = export_art(Project.load(PROJECT), order)
    if not a.no_gif:
        write_gif(frames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
