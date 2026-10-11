#!/usr/bin/env python3
"""render.py: makes the enemies of SlimeJumpHeads: a head rendered with Blender (through prowl.py --blend-script) as a 32x32 sprite of 8 frames, on a body drawn
as ASCII art (bodies.txt, in the sprite ASCII format of prowl.py --import-ascii).

    python3 tools/slime_heads/render.py [KIND ..] [--size 32]

Writes tools/slime_heads/art/KIND_head_N.png (the head, 32x32, N = 0..7), KIND_N.png (the head on its body, the sprite the game draws) and KIND.json (a Prowl2D
project with the head's frames as a sprite). Needs Blender (see EDITOR.md: put it on the PATH or set BLENDER). In bodies.txt a run of '@' marks where the
head goes in each frame: that is the 32x32 square, and a body frame can move it (a bob) between frames."""
import argparse, json, os, shutil, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KINDS = ("cat", "dog", "frog", "ogre")
BODY = {"cat": "body_bat", "dog": "body_legs", "frog": "body_tentacles", "ogre": "body_brute"}       # which ASCII body each head is on
sys.path.insert(0, ROOT)

def body_frames(name):
    """[(Image, (x, y) of the head's square)] for the frames of an ASCII body: '@' is where the head goes, the other letters are the palette's colours."""
    from prowl_editor import asciiart
    with open(os.path.join(HERE, "bodies.txt"), encoding="utf-8") as f:
        block = [b for b in asciiart.parse_sprite_text(f.read()) if b.name == name][0]
    out = []
    for rows in block.frames:
        im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
        px = im.load()
        xs, ys = [], []
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "@":
                    xs.append(x); ys.append(y)
                elif ch in block.header_colors:
                    px[x, y] = tuple(block.header_colors[ch]) + (255,)
        out.append((im, (min(xs), min(ys))))
    return out

def compose(kind, heads, art):
    """KIND_N.png: frame N of the head on frame N of the body (the body has fewer frames and goes round again)."""
    bodies = body_frames(BODY[kind])
    for i, head in enumerate(heads):
        body, (hx, hy) = bodies[i % len(bodies)]
        im = body.copy()
        im.alpha_composite(head, (hx, hy))
        im.save(os.path.join(art, "%s_%d.png" % (kind, i)))
    anchors = {}
    path = os.path.join(art, "anchors.json")
    if os.path.exists(path):
        with open(path) as f:
            anchors = json.load(f)
    hx, hy = bodies[0][1]
    anchors[kind] = [hx + head.width // 2, hy + head.height // 2]              # the centre of the head, in the picture: the game's position for the enemy
    with open(path, "w") as f:
        json.dump(anchors, f, indent=1, sort_keys=True)
    print("%s: %dx%d with a body of %d frames" % (kind, im.width, im.height, len(bodies)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kinds", nargs="*", default=list(KINDS))
    ap.add_argument("--size", type=int, default=32)
    ap.add_argument("--samples", type=int, default=24)
    a = ap.parse_args()
    art = os.path.join(HERE, "art")
    os.makedirs(art, exist_ok=True)
    for kind in a.kinds:
        keep = os.path.join(art, "_" + kind)
        shutil.rmtree(keep, ignore_errors=True)
        env = dict(os.environ, HEAD_KIND=kind)
        subprocess.run([sys.executable, os.path.join(ROOT, "prowl.py"), "--blend-script", os.path.join(HERE, "make_head.py"), "--blend-size", str(a.size),
                        "--blend-samples", str(a.samples), "--blend-keep", keep, "--no-gui", "-o", os.path.join(art, kind + ".json")], check=True, env=env)
        names = sorted(f for f in os.listdir(keep) if f.endswith(".png"))
        frames = [Image.open(os.path.join(keep, f)).convert("RGBA") for f in names]
        box = None                                   # one crop for all frames, then the longest side made to be exactly `size`
        for im in frames:
            b = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        heads = []
        for i, im in enumerate(frames):
            im = im.crop(box)
            canvas = Image.new("RGBA", (a.size, a.size), (0, 0, 0, 0))
            if max(im.size) != a.size:
                k = a.size / max(im.size)
                im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
            canvas.paste(im, ((a.size - im.width) // 2, a.size - im.height))       # on the floor of a 64x64 cell, centred
            canvas.save(os.path.join(art, "%s_head_%d.png" % (kind, i)))
            heads.append(canvas)
        compose(kind, heads, art)
        shutil.rmtree(keep, ignore_errors=True)
        print("%s: %d frames of %dx%d" % (kind, len(frames), a.size, a.size))

if __name__ == "__main__":
    main()
