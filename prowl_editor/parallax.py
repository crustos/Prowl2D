"""parallax.py: what the viewport draws for a level's parallax layers, as textured triangles (no GUI, no engine and no ctypes in here, so it is tested on its own).

`plan(level, cam_left, cam_top, clock)` gives two lists of batches, `(image name, vertices)`: the layers behind the tiles and the layers in front of them, each in the order to draw. A vertex is
what `gfx_triangles` takes: x, y (world units, y up), u, v (v = 0 is the top of the picture), r, g, b, a (the tint). Three vertices a triangle, two triangles a quad.

Positions in a layer are cells from the level's top left corner, y down (the way its rows are written). A layer follows `parallax` of the camera: the camera's left edge is `cam_left` cells
from the level's left edge and its top edge `cam_top` cells below the level's top, so an item at layer x is drawn at x + cam_left * (1 - parallax) in the level: 1 moves with the level, 0 stays
on the screen, 0.2 drifts slowly. Layers are drawn from the least parallax to the most (far to near).

Animation is the same as levelang's preview: `swim` [cells, cells per second] swims there and back (turning over at each end), `bob` rises and falls a fifth of a cell, `sway` leans the picture
more toward its top: the quad is cut into strips whose corners are moved sideways, so a tall kelp bends along its length.

`haze` (a colour and an amount) is done as a tint: a layer's colours are multiplied by the haze colour mixed with white by that amount. That darkens as well as fogs (the preview mixes toward
the colour instead); baking it into a layer's pictures would need a copy of every picture per layer, and the renderer has 63 textures.
"""
import array
import math

ANIM_PERIOD = 2.4          # seconds for one sway or bob (the preview's)
SWAY_DEFAULT = 0.10        # cells of lean per cell above the foot, when an item says only `sway`
BOB_CELLS = 0.22
WHITE = (1.0, 1.0, 1.0)


def _hex(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def tint(layer):
    """(r, g, b, a) the vertices of a layer carry."""
    r, g, b = WHITE
    if layer.get("haze"):
        colour, amount = layer["haze"]
        hr, hg, hb = _hex(colour)
        r, g, b = (1.0 - amount) + amount * hr, (1.0 - amount) + amount * hg, (1.0 - amount) + amount * hb
    return r, g, b, layer.get("alpha", 1.0)


def phase(item):
    """0..1, repeatable, from where the item is, so a row of kelp does not sway in step."""
    return ((int(item["x"] * 4) * 73856093) ^ (int(item["y"] * 4) * 19349663)) % 1000 / 1000.0


def sway_phase(item):
    """The phase of a sway depends on where the item is across, not up and down, so plants standing on each other (`base`) lean in step."""
    return (int(item["x"] * 4) * 73856093) % 1000 / 1000.0


def swim_period(swim):
    n, speed = swim
    return ANIM_PERIOD * max(1, round(2 * n / (speed * ANIM_PERIOD)))


def motion(item, clock):
    """(dx, dy, flipped) in cells for an item at `clock` seconds; dy is down."""
    dx = dy = 0.0
    flipped = bool(item.get("flip"))
    ph = phase(item)
    if item.get("swim"):
        n = item["swim"][0]
        w = (clock / swim_period(item["swim"]) + ph) % 1.0
        dx = (1.0 - abs(2.0 * w - 1.0)) * n
        flipped = flipped != (w > 0.5)
    if item.get("bob"):
        dy = math.sin(2.0 * math.pi * ((clock / ANIM_PERIOD + ph) % 1.0)) * BOB_CELLS
    return dx, dy, flipped


def strips(h):
    """How many strips a swaying item of h cells is cut into."""
    return max(4, min(16, int(math.ceil(h * 2))))


def item_vertices(item, layer_offset, height, clock, rgba, animate=True):
    """The triangles of one item: a quad, or strips when it sways. `layer_offset` is (cells right, cells down) the layer is moved by the camera; `height` is the level's, to turn y down into y up."""
    dx, dy, flipped = motion(item, clock) if animate else (0.0, 0.0, bool(item.get("flip")))
    x = item["x"] + layer_offset[0] + dx
    y = item["y"] + layer_offset[1] + dy
    w, h = item["w"], item["h"]
    sway = item.get("sway") if animate else None
    n = strips(h) if sway is not None else 1
    amp = SWAY_DEFAULT if not sway else sway
    u = (clock / ANIM_PERIOD + sway_phase(item)) % 1.0
    r, g, b, a = rgba
    left_u, right_u = (1.0, 0.0) if flipped else (0.0, 1.0)

    def row(k):
        """The left and right corners of the line k / n of the way down: (x_left, x_right, y up, v)."""
        v = k / float(n)
        lean = 0.0
        if sway is not None:
            above = item.get("base", 0.0) + h * (1.0 - v)             # cells above the foot (of the whole column of plants, if it stands on others)
            lean = amp * above * math.sin(2.0 * math.pi * u - 0.9 * above)
        return x + lean, x + w + lean, height - (y + h * v), v

    out = array.array("f")
    for k in range(n):
        tl, tr, ty, tv = row(k)
        bl, br, by, bv = row(k + 1)
        for px, py, pu, pv in ((tl, ty, left_u, tv), (tr, ty, right_u, tv), (br, by, right_u, bv),
                               (tl, ty, left_u, tv), (br, by, right_u, bv), (bl, by, left_u, bv)):
            out.extend((px, py, pu, pv, r, g, b, a))
    return out


def plan(level, cam_left, cam_top, clock, animate=True):
    """(behind, over): lists of (image name, array('f') of vertices) in drawing order; consecutive items with the same picture share a batch."""
    height = level.height
    behind, over = [], []
    for layer in sorted(level.layers, key=lambda l: l["parallax"][0]):
        px, py = layer["parallax"]
        offset = (cam_left * (1.0 - px), cam_top * (1.0 - py))
        rgba = tint(layer)
        batches = over if layer.get("over") else behind
        for item in layer["items"]:
            verts = item_vertices(item, offset, height, clock, rgba, animate)
            if batches and batches[-1][0] == item["image"]:
                batches[-1][1].extend(verts)
            else:
                batches.append((item["image"], verts))
    return behind, over


def chunks(verts, most=60000):
    """A batch cut into pieces of at most `most` vertices (a multiple of 3: whole triangles), for the renderer's limit on one call."""
    per = 8
    step = (most // 3) * 3 * per
    for i in range(0, len(verts), step):
        yield verts[i:i + step]
