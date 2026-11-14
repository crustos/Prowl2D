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
