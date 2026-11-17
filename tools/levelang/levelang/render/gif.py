"""Level -> animated GIF with a bot playing it (Pillow only; SVG tiles need cairosvg)."""
from __future__ import annotations

import math
import sys

from PIL import Image, ImageChops

from .. import bot as botmod
from ..runtime import Level, Placed
from .captions import draw_caption
from .skin import skin_loops, skin_mask, skin_outline
from .sprites import Sprites, color, default_bot_sprite

ANIM_PERIOD = 2.4  # seconds for sway/bob cycles
SWAY_STEPS = 24
SWAY_AMP = 0.10  # tiles of sideways travel per tile of height above the base
SWIM_SPEED = 1.3  # tiles / second


def _phase(p) -> float:
    return ((int(p.x * 4) * 73856093) ^ (int(p.y * 4) * 19349663)) % 1000 / 1000.0


def _swim(v) -> tuple:
    """swim -> (cells, cells per second): `swim`, `swim(8)` or `swim(30, 2)` (a whale is long and slow)."""
    if v is None or v is True:
        return 6, SWIM_SPEED
    if isinstance(v, (tuple, list)):
        return v[0], (v[1] if len(v) > 1 else SWIM_SPEED)
    return v, SWIM_SPEED


def _over(dst: Image.Image, spr: Image.Image, x: float, y: float) -> None:
    """dst <- spr over dst at (x, y), clipped to dst (both RGBA)."""
    x, y = round(x), round(y)
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(spr.width, dst.width - x), min(spr.height, dst.height - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0, spr.width, spr.height):
        spr = spr.crop((x0, y0, x1, y1))
    dst.alpha_composite(spr, (x + x0, y + y0))


def layer_offset(layer, left: float, top: float) -> tuple:
    """How far a parallax layer is shifted left and up (in the same units as the camera's left and top edge): it follows `parallax` of the camera."""
    return left * layer.parallax, top * layer.parallax_y


def _veil(img: Image.Image, haze, alpha: float) -> Image.Image:
    """A layer's distance: blend toward the haze colour, fade by alpha."""
    if not haze and alpha >= 1.0:
        return img
    rgb, a = img.convert("RGB"), img.getchannel("A")
    if haze:
        rgb = Image.blend(rgb, Image.new("RGB", img.size, color(haze[0])), float(haze[1]))
    if alpha < 1.0:
        a = a.point(lambda v: int(v * alpha))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def _gradient(size, top, bottom) -> Image.Image:
    w, h = size
    mask = Image.linear_gradient("L").resize((w, h))
    return Image.composite(Image.new("RGB", size, color(bottom)), Image.new("RGB", size, color(top)), mask)


def _sway(img: Image.Image, below: int, step: int, px: int, amp: float = SWAY_AMP, tiles_high: float = 1) -> Image.Image:
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    h = img.height
    for v in range(h):
        s = below + tiles_high * (1 - (v + 0.5) / h)  # tiles above the base of the plant
        dx = round(amp * s * math.sin(2 * math.pi * step / SWAY_STEPS - 0.9 * s) * px)
        out.paste(img.crop((0, v, img.width, v + 1)), (dx, v))
    return out


def _swim_period(v) -> float:
    """Seconds for a fish to swim n tiles and back, rounded to whole sway periods so a GIF can loop."""
    n, speed = _swim(v)
    return ANIM_PERIOD * max(1, round(2 * n / (speed * ANIM_PERIOD)))


def _smooth(pts, k=3):
    if k <= 1 or len(pts) < 3:
        return pts
    r = k // 2
    out = []
    for i in range(len(pts)):
        lo, hi = max(0, i - r), min(len(pts), i + r + 1)
        seg = pts[lo:hi]
        out.append((sum(p[0] for p in seg) / len(seg), sum(p[1] for p in seg) / len(seg)))
    return out


def _skin_image(level: Level, sk, placed, sprites: Sprites, px: int, x0: int, y0: int, cols: int, rows: int) -> Image.Image:
    """The cells a skin covers, drawn with their own tiles and shown through the skin's smooth outline."""
    W, H = cols * px, rows * px
    cells = {}
    for p in placed:  # later placements win the cell
        cells[(p.x - x0, p.y - y0)] = p
    tex = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (cx, cy), p in cells.items():
        _over(tex, sprites.get(p.tile, p.x, p.y), cx * px, cy * px)
    # the outline can lie a little outside the cells (rounded corners of an inside corner, the wobble): carry the neighbours' pictures one cell out
    near = [(0, 1), (0, -1), (-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]
    for cy in range(rows):
        for cx in range(cols):
            if (cx, cy) in cells:
                continue
            for dx, dy in near:
                q = cells.get((cx + dx, cy + dy))
                if q is not None:
                    _over(tex, sprites.get(q.tile, q.x, q.y), cx * px, cy * px)
                    break
    loops = skin_loops(set(cells), cols, rows, sk.corner, sk.smooth, sk.wobble, sk.seed)
    tex.putalpha(ImageChops.multiply(tex.getchannel("A"), skin_mask(loops, (W, H), px)))
    if sk.outline:
        line = Image.new("RGBA", (W, H), color(sk.outline) + (255,))
        line.putalpha(skin_outline(loops, (W, H), px, sk.outline_width))
        tex.alpha_composite(line)
    return tex


def render_gif(
    level: Level,
    out_path: str,
    *,
    tile_px: int = 16,
    max_width: int = 960,
    fps: int = 16,
    speed: float = 8.0,
    view: tuple | None = None,
    play: bool = True,
    hold: tuple = (0.6, 1.6),
    bot_scale: float = 1.6,
    log=print,
) -> dict:
    if not level.placements:
        raise ValueError("the level is empty: nothing to render")
    x0, y0, x1, y1 = level.bounds()
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    px = max(tile_px if view else min(tile_px, max_width // cols), 4)
    sprites = Sprites(px)
    W, H = cols * px, rows * px

    # ---- the world: a static layer (with transparency, so parallax layers show behind it), and what moves ----
    top, bottom = level.background or ("#20222c", "#20222c")
    backdrop = _gradient((W, H), top, bottom)
    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dynamic, items, spawns = [], [], []
    skinned: dict = {id(sk): [] for sk in level.skins}

    plain = []  # static tiles that are drawn as they are, in order

    for p in sorted(level.placements, key=lambda p: (p.tile.layer, p.order)):
        t = p.tile
        if t.has("spawn") and play:  # with a bot, the spawn tile is the bot
            spawns.append(p)
        elif t.has("item"):
            items.append(p)
        elif t.animated:
            dynamic.append(p)
        else:
            sk = next((k for k in level.skins if k.hide and k.covers(t)), None)
            if sk is not None:
                skinned[id(sk)].append(p)
            else:
                plain.append(p)

    def stamp(p) -> None:
        _over(static, sprites.get(p.tile, p.x, p.y, p.size), (p.x - x0) * px, (p.y - y0) * px)

    for p in plain:
        if p.tile.layer < 0:   # the plants behind the terrain
            stamp(p)
    for sk in level.skins:     # then the smooth terrain over them
        if skinned[id(sk)]:
            static.alpha_composite(_skin_image(level, sk, skinned[id(sk)], sprites, px, x0, y0, cols, rows))
    for p in plain:
        if p.tile.layer >= 0:
            stamp(p)

    # ---- parallax layers: a static picture each, and the placements that move ----
    layers = []
    for lay in sorted(level.layers, key=lambda l: l.parallax):  # far to near: the least parallax is drawn first
        stat = [p for p in lay.placements if not p.tile.animated]
        dyn = [p for p in lay.placements if p.tile.animated]
        img = ox = oy = None
        if stat:
            boxes = []
            for p in stat:
                w, h = p.size or p.tile.size
                boxes.append((int(round((p.x - x0) * px)), int(round((p.y - y0) * px)), int(w * px), int(h * px)))
            ox, oy = min(b[0] for b in boxes), min(b[1] for b in boxes)
            ex, ey = max(b[0] + b[2] for b in boxes), max(b[1] + b[3] for b in boxes)
            img = Image.new("RGBA", (max(1, ex - ox), max(1, ey - oy)), (0, 0, 0, 0))
            for p, b in zip(stat, boxes):
                spr = sprites.get(p.tile, p.x, p.y, p.size)
                _over(img, spr.transpose(Image.FLIP_LEFT_RIGHT) if p.flip else spr, b[0] - ox, b[1] - oy)
            img = _veil(img, lay.haze, lay.alpha)
        layers.append({"layer": lay, "img": img, "ox": ox, "oy": oy, "dyn": dyn})

    # ---- bot timeline ----
    plan = botmod.plan(level) if play else botmod.Plan()
    for n in plan.notes:
        log("levelang: bot:", n)
    bot_img = default_bot_sprite(px)
    if spawns and (spawns[0].tile.svg or spawns[0].tile.pattern or spawns[0].tile.fill):
        bot_img = sprites.get(spawns[0].tile, 0, 0)
    bs = max(int(px * bot_scale), 1)
    bot_img = bot_img.resize((bs, bs), Image.LANCZOS)
    bot_tile = spawns[0].tile if spawns and spawns[0].tile.frames and len(spawns[0].tile.frames) > 1 else None
    bot_cache: dict = {}

    def bot_at(t):
        """The bot's picture at time t: a kmj spawn tile with frames animates."""
        if bot_tile is None:
            return bot_img
        spr = sprites.get(bot_tile, 0, 0, None, t)
        if id(spr) not in bot_cache:
            bot_cache[id(spr)] = spr.resize((bs, bs), Image.LANCZOS)
        return bot_cache[id(spr)]
    bot_off = (bs - px) / 2  # sprite is bigger than a tile, centred on its cell
    pts = plan.points
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    travel = cum[-1] / speed if len(pts) > 1 else 0.0
    h0, h1 = hold
    # the story: the bot stops where a caption starts and stays for its `seconds`, so every line is read
    stops = []  # (path distance where it starts, caption)
    if play and pts and level.captions:
        for cap in sorted(level.captions, key=lambda c: c["x"]):
            j = next((n for n, (cx_, _) in enumerate(pts) if cx_ + 0.5 >= cap["x"]), None)
            if j is not None:
                stops.append((cum[j], cap))
    pauses = []  # (path distance, start time, duration): filled in below
    t_cursor, s_cursor = h0, 0.0
    for s_at, cap in stops:
        t_cursor += max(0.0, s_at - s_cursor) / speed
        s_cursor = max(s_cursor, s_at)
        pauses.append((s_cursor, t_cursor, cap["seconds"], cap))
        t_cursor += cap["seconds"]
    story_time = sum(d for _, _, d, _ in pauses)
    if play:
        total = h0 + travel + story_time + h1
    else:  # no bot: one seamless loop of the scenery
        swims = [p.tile.anim["swim"] for p in dynamic if "swim" in p.tile.anim]
        swims += [p.tile.anim["swim"] for L in layers for p in L["dyn"] if "swim" in p.tile.anim]
        total = max([4.8] + [_swim_period(v) for v in swims])
    n_frames = max(2, int(total * fps))

    def path_distance(t):
        """How far along the path the bot is at time t (it waits at each caption)."""
        s, last_t = 0.0, h0
        if t <= h0:
            return 0.0
        for s_at, t_start, dur, _ in pauses:
            if t < t_start:
                return min(s + (t - last_t) * speed, cum[-1])
            s, last_t = s_at, t_start + dur
            if t < last_t:
                return min(s, cum[-1])
        return min(s + (t - last_t) * speed, cum[-1])

    def raw_pos(t):
        s = path_distance(t)
        if len(pts) < 2:
            return (pts[0][0] + 0.5, pts[0][1] + 0.5) if pts else (0, 0)
        lo, hi = 0, len(cum) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if cum[mid] <= s else (lo, mid)
        seg = cum[hi] - cum[lo] or 1.0
        f = (s - cum[lo]) / seg
        return (pts[lo][0] + (pts[hi][0] - pts[lo][0]) * f + 0.5, pts[lo][1] + (pts[hi][1] - pts[lo][1]) * f + 0.5)

    track = _smooth([raw_pos(i / fps) for i in range(n_frames)], 3)
    collect_t = {id(it): h0 + cum[idx] / speed + sum(d for s_at, _, d, _ in pauses if s_at <= cum[idx]) for idx, it in plan.collects}

    # ---- camera ----
    if view:
        vw, vh = min(view[0] * px, W), min(view[1] * px, H)
    else:
        vw, vh = W, H

    sway_cache: dict = {}
    veil_cache: dict = {}

    def below(p) -> int:
        n = 0
        while n < 8 and any("sway" in q.tile.anim for q in level.cell(p.x, p.y + 1 + n)):
            n += 1
        return n

    below_cache = {id(p): below(p) for p in dynamic if "sway" in p.tile.anim}

    def animated(p, spr, t, base_below=0):
        """(sprite, dx, dy) of an animated placement at time t."""
        tile = p.tile
        u = (t / ANIM_PERIOD + _phase(p)) % 1.0
        dx = dy = 0
        flip = p.flip
        if "sway" in tile.anim:
            step = int(u * SWAY_STEPS) % SWAY_STEPS
            key = (id(spr), base_below, step)
            if key not in sway_cache:
                sway_cache[key] = _sway(spr, base_below, step, px, tile.anim["sway"] or SWAY_AMP, (p.size or tile.size)[1])
            spr = sway_cache[key]
        if "bob" in tile.anim:
            dy = round(math.sin(2 * math.pi * u) * 0.22 * px)
        if "swim" in tile.anim:
            n, spd = _swim(tile.anim["swim"])
            w = (t / _swim_period(tile.anim["swim"]) + _phase(p)) % 1.0
            dx = round((1 - abs(2 * w - 1)) * n * px)
            flip = flip != (w > 0.5)
        if flip:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        return spr, dx, dy

    def draw_layer(out, L, t, left, topc):
        lay = L["layer"]
        sx, sy = layer_offset(lay, left, topc)
        if L["img"] is not None:
            _over(out, L["img"], L["ox"] - sx, L["oy"] - sy)
        for p in L["dyn"]:
            spr = sprites.get(p.tile, p.x, p.y, p.size, t)
            vk = (id(lay), id(spr))
            if vk not in veil_cache:
                veil_cache[vk] = _veil(spr, lay.haze, lay.alpha)
            spr, dx, dy = animated(p, veil_cache[vk], t)
            _over(out, spr, (p.x - x0) * px + dx - sx, (p.y - y0) * px + dy - sy)

    story = [(t_start, cap) for _, t_start, _, cap in pauses]

    def frame(i: int) -> Image.Image:
        t = i / fps
        bx, by = track[min(i, len(track) - 1)] if pts else (0, 0)
        if view:
            cx = (bx - x0) * px if pts else W / 2
            cy = (by - y0) * px if pts else H / 2
            left = int(min(max(cx - vw / 2, 0), W - vw))
            topc = int(min(max(cy - vh / 2, 0), H - vh))
        else:
            left = topc = 0
        win = (left, topc, left + vw, topc + vh)
        out = backdrop.crop(win).convert("RGBA")
        for L in layers:
            if not L["layer"].over:
                draw_layer(out, L, t, left, topc)
        out.alpha_composite(static.crop(win))
        for p in dynamic:
            spr, dx, dy = animated(p, sprites.get(p.tile, p.x, p.y, p.size, t), t, below_cache.get(id(p), 0))
            _over(out, spr, (p.x - x0) * px + dx - left, (p.y - y0) * px + dy - topc)
        for it in items:
            if t < collect_t.get(id(it), 1e9):
                spr = sprites.get(it.tile, it.x, it.y, it.size)
                bob = round(math.sin(2 * math.pi * ((t / (ANIM_PERIOD / 2)) + _phase(it))) * 0.12 * px)
                _over(out, spr, (it.x - x0) * px - left, (it.y - y0) * px + bob - topc)
        if pts:
            nxt = track[min(i + 2, len(track) - 1)]
            face_left = nxt[0] < bx - 0.02 or (abs(nxt[0] - bx) <= 0.02 and getattr(frame, "left", False))
            frame.left = face_left
            pic = bot_at(t)
            spr = pic.transpose(Image.FLIP_LEFT_RIGHT) if face_left else pic
            wob = round(math.sin(2 * math.pi * t / 1.1) * 0.06 * px)
            _over(out, spr, (bx - x0 - 0.5) * px - bot_off - left, (by - y0 - 0.5) * px - bot_off + wob - topc)
        for L in layers:
            if L["layer"].over:
                draw_layer(out, L, t, left, topc)
        for t0, cap in story:
            draw_caption(out, cap, t - t0)
        return out.convert("RGB")

    # ---- encode (one shared palette, otherwise gradients flicker) ----
    frames = [frame(i) for i in range(n_frames)]
    sample = [frames[j] for j in sorted({0, n_frames // 3, 2 * n_frames // 3, n_frames - 1})]
    stack = Image.new("RGB", (sample[0].width, sample[0].height * len(sample)))
    for j, s in enumerate(sample):
        stack.paste(s, (0, j * s.height))
    pal = stack.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(out_path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=False)
    return {
        "frames": n_frames, "size": frames[0].size, "tile_px": px, "seconds": round(total, 1),
        "path_tiles": round(cum[-1], 1), "items": len(plan.collects), "reached_goal": bool(plan.goal and pts and pts[-1] == plan.goal),
    }
