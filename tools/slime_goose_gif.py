#!/usr/bin/env python3
"""slime_goose_gif.py -- record an animated GIF of the bot playing SlimeJumpGoose in the editor's viewport.

    xvfb-run -a python3 tools/slime_goose_gif.py [-o Samples/SlimeJumpGoose/slimejump.gif] [--every 4] [--scale 0.5] [--rust]

Needs libprowl2d.so (python3 build.py so) and Pillow. It builds the project's scripts as the editor's Build does, presses the bot key (global 6), follows the slime
with the camera and keeps every Nth rendered frame (the renderer's gfx_save_frame), until the goal is reached or a minute of game time has passed."""
import argparse, os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image
from prowl_editor import scriptbuild
from prowl_editor.engine import Engine, Viewport, find_library


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "Samples", "SlimeJumpGoose", "slimejump.gif"))
    ap.add_argument("--every", type=int, default=4, help="keep every Nth frame (60 frames a second of game time)")
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--rust", action="store_true", help="record SlimeJumpRust instead")
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--height", type=int, default=480)
    a = ap.parse_args()
    if find_library() is None:
        sys.exit("libprowl2d.so is not built (python3 build.py so)")
    if a.rust:
        from prowl_editor.slime_rust import make_slime_rust_project as make
    else:
        from prowl_editor.slime_goose import make_slime_goose_project as make
    work = tempfile.mkdtemp(prefix="slimegif_")
    frames_dir = os.path.join(work, "frames")
    os.makedirs(frames_dir)
    project = make()
    result = scriptbuild.Builder(os.path.join(work, "build")).build(project)
    if not result.ok:
        sys.exit("the scripts did not build: " + "; ".join(str(d) for d in result.diagnostics))
    engine = Engine(result.lib)
    engine.start(a.width, a.height)
    vp = Viewport(engine, project, a.width, a.height)
    vp.show_level(project.levels[0])
    vp.open()
    vp.toggle_play()
    lib = engine.lib
    node = lambda tag: next((n for n in range(lib.p2d_node_slots()) if lib.p2d_get_tag(n) == tag), None)
    for _ in range(30):
        vp.tick(1 / 60.0)
    lib.p2d_set_global(6, 1.0)                                                         # the T key: the bot plays
    slime = node(1)
    goal = next((n for n in range(lib.p2d_node_slots()) if lib.p2d_get_tag(n) == 99 or (lib.p2d_node_alive(n) and abs(lib.p2d_node_x(n) - 80.5) < 0.6 and abs(lib.p2d_node_y(n) - 12.5) < 0.6)), None)
    vp.half = 6.0
    kept = 0
    cwd = os.getcwd()
    os.chdir(frames_dir)
    try:
        for frame in range(60 * 60):
            s = node(1)
            if s is not None:
                tx, ty = lib.p2d_node_x(s), lib.p2d_node_y(s)
                vp.cx += (tx - vp.cx) * 0.15
                vp.cy += (ty + 1.0 - vp.cy) * 0.15
            vp.tick(1 / 60.0)
            if frame % a.every == 0:
                if lib.gfx_save_frame(kept):
                    kept += 1
            if goal is not None and lib.p2d_get_tag(goal) == 99:
                for extra in range(60):                                                # a moment on the goal
                    vp.tick(1 / 60.0)
                    if extra % a.every == 0 and lib.gfx_save_frame(kept):
                        kept += 1
                break
    finally:
        os.chdir(cwd)
    vp.close()
    imgs = []
    for i in range(kept):
        im = Image.open(os.path.join(frames_dir, "frame_%04d.ppm" % i)).convert("RGB")
        if a.scale != 1.0:
            im = im.resize((int(im.width * a.scale), int(im.height * a.scale)), Image.LANCZOS)
        imgs.append(im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))
    ms = int(round(1000.0 * a.every / 60.0))
    imgs[0].save(a.out, save_all=True, append_images=imgs[1:], duration=ms, loop=0, optimize=True, disposal=1)
    print("%s: %d frames, %.1f s, %d KiB" % (a.out, len(imgs), len(imgs) * ms / 1000.0, os.path.getsize(a.out) // 1024))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
