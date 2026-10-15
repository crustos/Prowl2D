#!/usr/bin/env python3
"""Exports a Prowl2D level as a web page that plays it on the GPU physics engine, in the browser.

    python3 tools/export_gpu_web.py --demo --out Build/GpuWeb
    python3 tools/export_gpu_web.py MyGame.prowl --level "first steps" --out Build/GpuWeb

Writes a folder to serve over http (python3 -m http.server -d Build/GpuWeb):

    index.html, player.js     the player (gpu/web)
    level.json                the level: cells, the tiles that are used (solid / movable / diggable) and their sprites as PNGs
    gpuphys.js, gpuphys.wasm  the engine on the CPU, in WebAssembly (everything: joints, events, polygons, material)
    gpuphys_webgpu.js, spirv/ the circle pipeline on WebGPU: the same kernels as WGSL (sand and balls by the thousand)

The page picks WebGPU when the browser has it and WebAssembly otherwise (`?engine=wasm` or `?engine=webgpu` force one).
Click drops a ball, B a crate, hold F and drag for sand, right click blasts (diggable tiles go), R restarts.
"""
import argparse
import base64
import json
import os
import shutil
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from prowl_editor.model import Project, Sprite, TileDef  # noqa: E402

WEB = os.path.join(ROOT, "gpu", "web")
SPIRV = os.path.join(ROOT, "gpu", "spirv")
PLAYER_FILES = ["player.html", "player.js", "gpuphys.js", "gpuphys.wasm", "gpuphys_webgpu.js"]


def png(width, height, rgba):
    """A PNG (RGBA, 8 bits) from straight-alpha bytes."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def sprite_url(project, sprite):
    """Frame 0 of a sprite as a data: URL, with its frame count (the page animates the others)."""
    frames = [png(sprite.width, sprite.height, sprite.rgba(project.palette, f)) for f in range(len(sprite.frames))]
    return [("data:image/png;base64," + base64.b64encode(f).decode()) for f in frames]


def demo_project():
    """The editor's demo project with a crate and some diggable ground to play with."""
    from prowl_editor.demo import make_demo_project
    from prowl_editor.asciiart import import_sprites
    p = make_demo_project()
    import_sprites("""\
# sprite: crate
NNNNNNNN
NTTTTTTN
NTNNNNTN
NTNTTNTN
NTNTTNTN
NTNNNNTN
NTTTTTTN
NNNNNNNN
""", p)
    crate = "\U0001f4e6"
    p.tiles[crate] = TileDef(crate, "crate", "", True, True)
    grass = "\U0001f7e9"
    p.tiles[grass].diggable = True
    lv = p.levels[0]
    for x, y in ((5, 2), (6, 2), (6, 1), (14, 1), (15, 1), (15, 0), (16, 1), (20, 0)):
        if lv.get(x, y) == "" or lv.get(x, y) == p.empty:
            lv.set(x, y, crate)
    return p, lv


def export_level(project, level):
    used = {}
    for cell in level.cells:
        if cell and cell not in used and cell in project.tiles:
            used[cell] = project.tiles[cell]
    tiles = {}
    for emoji, t in used.items():
        spr = project.sprite_for_tile(t)
        entry = {"name": t.name, "solid": bool(t.solid or t.dynamic), "dynamic": bool(t.dynamic), "diggable": bool(t.diggable)}
        if spr is not None:
            entry["sprite"] = sprite_url(project, spr)
            entry["fps"] = spr.fps
            entry["size"] = [spr.width, spr.height]
        tiles[emoji] = entry
    return {"name": level.name, "width": level.width, "height": level.height,
            "cells": [c if c in tiles else "" for c in level.cells],            # row by row from the top
            "tiles": tiles}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", help="a project file (.json)")
    ap.add_argument("--demo", action="store_true", help="the editor's demo project, with crates")
    ap.add_argument("--level", help="the level's name (default: the first)")
    ap.add_argument("--out", default=os.path.join(ROOT, "Build", "GpuWeb"))
    a = ap.parse_args(argv)
    if a.demo:
        project, level = demo_project()
    elif a.project:
        project = Project.load(a.project)
        level = project.level(a.level) if a.level else (project.levels[0] if project.levels else None)
        if level is None:
            sys.exit("export_gpu_web: no such level")
    else:
        ap.error("give a project file or --demo")
    os.makedirs(a.out, exist_ok=True)
    for name in PLAYER_FILES:
        src = os.path.join(WEB, name)
        if not os.path.exists(src):
            sys.exit("export_gpu_web: %s is missing (gpu/web is vendored from gpu-physics-engine: see GPU.md)" % src)
        shutil.copyfile(src, os.path.join(a.out, "index.html" if name == "player.html" else name))
    spirv = os.path.join(a.out, "spirv")
    shutil.rmtree(spirv, ignore_errors=True)
    os.makedirs(spirv)
    manifest = json.load(open(os.path.join(SPIRV, "manifest.json")))
    if manifest.get("_meta", {}).get("wgsl") is None:
        sys.exit("export_gpu_web: gpu/spirv has no WGSL (rebuild: gpu-physics-engine/build.py --wgsl --out gpu/spirv)")
    for name, rec in manifest.items():
        if name != "_meta":
            shutil.copyfile(os.path.join(SPIRV, rec["wgsl"]), os.path.join(spirv, rec["wgsl"]))
    # the page only needs entry points, bindings and the WGSL file names
    slim = {k: ({"wgsl": v["wgsl"], "entry_points": [{"name": e["name"], "local_size": e["local_size"], "push": [{"name": p["name"]} for p in e.get("push", [])],
                                                      "buffers": [{"binding": b["binding"], "name": b["name"]} for b in e["buffers"]]} for e in v["entry_points"]]}
                if k != "_meta" else v) for k, v in manifest.items()}
    json.dump(slim, open(os.path.join(spirv, "manifest.json"), "w"))
    data = export_level(project, level)
    json.dump(data, open(os.path.join(a.out, "level.json"), "w"), ensure_ascii=False)
    print("wrote %s: level %r %dx%d, %d tile kinds, %d files" % (a.out, level.name, level.width, level.height, len(data["tiles"]), len(os.listdir(a.out))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
