"""blender.py: export a Level to a Blender .blend of grease pencil objects.

    levelang export-blender level.lvl                        ->  /tmp/levelang-preview.blend
    levelang export-blender level.lvl -o shot.blend --blender /opt/blender/blender

The level is turned into a scene description here (blender_scene.py: every SVG read by our own parser, the bot's route and the camera worked out like the GIF preview), written as JSON, and
handed to Blender running headless (`blender -b --python blender_import.py`), which builds the grease pencil objects, the animation and the camera and saves the .blend. Open it, change what
you like, and render it at any resolution: the default settings are made to look right as they are (orthographic camera on the bot, flat colours, 24 fps, mp4 output).
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from . import blender_scene

DEFAULT_OUT = "/tmp/levelang-preview.blend" if os.name == "posix" else os.path.join(tempfile.gettempdir(), "levelang-preview.blend")
IMPORT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_import.py")
MIN_VERSION = (4, 3)            # grease pencil v3


class BlenderError(RuntimeError):
    pass


def _candidates():
    yield os.environ.get("BLENDER")
    yield shutil.which("blender")
    yield "/Applications/Blender.app/Contents/MacOS/Blender"
    yield "/usr/local/bin/blender"
    for pattern in ("C:/Program Files/Blender Foundation/Blender */blender.exe", "C:/Program Files (x86)/Blender Foundation/Blender */blender.exe",
                    os.path.expanduser("~/blender*/blender"), os.path.expanduser("~/Applications/blender*/blender"), "/opt/blender*/blender", "/snap/bin/blender",
                    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender"),
                    os.path.expanduser("~/.steam/steam/steamapps/common/Blender/blender")):
        for p in sorted(glob.glob(pattern), reverse=True):
            yield p


def find_blender(explicit: str | None = None) -> str | None:
    """The Blender executable to run: the one asked for, $BLENDER, `blender` on the PATH, then the usual install places. None when there is none."""
    if explicit:
        path = shutil.which(explicit) or explicit
        if not os.path.exists(path):
            raise BlenderError("no Blender at %s" % explicit)
        return path
    for c in _candidates():
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def blender_version(exe: str):
    """(major, minor) of an executable, or None if it will not say."""
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return None
    m = re.search(r"Blender\s+(\d+)\.(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def have_bpy() -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec("bpy") is not None
    except Exception:
        return False


def export_blender(level, out: str = DEFAULT_OUT, *, blender: str | None = None, name: str = "levelang", res=(1280, 800), fps: int = 24, view=(32, 20),
                   samples: int = 16, video: str = "mp4", play: bool = True, keep_scene: str | None = None, log=print, timeout: int = 1800) -> dict:
    """Build the .blend. Returns {"path", "frames", "seconds", "objects", ...}. Raises BlenderError when Blender cannot be run or fails."""
    scene = blender_scene.build(level, name=name, fps=fps, view=view, play=play, warn=lambda m: log(m))
    exe = find_blender(blender)
    cmd_prefix = None
    if exe:
        v = blender_version(exe)
        if v is not None and v < MIN_VERSION:
            raise BlenderError("Blender %d.%d is too old: grease pencil v3 needs %d.%d or newer" % (v + MIN_VERSION))
        cmd_prefix = [exe, "-b", "--factory-startup", "--python-exit-code", "1", "--python", IMPORT_SCRIPT, "--"]
    elif have_bpy():
        cmd_prefix = [sys.executable, IMPORT_SCRIPT, "--"]
        log("levelang: no Blender executable found; using the `bpy` Python module")
    else:
        raise BlenderError("Blender not found. Install Blender %d.%d+ and put it on the PATH (or set $BLENDER, or pass --blender PATH)." % MIN_VERSION)
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="levelang-") as tmp:
        scene_path = keep_scene or os.path.join(tmp, "scene.json")
        with open(scene_path, "w", encoding="utf-8") as f:
            json.dump(scene, f, separators=(",", ":"))
        cmd = cmd_prefix + [scene_path, out, "--res", "%dx%d" % tuple(res), "--samples", str(samples), "--video", video]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BlenderError("Blender did not finish in %d seconds" % timeout)
        if proc.returncode != 0 or not os.path.exists(out):
            tail = "\n".join((proc.stdout + "\n" + proc.stderr).strip().splitlines()[-25:])
            raise BlenderError("Blender failed (exit %s):\n%s" % (proc.returncode, tail))
    return {
        "path": out, "frames": int(round(scene["duration"] * fps)) + 1, "seconds": scene["duration"], "fps": fps,
        "objects": len(scene["objects"]) + len(scene["statics"]) + (1 if scene["bot"] else 0), "sprites": len(scene["sprites"]),
        "strokes": sum(len(l["strokes"]) for s in scene["statics"] for l in s["layers"]) + sum(len(sp["strokes"]) for sp in scene["sprites"].values()),
        "notes": scene["notes"],
    }
