"""scenery.py: bake a level's parallax layers and smooth skin into C# data for a game (`SceneryData.cs`), the way the game draws them with `GFX.Triangles`.

The editor project (`prowl_project.to_project`) already has everything as pictures: layers of items (image, x, y, w, h, and the animation), each picture a PNG. A game cannot load a PNG
(the C# subset has no files), so this packs all the pictures into ONE atlas (one texture, so one `GFX.Texture` and the renderer's 63 texture limit never comes up), reduces it to a
256 colour palette, run-length encodes it, and writes it as arrays that `Scenery.cs` decodes at startup. The layers' items follow as one flat float array.

Everything that needs unbounded integers (the phase of an item hashes its position) is worked out HERE with `prowl_editor.parallax` and written down, so the C# does no hashing and cannot
disagree with the editor.
"""
import base64
import io
import math

from PIL import Image

from .prowl_project import to_project

PALETTE_COLOURS = 256         # a run is `count * 256 + palette index` (see Scenery.Init)
RUN_MAX = 30000               # keeps count * 256 + index well inside an int
ITEM_FIELDS = ("u0", "v0", "u1", "v1", "x", "y", "w", "h", "flip", "swim_n", "swim_period", "bob", "sway", "base", "phase", "sway_phase")
LAYER_FIELDS = ("parallax_x", "parallax_y", "over", "r", "g", "b", "a", "first", "count")


def _parallax():
    """prowl_editor.parallax: the one definition of phase, swim period and tint (the repo root is on the path when this runs from the repo)."""
    import os
    import sys
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    from prowl_editor import parallax
    return parallax


def _shelf_pack(sizes, width):
    """Place rectangles (w, h) left to right in rows no wider than `width`: [(x, y)] and the height used."""
    x = y = row = 0
    spots = []
    for w, h in sizes:
        if x + w > width:
            x, y, row = 0, y + row, 0
        spots.append((x, y))
        x += w
        row = max(row, h)
    return spots, y + row


def build_atlas(images, max_px=128, skin_px=768, gutter=1, width=1024):
    """Pack the project's images. Returns (atlas RGBA Image, {name: (u0, v0, u1, v1)}): the uv rectangle is inset half a texel so linear filtering does not read a neighbour."""
    pics = {}
    for im in images:
        pic = Image.open(io.BytesIO(base64.b64decode(im["png"]))).convert("RGBA")
        w, h = pic.size
        s = min(1.0, (skin_px if im["name"].startswith("skin") else max_px) / float(max(w, h)))      # a skin is one picture of a whole level: it needs more pixels than a coral
        if s < 1.0:
            pic = pic.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
        pics[im["name"]] = pic
    names = list(pics)
    cells = [(pics[n].width + 2 * gutter, pics[n].height + 2 * gutter) for n in names]
    spots, height = _shelf_pack(cells, width)
    atlas = Image.new("RGBA", (width, max(1, height)), (0, 0, 0, 0))
    uv = {}
    for n, (cx, cy) in zip(names, spots):
        pic = pics[n]
        w, h = pic.size
        ox, oy = cx + gutter, cy + gutter
        atlas.paste(pic, (ox, oy))
        for g in range(gutter):                       # repeat the edge pixels outward: the bilinear fetch at the border then reads the picture, not air
            atlas.paste(pic.crop((0, 0, w, 1)), (ox, oy - 1 - g))
            atlas.paste(pic.crop((0, h - 1, w, h)), (ox, oy + h + g))
        for g in range(gutter):
            atlas.paste(atlas.crop((ox, oy - gutter, ox + 1, oy + h + gutter)), (ox - 1 - g, oy - gutter))
            atlas.paste(atlas.crop((ox + w - 1, oy - gutter, ox + w, oy + h + gutter)), (ox + w + g, oy - gutter))
        e = 0.5
        uv[n] = ((ox + e) / width, (oy + e) / atlas.height, (ox + w - e) / width, (oy + h - e) / atlas.height)
    return atlas, uv


def quantize_atlas(atlas):
    """(palette [(r, g, b, a)] with index 0 air (fully transparent), indices [int] row by row). 256 colours with alpha."""
    q = atlas.quantize(colors=PALETTE_COLOURS - 1, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    raw = q.getpalette(rawmode="RGBA") or []
    pal = [(0, 0, 0, 0)] + [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)][:PALETTE_COLOURS - 1]       # entry 0 is air; the picture's 255 colours follow
    while len(pal) < PALETTE_COLOURS:
        pal.append((0, 0, 0, 0))
    alpha = atlas.getchannel("A").tobytes()
    idx = [0 if al == 0 else i + 1 for i, al in zip(q.tobytes(), alpha)]
    return pal, idx


def rle(indices):
    """Runs as ints: count * 256 + palette index."""
    out = []
    i, n = 0, len(indices)
    while i < n:
        v = indices[i]
        j = i
        while j < n and indices[j] == v and j - i < RUN_MAX:
            j += 1
        out.append((j - i) * PALETTE_COLOURS + v)
        i = j
    return out


def decode(palette, runs, width, height):
    """The inverse of the above (what Scenery.cs does), used by the tests: an RGBA Image."""
    data = bytearray()
    for r in runs:
        count, idx = divmod(r, PALETTE_COLOURS)
        data += bytes(palette[idx]) * count
    return Image.frombytes("RGBA", (width, height), bytes(data))


def scenery(level, name="levelang", ppc=32, tile_px=16, max_px=128, skin_px=768, warn=print):
    """The numbers `SceneryData.cs` holds, as a dict (kept apart from the text so the tests can read them)."""
    par = _parallax()
    project = to_project(level, name, ppc=ppc, tile_px=tile_px, warn=warn)
    lv = project["levels"][0]
    x0, y0, x1, y1 = level.bounds()
    height = int(level.meta["height"]) if level.meta.get("height") else y1 - y0 + 1
    atlas, uv = build_atlas(project["images"], max_px=max_px, skin_px=skin_px)
    palette, idx = quantize_atlas(atlas)
    layers, items = [], []
    for layer in sorted(lv["layers"], key=lambda l: l["parallax"][0]):
        r, g, b, a = par.tint(layer)
        first = len(items)
        for it in layer["items"]:
            u0, v0, u1, v1 = uv[it["image"]]
            swim = it.get("swim")
            sway = it.get("sway")
            items.append({
                "u0": u0, "v0": v0, "u1": u1, "v1": v1, "x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"],
                "flip": 1.0 if it.get("flip") else 0.0,
                "swim_n": float(swim[0]) if swim else 0.0,
                "swim_period": par.swim_period(swim) if swim else 1.0,
                "bob": 1.0 if it.get("bob") else 0.0,
                "sway": -1.0 if sway is None else (par.SWAY_DEFAULT if not sway else float(sway)),
                "base": float(it.get("base", 0.0)),
                "phase": par.phase(it),
                "sway_phase": par.sway_phase(it),
            })
        layers.append({"parallax_x": layer["parallax"][0], "parallax_y": layer["parallax"][1], "over": 1.0 if layer.get("over") else 0.0,
                       "r": r, "g": g, "b": b, "a": a, "first": first, "count": len(items) - first})
    return {"atlas_w": atlas.width, "atlas_h": atlas.height, "palette": palette, "runs": rle(idx), "layers": layers, "items": items,
            "level_height": height, "atlas": atlas}


def _floats(values, per_line=8):
    lines = []
    for i in range(0, len(values), per_line):
        lines.append("        " + ", ".join(_f(v) for v in values[i:i + per_line]) + ",")
    return "\n".join(lines)


def _f(v):
    s = repr(round(float(v), 5))
    if "e" in s or "E" in s:
        s = "%.5f" % v
    if "." not in s:
        s += ".0"
    return s + "f"


def _ints(values, per_line=16):
    return "\n".join("        " + ", ".join(str(v) for v in values[i:i + per_line]) + "," for i in range(0, len(values), per_line))


def to_csharp(data, source="level.lvl"):
    flat_layers = [l[k] for l in data["layers"] for k in LAYER_FIELDS]
    flat_items = [it[k] for it in data["items"] for k in ITEM_FIELDS]
    palette = [c for rgba in data["palette"] for c in rgba]
    return f"""// GENERATED by `levelang export-scenery {source}`: do not edit (edit the .lvl and run it again).
// The parallax layers and the smooth skin of the level, baked: one atlas (palette + run-length runs) and the layers' items. Scenery.cs decodes and draws it.
static class SceneryData
{{
    public const int AtlasW = {data["atlas_w"]};
    public const int AtlasH = {data["atlas_h"]};
    public const int LevelHeight = {data["level_height"]};
    public const int LayerCount = {len(data["layers"])};
    public const int LayerStride = {len(LAYER_FIELDS)};        // {", ".join(LAYER_FIELDS)}
    public const int ItemCount = {len(data["items"])};
    public const int ItemStride = {len(ITEM_FIELDS)};          // {", ".join(ITEM_FIELDS)}
    public const int RunCount = {len(data["runs"])};

    // r, g, b, a of each of the {PALETTE_COLOURS} colours (0 is air)
    public static int[] Palette = {{
{_ints(palette)}
    }};

    // the atlas, row by row: count * {PALETTE_COLOURS} + palette index
    public static int[] Runs = {{
{_ints(data["runs"])}
    }};

    // layers from the farthest to the nearest
    public static float[] Layers = {{
{_floats(flat_layers, len(LAYER_FIELDS))}
    }};

    public static float[] Items = {{
{_floats(flat_items, len(ITEM_FIELDS))}
    }};
}}
"""
