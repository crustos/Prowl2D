#!/usr/bin/env python3
"""stockton_gif.py -- draw an animated GIF of Samples/SlimeJumpStockton from its own run.

    python3 tools/stockton_gif.py [-o OUT.gif] [--every N] [--scale S]

The sample is headless: this copies it to a scratch folder, adds a recorder (the terrain window around the slime, the nodes and the lasso, every N frames), runs it
with the native player and draws the printout with Pillow. The sample itself is not changed."""
import argparse, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_gif                       # the faces' art: head_frame (8 frames, looping), anchors

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "Samples", "SlimeJumpStockton")
WIN = 400                      # window width, in terrain pixels (50 units)
PPU = 8
KEEP = 1500                    # frames to record (the run is over at about 750, the sewage pipe pours until 1600)

REC = '''using System;
using Prowl.Core2D;
static class Rec
{
    static int Mi(float v) { return (int)(v * 1000f); }
    public static void Frame(Scene2D scene, int frame, Node player)
    {
        if (frame % EVERY != 0) return;
        int x0 = (int)(player.WorldX() * 8f) - WIN / 2;
        if (x0 < 0) x0 = 0;
        if (x0 > 768 - WIN) x0 = 768 - WIN;
        Console.WriteLine("F " + frame + " " + x0);
        for (int y = 0; y < 288; y++)
        {
            string row = "R";
            int last = -1;
            int run = 0;
            for (int x = x0; x < x0 + WIN; x++)
            {
                int c = Destruct.Code(x, y);
                if (c == last) { run++; continue; }
                if (run > 0) row = row + " " + last + ":" + run;
                last = c;
                run = 1;
            }
            row = row + " " + last + ":" + run;
            Console.WriteLine(row);
        }
        for (int q = 0; q < scene.NodeHighWater; q++)
        {
            Node bn = scene.NodeAt(q);
            if (bn == null || !bn.Alive || bn.Destroyed) continue;
            if (bn.Layer == 7) continue;
            Component cc = scene.Find(bn, ComponentKind.PolygonCollider2D);
            string line = "N " + bn.Tag + " " + Mi(bn.WorldX()) + " " + Mi(bn.WorldY());
            if (cc != null)
            {
                Collider2D col = cc.Collider;
                line = line + " P " + col.PolyCount;
                for (int i = 0; i < col.PolyCount; i++)
                {
                    float wx;
                    float wy;
                    bn.ToWorld(col.Poly[2 * i], col.Poly[2 * i + 1], out wx, out wy);
                    line = line + " " + Mi(wx) + " " + Mi(wy);
                }
                Console.WriteLine(line);
                continue;
            }
            cc = scene.Find(bn, ComponentKind.BoxCollider2D);
            if (cc != null)
            {
                Collider2D col = cc.Collider;
                float wx;
                float wy;
                float hw = col.SizeX * 0.5f;
                float hh = col.SizeY * 0.5f;
                line = line + " P 4";
                bn.ToWorld(col.OffsetX - hw, col.OffsetY - hh, out wx, out wy); line = line + " " + Mi(wx) + " " + Mi(wy);
                bn.ToWorld(col.OffsetX - hw, col.OffsetY + hh, out wx, out wy); line = line + " " + Mi(wx) + " " + Mi(wy);
                bn.ToWorld(col.OffsetX + hw, col.OffsetY + hh, out wx, out wy); line = line + " " + Mi(wx) + " " + Mi(wy);
                bn.ToWorld(col.OffsetX + hw, col.OffsetY - hh, out wx, out wy); line = line + " " + Mi(wx) + " " + Mi(wy);
                Console.WriteLine(line);
            }
        }
        for (int q = 0; q < Shared.EnemyCount(); q++)
            if (Shared.EnemyAlive(q)) Console.WriteLine("K " + (Shared.TagEnemyBase + q) + " " + Shared.EnemyKind(q));
        Console.WriteLine("L " + (Shared.LassoActive ? 1 : 0) + " " + (Shared.LassoAttached ? 1 : 0) + " " + Mi(Shared.LassoTipX) + " " + Mi(Shared.LassoTipY));
        Console.WriteLine("E");
    }
}
'''

def record(every):
    work = tempfile.mkdtemp(prefix="stocktongif_")
    game = os.path.join(work, "SlimeJumpStockton")
    shutil.copytree(SAMPLE, game, ignore=shutil.ignore_patterns("*.md", "*.gif"))
    open(os.path.join(game, "Rec.cs"), "w").write(REC.replace("EVERY", str(every)).replace("WIN", str(WIN)))
    p = os.path.join(game, "Game.cs")
    s = open(p).read()
    anchor = "            World.Tick();\n"
    assert anchor in s
    s = s.replace(anchor, anchor + "            Rec.Frame(scene, frame, player);\n", 1)
    assert "&& !Shared.Won" in s
    open(p, "w").write(s.replace("&& !Shared.Won", "&& (!Shared.Won || frame < " + str(KEEP) + ")", 1))      # the world runs on after the win: the inflows go on pouring
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "ccsharp", "player_build.py"), game, "-o", os.path.join(work, "pkg"), "--run"], capture_output=True, text=True)
    if r.returncode != 0 and "won=1" not in r.stdout:
        sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout, work

def parse(text):
    frames, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("F "):
            _, f, x0 = ln.split()
            cur = {"frame": int(f), "x0": int(x0), "rows": [], "nodes": [], "lasso": None}
        elif cur is None:
            continue
        elif ln.startswith("R"):
            cur["rows"].append([tuple(map(int, t.split(":"))) for t in ln.split()[1:]])
        elif ln.startswith("N "):
            w = ln.split()
            node = {"tag": int(w[1]), "x": int(w[2]) / 1000, "y": int(w[3]) / 1000, "poly": None}
            if len(w) > 4 and w[4] == "P":
                n = int(w[5]); v = [int(t) / 1000 for t in w[6:6 + 2 * n]]
                node["poly"] = list(zip(v[0::2], v[1::2]))
            cur["nodes"].append(node)
        elif ln.startswith("K "):
            _, tag, kind = ln.split()
            for n in cur["nodes"]:
                if n["tag"] == int(tag): n["kind"] = int(kind)
        elif ln.startswith("L "):
            _, act, att, tx, ty = ln.split()
            cur["lasso"] = (act == "1", att == "1", int(tx) / 1000, int(ty) / 1000)
        elif ln == "E":
            frames.append(cur); cur = None
    return frames

def hsh(a, b, salt=0):
    h = (a * 374761393 + b * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0x1000000)

def clamp(v): return max(0, min(255, int(v)))
def shade(c, k): return (clamp(c[0] + k), clamp(c[1] + k), clamp(c[2] + k))

STREET_PX = 16 * PPU
SEWER_TOP_PX = int(7.5 * PPU)
VAULT_PX = int(34.5 * PPU)                          # the vault over the sewer: the sewer's ceiling, hung with the tanks' chains
SAND, WATER, SEWAGE = (222, 190, 96), (70, 140, 235), (92, 110, 58)
TANKS = ((49, 56, (122, 98, 70)), (60, 67, (74, 110, 150)), (71, 78, (84, 112, 84)))   # the three tanks the slime swings on: a septic tank, a water tank, a plain one (x0, x1, colour)

def tank_pixel(x, y, base):
    """a riveted steel tank: bands, rivets, rust, a shadow along the bottom"""
    lx, ly = x % 8, y % 8
    c = base
    band = (y // 8) % 4 == 0
    if band: c = shade(c, -26)
    if lx == 4 and ly == 4 and not band: c = shade(c, 40)           # a rivet
    c = shade(c, (hsh(x // 2, y // 2, 8) - 0.5) * 12)
    if hsh(x // 3, y // 4, 9) > 0.93: c = (140, 84, 46)              # rust
    if y % 8 == 7: c = shade(c, -14)
    return c

def rock_pixel(x, y):
    """a concrete walkway with a hazard edge, brick (mossy) under it, concrete at the bottom of the sewer, and the tanks"""
    wx, wy = x / PPU, y / PPU
    for x0, x1, base in TANKS:
        if x0 - 0.1 <= wx <= x1 + 0.1 and 27.9 <= wy <= 32.1:
            return tank_pixel(x, y, base)
    if y >= STREET_PX - 4:
        if y >= STREET_PX - 1.2 * PPU // 8 and (x // 4 + y // 4) % 2 == 0 and y >= STREET_PX - 2: return (214, 176, 40)
        g = 142 + int(hsh(x // 2, y // 2) * 14)
        if x % 16 == 0: g -= 30
        return (g, g, g - 6)
    if y >= SEWER_TOP_PX:
        row = y // 6
        xo = x + (6 if row & 1 else 0)
        col = xo // 12
        if xo % 12 == 0 or y % 6 == 0:
            return (92, 90, 82)
        n = hsh(col, row, 1)
        c = shade((136 + int(n * 30) - 15, 78 + int(n * 20) - 10, 56), (hsh(x, y, 2) - 0.5) * 6)
        moss = hsh(col // 2, row // 2, 4)
        if moss > 0.72: c = (62 + int(n * 20), 92 + int(n * 24), 52)                  # moss and slime
        return c
    g = 92 + int(hsh(x // 3, y // 3, 5) * 18)
    return (g, g + 2, g - 6)

def pipe_metal(x, y, wx, wy, horizontal, rim):
    t = ((wy - 32.9) / 1.6) if horizontal else ((wx - 1.2) / 1.3)
    k = int(max(0, min(9, t * 10)))
    c = shade((92, 100, 98), (-34, 6, 28, 34, 22, 6, -12, -30, -40, -46)[k])
    if rim: c = shade(c, -34)
    if hsh(x // 3, y // 3, 15) > 0.88: c = (130, 82, 44)
    return c

LAMPS = (14, 38, 62, 86)                                    # caged lamps on the vault (x, in units)

def back_pixel(x, y):
    """the sewer behind: dim brick, arch ribs, pipes, caged lamps; the lower tunnel is the same, darker, with a drain's light"""
    wx, wy = x / PPU, y / PPU
    row = y // 6
    xo = x + (6 if row & 1 else 0)
    col = xo // 12
    mortar = xo % 12 == 0 or y % 6 == 0
    n = hsh(col, row, 1)
    base = (44 + int(n * 14), 52 + int(n * 12), 46 + int(n * 8)) if not mortar else (30, 34, 32)
    low = y < SEWER_TOP_PX                                      # the lower tunnel
    k = 0.55 if low else 1.0
    c = (int(base[0] * k), int(base[1] * k), int(base[2] * k))
    if y >= VAULT_PX:                                           # the vault: a concrete slab
        g = 70 + int(hsh(x // 4, y // 4, 3) * 12)
        return (g, g + 2, g - 4)
    # the inflows: a sewage pipe at the top left, and a sand chute over the dune in the first lot (Destruct.Step pours from their mouths)
    if (wx < 2.6 and 32.9 <= wy < 34.5) or (1.2 <= wx < 2.5 and 32.3 <= wy < 32.9):
        return pipe_metal(x, y, wx, wy, horizontal=wy >= 32.9, rim=(wx > 2.2 or (wy < 32.9 and wy < 32.5)))
    if (14.0 <= wx < 16.0 and 33.4 <= wy < 34.5) or (14.5 <= wx < 15.4 and 32.3 <= wy < 33.4):
        return pipe_metal(x, y, wx, wy, horizontal=False, rim=wy < 32.5)
    if x % 128 < 6 and not low:                                 # an arch rib, a concrete pier every 16 units
        g = 78 + int(hsh(x // 2, y // 2, 6) * 10)
        return (g, g + 3, g - 2)
    for py, w in ((26 * PPU, 5), (11 * PPU, 4)):                # pipes along the sewer: a big one high up, a smaller one low
        if py <= y < py + w * 2:
            kk = y - py
            metal = (84, 92, 94)
            cc = shade(metal, (-30, 4, 26, 30, 18, 4, -14, -34, -40, -44)[min(kk, 9)] if w == 5 else (-26, 16, 30, 10, -20, -40, -44, -44)[min(kk, 7)])
            if x % 96 < 3: cc = shade(cc, -28)                  # a flange
            if hsh(x // 4, y // 3, 12) > 0.9: cc = (126, 80, 44) # rust
            return cc
    for lx in LAMPS:                                            # a caged lamp: a warm glow on the vault
        dx, dy = wx - lx, wy - 33.4
        d2 = dx * dx + dy * dy
        if d2 < 0.3: return (255, 232, 150)
        if d2 < 0.55: return (90, 90, 90)                       # the cage
        if d2 < 18 and not low:
            t = (18 - d2) / 18 * 0.35
            return (int(c[0] + (255 - c[0]) * t * 0.7), int(c[1] + (210 - c[1]) * t * 0.7), int(c[2] + (90 - c[2]) * t * 0.5))
    for x0, x1, base in TANKS:                                  # the tank's chains up to the vault
        for cx in (x0 + 1.5, x1 - 1.5):
            if abs(wx - cx) < 0.18 and 32 <= wy < 34.5 and int(wy * 4) % 2 == 0: return (30, 30, 34)
            if abs(wx - cx) < 0.12 and 32 <= wy < 34.5: return (58, 58, 64)
    if low and 27 <= wx <= 32:                                  # a storm drain's light falling into the lower tunnel
        t = 0.22 if int(wx * 8) % 3 else 0.1
        return (int(c[0] + (200 - c[0]) * t), int(c[1] + (210 - c[1]) * t), int(c[2] + (170 - c[2]) * t))
    # a vertical ladder of rungs on the pier's side, every so often, and green drips down the wall
    if (x % 256) in (140, 141) and y % 7 == 0: return (110, 100, 80)
    if hsh(x // 6, 77) > 0.9 and hsh(x // 6, y // 4, 3) > 0.45 and not low: return (int(c[0] * 0.8), int(c[1] * 1.15), int(c[2] * 0.8))
    return c

def draw(fr, scale):
    h = 288
    small = Image.new("RGB", (WIN, h)); sp = small.load()
    x0 = fr["x0"]
    for y, row in enumerate(fr["rows"]):
        x = 0
        for c, n in row:
            for xx in range(x, x + n):
                gx = x0 + xx
                if c == 0: col = back_pixel(gx, y)
                elif c == 1: col = rock_pixel(gx, y)
                elif c == 2: col = shade(SAND, ((gx * 7 + y * 13) % 5 - 2) * 4)
                elif c == 3: col = shade(WATER, ((gx * 5 + y * 3 + fr["frame"] // 4) % 5 - 2) * 5)
                else: col = shade(SEWAGE, ((gx * 5 + y * 3 + fr["frame"] // 4) % 5 - 2) * 5)
                sp[xx, h - 1 - y] = col
            x += n
    img = small.resize((WIN * scale, h * scale), Image.NEAREST)
    d = ImageDraw.Draw(img)
    def S(wx, wy): return ((wx * PPU - x0) * scale, (h - wy * PPU) * scale)
    slime = None
    faces = []
    for n in fr["nodes"]:
        if n["poly"] is None: continue
        pts = [S(x, y) for x, y in n["poly"]]
        t = n["tag"]
        if n.get("kind", 0) >= 2:
            faces.append(n)
            continue
        if t == 1:
            slime = n
            d.polygon(pts, fill=(70, 220, 110), outline=(20, 90, 40))
            cx, cy = S(n["x"], n["y"]); e = scale * 1.6
            d.ellipse([cx - 2 * e, cy - e * 1.4, cx - 0.4 * e, cy - e * 0.1], fill=(255, 255, 255))
            d.ellipse([cx + 0.4 * e, cy - e * 1.4, cx + 2 * e, cy - e * 0.1], fill=(255, 255, 255))
        elif t == 6: d.polygon(pts, outline=(255, 215, 0))
        elif t == 7: cx, cy = S(n["x"], n["y"]); d.ellipse([cx - 2 * scale, cy - 2 * scale, cx + 2 * scale, cy + 2 * scale], fill=(255, 240, 120))
        elif t >= 200: d.polygon(pts, fill=(196, 120, 50), outline=(110, 60, 20))
        else: d.polygon(pts, fill=(170, 100, 80), outline=(70, 40, 34))
    for n in faces:                                                 # a face on its body, looking toward the slime
        src = sand_gif.head_frame(n["kind"], fr["frame"])
        k = scale * 8.0 / sand_gif.ART_PPU
        sprite = src.resize((max(1, round(src.width * k)), max(1, round(src.height * k))), Image.NEAREST)
        if slime is not None and slime["x"] > n["x"]: sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
        cx, cy = S(n["x"], n["y"])
        ax, ay = sand_gif.anchors()[sand_gif.HEADS[n["kind"]]]
        img.paste(sprite, (int(cx - ax * k), int(cy - ay * k)), sprite)
    d = ImageDraw.Draw(img)
    act, att, tx, ty = fr["lasso"]
    if act and slime is not None:
        d.line([S(slime["x"], slime["y"]), S(tx, ty)], fill=(240, 220, 160), width=max(1, scale))
        if att:
            cx, cy = S(tx, ty); d.ellipse([cx - 3 * scale, cy - 3 * scale, cx + 3 * scale, cy + 3 * scale], fill=(255, 90, 60))
    return img

def main():
    sand_gif.use_art(sand_gif.SAMPLE_ART["SlimeJumpFaces"])
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out")
    ap.add_argument("--every", type=int, default=6)
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
    out = a.out or os.path.join(SAMPLE, "slimejumpstockton.gif")
    text, work = record(a.every)
    frames = parse(text)
    shutil.rmtree(work, ignore_errors=True)
    print("recorded %d frames" % len(frames))
    imgs = [draw(f, a.scale) for f in frames]
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=int(a.every * 10), loop=0, optimize=False)
    print("wrote", out, os.path.getsize(out) // 1024, "KiB")

if __name__ == "__main__":
    main()
