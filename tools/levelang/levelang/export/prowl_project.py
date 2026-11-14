"""Level -> a Prowl2D editor project (``prowl.py project.json``): the level's grid for the editor's physics, its parallax layers and smooth skin as true-colour images.

What goes where:

* Tiles with a gameplay meaning (solid, hazard, item, climb, spawn, goal ... or an enemy) stay in the **grid**, one tile per cell (the strongest wins), drawn as small pixel-art
  sprites (the tile's picture at ``tile_px`` pixels, folded into one shared palette of 255 colours).
* Everything that is only a picture (the ``bg`` and ``fg`` decoration, anything animated with sway, bob or swim) and every parallax layer becomes a **layer** of images, at the positions and
  sizes it has in the level: the world's own decoration on layers with parallax 1, behind the grid or in front of it. An image is the tile's SVG rasterized at ``ppc`` pixels per cell.
* A **skin** becomes one image of the whole smooth terrain (rasterized at ``ppc``), on a layer of its own, and the tiles it covers become ``hidden`` in the grid: they still collide, and
  the image is what is drawn.

The editor draws layers as linear-filtered textured triangles (prowl_editor/parallax.py), so smooth shapes stay smooth. Its renderer has 63 textures in all, shared with the grid's sprites:
the exporter says so when a level needs more.
"""
from __future__ import annotations

import base64
import io
import re

from PIL import Image, ImageColor

from ..emoji import VS15, VS16
from ..render.gif import _skin_image, _swim
from ..render.sprites import Sprites

GAMEPLAY = ("solid", "hazard", "item", "spawn", "goal", "climb", "save", "anchor", "crumbly")
PRIORITY = ("solid", "crumbly", "hazard", "goal", "spawn", "save", "anchor", "item", "climb")   # which tile a cell shows, when more than one stands in it
PARAMS = ("enemy", "shooter")
SWAY_DEFAULT = 0.10
MAX_TEXTURES = 63
KEYS = [chr(c) for c in range(0x21, 0x7F) if chr(c) != "."] + [chr(c) for c in range(0xC0, 0x180)]   # a palette key is one visible character: 93 of ASCII, then Latin letters


class ProjectExportError(ValueError):
    pass


def is_gameplay(tile) -> bool:
    return any(f in tile.flags for f in GAMEPLAY) or any(k in tile.params for k in PARAMS)


def rank(tile) -> int:
    for i, f in enumerate(PRIORITY):
        if f in tile.flags:
            return i
    return len(PRIORITY)


def slug(tile) -> str:
    s = re.sub(r"^tile_", "", tile.name).lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "tile"


def hex_color(c) -> str:
    r, g, b = ImageColor.getrgb(c)[:3]
    return "#%02x%02x%02x" % (r, g, b)


def png_bytes(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def quantize_sprites(images: dict) -> tuple[list, dict]:
    """Folds the tile pictures into one palette of at most 255 colours (index 0 is transparent: pixels under half opaque). Returns (palette json, {name: rows of keys})."""
    if not images:
        return [{"key": ".", "name": "transparent", "color": None}], {}
    mosaic_w = sum(im.width for im in images.values())
    mosaic = Image.new("RGB", (mosaic_w, max(im.height for im in images.values())), (0, 0, 0))
    x = 0
    for im in images.values():
        rgb = Image.new("RGB", im.size, (0, 0, 0))
        rgb.paste(im.convert("RGB"), mask=im.getchannel("A").point(lambda v: 255 if v >= 128 else 0))
        mosaic.paste(rgb, (x, 0))
        x += im.width
    pal_img = mosaic.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = pal_img.getpalette()[: 255 * 3]
    used = len(flat) // 3
    palette = [{"key": ".", "name": "transparent", "color": None}]
    for i in range(used):
        palette.append({"key": KEYS[i], "name": "c%d" % (i + 1), "color": "#%02x%02x%02x" % tuple(flat[i * 3:i * 3 + 3])})
    rows = {}
    for name, im in images.items():
        idx = im.convert("RGB").quantize(palette=pal_img, dither=Image.Dither.NONE)
        alpha = im.getchannel("A")
        out = []
        for y in range(im.height):
            out.append("".join("." if alpha.getpixel((x, y)) < 128 else KEYS[min(idx.getpixel((x, y)), used - 1)] for x in range(im.width)))
        rows[name] = out
    return palette, rows


def to_project(level, name: str = "levelang", ppc: int = 32, tile_px: int = 16, warn=print) -> dict:
    """The editor project (a JSON-able dict) for a Level. ``ppc`` is the pixels per cell of the layer images, ``tile_px`` of the grid's sprites."""
    if not level.placements:
        raise ProjectExportError("the level is empty: nothing to export")
    x0, y0, x1, y1 = level.bounds()
    if level.meta.get("width") and level.meta.get("height"):
        x1, y1 = x0 + int(level.meta["width"]) - 1, y0 + int(level.meta["height"]) - 1
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    ppc = max(4, min(ppc, 4096 // max(cols, rows)))   # a skin image of the whole level must fit the renderer's 8192 pixels, and 4096 is plenty

    skin_of = lambda t: next((k for k in level.skins if k.hide and k.covers(t)), None)
    ordered = sorted(level.placements, key=lambda p: (p.tile.layer, p.order))

    # ---- the grid: one gameplay tile a cell; the rest are pictures
    grid: dict = {}
    decor_back, decor_front = [], []
    for p in ordered:
        t = p.tile
        if is_gameplay(t) and not t.anim.keys() - {"bob"}:      # (a gem bobs: it is still a gem; a fish that swims is scenery whatever flags it has)
            cur = grid.get((p.x, p.y))
            if cur is None or rank(t) < rank(cur.tile):
                if cur is not None:
                    warn(f"levelang: export: cell ({p.x}, {p.y}) holds two gameplay tiles; the editor's grid keeps one")
                grid[(p.x, p.y)] = p
            elif cur is not None and cur.tile is not t:
                warn(f"levelang: export: cell ({p.x}, {p.y}) holds two gameplay tiles; the editor's grid keeps one")
        elif not (skin_of(t) and not t.anim):
            (decor_front if t.layer > 0 else decor_back).append(p)

    # ---- tile pictures: the grid's sprites and the layers' images
    tiles_in_grid = {}
    for p in grid.values():
        tiles_in_grid.setdefault(p.tile.name, p.tile)
    sprite_imgs = {slug(t): Sprites(tile_px).get(t, 0, 0) for t in tiles_in_grid.values()}
    palette, sprite_rows = quantize_sprites(sprite_imgs)

    def below(p, group) -> int:
        """Swaying plants standing on this one (the editor leans a column of them as one)."""
        n = 0
        while n < 8 and any("sway" in q.tile.anim for q in group.get((p.x, p.y + 1 + n), [])):
            n += 1
        return n

    def item_json(p, below_n=0, dx=0, dy=0) -> dict:
        t = p.tile
        w, h = p.size or t.size
        d = {"image": slug(t), "x": round(p.x - x0 + dx, 4), "y": round(p.y - y0 + dy, 4), "w": float(w), "h": float(h), "flip": bool(p.flip)}
        if "sway" in t.anim:
            d["sway"] = float(t.anim["sway"] or SWAY_DEFAULT)
            if below_n:
                d["base"] = float(below_n)
        if "bob" in t.anim:
            d["bob"] = True
        if "swim" in t.anim:
            n, speed = _swim(t.anim["swim"])
            d["swim"] = [float(n), float(speed)]
        return d

    used_images: dict = {}      # image name -> (tile, widest and tallest in cells it is drawn at)

    def note(p):
        t = p.tile
        w, h = p.size or t.size
        old = used_images.get(slug(t))
        used_images[slug(t)] = (t, max(w, old[1] if old else 0), max(h, old[2] if old else 0))

    layers = []
    if level.background:      # the water: a gradient that stays put across, and runs down the level (the editor's own background is flat)
        top, bottom = level.background
        grad = Image.new("RGB", (2, 256))
        ramp = Image.linear_gradient("L").resize((2, 256))
        grad = Image.composite(Image.new("RGB", (2, 256), ImageColor.getrgb(bottom)), Image.new("RGB", (2, 256), ImageColor.getrgb(top)), ramp)
        images_extra = {"water": png_bytes(grad)}
        margin = 40.0
        layers.append({"name": "water", "parallax": [0.0, 1.0], "over": False, "alpha": 1.0, "haze": None,
                       "items": [{"image": "water", "x": -margin, "y": 0.0, "w": cols + 2 * margin, "h": float(rows), "flip": False, "sway": None, "bob": False, "swim": None}]})
    else:
        images_extra = {}
    for lay in sorted(level.layers, key=lambda l: l.parallax):
        items = []
        for p in lay.placements:
            note(p)
            items.append(item_json(p, dx=0, dy=0))
        layers.append({"name": lay.name, "parallax": [lay.parallax, lay.parallax_y], "over": lay.over, "alpha": lay.alpha,
                       "haze": [hex_color(lay.haze[0]), float(lay.haze[1])] if lay.haze else None, "items": items})
    for label, group, over in (("decor", decor_back, False), ("decor in front", decor_front, True)):
        if group:
            cells: dict = {}
            for q in group:
                cells.setdefault((q.x, q.y), []).append(q)
            items = []
            for p in group:
                note(p)
                items.append(item_json(p, below(p, cells) if "sway" in p.tile.anim else 0))
            layers.append({"name": label, "parallax": [1.0, 1.0], "over": over, "alpha": 1.0, "haze": None, "items": items})

    images = [{"name": n, "png": base64.b64encode(b).decode("ascii")} for n, b in images_extra.items()]
    for iname, (t, w, h) in used_images.items():
        side = max(w, h) * ppc
        px = ppc if side <= 1024 else ppc * 1024 / side           # one picture at most 1024 pixels a side, the most it needs for the biggest it is drawn
        images.append({"name": iname, "png": base64.b64encode(png_bytes(Sprites(max(1, round(px))).get(t, 0, 0, (w, h)))).decode("ascii")})

    # ---- the skin(s): one image each, over the world's decoration and under the grid
    hidden = set()
    skin_layers = []
    for k, sk in enumerate(level.skins):
        placed = [p for p in ordered if not p.tile.anim and not p.tile.has("item") and sk.hide and sk.covers(p.tile) and skin_of(p.tile) is sk]
        if not placed:
            continue
        hidden.update(p.tile.name for p in placed)
        sprites = Sprites(ppc)
        img = _skin_image(level, sk, placed, sprites, ppc, x0, y0, cols, rows)
        iname = "skin" if len(level.skins) == 1 else f"skin_{k + 1}"
        images.append({"name": iname, "png": base64.b64encode(png_bytes(img)).decode("ascii")})
        skin_layers.append({"name": iname, "parallax": [1.0, 1.0], "over": False, "alpha": 1.0, "haze": None,
                            "items": [{"image": iname, "x": 0.0, "y": 0.0, "w": float(cols), "h": float(rows), "flip": False, "sway": None, "bob": False, "swim": None}]})
        for p in placed:       # the tiles it covers are in the grid, to collide, and hidden
            grid.setdefault((p.x, p.y), p)
    layers += skin_layers
    for p in list(grid.values()):
        if p.tile.name in hidden and p.tile.name not in tiles_in_grid:
            tiles_in_grid[p.tile.name] = p.tile

    # ---- the grid as a level
    glyphs = {t.glyph for t in tiles_in_grid.values()}
    empty = next((e for e in ("⬛", "⬜", "▫️", "▪️") if e not in glyphs), None)
    if empty is None:
        raise ProjectExportError("every candidate for the empty cell is a tile of this level")
    out_rows = []
    for y in range(y0, y1 + 1):
        out_rows.append("".join(grid[(x, y)].tile.glyph if (x, y) in grid else empty for x in range(x0, x1 + 1)))
    if len(images) + len(tiles_in_grid) > MAX_TEXTURES:
        warn(f"levelang: export: {len(images)} images and {len(tiles_in_grid)} tile sprites need up to {len(images) + len(tiles_in_grid)} textures; the editor's renderer has {MAX_TEXTURES}, "
             "and an item whose texture does not fit is not drawn")

    sprites_json = []
    for t in tiles_in_grid.values():
        if slug(t) in sprite_rows:
            sprites_json.append({"name": slug(t), "width": tile_px, "height": tile_px, "fps": 8, "frames": [sprite_rows[slug(t)]]})
    tiles_json = []
    for t in tiles_in_grid.values():
        d = {"emoji": t.glyph, "name": slug(t), "sprite": slug(t), "solid": t.has("solid") or t.has("crumbly")}
        if t.name in hidden:
            d["hidden"] = True
        tiles_json.append(d)
    return {"format": "prowl2d-project", "version": 3, "name": name, "palette": palette, "sprites": sprites_json, "empty": empty, "tiles": tiles_json,
            "levels": [{"name": name, "rows": out_rows, "layers": layers}], "images": images}
