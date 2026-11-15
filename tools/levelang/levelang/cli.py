from __future__ import annotations

import argparse
import ast
import json
import os
import sys

from .parser import translate
from .runtime import load_file
from .transform import transform


def _view(s: str):
    w, h = s.lower().split("x")
    return int(w), int(h)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="levelang", description="levelang: emoji/ASCII/SVG level language")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("translate", help="print the generated Python")
    t.add_argument("file")
    t.add_argument("--ast", action="store_true", help="show the code after the AST transformer instead")

    g = sub.add_parser("gif", help="render a preview GIF with a bot playing the level")
    g.add_argument("file")
    g.add_argument("-o", "--out", default=None)
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--tile", type=int, default=16, help="max pixels per tile")
    g.add_argument("--width", type=int, default=960, help="max GIF width when showing the whole level")
    g.add_argument("--fps", type=int, default=16)
    g.add_argument("--speed", type=float, default=8.0, help="bot speed, tiles/second")
    g.add_argument("--view", type=_view, default=None, help="follow-camera window in tiles, e.g. 40x22")
    g.add_argument("--no-bot", action="store_true")

    j = sub.add_parser("json", help="dump the engine-neutral level data")
    j.add_argument("file")
    j.add_argument("-o", "--out", default=None)
    j.add_argument("--seed", type=int, default=None)

    e = sub.add_parser("export-cs", help="export the level as a Prowl2D SlimeJump-style Level.cs")
    e.add_argument("file")
    e.add_argument("-o", "--out", default=None, help="default: Level.cs next to the .lvl")
    e.add_argument("--seed", type=int, default=None)
    e.add_argument("--layers-from", default=None, help="a Level.cs whose LayerRows() the game needs (default: Samples/SlimeJump's)")

    q = sub.add_parser("export-project", help="export the level as a Prowl2D editor project (prowl.py FILE.json): the grid, plus layers and the skin as images")
    q.add_argument("file")
    q.add_argument("-o", "--out", default=None, help="default: the .lvl's name with .json")
    q.add_argument("--seed", type=int, default=None)
    q.add_argument("--ppc", type=int, default=32, help="pixels per cell of the layer images (default 32)")
    q.add_argument("--tile", type=int, default=16, help="pixels of the grid's pixel-art tile sprites (default 16)")

    sc = sub.add_parser("export-scenery", help="bake the layers and the skin into SceneryData.cs, which the game's Scenery.cs draws with GFX.Triangles")
    sc.add_argument("file")
    sc.add_argument("-o", "--out", default=None, help="default: SceneryData.cs next to the .lvl")
    sc.add_argument("--seed", type=int, default=None)
    sc.add_argument("--max-px", type=int, default=128, help="longest side of a picture in the atlas (default 128)")

    b = sub.add_parser("export-blender", help="export the level as Blender grease pencil objects, animated like the GIF preview, to a .blend (runs Blender headless)")
    b.add_argument("file")
    b.add_argument("-o", "--out", default=None, help="default: /tmp/levelang-preview.blend (the system temp folder)")
    b.add_argument("--blender", default=None, help="the Blender executable (default: $BLENDER, `blender` on the PATH, the usual install folders)")
    b.add_argument("--seed", type=int, default=None)
    b.add_argument("--res", type=_view, default=(1280, 800), help="render size saved in the .blend, WxH (default 1280x800; change it in Blender any time)")
    b.add_argument("--fps", type=int, default=24)
    b.add_argument("--view", type=_view, default=(32, 20), help="cells the camera shows, WxH (default 32x20, like the GIF); the height is what is kept for any render size")
    b.add_argument("--samples", type=int, default=16, help="render anti-aliasing samples (default 16)")
    b.add_argument("--video", choices=["mp4", "png", "none"], default="mp4", help="what a render writes: an mp4, PNG frames, or leave the output as it is (default mp4)")
    b.add_argument("--no-bot", action="store_true", help="no bot and a still camera: only the scenery moves")
    b.add_argument("--scene-json", default=None, help="also keep the scene description that Blender is given, at this path")

    f = sub.add_parser("from-cs", help="convert an existing Level.cs into levelang art you can edit as a picture")
    f.add_argument("file")
    f.add_argument("-o", "--out", default=None, help="default: level.lvl next to the Level.cs")

    a = ap.parse_args(argv)
    if a.cmd == "translate":
        with open(a.file, encoding="utf-8") as f:
            tr = translate(f.read(), a.file)
        if a.ast:
            print(ast.unparse(transform(ast.parse(tr.python), tr.tiles)))
        else:
            print(tr.python)
        return 0

    if a.cmd == "from-cs":
        from .export import level_cs_to_lvl

        with open(a.file, encoding="utf-8") as f:
            text = level_cs_to_lvl(f.read())
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.file)), "level.lvl")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {out}")
        return 0

    level, _ = load_file(a.file, a.seed)
    if a.cmd == "export-cs":
        from .export import to_level_cs

        text, warnings = to_level_cs(level, os.path.basename(a.file), a.layers_from)
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.file)), "Level.cs")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        for w in warnings:
            print("levelang: warning:", w, file=sys.stderr)
        print(f"wrote {out}")
        return 0
    if a.cmd == "export-project":
        from .export import to_project

        name = os.path.splitext(os.path.basename(a.file))[0]
        data = to_project(level, name, ppc=a.ppc, tile_px=a.tile, warn=lambda m: print(m, file=sys.stderr))
        out = a.out or os.path.splitext(a.file)[0] + ".json"
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        lv = data["levels"][0]
        print(f"wrote {out}: a {len(lv['rows'][0])}x{len(lv['rows'])} grid, {len(lv['layers'])} layers, {len(data['images'])} images, {len(data['sprites'])} tile sprites")
        return 0
    if a.cmd == "export-blender":
        from .export.blender import DEFAULT_OUT, BlenderError, export_blender

        try:
            info = export_blender(level, a.out or DEFAULT_OUT, blender=a.blender, name=os.path.splitext(os.path.basename(a.file))[0], res=a.res, fps=a.fps, view=a.view,
                                  samples=a.samples, video=a.video, play=not a.no_bot, keep_scene=a.scene_json, log=lambda m: print(m, file=sys.stderr))
        except BlenderError as e:
            print("levelang:", e, file=sys.stderr)
            return 1
        print(f"wrote {info['path']}: {info['seconds']} s at {info['fps']} fps ({info['frames']} frames), {info['objects']} objects, {info['strokes']} strokes")
        return 0
    if a.cmd == "export-scenery":
        from .export.scenery import scenery, to_csharp

        data = scenery(level, os.path.splitext(os.path.basename(a.file))[0], max_px=a.max_px, warn=lambda m: print(m, file=sys.stderr))
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.file)), "SceneryData.cs")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(to_csharp(data, os.path.basename(a.file)))
        print(f"wrote {out}: atlas {data['atlas_w']}x{data['atlas_h']}, {len(data['runs'])} runs, {len(data['layers'])} layers, {len(data['items'])} items")
        return 0
    if a.cmd == "json":
        text = json.dumps(level.to_dict(), ensure_ascii=False, indent=1)
        (open(a.out, "w", encoding="utf-8").write(text) if a.out else print(text))
        return 0

    from .render import render_gif

    out = a.out or a.file.rsplit(".", 1)[0] + ".gif"
    info = render_gif(level, out, tile_px=a.tile, max_width=a.width, fps=a.fps, speed=a.speed, view=a.view, play=not a.no_bot)
    print(f"wrote {out}: {info['frames']} frames, {info['size'][0]}x{info['size'][1]}px, {info['seconds']}s, "
          f"{info['items']} items collected, goal reached: {info['reached_goal']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
