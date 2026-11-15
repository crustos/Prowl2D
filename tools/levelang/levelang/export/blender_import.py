"""blender_import.py: runs INSIDE Blender (its own Python, no PIL or levelang): reads the scene JSON that blender_scene.py wrote and builds it as grease pencil, then saves a .blend.

    blender -b --factory-startup --python blender_import.py -- scene.json out.blend [--res 1280x800] [--samples 16] [--video mp4|png|none]

It also runs under the `bpy` module (`python blender_import.py -- scene.json out.blend`), which is how the tests drive it.

The picture is built for Blender 4.3 or newer (grease pencil v3; written and tested on 5.x): every stroke is a grease pencil stroke with its own fill and line colour in a single
material, so there are no hundreds of materials to manage. Layout of the .blend:

  levelang_camera        orthographic, looks along +Y; keyframed to follow the bot like the GIF. Vertical size is fixed (view rows), so any resolution shows the same height.
  levelang_backdrop      a mesh with the level's sky gradient
  parallax/<layer>       an empty per parallax layer whose position is DRIVEN by the camera (so moving the camera by hand keeps the depth); its scenery is parented to it
  <statics>              terrain, standing scenery and the smooth skin (its art is masked by its shape layer)
  <sprites>              one grease pencil datablock per kind of moving thing, linked by every copy; sway is a loop of drawings, each copy offset by its own phase (Time Offset)
  levelang_bot           the bot, keyframed

Units: 1 cell = 1 Blender unit; x right, z up (the scene's y is down, so z = -y). Depth is the Y axis, nearer things at smaller Y.
"""
import json
import math
import sys

import bpy

DEPTH_STEP = 0.02
CAM_Y = -200.0


def lin(c):
    """sRGB 0..1 to the scene-linear value Blender stores."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin3(rgb, a=1.0):
    return (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), a)


def gp_collection():
    return getattr(bpy.data, "grease_pencils_v3", None) or bpy.data.grease_pencils


def make_material():
    mat = bpy.data.materials.new("levelang")
    bpy.data.materials.create_gpencil_data(mat)
    g = mat.grease_pencil
    g.color = (1.0, 1.0, 1.0, 1.0)
    g.fill_color = (1.0, 1.0, 1.0, 1.0)
    g.mix_factor = 1.0           # the colour is the stroke's own, not the material's
    g.mix_stroke_factor = 1.0
    return mat


# ---- strokes -------------------------------------------------------------------------------------------------------------------------------------

def densify(pts, step):
    """Insert points so no segment is longer than `step` (a swaying plant bends along its length)."""
    out = []
    n = len(pts) // 2
    for i in range(n - 1):
        x0, y0, x1, y1 = pts[2 * i], pts[2 * i + 1], pts[2 * i + 2], pts[2 * i + 3]
        k = max(1, int(math.ceil(math.hypot(x1 - x0, y1 - y0) / step)))
        for j in range(k):
            f = j / float(k)
            out.extend((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
    out.extend(pts[-2:])
    return out


def write_strokes(drawing, strokes, dx=0.0, dy=0.0, bend=None):
    """Add `strokes` (scene format) to a drawing. (dx, dy) is subtracted from every point (a sprite's origin is its centre). `bend(x, y)` moves a point sideways (sway)."""
    if not strokes:
        return
    pts_of = []
    for s in strokes:
        p = s["p"]
        if bend is not None:
            p = densify(p, 0.2)
            q = []
            for i in range(0, len(p), 2):
                q.extend((p[i] + bend(p[i], p[i + 1]), p[i + 1]))
            p = q
        pts_of.append(p)
    # a polyline of one point cannot be a stroke
    keep = [(s, p) for s, p in zip(strokes, pts_of) if len(p) >= 4]
    if not keep:
        return
    first = len(drawing.strokes)
    drawing.add_strokes([len(p) // 2 for _, p in keep])
    for i, (s, p) in enumerate(keep):
        st = drawing.strokes[first + i]
        st.cyclic = bool(s["closed"])
        line = s["line"]
        fill = s["fill"]
        lc = lin3(line) if line else (0.0, 0.0, 0.0, 1.0)
        radius = max(s["w"], 0.0) / 2.0
        op = s["lo"] if line else 0.0
        for j, pt in enumerate(st.points):
            pt.position = (p[2 * j] - dx, 0.0, -(p[2 * j + 1] - dy))
            pt.radius = radius
            pt.vertex_color = lc
            pt.opacity = op
        if fill is not None and s["g"]:
            safe_set(st, "fill_color", lin3(fill))
            safe_set(st, "fill_opacity", s["fo"])
            safe_set(st, "fill_id", int(s["g"]))      # a stroke only has a fill when it is in a fill group
        else:
            safe_set(st, "fill_opacity", 0.0)
            safe_set(st, "fill_id", 0)
        safe_set(st, "hide_stroke", line is None)
        set_caps(st, s["cap"] == "round")
    drawing.tag_positions_changed()


def safe_set(obj, attr, value):
    """Set a property that an older Blender 4.x may not have (the picture is then a little poorer, not a crash)."""
    try:
        setattr(obj, attr, value)
    except (AttributeError, TypeError):
        MISSING.add(attr)


MISSING = set()


def set_caps(st, rounded):
    for attr in ("start_cap", "end_cap"):
        try:
            setattr(st, attr, 0 if rounded else 1)
        except Exception:
            try:
                setattr(st, attr, "ROUND" if rounded else "FLAT")
            except Exception:
                pass


def new_layer(gp, name, frame=1):
    """(layer, drawing of its first frame)."""
    layer = gp.layers.new(name)
    layer.use_lights = False
    return layer, layer.frames.new(frame).drawing


# ---- the scene ---------------------------------------------------------------------------------------------------------------------------------------

class Builder:
    def __init__(self, scene_data, opts):
        self.d = scene_data
        self.opts = opts
        self.scene = bpy.context.scene
        self.fps = scene_data["fps"]
        self.mat = make_material()
        self.root = bpy.data.collections.new("levelang")
        self.scene.collection.children.link(self.root)
        self.rigs = {}
        self.sprite_data = {}
        self.cam = None

    # depth: the scene's depth keys are 1, 2, 3 ... in drawing order; nearer = smaller Y
    def y_of(self, depth):
        return -depth * DEPTH_STEP

    def link(self, obj):
        self.root.objects.link(obj)

    def frame_of(self, t):
        return 1.0 + t * self.fps

    # ---- camera, backdrop, rigs ----
    def camera(self):
        d = self.d
        cam = bpy.data.cameras.new("levelang_camera")
        cam.type = "ORTHO"
        cam.sensor_fit = "VERTICAL"
        cam.ortho_scale = float(d["view"][1])
        cam.clip_start = 1.0
        cam.clip_end = 2000.0
        obj = bpy.data.objects.new("levelang_camera", cam)
        obj.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
        obj.location = (d["view"][0] / 2.0, CAM_Y, -d["view"][1] / 2.0)
        self.link(obj)
        self.scene.camera = obj
        for t, cx, cy in d["camera"]:
            obj.location = (cx, CAM_Y, -cy)
            obj.keyframe_insert("location", frame=self.frame_of(t))
        self.cam = obj
        for fc in fcurves(obj):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"

    def backdrop(self):
        d = self.d
        cols, rows = d["cells"]["cols"], d["cells"]["rows"]
        pad = 60.0
        top = tuple(int(d["background"][0][i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        bot = tuple(int(d["background"][1][i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        zs = [(pad, top), (0.0, top), (-rows, bot), (-rows - pad, bot)]
        verts, faces, cols_ = [], [], []
        for z, c in zs:
            verts.append((-pad, 0.0, z))
            verts.append((cols + pad, 0.0, z))
            cols_.extend([lin3(c), lin3(c)])
        for i in range(len(zs) - 1):
            faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        mesh = bpy.data.meshes.new("levelang_backdrop")
        mesh.from_pydata(verts, [], faces)
        attr = mesh.color_attributes.new("sky", "FLOAT_COLOR", "POINT")
        for i, c in enumerate(cols_):
            attr.data[i].color = c
        mat = bpy.data.materials.new("levelang_sky")
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        a = nt.nodes.new("ShaderNodeVertexColor")
        a.layer_name = "sky"
        e = nt.nodes.new("ShaderNodeEmission")
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(a.outputs["Color"], e.inputs["Color"])
        nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
        mesh.materials.append(mat)
        obj = bpy.data.objects.new("levelang_backdrop", mesh)
        obj.location = (0.0, 40.0, 0.0)      # behind everything (the nearest thing is at Y = 0, the farthest a few units in)
        self.link(obj)

    def rig(self, name):
        """The empty a parallax layer hangs on; its position follows the camera: x = (camera x - half the view) * (1 - parallax), z = (camera z + half the view height) * (1 - parallax y)."""
        if name in self.rigs:
            return self.rigs[name]
        lay = next((l for l in self.d["layers"] if "layer:" + l["name"] == name), None)
        e = bpy.data.objects.new("parallax/" + (lay["name"] if lay else name), None)
        e.empty_display_type = "PLAIN_AXES"
        e.empty_display_size = 0.5
        self.link(e)
        if lay:
            px, py = lay["parallax"]
            hw, hh = self.d["view"][0] / 2.0, self.d["view"][1] / 2.0
            for idx, ttype, expr in ((0, "LOC_X", "(v - %r) * %r" % (hw, 1.0 - px)), (2, "LOC_Z", "(v + %r) * %r" % (hh, 1.0 - py))):
                fc = e.driver_add("location", idx)
                drv = fc.driver
                drv.type = "SCRIPTED"
                var = drv.variables.new()
                var.name = "v"
                var.type = "TRANSFORMS"
                tg = var.targets[0]
                tg.id = self.cam
                tg.transform_type = ttype
                tg.transform_space = "WORLD_SPACE"
                drv.expression = expr
        self.rigs[name] = e
        return e

    # ---- static objects ----
    def statics(self):
        for so in self.d["statics"]:
            gp = gp_collection().new(so["name"])
            gp.materials.append(self.mat)
            layers = {}
            for ly in so["layers"]:
                layer, drawing = new_layer(gp, ly["name"])
                layers[ly["name"]] = layer
                write_strokes(drawing, ly["strokes"])
            for ly in so["layers"]:
                if ly.get("mask"):
                    layer = layers[ly["name"]]
                    layer.use_masks = True
                    layer.mask_layers.add(layers[ly["mask"]])
            obj = bpy.data.objects.new(so["name"], gp)
            obj.location = (0.0, self.y_of(so["depth"]), 0.0)
            if so["parent"]:
                obj.parent = self.rig(so["parent"])
            self.link(obj)

    # ---- sprites ----
    def sprite(self, key):
        """The grease pencil datablock of a moving sprite (origin at its centre); a swaying one has one drawing per pose."""
        if key in self.sprite_data:
            return self.sprite_data[key]
        sp = self.d["sprites"][key]
        gp = gp_collection().new("sprite/" + key[:48])
        gp.materials.append(self.mat)
        layer = gp.layers.new("art")
        layer.use_lights = False
        w, h = sp["w"], sp["h"]
        sway = sp.get("sway")
        if sway:
            n = sway["poses"]
            for k in range(n):
                fr = layer.frames.new(k + 1)
                amp, base = sway["amp"], sway["base"]

                def bend(x, y, k=k, amp=amp, base=base):
                    above = base + (h - y)          # cells above the plant's foot (the bottom of its box)
                    return amp * above * math.sin(2 * math.pi * k / n - 0.9 * above)

                write_strokes(fr.drawing, sp["strokes"], w / 2.0, h / 2.0, bend)
        else:
            fr = layer.frames.new(1)
            write_strokes(fr.drawing, sp["strokes"], w / 2.0, h / 2.0)
        self.sprite_data[key] = gp
        return gp

    def key_time(self, obj, path, index, pairs, interpolation="LINEAR"):
        for t, v in pairs:
            if index is None:
                setattr(obj, path, v)
                obj.keyframe_insert(path, frame=self.frame_of(t))
            else:
                getattr(obj, path)[index] = v
                obj.keyframe_insert(path, index=index, frame=self.frame_of(t))
        set_interpolation(obj, path, index, interpolation)

    def movers(self):
        d = self.d
        duration = d["duration"]
        for o in d["objects"]:
            sp = d["sprites"][o["sprite"]]
            gp = self.sprite(o["sprite"])
            obj = bpy.data.objects.new(o["name"], gp)
            y = self.y_of(o["depth"])
            cx, cz = o["x"] + o["w"] / 2.0, -(o["y"] + o["h"] / 2.0)
            obj.location = (cx, y, cz)
            if o["parent"]:
                obj.parent = self.rig(o["parent"])
            self.link(obj)
            a = o["anim"]
            if o["flip"]:
                obj.scale = (-1.0, 1.0, 1.0)
            if "sway" in a and "sway" in sp:
                m = obj.modifiers.new("sway", "GREASE_PENCIL_TIME")
                n = sp["sway"]["poses"]
                m.mode = "NORMAL"
                m.use_custom_frame_range = True
                m.frame_start, m.frame_end = 1, n
                m.use_keep_loop = True
                m.frame_scale = n / (a["sway"]["period"] * self.fps)      # n drawings in one period
                m.offset = int(round(a["sway"]["phase"] * n)) % n
            if "bob" in a:
                b = a["bob"]
                steps = 8
                times = [i * b["period"] / steps for i in range(int(duration / (b["period"] / steps)) + 2)]
                self.key_time(obj, "location", 2, [(t, cz - b["amp"] * math.sin(2 * math.pi * ((t / b["period"] + b["phase"]) % 1.0))) for t in times], "BEZIER")
            if "swim" in a:
                s = a["swim"]
                half = s["period"] / 2.0
                # w = (t / period + phase) % 1; x moves (1 - |2w - 1|) * n; the sprite is turned over while w > .5. The path bends at w = 0 and w = .5: key those times.
                t0 = -((s["phase"] % 1.0) * s["period"])
                xs, flips = [], []
                k = 0
                while t0 + k * half <= duration + half:
                    t = t0 + k * half
                    w = round((t / s["period"] + s["phase"]) % 1.0, 6) % 1.0
                    xs.append((t, cx + (1.0 - abs(2.0 * w - 1.0)) * s["n"]))
                    second_half = abs(w - 0.5) < 1e-4                     # this segment runs from w = .5 to 1: turned over
                    turned = bool(o["flip"]) != second_half
                    flips.append((t, -1.0 if turned else 1.0))
                    k += 1
                self.key_time(obj, "location", 0, xs, "LINEAR")
                self.key_time(obj, "scale", 0, flips, "CONSTANT")
            if "hide_at" in o and o["hide_at"] is not None:
                t = o["hide_at"]
                for tt, hidden in ((max(0.0, t - 1.0 / self.fps), False), (t, True)):
                    obj.hide_render = hidden
                    obj.hide_viewport = hidden
                    obj.keyframe_insert("hide_render", frame=self.frame_of(tt))
                    obj.keyframe_insert("hide_viewport", frame=self.frame_of(tt))
                set_interpolation(obj, "hide_render", None, "CONSTANT")
                set_interpolation(obj, "hide_viewport", None, "CONSTANT")

    def bot(self):
        b = self.d["bot"]
        if not b:
            return
        sp = self.d["sprites"][b["sprite"]]
        gp = self.sprite(b["sprite"])
        obj = bpy.data.objects.new("levelang_bot", gp)
        s = float(b["size"])
        obj.scale = (s, s, s)
        obj.location = (0.0, self.y_of(b["depth"]), 0.0)
        self.link(obj)
        last_flip = None
        for t, x, y, left in b["keys"]:
            f = self.frame_of(t)
            obj.location = (x, self.y_of(b["depth"]), -y)
            obj.keyframe_insert("location", index=0, frame=f)
            obj.keyframe_insert("location", index=2, frame=f)
            if left != last_flip:
                obj.scale = (-s if left else s, s, s)
                obj.keyframe_insert("scale", index=0, frame=f)
                last_flip = left
        set_interpolation(obj, "location", None, "LINEAR")
        set_interpolation(obj, "scale", 0, "CONSTANT")

    # ---- the scene's settings ----
    def settings(self):
        sc = self.scene
        o = self.opts
        sc.render.fps = self.fps
        sc.frame_start = 1
        sc.frame_end = max(2, int(round(self.d["duration"] * self.fps)) + 1)
        sc.render.resolution_x, sc.render.resolution_y = o["res"]
        sc.render.resolution_percentage = 100
        try:
            sc.render.engine = "BLENDER_EEVEE"
        except TypeError:
            sc.render.engine = "BLENDER_EEVEE_NEXT"
        try:
            sc.eevee.taa_render_samples = o["samples"]
            sc.eevee.taa_samples = min(o["samples"], 16)
        except Exception:
            pass
        sc.view_settings.view_transform = "Standard"     # the colours of the SVGs, not a filmic tone curve
        try:
            sc.view_settings.look = "None"
        except Exception:
            pass
        sc.render.film_transparent = False
        sc.world = sc.world or bpy.data.worlds.new("levelang_world")
        video = o["video"]
        if video == "mp4":
            try:
                try:
                    sc.render.image_settings.media_type = "VIDEO"
                except Exception:
                    pass
                sc.render.image_settings.file_format = "FFMPEG"
                sc.render.ffmpeg.format = "MPEG4"
                sc.render.ffmpeg.codec = "H264"
                sc.render.ffmpeg.constant_rate_factor = "HIGH"
                sc.render.filepath = "//levelang-preview.mp4"
            except Exception as e:
                print("levelang: no mp4 output here (%s): rendering PNG frames" % e)
                video = "png"
        if video == "png":
            sc.render.image_settings.file_format = "PNG"
            sc.render.filepath = "//levelang-preview/frame_"
        sc["levelang"] = json.dumps({"name": self.d["name"], "cells": self.d["cells"], "duration": self.d["duration"]})

    def build(self):
        self.camera()
        self.backdrop()
        self.statics()
        self.movers()
        self.bot()
        self.settings()


# ---- animation helpers -------------------------------------------------------------------------------------------------------------------------------

def fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []                                         # Blender 4.4+/5: actions have layers, strips and channelbags
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def set_interpolation(obj, path, index, mode):
    for fc in fcurves(obj):
        if fc.data_path == path and (index is None or fc.array_index == index):
            for kp in fc.keyframe_points:
                kp.interpolation = mode


# ---- entry -----------------------------------------------------------------------------------------------------------------------------------------------

def parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) < 2:
        raise SystemExit("usage: blender -b --python blender_import.py -- scene.json out.blend [--res WxH] [--samples N] [--video mp4|png|none]")
    opts = {"res": (1280, 800), "samples": 16, "video": "mp4"}
    i = 2
    while i < len(argv):
        if argv[i] == "--res":
            w, h = argv[i + 1].lower().split("x")
            opts["res"] = (int(w), int(h))
            i += 2
        elif argv[i] == "--samples":
            opts["samples"] = int(argv[i + 1])
            i += 2
        elif argv[i] == "--video":
            opts["video"] = argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown option " + argv[i])
    return argv[0], argv[1], opts


def main(argv=None):
    scene_path, out_path, opts = parse_args(argv if argv is not None else sys.argv)
    with open(scene_path, encoding="utf-8") as f:
        data = json.load(f)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    Builder(data, opts).build()
    if MISSING:
        print("levelang: this Blender lacks the grease pencil properties %s: fills or caps may look different" % ", ".join(sorted(MISSING)))
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    print("levelang: wrote", out_path)


if __name__ == "__main__":
    main()
