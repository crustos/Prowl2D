"""prowl_blender.py: build and animate things with code, inside Blender, for prowl.py --blend-script.

A script that makes its own objects can animate them in the same breath, and prowl.py renders the frames (and the layers) to sprites:

    import prowl_blender as pb

    pb.new_scene(frames=12, fps=12)                       # an empty scene with 12 frames; prowl.py renders all of them
    cat = pb.head("cat", name="cat")                      # a head made of parts: skin, eyes, pupils, lids, mouth, lip, teeth ...
    for f in pb.frames():                                 # f.number is the frame, f.t goes 0 -> 1 over the loop
        cat.look(x=pb.sin(f.t), y=0)                      # the pupils (and lids) look sideways, once round the loop
        cat.blink(1.0 if f.i == 8 else 0.0)               # one blink
        cat.mouth(0.5 + 0.5 * pb.sin(f.t, 2))             # the lip opens and closes, twice

    python3 prowl.py --blend-script cat.py --blend-ppu 64 -o cat.json

The heads follow zigzag (https://github.com/brentharts/zigzag, MIT License, Copyright (c) 2024 brent hartshorn): Blender's Suzanne with the vertices of some
of her points moved (prowl_blender_heads.json) makes a cat, a dog, a bear, a gorilla, an alien, a frog or an ogre with the same topology, so the same polygon
ranges are the same face parts in every head; a part is the polygons of one material. A material has a role (pupil, upper eyelid, lower eyelid, lower lip) that
says how it moves, and the parts are separate objects, so animating one is moving an object: keyframes you can see and change in Blender, and renders that do
not need this file. Each head is a collection with child collections for its layers (head, mouth, eyes): prowl.py renders the head and each layer as a sprite,
framed alike, so the layers lie exactly over each other.

This file runs inside Blender (it needs bpy). prowl.py puts its folder on Blender's Python path for --blend-script, so `import prowl_blender` works.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FACE_VERTICES = 507                  # Suzanne's vertices: a head table moves some of them
LAYER_PROPERTY = "prowl_layers"      # a collection with this custom property set has its child collections rendered as sprites too (tools/blender_render_collections.py)
FRAMES_PROPERTY = "prowl_frames"     # a scene with this custom property ("all" or "START:END") is rendered as an animation without --blend-frames


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# small things

def sin(t, turns=1.0, phase=0.0):
    """sin of t (0..1 over the loop) times `turns` turns: sin(f.t) is one smooth swing from 0 and back, sin(f.t, 2) is two."""
    return math.sin(2.0 * math.pi * (t * turns + phase))


def cos(t, turns=1.0, phase=0.0):
    return math.cos(2.0 * math.pi * (t * turns + phase))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def new_scene(frames=1, fps=12, clear=True):
    """The scene to build in: `clear` removes what is in it, `frames` is the length of the animation (1: a still), `fps` its speed. Returns the scene.
    With more than one frame prowl.py renders them all, as the frames of each sprite (the same as --blend-frames all)."""
    scene = bpy.context.scene
    if clear:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        for coll in list(bpy.data.collections):
            bpy.data.collections.remove(coll)
    scene.frame_start, scene.frame_end = 1, max(1, int(frames))
    scene.render.fps, scene.render.fps_base = int(fps), 1.0
    scene.frame_set(1)
    if frames > 1:
        scene[FRAMES_PROPERTY] = "all"
    elif FRAMES_PROPERTY in scene:
        del scene[FRAMES_PROPERTY]
    return scene


def collection(name, parent=None, layers=False):
    """A new collection (under `parent`, a collection, or the scene's). With `layers`, its child collections are rendered as sprites too, framed like it."""
    coll = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(coll)
    if layers:
        coll[LAYER_PROPERTY] = True
    return coll


class Frame:
    """One frame of the loop: `number` (the scene's frame), `i` (0 for the first), `t` (i / the number of frames: 0 up to, not including, 1, so a loop that is a
    function of t repeats without a stutter)."""
    def __init__(self, number, i, count):
        self.number, self.i, self.count = number, i, count
        self.t = i / float(count)

    def __repr__(self):
        return "Frame(%d, t=%.3f)" % (self.number, self.t)


def frames():
    """Steps through the scene's frames, setting the current frame, and gives a Frame each: the loop body animates what it likes at that frame."""
    scene = bpy.context.scene
    first, last = scene.frame_start, scene.frame_end
    count = last - first + 1
    for i, number in enumerate(range(first, last + 1)):
        scene.frame_set(number)
        yield Frame(number, i, count)
    scene.frame_set(first)


def key(ob, location=None, rotation=None, scale=None, interpolation=None):
    """Sets and keyframes (at the current frame) the object's `location`, `rotation` (degrees, x y z) and/or `scale`, the ones given. `interpolation` is
    'BEZIER' (Blender's default: smooth), 'LINEAR' or 'CONSTANT' (a pose that holds): for the keys made by this call."""
    edit = bpy.context.preferences.edit
    previous = edit.keyframe_new_interpolation_type
    if interpolation:
        edit.keyframe_new_interpolation_type = interpolation
    try:
        if location is not None:
            ob.location = location
            ob.keyframe_insert("location")
        if rotation is not None:
            ob.rotation_euler = [math.radians(a) for a in rotation]
            ob.keyframe_insert("rotation_euler")
        if scale is not None:
            ob.scale = scale
            ob.keyframe_insert("scale")
    finally:
        edit.keyframe_new_interpolation_type = previous
    return ob


def material(name, rgb, role="NONE"):
    """A flat-coloured material. `role` is what the part that wears it does (see ROLES): it is kept on the material (zigzag's `zigzag_object_type`)."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    try:
        mat.use_nodes = True                                 # the render uses the node tree; the viewport colour above is for the viewport
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9
    except Exception:                                        # a Blender that has no use_nodes any more makes the node tree itself
        pass
    mat["role"] = role
    return mat


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# heads

_HEADS = None

# the face materials of zigzag's libgenzag.setup_face_materials, in its order: (part name, role, colour ranges (r, g, b) as (low, high); "skin" for the head's own)
ROLES = ("NONE", "PUPIL", "UPPER_EYELID", "LOWER_EYELID", "LOWER_LIP")
FACE_MATERIALS = [
    ("skin", "NONE", "skin"),
    ("pupil", "PUPIL", ((0, 0.3), (0, 0.3), (0, 0.5))),
    ("eye", "NONE", ((0.8, 1), (0.8, 1), (0.8, 1))),
    ("teeth_lower", "NONE", ((0.8, 1), (0.8, 1), (0.8, 1))),
    ("hair", "NONE", "skin"),
    ("mouth", "NONE", ((0.3, 0.8), (0, 0.1), (0.1, 0.3))),
    ("mouth_back", "NONE", ((0, 0), (0, 0), (0, 0))),
    ("teeth_upper", "NONE", ((0.4, 0.5), (0.4, 0.5), (0.4, 0.5))),
    ("lip_lower", "LOWER_LIP", ((0.5, 0.9), (0.1, 0.3), (0.2, 0.5))),
    ("lids", "NONE", ((0.4, 0.8), (0.2, 0.5), (0.3, 0.6))),
    ("lid_upper", "UPPER_EYELID", ((0.1, 0.3), (0, 0.1), (0, 0.1))),
    ("lid_lower", "LOWER_EYELID", ((0.2, 0.5), (0, 0.3), (0, 0.3))),
    ("nose", "NONE", ((0.4, 0.8), (0.2, 0.5), (0.3, 0.6))),
]
PART_INDEX = {name: i for i, (name, _, _) in enumerate(FACE_MATERIALS)}

# how each kind of head is made: the table of vertex offsets (a key of prowl_blender_heads.json), whether it has teeth (zigzag's monkey has 8 cubes, the gorilla one),
# the nose polygons, and the skin colour ranges (zigzag's defaults when not given)
DEFAULT_SKIN = ((0.4, 0.8), (0.2, 0.5), (0.3, 0.6))
KINDS = {
    "monkey": {"teeth": 8, "skin": DEFAULT_SKIN},
    "cat": {"nose": True, "skin": ((0.6, 1), (0.6, 1), (0.6, 1))},
    "dog": {"nose": True, "skin": ((0.3, 0.6), (0.2, 0.4), (0.2, 0.5))},
    "bear": {"nose": True, "skin": DEFAULT_SKIN},
    "gorilla": {"teeth": 1, "skin": DEFAULT_SKIN},
    "alien": {"skin": DEFAULT_SKIN},
    "frog": {"skin": DEFAULT_SKIN},
    "ogre": {"skin": DEFAULT_SKIN},
}
EMOJI = {"🐵": "monkey", "🐱": "cat", "🐶": "dog", "🐻": "bear", "🦍": "gorilla", "👽": "alien", "🐸": "frog", "👹": "ogre"}


def head_kinds():
    """The names of the kinds of head."""
    return list(KINDS)


def _head_table(kind):
    global _HEADS
    if _HEADS is None:
        with open(os.path.join(HERE, "prowl_blender_heads.json"), encoding="utf-8") as f:
            _HEADS = json.load(f)["heads"]
    return _HEADS[kind]


def _teeth(bm, count):
    """Cubes for teeth, like zigzag's monkey(): a row of four at the front of the mouth, and a second row below it (8 cubes), or a single cube (the gorilla's)."""
    size = 0.04
    rows, cols = (2, 4) if count == 8 else (1, 1)
    for r in range(rows):
        for c in range(cols):
            geom = bmesh.ops.create_cube(bm, size=2.0)["verts"]
            x, z = -0.144 + c * 1.2 * 2 * size, -0.66 - r * 1.9 * 2 * size
            bmesh.ops.scale(bm, vec=(size, size, size), verts=geom)
            bmesh.ops.translate(bm, vec=(x, -0.62, z), verts=geom)


def _face_styles(bm, kind):
    """zigzag's basic_face_style: which polygons are which material (later lines win). Suzanne's polygons have the same order in every head."""
    faces = list(bm.faces)

    def assign(lo, hi, index):
        for f in faces[lo:hi]:
            f.material_index = index
    n = len(faces)
    assign(0, 64, PART_INDEX["pupil"])
    assign(0, 32, PART_INDEX["eye"])
    assign(n - 300, n, PART_INDEX["hair"])
    assign(170, 194, PART_INDEX["mouth"])
    assign(178, 182, PART_INDEX["lip_lower"])
    assign(190, 192, PART_INDEX["mouth_back"])
    assign(170, 174, PART_INDEX["skin"])
    teeth = KINDS[kind].get("teeth", 0) * 6                  # the teeth are the last polygons: the first half upper, the second half lower
    if teeth:
        assign(n - teeth, n - teeth // 2, PART_INDEX["teeth_upper"])
        assign(n - teeth // 2, n, PART_INDEX["teeth_lower"])
    assign(192, 246, PART_INDEX["lids"])
    assign(220, 230, PART_INDEX["lid_upper"])
    assign(202, 206, PART_INDEX["lid_lower"])
    if KINDS[kind].get("nose"):
        assign(146, 160, PART_INDEX["nose"])


def _colour(rng, ranges):
    return tuple(rng.uniform(lo, hi) for lo, hi in ranges)


def head_mesh(kind, name, skin=None, seed=0):
    """(the whole head as one mesh with its 13 face materials, the materials): Suzanne shaped as `kind`, polygons given their parts."""
    if kind in EMOJI:
        kind = EMOJI[kind]
    if kind not in KINDS:
        raise ValueError("no head '%s' (there are: %s)" % (kind, ", ".join(KINDS)))
    rng = random.Random("%s/%s" % (kind, seed))
    bm = bmesh.new()
    bmesh.ops.create_monkey(bm)
    bm.verts.ensure_lookup_table()
    for index, offset in _head_table(kind).items():
        bm.verts[int(index)].co += Vector(offset)
    if KINDS[kind].get("teeth"):
        _teeth(bm, KINDS[kind]["teeth"])
    bm.faces.ensure_lookup_table()
    _face_styles(bm, kind)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ranges = KINDS[kind]["skin"]
    materials = []
    for part, role, colour in FACE_MATERIALS:
        if colour == "skin":
            rgb = tuple(skin) if skin is not None else (ranges[0][0], rng.uniform(*ranges[1]), rng.uniform(*ranges[2]))
        else:
            rgb = _colour(rng, colour)
        materials.append(material("%s_%s" % (name, part), rgb, role))
    return me, materials


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# a head made of parts

# which layer (child collection) each part is in, and how far a part moves for look / blink / mouth (in head units: Suzanne is about 2 wide)
LAYER_OF = {
    "skin": "head", "hair": "head", "nose": "head", "lids": "head",
    "eye": "eyes", "pupil": "eyes", "lid_upper": "eyes", "lid_lower": "eyes",
    "mouth": "mouth", "mouth_back": "mouth", "lip_lower": "mouth", "teeth_lower": "mouth", "teeth_upper": "mouth",
}
LAYER_ORDER = ("head", "mouth", "eyes")
LOOK_RANGE = 0.07            # how far the pupils (and the lids with them) slide for look(x=1)
BLINK_RANGE = 0.13           # how far the upper lid comes down (and the lower one comes up, by half as much) for blink(1)
MOUTH_RANGE = 0.14           # how far the lower lip (and its teeth) drops for mouth(1)


def _split(mesh_data, materials, index, name):
    """An object holding only the polygons of material `index` (None when there are none), its origin at their centre."""
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    doomed = [f for f in bm.faces if f.material_index != index]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.verts.ensure_lookup_table()
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    if not bm.faces:
        bm.free()
        return None
    centre = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    bmesh.ops.translate(bm, vec=-centre, verts=list(bm.verts))
    for f in bm.faces:
        f.material_index = 0
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(materials[index])
    ob = bpy.data.objects.new(name, me)
    ob.location = centre
    return ob


class Face:
    """A head built by head(): `root` (an empty to move the whole head), `parts` (part name -> object), and the things to animate it with.
    look, blink and mouth set and keyframe the parts for the current frame (see frames())."""

    def __init__(self, kind, name, root, parts, layers):
        self.kind, self.name, self.root, self.parts, self.layers = kind, name, root, parts, layers
        self.rest = {part: Vector(ob.location) for part, ob in parts.items()}
        self.rest_root = Vector(root.location)

    def role(self, role):
        """The parts whose material has this role (PUPIL, UPPER_EYELID, LOWER_EYELID, LOWER_LIP)."""
        return [ob for ob in self.parts.values() if ob.active_material is not None and ob.active_material.get("role") == role]

    def _put(self, part, dx=0.0, dz=0.0, interpolation=None):
        ob = self.parts.get(part)
        if ob is not None:
            r = self.rest[part]
            key(ob, location=(r.x + dx, r.y, r.z + dz), interpolation=interpolation)

    def look(self, x=0.0, y=0.0, interpolation=None):
        """The pupils look: x -1..1 left to right, y -1..1 down to up (as the head faces you)."""
        for ob in self.role("PUPIL"):
            part = [p for p, o in self.parts.items() if o is ob][0]
            self._put(part, -x * LOOK_RANGE, y * LOOK_RANGE, interpolation)

    def blink(self, amount=1.0, interpolation=None):
        """The eyelids close: 0 open, 1 shut."""
        amount = clamp(amount)
        for ob in self.role("UPPER_EYELID"):
            part = [p for p, o in self.parts.items() if o is ob][0]
            self._put(part, 0.0, -amount * BLINK_RANGE, interpolation)
        for ob in self.role("LOWER_EYELID"):
            part = [p for p, o in self.parts.items() if o is ob][0]
            self._put(part, 0.0, amount * BLINK_RANGE * 0.5, interpolation)

    def mouth(self, amount=0.0, interpolation=None):
        """The lower lip (and the lower teeth with it) drops: 0 closed, 1 wide open."""
        amount = clamp(amount)
        for part in ("lip_lower", "teeth_lower"):
            self._put(part, 0.0, -amount * MOUTH_RANGE, interpolation)

    def move(self, location=None, rotation=None, scale=None, interpolation=None):
        """Moves the whole head (location is added to where it was made), keyframed."""
        if location is not None:
            location = (self.rest_root.x + location[0], self.rest_root.y + location[1], self.rest_root.z + location[2])
        key(self.root, location, rotation, scale, interpolation)

    def rest_pose(self):
        """Keys every part where it was made, at the current frame."""
        for part in self.parts:
            self._put(part)


def head(kind="monkey", name=None, skin=None, seed=0, location=(0, 0, 0), layers=True, collection_=None, scale=1.0):
    """A head of the given kind (monkey, cat, dog, bear, gorilla, alien, frog, ogre, or their emoji) as a Face. It is a collection of its own (in the scene's, or
    `collection_`) with child collections for the layers when `layers` is true: 'head', 'mouth' and 'eyes' (or a dict {layer: [part names]}, or False for none).
    `skin` is an (r, g, b) colour, else a random one in the kind's range (the same for the same `seed`)."""
    kind = EMOJI.get(kind, kind)
    name = name or kind
    mesh_data, materials = head_mesh(kind, name, skin, seed)
    top = collection(name, collection_, layers=bool(layers))
    root = bpy.data.objects.new(name + "_root", None)
    top.objects.link(root)
    root.location = location
    root.scale = (scale, scale, scale)
    if isinstance(layers, dict):
        where = {part: layer for layer, parts in layers.items() for part in parts}
    else:
        where = LAYER_OF
    subs = {}
    parts = {}
    for index, (part, _, _) in enumerate(FACE_MATERIALS):
        ob = _split(mesh_data, materials, index, "%s_%s" % (name, part))
        if ob is None:
            continue
        ob.parent = root
        layer = where.get(part, "head") if layers else None
        if layer is None:
            home = top
        else:
            if layer not in subs:
                subs[layer] = collection("%s_%s" % (name, layer), top)
            home = subs[layer]
        home.objects.link(ob)
        parts[part] = ob
    bpy.data.meshes.remove(mesh_data)
    if subs:                                                  # the layers in a stable order: head, mouth, eyes, then any others
        order = [l for l in LAYER_ORDER if l in subs] + [l for l in subs if l not in LAYER_ORDER]
        for l in order:
            top.children.unlink(subs[l])
            top.children.link(subs[l])
    return Face(kind, name, root, parts, {l: c for l, c in subs.items()})
