"""emoji_faces.py: a face in an emoji level, as a Grease Pencil head on an ASCII art body (no Qt, so the command line can use it too).

In a level's legend, `face` makes a tile's emoji a face and the sprite after `->` its body:

    # level: faces
    # empty: ⬛
    # 🤪 = zany (face) -> body_bat
    # 😠 = grump (face=shake) -> body_legs
    ⬛⬛🤪⬛
    ⬛😠⬛⬛

The head is made by blender.py of https://github.com/crustos/3d-emoji-assets-generator (Twemoji's SVG as a Grease Pencil rig whose eyes, brows and mouth are layers,
with animations: blink, talk, look_around, ...). prowl.py runs it as a subprocess (--emoji-gen PATH, or $EMOJI_GEN, or a folder next to this one), which runs Blender,
renders the animation (`face=NAME`, default talk) with tools/blender_render_collections.py (the same render as --blend-script, so the head is pixel art: no anti-aliasing,
colours folded into the project's palette) and puts each frame on the body. The body is an ordinary sprite (see asciiart.py) with a square of magenta `@` (#ff00ff, the
key @ of the palette header) where the head goes, which may move from frame to frame; the head is drawn as large as that square is wide (an emoji is 2 Blender units
across) and stands on its floor. The body's frames go round again under the head's. The result is a new sprite named after the tile, which is the tile's sprite.

A tile whose sprite exists is left as it is, so a project that has been saved is not rendered again.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from . import blender_import
from .model import Sprite, ProjectError, slug

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATOR_REPO = "https://github.com/crustos/3d-emoji-assets-generator"
MARKER = (255, 0, 255)             # the colour of the '@' that marks where a body's head goes
HEAD_UNITS = 2.0                   # an emoji is 2 Blender units across (blender.py --size): that many pixels per unit is the head's size in pixels
DEFAULT_CLIP = "talk"
DEFAULT_FRAMES = 8
DEFAULT_COLORS = 24                # the colours of one head (--blend-colors is 32 for a whole import)


class FaceError(ProjectError):
    """A face could not be made; the message says what to do."""


class Options:
    def __init__(self, generator=None, skin="zombie", frames=DEFAULT_FRAMES, colors=DEFAULT_COLORS, blend=None):
        self.generator = generator      # blender.py, or the folder it is in (default: $EMOJI_GEN, then next to Prowl2D)
        self.skin = skin                # blender.py --skin: 'zombie' (green, the default there) or 'none' (Twemoji's yellow)
        self.frames = frames            # frames of a head's animation in the sprite
        self.colors = colors            # at most this many colours in a head
        self.blend = blend or blender_import.Options()      # which Blender, and how it renders (its samples, engine and ppu are set here)

    @staticmethod
    def from_args(a):
        return Options(getattr(a, "emoji_gen", None), getattr(a, "face_skin", "zombie"), getattr(a, "face_frames", DEFAULT_FRAMES),
                       getattr(a, "face_colors", DEFAULT_COLORS), blender_import.Options.from_args(a))


def register(prowl):
    """Adds the face options to prowl.py (through the interface a plugin uses)."""
    prowl.add_argument("--emoji-gen", metavar="PATH", help="blender.py of %s, or its folder, which makes the heads of `face` tiles (default: $EMOJI_GEN, or 3d-emoji-assets-generator next to Prowl2D)" % GENERATOR_REPO)
    prowl.add_argument("--face-skin", choices=("zombie", "none"), default="zombie", help="the skin of a face: zombie (green, the default) or none (the yellow of the emoji)")
    prowl.add_argument("--face-frames", type=int, default=DEFAULT_FRAMES, metavar="N", help="frames of a face's animation (default %d)" % DEFAULT_FRAMES)
    prowl.add_argument("--face-colors", type=int, default=DEFAULT_COLORS, metavar="N", help="at most N colours in one face (default %d)" % DEFAULT_COLORS)


def emoji_code(emoji):
    """'🤪' -> '1f92a': the name of its SVG in blender.py (lower case hex, joined by '-', without the variation selector)."""
    return "-".join("%x" % ord(c) for c in emoji if ord(c) != 0xFE0F)


def find_generator(explicit=None):
    """The path of blender.py: `explicit` (the file or its folder), else $EMOJI_GEN, else the folders it is usually cloned to. Raises FaceError with how to get it."""
    wanted = [(explicit, "--emoji-gen"), (os.environ.get("EMOJI_GEN"), "$EMOJI_GEN")]
    for given, what in wanted:
        if given:
            path = os.path.join(given, "blender.py") if os.path.isdir(given) else given
            if not os.path.isfile(path):
                raise FaceError("%s %s is not blender.py of 3d-emoji-assets-generator (or its folder)" % (what, given))
            return os.path.abspath(path)
    for folder in (os.path.join(os.path.dirname(ROOT), "3d-emoji-assets-generator"), os.path.expanduser("~/3d-emoji-assets-generator")):
        path = os.path.join(folder, "blender.py")
        if os.path.isfile(path):
            return path
    raise FaceError("a face tile needs blender.py of the emoji generator: git clone %s, then give its folder with --emoji-gen PATH (or set $EMOJI_GEN)" % GENERATOR_REPO)


def generate(generator, emojis, blender, skin, folder, say=None):
    """Runs blender.py (it starts Blender) for the emoji; returns {emoji: (the .blend, [{"name", "start", "end"} of its animations])}. Raises FaceError."""
    codes = {e: emoji_code(e) for e in emojis}
    cmd = [sys.executable, generator, "--emojis", ",".join(codes.values()), "--output", folder, "--skin", skin, "--naming", "unicode", "--blender", blender]
    try:
        run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, errors="replace", cwd=os.path.dirname(generator))
    except OSError as e:
        raise FaceError("could not run %s: %s" % (generator, e))
    out = {}
    for emoji, code in codes.items():
        blend, facemap = os.path.join(folder, code + ".blend"), os.path.join(folder, code + ".facemap.json")
        if not (os.path.isfile(blend) and os.path.isfile(facemap)):
            tail = "\n  ".join(run.stdout.strip().splitlines()[-8:])
            raise FaceError("blender.py made no face for %s (U+%s)%s\n  %s\n(python3 blender.py --list-faces shows the faces it can make)" % (
                emoji, code.upper().replace("-", " U+"), "" if run.returncode == 0 else ", exit code %d" % run.returncode, tail))
        with open(facemap, encoding="utf-8") as f:
            out[emoji] = (blend, json.load(f).get("animations", []))
    if say:
        say("blender.py made %d face%s" % (len(out), "" if len(out) == 1 else "s"))
    return out


def choose_clip(animations, wanted, emoji):
    """The animation to play: {"name", "start", "end"} of `wanted` (default: talk, else the first one)."""
    names = [a["name"] for a in animations]
    if not animations:
        raise FaceError("%s has no animations" % emoji)
    if wanted:
        for a in animations:
            if a["name"] == wanted:
                return a
        raise FaceError("%s has no animation '%s' (it has: %s)" % (emoji, wanted, ", ".join(names)))
    for a in animations:
        if a["name"] == DEFAULT_CLIP:
            return a
    return animations[0]


def marker_boxes(project, body):
    """[(x, y, w, h) of the square of '@' in each frame of the body]. Raises FaceError if a frame has none."""
    marks = {i for i, e in enumerate(project.palette.entries) if e.rgb is not None and tuple(e.rgb) == MARKER}       # (entry 0, transparent, has no colour)
    boxes = []
    for n, frame in enumerate(body.frames):
        xs, ys = [], []
        for y in range(body.height):
            for x in range(body.width):
                if frame[y * body.width + x] in marks:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            raise FaceError("body '%s' (frame %d) has no square of @ (magenta, #ff00ff) where the head goes" % (body.name, n + 1))
        boxes.append((min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    return boxes, marks


def compose(project, name, body, head, count):
    """A new Sprite of `count` frames: frame i is the head's frame (head.frames[i * its frames // count]) on the body's frame i % its frames, in the body's square of '@'."""
    boxes, marks = marker_boxes(project, body)
    out = Sprite(name, body.width, body.height, body.fps or 8.0)
    out.frames = []
    for i in range(count):
        n = i % len(body.frames)
        frame = bytearray(0 if v in marks else v for v in body.frames[n])        # the square is where the head goes: whatever the head leaves is empty
        hf = head.frames[i * len(head.frames) // count]
        mx, my, mw, mh = boxes[n]
        ox, oy = mx + (mw - head.width) // 2, my + mh - head.height              # centred, standing on the floor of the square
        for y in range(head.height):
            for x in range(head.width):
                v = hf[y * head.width + x]
                if v and 0 <= ox + x < body.width and 0 <= oy + y < body.height:
                    frame[(oy + y) * body.width + ox + x] = v
        out.frames.append(frame)
    return out


def make_face_sprites(project, options=None, say=None):
    """Makes the sprite of every face tile that has none (see the top of this file) and sets the tile's sprite to it. Returns the Sprites made."""
    options = options or Options()
    todo = [t for t in project.tiles.values() if t.face and not (t.sprite and project.sprite(t.sprite))]
    if not todo:
        return []
    for t in todo:
        if not t.body or project.sprite(t.body) is None:
            raise FaceError("face %s (%s) needs a body: a sprite named after `->` in the legend, with a square of @ where the head goes%s" % (
                t.emoji, t.name, " (there is no sprite '%s': give the bodies with --sprites)" % t.body if t.body else ""))
    generator = find_generator(options.generator)
    blender = blender_import.find_blender(options.blend.blender)
    made = []
    folder = tempfile.mkdtemp(prefix="prowl_faces_")
    try:
        files = generate(generator, [t.emoji for t in todo], blender, options.skin, folder, say)
        for t in todo:
            blend, animations = files[t.emoji]
            clip = choose_clip(animations, t.clip, t.emoji)
            body = project.sprite(t.body)
            boxes, _ = marker_boxes(project, body)
            o = blender_import.Options(blender=options.blend.blender, view="front", ppu=boxes[0][2] / HEAD_UNITS, engine=options.blend.engine,
                                       samples=1, colors=options.colors, frames="%d:%d" % (clip["start"], clip["end"]))
            report = blender_import.import_blend(project, blend, o)
            head = report.sprites[0]
            project.sprites.remove(head)                              # only its colours stay: the palette entries it added
            sprite = project.add_sprite(compose(project, slug(t.name), body, head, options.frames))
            t.sprite = sprite.name
            made.append(sprite)
            if say:
                say("%s %s: %d frames of '%s' on %s, %dx%d" % (t.emoji, t.name, len(sprite.frames), clip["name"], body.name, sprite.width, sprite.height))
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    project.touch()
    return made
