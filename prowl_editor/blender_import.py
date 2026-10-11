"""blender_import.py: the collections of a Blender scene as sprites (no Qt, so the command line can use it too).

    python3 prowl.py scene.blend                     the collections of scene.blend, rendered and added to the project the editor opens
    python3 prowl.py --blend-script make_scene.py    a Blender Python script that builds a scene (it does not have to save it): its collections, rendered

Blender renders in the background (a Blender on the PATH, or --blender PATH, or the BLENDER environment variable): tools/blender_render_collections.py runs inside
it and writes one transparent PNG per collection (every collection under the scene's collection is a sprite; see that file for what is rendered and how). The
PNGs are cropped to what they show and their colours folded into the project's palette (--blend-colors says how many at most), the way the Unity import does it
(unity_import.py), and each becomes a sprite named after its collection. All sprites share one scale, so the coin stays smaller than the hero.

A collection named like `Level_1` (it starts with "level") is a level instead: its collection instances are the tiles. Each instanced collection is a sprite, the
instance's place (snapped to a grid of --blend-cell Blender units, one by default) is its cell, and a custom property `solid` on the collection makes the tile solid.
"""
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections import deque

from . import unity_import as ui
from .model import MAX_LEVEL_SIDE, Level, ProjectError
from .unity_scene import _emoji_pool, tile_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELPER = os.path.join(ROOT, "tools", "blender_render_collections.py")
VIEWS = ("front", "back", "left", "right", "top", "bottom")
ENGINES = ("cycles", "eevee", "workbench")
EMPTY_SCENE = "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True)"     # a script starts from an empty scene, not Blender's cube


class BlenderError(ProjectError):
    """Blender could not be found or run, or it rendered nothing; the message says why."""


class Options:
    """What to render and how. The defaults are prowl.py's."""

    def __init__(self, blender=None, view="front", size=32.0, ppu=0.0, engine="cycles", samples=16, collections=(), colors=32, keep=None, cell=1.0, frames=""):
        self.blender = blender          # the Blender executable (default: look for one)
        self.view = view                # which side the camera looks from, one of VIEWS
        self.size = size                # pixels of the longest side of the biggest collection
        self.ppu = ppu                  # or: pixels per Blender unit (replaces size)
        self.engine = engine
        self.samples = samples
        self.collections = list(collections)    # only these collections (names, * and ? work, any depth); none: every collection under the scene's
        self.colors = colors            # at most this many colours across the imported sprites (0: no limit besides the palette's)
        self.keep = keep                # a folder to leave Blender's renders in (and manifest.json); None: a temporary folder, removed
        self.cell = cell                # the size of a level's grid cell, in Blender units
        self.frames = frames            # "": a still of the scene's current frame; "all" or "START:END": every frame of the range, as the frames of each sprite

    @staticmethod
    def from_args(a):
        """From prowl.py's parsed command line (the --blend-* options, see register)."""
        names = [n.strip() for item in (a.blend_collections or []) for n in item.split(",") if n.strip()]
        return Options(a.blender, a.blend_view, a.blend_size, a.blend_ppu, a.blend_engine, a.blend_samples, names, a.blend_colors, a.blend_keep, a.blend_cell, a.blend_frames or "")


class BlenderReport:
    def __init__(self):
        self.sprites = []               # the Sprites added to the project
        self.levels = []                # the Levels added, from the collections named like "Level_1"
        self.notes = []                 # what was skipped, scaled or merged

    def summary(self):
        text = "%d sprite%s from Blender collections" % (len(self.sprites), "" if len(self.sprites) == 1 else "s")
        return text + ("; %d level%s" % (len(self.levels), "" if len(self.levels) == 1 else "s") if self.levels else "")


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# running Blender

def _executable(path):
    """`path` as something to run: a file, or a macOS Blender.app."""
    if os.path.isdir(path) and path.rstrip("/").endswith(".app"):
        path = os.path.join(path, "Contents", "MacOS", "Blender")
    return path if os.path.isfile(path) else None


def find_blender(explicit=None):
    """The Blender executable: `explicit`, else $BLENDER, else `blender` on the PATH, else where installers put it. Raises BlenderError with what to do."""
    for given, what in ((explicit, "--blender"), (os.environ.get("BLENDER"), "$BLENDER")):
        if given:
            found = _executable(given) or shutil.which(given)
            if not found:
                raise BlenderError("%s %s is not an executable" % (what, given))
            return found
    found = shutil.which("blender")
    if found:
        return found
    spots = ["/Applications/Blender.app", os.path.expanduser("~/Applications/Blender.app"), "/snap/bin/blender", "/opt/blender/blender", "/usr/local/blender/blender"]
    spots += sorted(glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Blender Foundation", "Blender *", "blender.exe")), reverse=True)
    for spot in spots:
        found = _executable(spot)
        if found:
            return found
    raise BlenderError("Blender was not found: install it (blender.org), put it on the PATH, or give its path with --blender PATH (or the BLENDER environment variable)")


def _command(blender, blend, script, folder, o):
    cmd = [blender, "--background", "--factory-startup", "--python-exit-code", "1"]
    if blend:
        cmd.append(blend)                                   # the file comes before the scripts that work on it
    else:
        cmd += ["--python-expr", EMPTY_SCENE + "; import sys; sys.path.insert(0, %r)" % os.path.dirname(HELPER)]     # tools/ too: `import prowl_blender`
    if script:
        cmd += ["--python", script]
    cmd += ["--python", HELPER, "--", "--out", folder, "--view", o.view, "--engine", o.engine, "--samples", str(o.samples)]
    cmd += ["--ppu", repr(float(o.ppu))] if o.ppu else ["--size", repr(float(o.size))]
    if o.frames:
        cmd += ["--frames", o.frames]
    if o.collections:
        cmd += ["--collections"] + list(o.collections)
    return cmd


def render(blend, script, folder, options, progress=None):
    """Runs Blender on `blend` (a .blend file, or None) and `script` (a Python script, or None) and renders the scene's collections into `folder`. Returns the
    manifest dict (see tools/blender_render_collections.py). `progress(line)` gets the lines Blender reports."""
    if not os.path.isfile(HELPER):
        raise BlenderError("%s is missing" % HELPER)
    blender = find_blender(options.blender)
    cmd = _command(blender, blend, script, folder, options)
    manifest_path = os.path.join(folder, "manifest.json")
    if os.path.exists(manifest_path):                       # a kept folder from an earlier run: never read its manifest as this run's
        os.remove(manifest_path)
    tail = deque(maxlen=25)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, errors="replace", bufsize=1)
    except OSError as e:
        raise BlenderError("could not run %s: %s" % (blender, e))
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line.startswith("prowl:"):
                if progress:
                    progress(line[len("prowl:"):].strip())
            elif line:
                tail.append(line)
        code = proc.wait()
    except BaseException:                                   # Ctrl-C: do not leave Blender running
        proc.kill()
        raise
    finally:
        proc.stdout.close()
    if code != 0 or not os.path.isfile(manifest_path):
        why = "Blender stopped with exit code %d" % code if code else "Blender ended without rendering (did the script quit Blender?)"
        raise BlenderError("%s:\n  %s" % (why, "\n  ".join(tail) if tail else "(no output)"))
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise BlenderError("Blender's render list is unreadable: %s" % e)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# PNGs to sprites

def alpha_bounds(w, h, rgba):
    """(x0, y0, x1, y1), inclusive, of the opaque pixels (see ui.ALPHA_CUTOFF) of an RGBA image, or None if there are none."""
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if rgba[row + x * 4 + 3] >= ui.ALPHA_CUTOFF:
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
    return (x0, y0, x1, y1) if x1 >= 0 else None


def crop_box(w, h, rgba, box):
    """(w, h, rgba) of the rectangle `box` (x0, y0, x1, y1 inclusive) of an image."""
    x0, y0, x1, y1 = box
    out = bytearray()
    for y in range(y0, y1 + 1):
        out += rgba[(y * w + x0) * 4:(y * w + x1 + 1) * 4]
    return x1 - x0 + 1, y1 - y0 + 1, bytes(out)


def crop_to_alpha(w, h, rgba):
    """(w, h, rgba) of the smallest rectangle holding every opaque pixel, or None if there is none."""
    box = alpha_bounds(w, h, rgba)
    return crop_box(w, h, rgba, box) if box else None


def reduce_colors(pendings, limit):
    """Folds the opaque colours of all the pending sprites into at most `limit` (median cut, as the palette quantizer does it). Returns how many colours there were."""
    counts = {}
    for p in pendings:
        for _w, _h, rgba in p.frames:
            for i in range(0, len(rgba), 4):
                if rgba[i + 3] >= ui.ALPHA_CUTOFF:
                    key = (rgba[i], rgba[i + 1], rgba[i + 2])
                    counts[key] = counts.get(key, 0) + 1
    if not limit or len(counts) <= limit:
        return len(counts)
    chosen = ui._median_cut(counts, limit)
    table = list(enumerate(chosen))
    fold = {c: chosen[ui._nearest(c, table)] for c in counts}
    for p in pendings:
        frames = []
        for w, h, rgba in p.frames:
            out = bytearray(rgba)
            for i in range(0, len(out), 4):
                if out[i + 3] >= ui.ALPHA_CUTOFF:
                    out[i:i + 3] = bytes(fold[(out[i], out[i + 1], out[i + 2])])
            frames.append((w, h, bytes(out)))
        p.frames = frames
    return len(counts)


def build_levels(project, manifest, made, cell, report):
    """Adds the levels of the manifest to `project`. `made` is {the collection's name: (the Sprite, solid)} of the sprites just added."""
    if cell <= 0 or not math.isfinite(cell):
        raise BlenderError("the cell size must be above zero (got %r)" % cell)
    for item in manifest.get("levels", []):
        name, cells, missing, off_grid, hidden = item["name"], {}, set(), 0, 0
        for t in item["tiles"]:
            if t["sprite"] not in made:
                missing.add(t["sprite"])
                continue
            fx, fy = t["x"] / cell, t["y"] / cell
            key = (int(math.floor(fx + 0.5)), int(math.floor(fy + 0.5)))
            off_grid += 1 if abs(fx - key[0]) > 0.25 or abs(fy - key[1]) > 0.25 else 0
            hidden += 1 if key in cells else 0
            cells[key] = t["sprite"]
        for n in sorted(missing):
            report.notes.append("level '%s': '%s' made no sprite, so its tiles are skipped" % (name, n))
        if not cells:
            report.notes.append("level '%s' has no tiles (skipped)" % name)
            continue
        xs, ys = [k[0] for k in cells], [k[1] for k in cells]
        width, height = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if width > MAX_LEVEL_SIDE or height > MAX_LEVEL_SIDE:
            report.notes.append("level '%s': %dx%d cells is bigger than a level can be (%d); skipped (try a bigger --blend-cell)" % (name, width, height, MAX_LEVEL_SIDE))
            continue
        level = Level(name, width, height)
        pool = _emoji_pool()
        for (ix, iy), source in cells.items():
            sprite, solid = made[source]
            level.cells[(max(ys) - iy) * width + (ix - min(xs))] = tile_for(project, sprite.name, solid, False, pool)
        for count, text in ((off_grid, "not on the grid and moved to the nearest cell"), (hidden, "hidden behind another tile in the same cell")):
            if count:
                report.notes.append("level '%s': %d tile%s %s" % (name, count, " was" if count == 1 else "s were", text))
        report.levels.append(project.add_level(level))


def add_rendered(project, folder, manifest, colors, cell, report):
    """Adds the sprites (and levels) of a render folder (its manifest and PNGs) to `project`; what happened goes into report.notes."""
    report.notes += manifest.get("notes", [])
    pendings, solid, fps = [], {}, {}
    loaded = []                                             # (item, images) of the sprites with usable renders
    for item in manifest.get("sprites", []):
        name = item["name"]
        images = [ui.load_png(os.path.join(folder, f)) for f in (item.get("files") or [item["file"]])]
        if len({(w, h) for w, h, _ in images}) != 1:
            report.notes.append("'%s': its frames are not all the same size (skipped)" % name)
            continue
        loaded.append((item, images))
    groups = {}                                             # a layered collection and its layers: {composite name: [their loaded entries]}, cropped and timed alike
    for entry in loaded:
        groups.setdefault(entry[0].get("group") or entry[0]["name"], []).append(entry)
    crops, still = {}, {}
    for key, members in groups.items():
        still[key] = all(all(rgba == images[0][2] for _, _, rgba in images) for _, images in members)      # nothing moves: one frame, not a still repeated
        boxes = [alpha_bounds(w, h, rgba) for _, images in members for w, h, rgba in images]
        boxes = [b for b in boxes if b]
        if boxes:                                           # one crop for all frames of all the layers: they stay aligned
            crops[key] = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    for item, images in loaded:
        name, key = item["name"], item.get("group") or item["name"]
        if key not in crops or alpha_bounds(*images[0]) is None and all(alpha_bounds(*im) is None for im in images):
            report.notes.append("'%s' rendered nothing visible (skipped)" % name)
            continue
        if still[key]:
            images = images[:1]
        p = ui.Pending(name, "collection '%s'" % name)
        for w, h, rgba in images:
            cw, ch, crgba = crop_box(w, h, rgba, crops[key])
            nw, nh, nrgba, scaled = ui._shrink(cw, ch, crgba)
            if scaled and p.scaled_from is None:
                p.scaled_from = (cw, ch)
            p.frames.append((nw, nh, nrgba))
        solid[name] = bool(item.get("solid"))
        fps[name] = float(item.get("fps") or ui.DEFAULT_FPS)
        pendings.append(p)
    if not pendings:
        build_levels(project, manifest, {}, cell, report)
        return
    made = {}                                               # the collection's name -> (its Sprite, solid), for the levels
    seen = reduce_colors(pendings, colors)
    if colors and seen > colors:
        report.notes.append("%d colours folded into %d (--blend-colors)" % (seen, colors))
    mapping, merged = ui.build_palette_mapping(project, pendings, label="blender")
    if merged:
        report.notes.append("%d colours did not fit in the palette (at most %d) and were merged into their nearest" % (merged, ui.MAX_PALETTE))
    for p in pendings:
        if p.scaled_from:
            report.notes.append("%s: %dx%d is bigger than a sprite can be (%d), scaled to %dx%d" % (
                p.source, p.scaled_from[0], p.scaled_from[1], ui.MAX_SPRITE_SIDE, p.frames[0][0], p.frames[0][1]))
        report.sprites.append(project.add_sprite(ui.pending_to_sprite(p, mapping)))
        report.sprites[-1].fps = fps[p.name]
        made[p.name] = (report.sprites[-1], solid[p.name])
    build_levels(project, manifest, made, cell, report)
    project.touch()


def _import(project, blend, script, options, progress):
    options = options or Options()
    report = BlenderReport()
    if options.keep:
        os.makedirs(options.keep, exist_ok=True)
    folder = options.keep or tempfile.mkdtemp(prefix="prowl_blend_")
    try:
        manifest = render(blend, script, folder, options, progress)
        add_rendered(project, folder, manifest, options.colors, options.cell, report)
    finally:
        if not options.keep:
            shutil.rmtree(folder, ignore_errors=True)
    if not report.sprites and not report.levels:            # asked for sprites and got none: that is a failure, not a quiet success
        raise BlenderError("no sprites came out of %s%s" % (blend or script, "".join("\n  " + n for n in report.notes) if report.notes else
                                                              ": the scene has no collections with geometry"))
    return report


def import_blend(project, path, options=None, progress=None):
    """Renders the collections of the .blend file `path` and adds them to `project` as sprites. Returns a BlenderReport."""
    if not os.path.isfile(path):
        raise BlenderError("%s does not exist" % path)
    return _import(project, os.path.abspath(path), None, options, progress)


def import_blend_script(project, script, options=None, progress=None):
    """Runs the Blender Python script `script` (it builds a scene, in Blender's empty startup scene) and adds the scene's collections to `project` as sprites."""
    if not os.path.isfile(script):
        raise BlenderError("%s does not exist" % script)
    return _import(project, None, os.path.abspath(script), options, progress)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# prowl.py

def frames_spec(text):
    """argparse type of --blend-frames: all, or START:END."""
    import argparse
    import re
    if text == "all" or re.fullmatch(r"\d+:\d+", text):
        return text
    raise argparse.ArgumentTypeError("'%s' is not all or START:END (a file name after --blend-frames is taken as its value: put the files first, or say --blend-frames all)" % text)


def register(prowl):
    """Adds the Blender options and the .blend importer to prowl.py (through the same interface a plugin uses)."""
    prowl.add_argument("--blender", metavar="PATH", help="the Blender executable (default: $BLENDER, the PATH, the usual install folders)")
    prowl.add_argument("--blend-script", action="append", default=[], metavar="SCRIPT.py",
                       help="run a Blender Python script that builds a scene (from an empty scene; it need not save it) and import its collections as sprites; repeatable")
    prowl.add_argument("--blend-view", choices=VIEWS, default="front", help="the side the camera looks from: front for a side-scroller, top for a top-down game (default front)")
    prowl.add_argument("--blend-size", type=float, default=32.0, metavar="PIXELS", help="the longest side of the biggest collection, in pixels: sets the scale of all sprites (default 32)")
    prowl.add_argument("--blend-ppu", type=float, default=0.0, metavar="N", help="pixels per Blender unit, instead of --blend-size (a 1 unit tile at --blend-ppu 16 is 16 pixels)")
    prowl.add_argument("--blend-collections", action="append", default=[], metavar="NAME[,NAME]",
                       help="render only these collections (any depth; * and ? match; repeatable) instead of every collection under the scene's")
    prowl.add_argument("--blend-engine", choices=ENGINES, default="cycles", help="Blender's renderer (default cycles, which needs no GPU)")
    prowl.add_argument("--blend-samples", type=int, default=16, metavar="N", help="render samples (default 16)")
    prowl.add_argument("--blend-colors", type=int, default=32, metavar="N", help="at most N colours across the imported sprites, 0 for no limit (default 32)")
    prowl.add_argument("--blend-frames", nargs="?", const="all", type=frames_spec, metavar="all|START:END",
                       help="animation: render every frame of the scene's frame range (or of START:END) as the frames of each sprite, at the scene's frame rate; sprites that do not move keep one frame")
    prowl.add_argument("--blend-cell", type=float, default=1.0, metavar="UNITS", help="the size of a level's grid cell, in Blender units: a collection named Level_* is a level of its collection instances (default 1)")
    prowl.add_argument("--blend-keep", metavar="DIR", help="keep Blender's full-size renders (and manifest.json) in DIR")
    prowl.add_importer(".blend", lambda project, path, args: import_blend(project, path, Options.from_args(args), _say))


def _say(line):
    print("  blender: " + line, flush=True)
