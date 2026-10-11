"""blender_render_collections.py: renders the collections of a Blender scene to transparent PNGs, one per collection, for prowl.py's sprite import.

This file runs INSIDE Blender (it needs bpy), it is not for the system Python. prowl.py (prowl_editor/blender_import.py) starts it:

    blender --background FILE.blend --python tools/blender_render_collections.py -- --out DIR [options]
    blender --background --python my_scene_script.py --python tools/blender_render_collections.py -- --out DIR      (the script builds the scene)

What it does: every collection directly under the scene's collection (or the ones named by --collections, at any depth) is a sprite: everything else is left out
of the render (the other collections are excluded from the view layer, which keeps them usable as instances; lights stay), an orthographic camera looks at it
from --view, and the scene is rendered with a transparent background. All sprites share one
scale (pixels per Blender unit), so a coin stays smaller than a hero. A collection with no geometry (a "Lights" collection), one that is hidden from renders
or excluded from the view layer is skipped. If the scene has no light, a sun and an ambient world are added, so a bare scene is not black.

A collection whose name starts with "level" is a level, not a sprite: it is not rendered, its collection instances (empties that instance a collection) are the tiles.
Each tile is the instanced collection, which is rendered as a sprite, at the instance's position along the camera's right and up axes.
A custom property "solid" on a rendered collection is passed on (the tiles of that sprite are solid).

With --frames (all, or START:END) every frame of the range is rendered, as the frames of the sprite: a collection is framed once, around everything it covers in
any frame, so the animation does not jitter. Without it, one still of the scene's current frame.

It writes DIR/sprite_N.png (sprite_N_K.png for frame K of an animation) and DIR/manifest.json:
{"sprites": [{"name", "file", "files", "width", "height", "scale", "solid", "fps"}], "levels": [{"name", "tiles": [{"sprite", "x", "y"}]}],
"notes": [...], "blender": "x.y.z"}, with x and y in Blender units.
Progress goes to stdout in lines that start with "prowl:".
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

# view: (the direction the camera looks, what is up in the image). "front" looks along +Y with Z up, so X is to the right: what a side-scrolling game shows.
VIEWS = {
    "front": ((0, 1, 0), (0, 0, 1)),
    "back": ((0, -1, 0), (0, 0, 1)),
    "right": ((-1, 0, 0), (0, 0, 1)),
    "left": ((1, 0, 0), (0, 0, 1)),
    "top": ((0, 0, -1), (0, 1, 0)),              # a top-down game
    "bottom": ((0, 0, 1), (0, -1, 0)),
}
BOUNDED = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME", "GREASEPENCIL", "GPENCIL"}   # what has a bounding box to frame
PAD = 2                          # transparent pixels around a render; prowl.py crops them
MAX_RESOLUTION = 2048            # a render never gets bigger than this on a side
MAX_FRAMES = 256                 # frames of one animation
HELPERS = "_prowl_"              # the names of the camera, light and world this script adds
LAYER_PROPERTY = "prowl_layers"
FRAMES_PROPERTY = "prowl_frames"
LEVEL_PREFIX = "level"           # a collection with a name that starts like this is a level (case does not matter)


def say(text):
    print("prowl: " + text, flush=True)


def parse(argv):
    ap = argparse.ArgumentParser(prog="blender_render_collections")
    ap.add_argument("--out", required=True, help="the folder for the PNGs and manifest.json")
    ap.add_argument("--view", choices=sorted(VIEWS), default="front")
    ap.add_argument("--size", type=float, default=32.0, help="pixels of the longest side of the biggest collection (sets the scale)")
    ap.add_argument("--ppu", type=float, default=0.0, help="pixels per Blender unit (replaces --size)")
    ap.add_argument("--engine", choices=("cycles", "eevee", "workbench"), default="cycles")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--collections", nargs="*", default=[], help="render only collections with these names (any depth; * and ? work)")
    ap.add_argument("--frames", default="", metavar="all|START:END", help="render every frame of the scene's frame range (or of START:END) as the frames of each sprite")
    return ap.parse_args(argv)


def frame_list(scene, spec):
    """The frames to render: the scene's current one, or the range `spec` (all, or START:END)."""
    if not spec:
        return [scene.frame_current]
    if spec == "all":
        first, last = scene.frame_start, scene.frame_end
    else:
        try:
            first, last = (int(v) for v in spec.split(":"))
        except ValueError:
            raise SystemExit("--frames is 'all' or START:END (two whole numbers), got '%s'" % spec)
    if last < first:
        raise SystemExit("--frames %s: the last frame is before the first" % spec)
    if last - first + 1 > MAX_FRAMES:
        raise SystemExit("%d frames is more than a sprite can have here (%d): give a shorter range with --frames START:END" % (last - first + 1, MAX_FRAMES))
    return list(range(first, last + 1))


def merge_boxes(a, b):
    """The box (lo, hi) that holds boxes a and b; either may be None."""
    if a is None or b is None:
        return a or b
    return [min(x, y) for x, y in zip(a[0], b[0])], [max(x, y) for x, y in zip(a[1], b[1])]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# what to render

def layer_collections(lc, out):
    out[lc.collection.name_full] = lc
    for child in lc.children:
        layer_collections(child, out)
    return out


def pick_collections(scene, patterns, notes):
    """[(name, collection)]: the top-level collections, or the ones matching `patterns` at any depth."""
    if not patterns:
        return [(c.name, c) for c in scene.collection.children]
    import fnmatch
    everywhere = list(scene.collection.children_recursive)
    picked = []
    for pat in patterns:
        hits = [c for c in everywhere if fnmatch.fnmatchcase(c.name.lower(), pat.lower())]
        if not hits:
            notes.append("no collection is named '%s'" % pat)
        for c in hits:
            if all(c is not p for _, p in picked):
                picked.append((c.name, c))
    return picked


def render_objects(top, layers, visible):
    """{name: object}: the objects of collection `top` (and the collections in it) that a render shows. `visible` is the names of the view layer's objects."""
    found = {}

    def walk(c):
        lc = layers.get(c.name_full)
        if c.hide_render or (lc is not None and lc.exclude):
            return
        for o in c.objects:
            if not o.hide_render and o.name_full in visible:
                found[o.name_full] = o
        for child in c.children:
            walk(child)
    walk(top)
    return found


def basis(view):
    forward, up = (Vector(v) for v in VIEWS[view])
    return forward.cross(up), up, forward                   # right, up, forward


def extents(depsgraph, owners, right, up, forward):
    """((min x, min y, min z), (max x, max y, max z)) of the geometry of the objects `owners` (names), in the camera's axes (x right, y up, z forward), or None.
    It reads the evaluated objects, so modifiers and collection instances count."""
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    for inst in depsgraph.object_instances:
        obj = inst.object
        if obj.type not in BOUNDED:
            continue
        owner = inst.parent.original if inst.is_instance and inst.parent else obj.original
        if owner.name_full not in owners:
            continue
        try:
            corners = [Vector(c) for c in obj.bound_box]
        except (AttributeError, TypeError):
            continue
        for corner in corners:
            p = inst.matrix_world @ corner
            for axis, v in enumerate((p.dot(right), p.dot(up), p.dot(forward))):
                lo[axis], hi[axis] = min(lo[axis], v), max(hi[axis], v)
    return (lo, hi) if lo[0] <= hi[0] else None


def parent_map(collection, out):
    """{collection name: its parent collection} for everything under `collection`."""
    for child in collection.children:
        out[child.name_full] = collection
        parent_map(child, out)
    return out


def related_names(top, parents):
    """The names of `top`, of its ancestors and of everything inside it: what has to stay in the view layer for `top` to render."""
    names, up = set(), top
    while up is not None:
        names.add(up.name_full)
        up = parents.get(up.name_full)
    names.update(c.name_full for c in top.children_recursive)
    return names


def light_names(scene, parents):
    """The names of the collections that hold a light directly, and of their ancestors: they stay in the view layer, so the scene stays lit."""
    names = set()
    for c in [scene.collection] + list(scene.collection.children_recursive):
        if any(o.type == "LIGHT" for o in c.objects):
            up = c
            while up is not None:
                names.add(up.name_full)
                up = parents.get(up.name_full)
    return names


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# the render setup

def attempt(obj, name, value):
    try:
        setattr(obj, name, value)
    except (AttributeError, TypeError, ValueError):          # a setting an older or newer Blender does not have
        pass


def _choose_engine(scene, identifiers):
    for ident in identifiers:
        try:
            scene.render.engine = ident
            return True
        except TypeError:                                    # not an engine of this Blender version
            continue
    return False


def set_engine(scene, engine, samples):
    identifiers = {"cycles": ["CYCLES"], "eevee": ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"], "workbench": ["BLENDER_WORKBENCH"]}[engine]
    if not _choose_engine(scene, identifiers) and engine == "cycles":
        try:                                                 # Blender run as a Python module does not switch its add-ons on by itself
            bpy.ops.preferences.addon_enable(module="cycles")
        except Exception:
            pass
    if scene.render.engine not in identifiers and not _choose_engine(scene, identifiers):
        raise RuntimeError("this Blender has no '%s' render engine" % engine)
    if engine == "cycles":
        c = scene.cycles
        attempt(c, "device", "CPU")                          # works without a GPU, which a headless machine may not have
        attempt(c, "samples", max(1, samples))
        attempt(c, "use_adaptive_sampling", False)
        attempt(c, "use_denoising", False)
        attempt(c, "filter_width", 0.01)                     # almost no anti-aliasing: pixel art has hard edges
        attempt(c, "max_bounces", 4)
    elif engine == "eevee":
        attempt(scene.eevee, "taa_render_samples", max(1, samples))
    vs = scene.view_settings
    attempt(vs, "view_transform", "Standard")                # the colours of the materials as they are, not tone-mapped
    attempt(vs, "look", "None")
    attempt(vs, "exposure", 0.0)
    attempt(vs, "gamma", 1.0)
    r = scene.render
    r.film_transparent = True
    r.use_border = False
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    r.resolution_percentage = 100
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    r.use_file_extension = True


def add_camera(scene):
    data = bpy.data.cameras.new(HELPERS + "camera")
    data.type = "ORTHO"
    cam = bpy.data.objects.new(HELPERS + "camera", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def has_ambient(world):
    """True if the scene's world already lights it (a bright colour or an image: an HDRI), so it is left alone."""
    if world is None or not world.use_nodes:
        return False
    bg = world.node_tree.nodes.get("Background")
    if bg is None:
        return False
    colour = bg.inputs[0]
    return colour.is_linked or bg.inputs[1].default_value * max(colour.default_value[:3]) >= 0.3


def add_light_if_needed(scene, visible, right, up, forward):
    """A scene with no lights renders black: give it a sun (from the upper left of the image) and a grey world."""
    if any(o.type == "LIGHT" for o in visible.values()):
        return False
    sun = bpy.data.objects.new(HELPERS + "sun", bpy.data.lights.new(HELPERS + "sun", "SUN"))
    sun.data.energy = 2.5
    direction = forward * 0.5 + right * 0.4 - up * 0.6      # the way the light travels
    sun.rotation_euler = direction.normalized().to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    if not has_ambient(scene.world):
        world = bpy.data.worlds.new(HELPERS + "world")
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)
            bg.inputs[1].default_value = 0.4
        scene.world = world
    return True


def place_camera(cam, scene, lo, hi, right, up, forward, ppu):
    """Frames the extents (lo, hi) so that one pixel is 1/ppu units; returns (width px, height px, the pixels per unit really used)."""
    width, height, depth = (hi[i] - lo[i] for i in range(3))
    rx, ry = math.ceil(width * ppu) + 2 * PAD, math.ceil(height * ppu) + 2 * PAD
    if max(rx, ry) > MAX_RESOLUTION:
        ppu *= MAX_RESOLUTION / float(max(rx, ry))
        rx, ry = math.ceil(width * ppu) + 2 * PAD, math.ceil(height * ppu) + 2 * PAD
    rx, ry = max(1, rx), max(1, ry)
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    cam.data.ortho_scale = max(rx, ry) / ppu                 # the larger side of the image, in units
    distance = depth / 2 + max(1.0, depth) + 1.0
    centre = right * ((lo[0] + hi[0]) / 2) + up * ((lo[1] + hi[1]) / 2) + forward * ((lo[2] + hi[2]) / 2)
    rotation = Matrix(((right.x, up.x, -forward.x), (right.y, up.y, -forward.y), (right.z, up.z, -forward.z)))     # the camera looks along its -Z, up is +Y
    cam.matrix_world = Matrix.Translation(centre - forward * distance) @ rotation.to_4x4()
    cam.data.clip_start = 0.001
    cam.data.clip_end = 2 * distance + depth + 10.0
    return rx, ry, ppu


def show_only(view_layer, layers, original_exclude, original_hide, snapshot, keep, objs):
    """Leaves in the render only the objects `objs`: the collections not in `keep` are excluded from the view layer (an excluded collection still renders where it
    is instanced, which hiding its objects would not), and the objects in the collections that stay, but not in `objs`, are hidden from the render."""
    for name, o in snapshot.items():                         # back to how the file had them, so nothing hidden for the last sprite hides an instance now
        o.hide_render = original_hide[name]
    for name, lc in layers.items():                          # parents come before their children
        if lc is not view_layer.layer_collection:
            lc.exclude = original_exclude[name] or name not in keep
    view_layer.update()
    for o in view_layer.objects:
        if o.type not in ("LIGHT", "CAMERA"):
            o.hide_render = original_hide.get(o.name_full, o.hide_render) or o.name_full not in objs


# ---------------------------------------------------------------------------------------------------------------------------------------------------

def run(argv):
    args = parse(argv)
    os.makedirs(args.out, exist_ok=True)
    scene, view_layer = bpy.context.scene, bpy.context.view_layer
    view_layer.update()                                      # a scene a script has just built has no object matrices yet: positions would all read as the origin
    notes, sprites = [], []
    layers = layer_collections(view_layer.layer_collection, {})
    visible = {o.name_full: o for o in view_layer.objects}
    original_hide = {n: o.hide_render for n, o in visible.items()}
    original_exclude = {n: lc.exclude for n, lc in layers.items()}
    parents = parent_map(scene.collection, {})
    lit = light_names(scene, parents)
    right, up, forward = basis(args.view)

    candidates, level_collections, group_of = [], [], {}
    for name, coll in pick_collections(scene, args.collections, notes):
        lc = layers.get(coll.name_full)
        if coll.hide_render or (lc is not None and lc.exclude):
            notes.append("'%s' is %s (skipped)" % (name, "hidden from renders" if coll.hide_render else "excluded from the view layer"))
        elif name.lower().startswith(LEVEL_PREFIX):
            level_collections.append((name, coll))
        else:
            candidates.append((name, coll, render_objects(coll, layers, visible)))
            if coll.get(LAYER_PROPERTY):                         # a collection of layers: its child collections are sprites too, framed like it
                for child in coll.children:
                    clc = layers.get(child.name_full)
                    if child.hide_render or (clc is not None and clc.exclude):
                        continue
                    candidates.append((child.name, child, render_objects(child, layers, visible)))
                    group_of[child.name] = name

    levels = []
    for name, coll in level_collections:                     # the tiles of a level, and the collections they instance, which are sprites too
        tiles, ignored, unusable = [], 0, set()
        objs = render_objects(coll, layers, visible)
        for key in sorted(objs):
            o = objs[key]
            inst = o.instance_collection if o.instance_type == "COLLECTION" else None
            if inst is None:
                ignored += 1 if o.type not in ("LIGHT", "CAMERA", "EMPTY") else 0
                continue
            ilc = layers.get(inst.name_full)
            if inst.hide_render or (ilc is not None and ilc.exclude):
                unusable.add(inst.name)
                continue
            if all(inst is not c for _, c, _ in candidates):
                candidates.append((inst.name, inst, render_objects(inst, layers, visible)))
            p = o.matrix_world.translation
            tiles.append({"sprite": inst.name, "x": p.dot(right), "y": p.dot(up)})
        if ignored:
            notes.append("level '%s': %d object%s that %s not a collection instance (ignored: only instances are tiles)" % (name, ignored, "" if ignored == 1 else "s", "is" if ignored == 1 else "are"))
        for n in sorted(unusable):
            notes.append("level '%s': '%s' is hidden from renders or excluded from the view layer, so its tiles are skipped (keep the collection enabled)" % (name, n))
        if tiles:
            levels.append({"name": name, "tiles": tiles})
        else:
            notes.append("level '%s' has no collection instances (skipped)" % name)

    frames = frame_list(scene, args.frames or str(scene.get(FRAMES_PROPERTY, "")))
    original_frame = scene.frame_current
    boxes = [None] * len(candidates)
    for f in frames:                                         # what each collection covers in any frame: its camera is placed once, for all of them
        if len(frames) > 1:
            scene.frame_set(f)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for i, (name, coll, objs) in enumerate(candidates):
            if objs:
                boxes[i] = merge_boxes(boxes[i], extents(depsgraph, objs, right, up, forward))
    scene.frame_set(original_frame)
    by_name = {c[0]: b for c, b in zip(candidates, boxes)}
    for i, (name, coll, objs) in enumerate(candidates):      # a layer is framed like the collection it belongs to, so they lie over each other
        if name in group_of:
            boxes[i] = by_name.get(group_of[name]) if objs else None
    framed = []
    for (name, coll, objs), box in zip(candidates, boxes):
        if box is None:
            notes.append("'%s' has nothing to render (skipped)" % name)
        else:
            framed.append((name, coll, objs, box))
    if not framed:
        if not candidates and not notes:
            notes.append("the scene has no collections: put the objects of each sprite in a collection")
        return finish(args, sprites, levels, notes)

    if args.ppu > 0:
        ppu = args.ppu
    else:
        longest = max(max(hi[0] - lo[0], hi[1] - lo[1]) for _, _, _, (lo, hi) in framed)
        ppu = args.size / longest if longest > 0 else 1.0
    say("%d collection%s, %g pixels per unit, view %s" % (len(framed), "" if len(framed) == 1 else "s", ppu, args.view))

    set_engine(scene, args.engine, args.samples)
    add_light_if_needed(scene, visible, right, up, forward)
    cam = add_camera(scene)
    for index, (name, coll, objs, (lo, hi)) in enumerate(framed):
        show_only(view_layer, layers, original_exclude, original_hide, visible, related_names(coll, parents) | lit, objs)
        rx, ry, used = place_camera(cam, scene, lo, hi, right, up, forward, ppu)
        if used < ppu:
            notes.append("'%s' is too big for the scale: rendered at %.3g pixels per unit instead of %.3g" % (name, used, ppu))
        files = []
        for k, f in enumerate(frames):
            if len(frames) > 1:
                scene.frame_set(f)
            files.append("sprite_%d.png" % index if len(frames) == 1 else "sprite_%d_%d.png" % (index, k))
            scene.render.filepath = os.path.join(args.out, files[-1])
            bpy.ops.render.render(write_still=True)
        sprites.append({"name": name, "file": files[0], "files": files, "width": rx, "height": ry, "scale": used, "solid": bool(coll.get("solid", False)), "group": group_of.get(name, ""),
                        "fps": scene.render.fps / (scene.render.fps_base or 1.0)})
        say("rendered %s (%dx%d%s)" % (name, rx, ry, ", %d frames" % len(frames) if len(frames) > 1 else ""))
    scene.frame_set(original_frame)
    return finish(args, sprites, levels, notes)


def finish(args, sprites, levels, notes):
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"sprites": sprites, "levels": levels, "notes": notes, "blender": bpy.app.version_string}, f, indent=1)
    return 0


if __name__ == "__main__":
    run(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
