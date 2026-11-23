"""Level IR -> ONE .html file: the scene() timelines played in the browser (no server, no files next to it).

Everything is inline: the tiles' pictures as SVG (emoji as text, fills and patterns as shapes), the stage of each scene as SVG groups,
the timelines as JSON, the player as CSS + JavaScript, an optional sound track as a base64 data URI. The JavaScript drives

  * the camera: the same keys, eases, punches, shakes and clamping as the GIF preview (`scene.py`), moving the SVG groups of the world and of
    the parallax layers (a layer follows `parallax` of the camera),
  * the actors: moves, hops, poses, mirroring, emotes, and the animated tiles (kmj frames, bob, sway, swim),
  * the dialog: `line(t, "...", who="Gelly")` is a speech bubble above that actor (a caption bar when nobody has that name), `card()` a title
    card, typed out; `fade()` and `fx()` over the picture,
  * the scenes: several .lvl files in one page; a scene ends into the next one (`scene(..., next="name")` says which) through a fade, and
    the viewer can jump with the buttons or the keys.

Not exported: the bot and the level's physics (a scene has no bot), and three post effects that need pixels (`posterize`, `kaleido`, `pixel`).
"""
from __future__ import annotations

import base64
import colorsys
import json
import mimetypes
import os
import re
import zlib
from html import escape

from ..render.gif import ANIM_PERIOD, SWAY_AMP, _phase, _swim, _swim_period
from ..render.skin import path_data, skin_loops
from ..runtime import Level

HERE = os.path.dirname(__file__)
UNSUPPORTED_FX = ("posterize", "kaleido", "pixel")
EMOJI_FONTS = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji","Twemoji Mozilla",sans-serif'


def _num(v) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _attr(s) -> str:
    return escape(str(s), quote=True)


# ---------------------------------------------------------------------------------------------------------------------------------------
# tiles
# ---------------------------------------------------------------------------------------------------------------------------------------

def _prefix_ids(svg: str, pfx: str) -> str:
    """Ids of an SVG inlined in a page must not clash with other pictures': prefix them (and their references)."""
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for i in ids:
        svg = svg.replace(f'id="{i}"', f'id="{pfx}{i}"').replace(f"url(#{i})", f"url(#{pfx}{i})")
        svg = svg.replace(f'href="#{i}"', f'href="#{pfx}{i}"')
    return svg


def _inline_svg(svg: str, ident: str) -> str:
    """The SVG text of a tile as a nested <svg id=ident> that a <use> can place at any size."""
    svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", "", svg.strip(), flags=re.S)
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise ValueError("not an SVG")
    head = m.group(0)
    body = _prefix_ids(svg[m.end():], ident + "_")
    head = re.sub(r'\s(?:id|width|height|x|y)="[^"]*"', "", head)
    if "xmlns=" not in head:
        head = head.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if "viewBox" not in head:
        head = head.replace("<svg", '<svg viewBox="0 0 100 100"', 1)
    return head.replace("<svg", f'<svg id="{ident}"', 1) + body


class Tiles:
    """The pictures of every tile of every scene, shared: `defs()` is the <defs> text, `place()` the markup of one placement."""

    def __init__(self, max_frames: int, warn):
        self.index: dict = {}
        self.max_frames, self.warn = max_frames, warn
        self.info: dict = {}            # idx -> {"frames": [ids], "fps": n} for animated tiles (what the player needs)
        self._defs: list = []

    def of(self, tile) -> int:
        k = id(tile)
        if k in self.index:
            return self.index[k]
        idx = self.index[k] = len(self.index)
        n = len(tile.frames) if tile.frames and len(tile.frames) > 1 else 0
        fps = tile.fps
        if n:
            seq = list(range(n))
            if n > self.max_frames:
                self.warn(f"levelang: tile {tile.glyph or tile.name}: {n} frames, keeping {self.max_frames} (--max-frames)")
                seq = [int(i * n / self.max_frames) for i in range(self.max_frames)]
                fps = fps * self.max_frames / n
            frames = [tile.frames[i] for i in seq]
        else:
            frames = [tile.svg] if tile.svg else []
        ids = []
        cache: dict = {}
        for n, f in enumerate(frames):
            if f in cache:
                ids.append(cache[f])
                continue
            ident = f"t{idx}" if len(frames) == 1 else f"t{idx}f{len(cache)}"
            try:
                self._defs.append(_inline_svg(f, ident))
                cache[f] = ident
                ids.append(ident)
            except Exception as e:
                self.warn(f"levelang: tile {tile.glyph or tile.name}: its SVG could not be inlined ({e})")
                ids.append(None)
        self.info[idx] = {"frames": ids, "fps": fps if len(ids) > 1 else 0}
        return idx

    def defs(self) -> str:
        return "\n".join(self._defs)

    def frame_ids(self, tile) -> list:
        return [i for i in self.info[self.of(tile)]["frames"] if i]

    def place(self, tile, x, y, w, h, flip=False, wx=0, wy=0, ident=None) -> str:
        """The markup of one tile drawn in the box (x, y, w, h) (cells), mirrored if `flip`. `ident` ids the <use> of an animated tile."""
        idx = self.of(tile)
        out = []
        if tile.fill is not None:
            out.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}" fill="{_attr(tile.fill)}"/>')
        pat = tile.pattern
        if pat:
            ph, pw = len(pat), max(len(r) for r in pat)
            ch = pat[wy % ph].ljust(pw)[wx % pw]
            if ch.strip():
                out.append(f'<text x="{_num(x + w / 2)}" y="{_num(y + h / 2)}" font-size="{_num(h * 0.85)}" text-anchor="middle" dominant-baseline="central" '
                           f'font-family="DejaVu Sans Mono,Menlo,Consolas,monospace" fill="{_attr(tile.stroke or "#ffffff")}">{escape(ch)}</text>')
        ids = self.frame_ids(tile)
        if ids:
            idat = f' id="{ident}"' if ident else ""
            out.append(f'<use{idat} href="#{ids[0]}" x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}"/>')
        if not out:
            if tile.glyph:
                out.append(f'<text x="{_num(x + w / 2)}" y="{_num(y + h / 2)}" font-size="{_num(min(w, h) * 0.86)}" text-anchor="middle" dominant-baseline="central" '
                           f'font-family=\'{EMOJI_FONTS}\'>{escape(tile.glyph)}</text>')
            else:
                hue = (zlib.crc32((tile.glyph or tile.name).encode()) % 360) / 360
                r, g, b = (int(255 * v) for v in colorsys.hsv_to_rgb(hue, 0.45, 0.85))
                m = w * 0.1
                out.append(f'<rect x="{_num(x + m)}" y="{_num(y + m)}" width="{_num(w - 2 * m)}" height="{_num(h - 2 * m)}" rx="{_num(w * 0.2)}" '
                           f'fill="rgb({r},{g},{b})" stroke="rgb({r // 2},{g // 2},{b // 2})" stroke-width="{_num(w * 0.04)}"/>')
        inner = "".join(out)
        if flip:
            return f'<g transform="matrix(-1 0 0 1 {_num(2 * x + w)} 0)">{inner}</g>'
        return inner


# ---------------------------------------------------------------------------------------------------------------------------------------
# a scene
# ---------------------------------------------------------------------------------------------------------------------------------------

def _is_dyn(tile) -> bool:
    return tile.animated


def _dyn(tiles: Tiles, p, x0, y0, n) -> tuple:
    """(markup, data) of an animated placement: a <g> the player moves, with the <use> whose picture it swaps."""
    t = p.tile
    w, h = p.size or t.size
    idx = tiles.of(t)
    info = tiles.info[idx]
    d = {"id": f"d{n}", "tile": idx, "x": p.x - x0, "y": p.y - y0, "w": w, "h": h, "flip": bool(p.flip), "phase": _phase(p),
         "frames": info["frames"] if len(info["frames"]) > 1 else None, "fps": info["fps"]}
    for k in ("bob", "sway"):
        if k in t.anim:
            d[k] = t.anim[k] if (k == "sway" and t.anim[k]) else True
    if "swim" in t.anim:
        cells, speed = _swim(t.anim["swim"])
        d["swim"] = [cells, speed, _swim_period(t.anim["swim"])]
    inner = tiles.place(t, 0, 0, w, h, False, p.x, p.y, ident=f"d{n}u")
    return f'<g class="dyn" id="d{n}">{inner}</g>', d


def _scene(level: Level, tiles: Tiles, sid: int, warn) -> dict:
    sc = level.scene
    x0, y0, x1, y1 = level.bounds()
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    vcols, vrows = min(sc.view[0], cols), min(sc.view[1], rows)
    top, bottom = level.background or ("#20222c", "#20222c")
    dyns: list = []
    defs: list = []
    counter = [0]

    def item(p, plain_out):
        if _is_dyn(p.tile):
            counter[0] += 1
            markup, data = _dyn(tiles, p, x0, y0, f"{sid}_{counter[0]}")
            dyns.append(data)
            return markup
        w, h = p.size or p.tile.size
        return tiles.place(p.tile, p.x - x0, p.y - y0, w, h, p.flip, p.x, p.y)

    # ---- the world: backdrop, blocky tiles, the skin, the dynamic things on top
    dynamic = [p for p in sorted(level.placements, key=lambda p: (p.tile.layer, p.order)) if _is_dyn(p.tile)]
    static = [p for p in sorted(level.placements, key=lambda p: (p.tile.layer, p.order)) if not _is_dyn(p.tile)]
    skinned = {id(sk): [] for sk in level.skins}
    plain = []
    for p in static:
        sk = next((k for k in level.skins if k.hide and k.covers(p.tile)), None)
        (skinned[id(sk)] if sk is not None else plain).append(p)
    back = f'<rect x="0" y="0" width="{cols}" height="{rows}" fill="url(#bg{sid})"/>'
    world = []
    defs.append(f'<linearGradient id="bg{sid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{_attr(top)}"/><stop offset="1" stop-color="{_attr(bottom)}"/></linearGradient>')
    world += [item(p, True) for p in plain if p.tile.layer < 0]
    for k, sk in enumerate(level.skins):
        placed = skinned[id(sk)]
        if not placed:
            continue
        cells = {}
        for p in placed:
            cells[(p.x - x0, p.y - y0)] = p
        pics = [tiles.place(p.tile, cx, cy, 1, 1, False, p.x, p.y) for (cx, cy), p in cells.items()]
        near = [(0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]
        for cy in range(rows):                      # the outline strays a little outside the cells: carry the neighbours' pictures one cell out
            for cx in range(cols):
                if (cx, cy) in cells:
                    continue
                q = next((cells[(cx + dx, cy + dy)] for dx, dy in near if (cx + dx, cy + dy) in cells), None)
                if q is not None:
                    pics.append(tiles.place(q.tile, cx, cy, 1, 1, False, q.x, q.y))
        loops = skin_loops(set(cells), cols, rows, sk.corner, sk.smooth, sk.wobble, sk.seed)
        d = path_data(loops)
        defs.append(f'<clipPath id="sk{sid}_{k}"><path clip-rule="evenodd" d="{d}"/></clipPath>')
        world.append(f'<g clip-path="url(#sk{sid}_{k})">{"".join(pics)}</g>')
        if sk.outline:
            world.append(f'<path d="{d}" fill="none" stroke="{_attr(sk.outline)}" stroke-width="{_num(sk.outline_width)}" stroke-linejoin="round"/>')
    world += [item(p, True) for p in plain if p.tile.layer >= 0]
    world += [item(p, True) for p in dynamic]

    # ---- the parallax layers: far ones behind the world, `over` ones in front
    far, near_l = [], []
    hazes: dict = {}
    for lay in sorted(level.layers, key=lambda l: l.parallax):
        if sc.rain and lay.name.startswith("rain"):
            continue                                    # the page draws the rain itself
        body = "".join(item(p, False) for p in lay.placements)
        style = ""
        if lay.haze:
            bx0 = min(q.x - x0 for q in lay.placements) - 1 if lay.placements else 0
            by0 = min(q.y - y0 for q in lay.placements) - 1 if lay.placements else 0
            bx1 = max(q.x - x0 + (q.size or q.tile.size)[0] for q in lay.placements) + 1 if lay.placements else 1
            by1 = max(q.y - y0 + (q.size or q.tile.size)[1] for q in lay.placements) + 1 if lay.placements else 1
            key = (lay.haze[0], float(lay.haze[1]), round(bx0), round(by0), round(bx1), round(by1))
            if key not in hazes:
                hazes[key] = f"hz{sid}_{len(hazes)}"
            style += f' filter="url(#{hazes[key]})"'
        if lay.alpha < 1.0:
            style += f' opacity="{_num(lay.alpha)}"'
        g = f'<g class="lay" data-px="{_num(lay.parallax)}" data-py="{_num(lay.parallax_y)}"{style}>{body}</g>'
        (near_l if lay.over else far).append(g)
    for (colour, amount, bx0, by0, bx1, by1), ident in hazes.items():
        r, g, b = _rgb(colour)
        a = amount
        defs.append(f'<filter id="{ident}" filterUnits="userSpaceOnUse" x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" color-interpolation-filters="sRGB">'
                    f'<feColorMatrix type="matrix" values="{1 - a:.4f} 0 0 0 {r * a:.4f}  0 {1 - a:.4f} 0 0 {g * a:.4f}  0 0 {1 - a:.4f} 0 {b * a:.4f}  0 0 0 1 0"/></filter>')

    # ---- the cast
    actors, actor_markup = [], []
    for n, (name, a) in enumerate(sc.actors.items()):
        poses = {}
        pmarkup = []
        for pname, tile in a.poses.items():
            w, h = a.width_height(tile)
            idx = tiles.of(tile)
            info = tiles.info[idx]
            poses[pname] = {"w": w, "h": h, "frames": info["frames"] if len(info["frames"]) > 1 else None, "fps": info["fps"]}
            pmarkup.append(f'<g class="pose" data-pose="{_attr(pname)}" style="display:none">{tiles.place(tile, 0, 0, w, h, False, 0, 0, ident=f"a{sid}_{n}_{len(pmarkup)}")}</g>')
            poses[pname]["use"] = f"a{sid}_{n}_{len(pmarkup) - 1}"
        emotes = []
        for k, (t, tile, secs) in enumerate(a.emotes):
            w, h = tile.size
            info = tiles.info[tiles.of(tile)]
            ident = f"e{sid}_{n}_{k}"
            emotes.append({"t": t, "sec": secs, "w": w, "h": h, "id": ident, "frames": info["frames"] if len(info["frames"]) > 1 else None, "fps": info["fps"]})
            actor_markup.append(f'<g class="emote" id="{ident}g" style="display:none">{tiles.place(tile, 0, 0, w, h, False, 0, 0, ident=ident)}</g>')
        actor_markup.append(f'<g class="actor" id="a{sid}_{n}" style="display:none">{"".join(pmarkup)}</g>')
        flips = sorted([[m.t0, m.x1 < m.x0] for m in a.moves if m.ease != "cut" and abs(m.x1 - m.x0) > 0.01] + [list(f) for f in a.faces])
        actors.append({"name": name, "id": f"a{sid}_{n}", "x": a.x - x0, "y": a.y - y0, "flip": a.flip, "poses": poses, "idle": "idle" if "idle" in a.poses else next(iter(a.poses)),
                       "moves": [[m.t0, m.t1, m.x0 - x0, m.y0 - y0, m.x1 - x0, m.y1 - y0, m.ease, m.hop] for m in a.moves],
                       "cues": [list(c) for c in a.pose_cues], "vis": [list(v) for v in a.vis], "flips": flips, "emotes": emotes})
    fx = [list(f) for f in sc.fxs]
    for f in sc.fxs:
        if f[2] in UNSUPPORTED_FX:
            warn(f"levelang: scene {sc.name}: the effect {f[2]!r} needs pixels and is skipped in HTML")
    ch = getattr(sc, "chaos", None)
    chaos = None
    if ch:
        pit = ch["pit"]
        chaos = {"shots": [[s[0] - x0, s[1] - y0, s[2]] for s in ch["shots"]], "floor": None if ch["floor"] is None else ch["floor"] - y0,
                 "singer": ch["singer"] and [ch["singer"][0] - x0, ch["singer"][1] - y0], "pit": pit and [pit[0] - x0, pit[1] - x0, pit[2] - y0],
                 "crowd": [tiles.of(t) for t in ch["crowd"]], "band": {k: tiles.of(t) for k, t in ch["band"].items()},
                 "lights": [[p[0] - x0, p[1] - y0] for p in ch["lights"]], "rate": ch["rate"], "grain": ch["grain"]}
    data = {
        "chaos": chaos, "rain": sc.rain, "name": sc.name, "seconds": sc.seconds, "fps": sc.fps, "bpm": sc.bpm, "view": [vcols, vrows], "world": [cols, rows], "next": getattr(sc, "next", None),
        "cams": [[c[0], c[1] - x0, c[2] - y0, c[3], c[4]] for c in sc.cams], "punches": [list(p) for p in sc.punches], "shakes": [list(k) for k in sc.shakes],
        "fades": sorted([list(f) for f in sc.fades]), "fx": fx, "captions": sc.captions, "actors": actors, "dyn": dyns,
    }
    markup = (f'<defs>{"".join(defs)}</defs><g class="back">{back}</g><g class="far">{"".join(far)}</g><g class="world">{"".join(world)}<g class="cast">{"".join(actor_markup)}</g></g>'
              f'<g class="nearl">{"".join(near_l)}</g>')
    return {"data": data, "markup": markup}


def _rgb(c) -> tuple:
    from ..render.sprites import color
    r, g, b = color(c)[:3]
    return r / 255.0, g / 255.0, b / 255.0


# ---------------------------------------------------------------------------------------------------------------------------------------
# the page
# ---------------------------------------------------------------------------------------------------------------------------------------

def _read(name: str) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def _data_uri(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "audio/mpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def to_html(levels: list, *, title: str = "levelang", audio: dict | None = None, loop: bool = False, max_frames: int = 240, warn=print) -> str:
    """One self-contained HTML page that plays the scene() of each level in order. `audio`: {scene name: path of a sound file}."""
    if not levels:
        raise ValueError("export-html needs at least one level")
    audio = dict(audio or {})
    tiles = Tiles(max_frames, warn)
    scenes, names = [], set()
    for lv in levels:
        sc = lv.scene
        if sc is None:
            raise ValueError("a level has no scene(): start one with scene(\"intro\", seconds=24)")
        if not lv.placements:
            raise ValueError(f"scene {sc.name!r}: the stage is empty: place some tiles for the scene to happen on")
        if sc.name in names:
            raise ValueError(f"two scenes are called {sc.name!r}: give each .lvl its own scene(\"name\")")
        names.add(sc.name)
        scenes.append(_scene(lv, tiles, len(scenes), warn))
    for s in scenes:
        nx = s["data"]["next"]
        if nx is not None and nx not in names:
            raise ValueError(f"scene {s['data']['name']!r}: next={nx!r} is not a scene of this page (the scenes are {', '.join(sorted(names))})")
    unknown = [n for n in audio if n not in names]
    if unknown:
        raise ValueError(f"--audio names no scene called {unknown[0]!r} (the scenes are {', '.join(sorted(names))})")
    show = {"title": title, "loop": bool(loop), "scenes": [s["data"] for s in scenes], "tiles": {str(k): v for k, v in tiles.info.items()},
            "audio": {n: i for i, n in enumerate(audio)}, "font": EMOJI_FONTS}
    j = json.dumps(show, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = "".join(f'<template id="scene{i}"><svg xmlns="http://www.w3.org/2000/svg">{s["markup"]}</svg></template>\n' for i, s in enumerate(scenes))
    aud = "".join(f'<audio id="audio{i}" preload="auto" src="{_data_uri(p)}"></audio>\n' for i, p in enumerate(audio.values()))
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{escape(title)}</title>\n'
            f'<style>\n{_read("html_player.css")}</style></head>\n<body>\n'
            '<div id="stage"><svg id="view" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice"><defs id="tiledefs">'
            + tiles.defs() +
            '</defs><g id="scenebox"><g id="back"></g><g id="far"></g><g id="cam"></g><g id="near"></g></g></svg>\n'
            '<div id="rain"><div class="far"></div><div class="near"></div></div><div id="fxlayer"></div><div id="chaoslights"></div><div id="bubbles"></div><div id="cards"></div><div id="fade"></div></div>\n'
            '<div id="bar"><button id="play" title="play / pause (space)">⏸</button><span id="scenes"></span><span id="clock"></span>'
            '<button id="sound" title="load a sound file (or drop one on the page)">♪</button><input id="soundin" type="file" accept="audio/*" hidden><button id="mute" title="sound (m)" hidden>🔊</button><button id="full" title="fullscreen (f)">⛶</button></div>\n'
            '<div id="start" hidden><button>▶ play</button></div>\n'
            + tpl + aud +
            f'<script id="show" type="application/json">{j}</script>\n<script>\n{_read("html_chaos.js")}</script>\n<script>\n{_read("html_player.js")}</script>\n</body></html>\n')
