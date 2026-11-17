"""Cutscene -> animated GIF: the level is the stage, the scene's timeline moves the actors, the camera and the fade (Pillow only)."""
from __future__ import annotations

import math

from PIL import Image, ImageChops

from ..runtime import Level
from .captions import draw_caption
from .fx import apply as apply_fx
from .gif import _gradient, _over, _skin_image, _veil, layer_offset
from .sprites import Sprites, color


def render_scene(level: Level, out_path: str, *, tile_px: int = 20, fps: int | None = None, seconds: float | None = None, at: list | None = None, mp4: str | None = None, audio: str | None = None, crf: int = 24, log=print):
    sc = level.scene
    if sc is None:
        raise ValueError("the level has no scene(): start one with scene(\"intro\", seconds=24)")
    if not level.placements:
        raise ValueError("the stage is empty: place some tiles for the scene to happen on")
    fps = fps or sc.fps
    total = seconds or sc.seconds
    px = tile_px
    sprites = Sprites(px)
    x0, y0, x1, y1 = level.bounds()
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    W, H = cols * px, rows * px
    vcols, vrows = min(sc.view[0], cols), min(sc.view[1], rows)
    out_w, out_h = int(vcols * px), int(vrows * px)

    # ---- the stage: what does not move is drawn once ----
    top, bottom = level.background or ("#20222c", "#20222c")
    backdrop = _gradient((W, H), top, bottom)
    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dynamic, skinned, plain = [], {id(sk): [] for sk in level.skins}, []
    for p in sorted(level.placements, key=lambda p: (p.tile.layer, p.order)):
        if p.tile.animated:
            dynamic.append(p)
            continue
        sk = next((k for k in level.skins if k.hide and k.covers(p.tile)), None)
        (skinned[id(sk)] if sk is not None else plain).append(p)

    def stamp(p) -> None:
        spr = sprites.get(p.tile, p.x, p.y, p.size)
        _over(static, spr.transpose(Image.FLIP_LEFT_RIGHT) if p.flip else spr, (p.x - x0) * px, (p.y - y0) * px)

    for p in plain:
        if p.tile.layer < 0:
            stamp(p)
    for sk in level.skins:
        if skinned[id(sk)]:
            static.alpha_composite(_skin_image(level, sk, skinned[id(sk)], sprites, px, x0, y0, cols, rows))
    for p in plain:
        if p.tile.layer >= 0:
            stamp(p)

    layers = []
    for lay in sorted(level.layers, key=lambda l: l.parallax):
        stat = [p for p in lay.placements if not p.tile.animated]
        dyn = [p for p in lay.placements if p.tile.animated]
        img = ox = oy = None
        if stat:
            boxes = [(int(round((p.x - x0) * px)), int(round((p.y - y0) * px)), int((p.size or p.tile.size)[0] * px), int((p.size or p.tile.size)[1] * px)) for p in stat]
            ox, oy = min(b[0] for b in boxes), min(b[1] for b in boxes)
            img = Image.new("RGBA", (max(1, max(b[0] + b[2] for b in boxes) - ox), max(1, max(b[1] + b[3] for b in boxes) - oy)), (0, 0, 0, 0))
            for p, b in zip(stat, boxes):
                spr = sprites.get(p.tile, p.x, p.y, p.size)
                _over(img, spr.transpose(Image.FLIP_LEFT_RIGHT) if p.flip else spr, b[0] - ox, b[1] - oy)
            img = _veil(img, lay.haze, lay.alpha)
        layers.append((lay, img, ox, oy, dyn))

    veil_cache: dict = {}

    def draw_layer(out, entry, t, left, topc) -> None:
        lay, img, ox, oy, dyn = entry
        sx, sy = layer_offset(lay, left, topc)
        if img is not None:
            _over(out, img, ox - sx, oy - sy)
        for p in dyn:
            spr = sprites.get(p.tile, p.x, p.y, p.size, t)
            k = (id(lay), id(spr))
            if k not in veil_cache:
                veil_cache[k] = _veil(spr, lay.haze, lay.alpha)
            spr = veil_cache[k]
            _over(out, spr.transpose(Image.FLIP_LEFT_RIGHT) if p.flip else spr, (p.x - x0) * px - sx, (p.y - y0) * px - sy)

    def faded(spr: Image.Image, a: float) -> Image.Image:
        if a >= 1:
            return spr
        spr = spr.copy()
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * a)))
        return spr

    def frame(i: int) -> Image.Image:
        t = i / fps
        hold = sc.stutter_at(t)
        if hold:
            t = math.floor(t / hold) * hold
        cx, cy, zoom = sc.camera(t)
        zoom = max(0.2, zoom)
        wcols, wrows = vcols / zoom, vrows / zoom
        cx = min(max(cx, x0 + wcols / 2), x0 + cols - wcols / 2) if wcols < cols else x0 + cols / 2
        cy = min(max(cy, y0 + wrows / 2), y0 + rows - wrows / 2) if wrows < rows else y0 + rows / 2
        left, topc = (cx - x0 - wcols / 2) * px, (cy - y0 - wrows / 2) * px
        win = (round(left), round(topc), round(left) + max(1, round(wcols * px)), round(topc) + max(1, round(wrows * px)))
        left, topc = win[0], win[1]
        out = backdrop.crop(win).convert("RGBA")
        for entry in layers:
            if not entry[0].over:
                draw_layer(out, entry, t, left, topc)
        out.alpha_composite(static.crop(win))
        for p in dynamic:
            spr = sprites.get(p.tile, p.x, p.y, p.size, t)
            dy = round(math.sin(2 * math.pi * (t / 2.4 + (p.x * 0.37))) * 0.22 * px) if "bob" in p.tile.anim else 0
            _over(out, spr.transpose(Image.FLIP_LEFT_RIGHT) if p.flip else spr, (p.x - x0) * px - left, (p.y - y0) * px + dy - topc)
        for a in sc.actors.values():
            if not a.visible(t):
                continue
            ax, ay = a.position(t)
            tile = a.poses[a.pose(t)]
            spr = sprites.get(tile, 0, 0, a.size, t)
            if a.facing_flip(t):
                spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
            _over(out, spr, (ax - x0) * px - left, (ay - y0) * px - topc)
            for et, etile, esec in a.emotes:
                age = t - et
                if 0 <= age <= esec:
                    u = age / esec
                    e = sprites.get(etile, 0, 0, None, age)
                    a_ = min(1.0, u * 6, (1 - u) * 3)
                    ew, eh = (etile.size[0] * px, etile.size[1] * px)
                    pop = 0.6 + 0.4 * min(1.0, u * 5)
                    e = e.resize((max(1, int(e.width * pop)), max(1, int(e.height * pop))), Image.LANCZOS)
                    aw = a.width_height(tile)[0] * px
                    _over(out, faded(e, a_), (ax - x0) * px - left + (aw - e.width) / 2, (ay - y0) * px - topc - eh * 0.9 - u * px * 0.8 * max(1.0, a.width_height(tile)[0] / 4))
        for entry in layers:
            if entry[0].over:
                draw_layer(out, entry, t, left, topc)
        out = out.resize((out_w, out_h), Image.LANCZOS) if out.size != (out_w, out_h) else out
        fxs = [e for e in sc.fx_at(i / fps) if e[0] != "stutter"]
        if fxs:
            out = apply_fx(out.convert("RGB"), fxs, i).convert("RGBA")
        for cap in sc.captions:
            draw_caption(out, cap, t - cap["t"])
        alpha, col = sc.fade(t)
        if alpha > 0:
            out.alpha_composite(Image.new("RGBA", out.size, color(col) + (int(255 * min(1.0, alpha)),)))
        return out.convert("RGB")

    n_frames = max(2, int(total * fps))
    if at is not None:      # a look at some moments (seconds) instead of the GIF: a list of PIL images
        return [frame(min(n_frames - 1, max(0, round(t * fps)))) for t in at]
    if mp4:                 # a video: frames go straight into ffmpeg, with the sound mixed in (the video is `total` seconds long)
        import subprocess
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-"]
        if audio:
            cmd += ["-i", audio]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", str(crf), "-r", str(fps)]
        if audio:
            cmd += ["-c:a", "aac", "-b:a", "96k", "-map", "0:v", "-map", "1:a", "-shortest"]
        proc = subprocess.Popen(cmd + [mp4], stdin=subprocess.PIPE)
        for i in range(n_frames):
            proc.stdin.write(frame(i).tobytes())
            if i % 400 == 0:
                log(f"levelang: frame {i}/{n_frames}")
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed (is it installed, with libx264?)")
        return {"frames": n_frames, "size": (out_w, out_h), "seconds": round(n_frames / fps, 1), "fps": fps}
    frames = [frame(i) for i in range(n_frames)]
    sample = [frames[j] for j in sorted({0, n_frames // 8, n_frames // 4, 3 * n_frames // 8, n_frames // 2, 5 * n_frames // 8, 3 * n_frames // 4, n_frames - 1})]
    stack = Image.new("RGB", (sample[0].width, sample[0].height * len(sample)))
    for j, s in enumerate(sample):
        stack.paste(s, (0, j * s.height))
    pal = stack.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(out_path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=False)
    return {"frames": n_frames, "size": frames[0].size, "seconds": round(n_frames / fps, 1), "fps": fps}
