#!/usr/bin/env python3
"""prowl.py -- the Prowl2D 2D editor (PyQt5). No .NET: the engine is libprowl2d.so (the C# runtime translated to C), called through ctypes.

    python3 prowl.py [project.json] [scene.blend ...]    open the editor (a demo project if none is given); a .blend file is rendered to sprites, one per collection (and levels, from collections named Level_*), and added to the project
    python3 prowl.py --blend-script make_scene.py        the same for a Blender Python script that builds a scene (--blender PATH, --blend-view, --blend-size, --blend-collections ...; see --help)
    python3 prowl.py --plugin tool.py [--plugin DIR]     load Python plugins: they add command-line options, importers for other file types, and hooks on the project and the editor (prowl_editor/plugins.py)
    python3 prowl.py --demo slime          open Samples/SlimeJumpDestruct as a project and play it in the viewport (the dirt wall is dug, crates burst)
    python3 prowl.py --demo slime-rust     open SlimeJump with its game logic in Rust scripts (Samples/SlimeJumpRust): press F5 to build them, then play (arrows or A/D, space, mouse: blaster and lasso, T: the bot)
    python3 prowl.py --viewport [...]      also open the engine's SDL2 window on the first level
    python3 prowl.py --export-ascii DIR project.json     no GUI: write the project's sprites and levels as ASCII art / emoji text into DIR
    python3 prowl.py --import-ascii [OUT.json] [--sprites A.txt ...] [--levels B.txt ...]    build a project from ASCII art and emoji levels, save it as OUT.json and open it in the editor
    python3 prowl.py --no-gui [--output OUT.json] ...    do the imports and save the project without opening the editor (what a script wants)
    python3 prowl.py --import-unity OUT.json --unity DIR [DIR|FILE.png ...] [--cell N] [--no-scenes]    no GUI: import the 2D sprites (PNGs, sprite sheets) and scenes (as levels) of a Unity project into OUT.json
    python3 prowl.py --selftest            run the tests (the model and text formats, then the GUI windows if PyQt5 is installed)
    python3 prowl.py --screenshots DIR     draw every window to a PNG in DIR (works without a display) and exit
    python3 prowl.py --quit-after SECONDS  close the editor by itself after a while, as if the user quit (for smoke tests)

The editor is several floating windows (project / palette / sprite editor / level editor); the viewport is the engine's own window. Build the engine once:

    python3 tools/prowl2d_so.py            -> /tmp/libprowl2d.so   (set PROWL2D_LIB to use another path)

Sand: the Sand window (or S in the viewport) switches on the GPU sand (compute shaders): the left mouse button paints sand, water or stone (keys 1 2 3, 0 erases, [ ] brush,
Space pauses, C clears), and the level's solid tiles are stone to it. It needs OpenGL ES 3.1 with compute (Mesa's software GL has it).

Scripts: the Scripts window is a small code editor for the project's scripts (C#, C++, Rust or RPython, picked next to New script; saved in the project file). Mark a class
[Script, MaxInstances(N)] with `public Component Self;` and callbacks (Update, OnCollisionBegin2D ...), tick it for a sprite (it runs on every tile showing that sprite) or for the
game (once per play), and press F5: the scripts are translated to C with the engine (needs the .NET SDK, about a minute), a new engine library is linked, the viewport's window
closes and opens again on it. Errors come back with their line. Scripts read keys and the mouse with Input2D (Native/Engine2D/Input2D.cs). Only the C# subset builds
(tools/ccsharp/README.md); the C++, Rust and RPython scripts are lowered to C by Crust's front ends and linked in too (tools/script_native.py; EDITOR.md, Scripts).

Without it everything but the viewport works. Sprites are indexed-palette pixel art (a letter per colour); levels are grids of emoji tiles, which an
exported level shows as text. See prowl_editor/asciiart.py for both formats.
"""
import argparse
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def load_project(path, demo=None):
    from prowl_editor.model import Project
    from prowl_editor.demo import make_demo_project
    if path:
        return Project.load(path)
    if demo == "slime":
        from prowl_editor.slime_demo import make_slime_project
        return make_slime_project()
    if demo == "slime-rust":
        from prowl_editor.slime_rust import make_slime_rust_project
        return make_slime_rust_project()
    return make_demo_project()


def cmd_export_ascii(out_dir, path):
    from prowl_editor.fileio import export_folder
    p = load_project(path)
    n = export_folder(p, out_dir)
    print("wrote %d file(s) to %s (%d sprites, %d levels)" % (n, out_dir, len(p.sprites), len(p.levels)))
    return 0


def import_ascii(p, sprites, levels, imported):
    """Adds the ASCII art sprites and emoji levels of the text files to project `p`; the Sprites and Levels made go on the list `imported` (sprites, levels)."""
    from prowl_editor import asciiart, fileio
    for path in sprites:
        text = fileio.name_first_sprite(fileio.read_text(path), fileio.stem(path))
        made, added = asciiart.import_sprites(text, p)
        imported[0].extend(made)
        print("sprites %s from %s%s" % (", ".join(s.name for s in made), path, "  (new palette keys: %s)" % " ".join(added) if added else ""))
    for path in levels:
        made, new = asciiart.import_levels(fileio.read_text(path), p, fileio.stem(path))
        imported[1].extend(made)
        print("levels %s from %s%s" % (", ".join(l.name for l in made), path, "  (new tiles: %s)" % " ".join(t.emoji for t in new) if new else ""))


def cmd_import_unity(out_json, roots, scenes=True, cell=None):
    from prowl_editor import fileio
    from prowl_editor.model import Project
    from prowl_editor.unity_scene import import_unity_project
    if not roots:
        print("--import-unity needs --unity DIR (a Unity project folder, any folder of PNGs, or a PNG)", file=sys.stderr)
        return 2
    p = Project.load(out_json) if os.path.exists(out_json) else Project(fileio.stem(out_json))      # an existing project is added to
    for root in roots:
        report = import_unity_project(p, root, scenes=scenes, cell=cell)
        print("%s: %s" % (root, report.summary()))
        for note in report.notes:
            print("  note:", note)
    p.save(out_json)
    print("wrote", out_json)
    return 0


def cmd_selftest():
    import unittest
    names = ["prowl_editor.test_core", "prowl_editor.test_cli", "prowl_editor.test_gpu_physics"]
    try:
        import PyQt5  # noqa: F401
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        names.append("prowl_editor.test_gui")
        names.append("prowl_editor.test_engine")
    except ImportError:
        print("(PyQt5 is not installed: only the model and text-format tests run)")
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def make_app(argv):
    from PyQt5 import QtWidgets
    from prowl_editor import gui
    app = QtWidgets.QApplication(argv)
    return app, gui


def cmd_screenshots(out_dir, project_path, demo=None):
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app, gui = make_app(sys.argv[:1])
    studio = gui.Studio(load_project(project_path, demo))
    main, windows = gui.create_windows(studio)
    os.makedirs(out_dir, exist_ok=True)
    shots = [("project", main)] + [(k, w) for k, w in windows.items()]
    for _, w in shots:
        w.show()
    studio.select_tile(next(iter(studio.project.tiles), None))      # a project of imported sprites has no tiles yet
    for _ in range(5):
        app.processEvents()
    for name, w in shots:
        path = os.path.join(out_dir, "%s.png" % name)
        w.grab().save(path)
        print("wrote", path)
    # the level editor again, as emoji
    windows["levels"].canvas.view = "emoji"
    windows["levels"].canvas.update()
    app.processEvents()
    path = os.path.join(out_dir, "levels_emoji.png")
    windows["levels"].grab().save(path)
    print("wrote", path)
    return 0


def cmd_gui(project, open_viewport, quit_after=None, demo=None, imported=None, api=None, args=None):
    """Opens the editor on `project`. `imported` is (sprites, levels) just imported into it: the first of each is selected. `api` and `args` are the plugins'
    interface and the parsed command line, for the plugins' GUI hooks."""
    app, gui = make_app(sys.argv[:1])
    studio = gui.Studio(project)
    main, windows = gui.create_windows(studio)
    gui.tile_windows(main, windows)
    main.show()
    for w in windows.values():
        w.show()
    if imported and imported[0]:
        studio.select_sprite(imported[0][0])
    if imported and imported[1]:
        studio.select_level(imported[1][0])
    if api is not None:
        api.run_gui_hooks(studio, main, windows, args)
    if args is not None and getattr(args, "gpu_physics", None):
        vc = main.viewport
        vc.gpu_backend, vc.gpu_scripts, vc.gpu_kernel_dir = args.gpu_physics, list(args.gpu_script), args.gpu_kernels
        main.gpu_action.setChecked(True)
    from PyQt5 import QtCore
    if demo == "slime":                          # show the slime's sprite (and its blinking eyes) and the dirt tile in the editors
        studio.select_sprite(next(sp for sp in studio.project.sprites if sp.name == "slime"))
        studio.select_tile(next(k for k, t in studio.project.tiles.items() if t.name == "dirt"))
    if demo == "slime":                          # SlimeJumpDestruct: the viewport plays it with a stand-in for the sample's bot
        from prowl_editor.slime_demo import SlimeDriver
        main.viewport.driver_factory = SlimeDriver
        main.viewport.autoplay = True
    if open_viewport or demo == "slime":
        QtCore.QTimer.singleShot(200, main.viewport.open)
    if quit_after:
        QtCore.QTimer.singleShot(int(quit_after * 1000), main.close)
    return app.exec_()


def can_open_gui():
    """False when Qt would have no screen to open the editor on (a Linux machine with no display), or PyQt5 is missing."""
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("QT_QPA_PLATFORM")):
        return False
    try:
        import PyQt5  # noqa: F401
    except ImportError:
        return False
    return True


def split_inputs(inputs, api):
    """The positional files: (the project to open or None, [the files to import]). A .blend (or whatever a plugin imports) is imported; anything else is the project."""
    from prowl_editor.model import ProjectError
    project, imports = None, []
    for path in inputs:
        if api.importer_for(path):
            imports.append(path)
        elif path.lower().endswith(".py"):
            raise ProjectError("%s: a .py file is a plugin (--plugin %s) or, to make sprites from a Blender script, --blend-script %s" % (path, path, path))
        elif project is not None:
            raise ProjectError("only one project can be opened (%s and %s); other files must be %s" % (project, path, ", ".join(api.extensions()) or "imports"))
        else:
            project = path
    return project, imports


def cmd_open(a, api):
    """The default command: build the project (the project file or demo, plus everything given on the command line to import into it), save it if asked,
    and open the editor on it."""
    from prowl_editor import fileio
    from prowl_editor.model import Project, ProjectError
    project_path, imports = split_inputs(a.inputs, api)
    ascii_given = a.import_ascii is not None
    importing = bool(ascii_given or imports or a.blend_script)
    output = a.output or (a.import_ascii if ascii_given and a.import_ascii else None)
    want_gui = not a.no_gui
    if want_gui and not can_open_gui():
        if importing and not output:
            print("prowl.py: the editor cannot open here (no display, or PyQt5 is not installed) and the imported project would be lost: add --output FILE.json", file=sys.stderr)
            return 2
        print("(the editor cannot open here: no display, or PyQt5 is not installed)")
        want_gui = False
    if project_path or a.demo or not importing:
        project = load_project(project_path, a.demo)
    else:                                                  # imports into a project of their own, not into the demo
        project = Project(fileio.stem(output or (imports or a.blend_script or ["untitled"])[0]))
    imported = ([], [])                                    # the sprites and levels the imports made
    if ascii_given:
        import_ascii(project, a.sprites, a.levels, imported)
    for path in imports:
        report = api.run_importer(path, project, a)
        report_import(path, report, imported)
    if a.blend_script:
        from prowl_editor import blender_import
        for script in a.blend_script:
            report = blender_import.import_blend_script(project, script, blender_import.Options.from_args(a), blender_import._say)
            report_import(script, report, imported)
    from prowl_editor import emoji_faces
    imported[0].extend(emoji_faces.make_face_sprites(project, emoji_faces.Options.from_args(a), blender_import_say))        # the heads of `face` tiles, on their bodies
    api.run_project_hooks(project, a)
    if output:
        project.save(output)
        print("wrote", output)
    elif importing and not want_gui:
        print("(not saved: add --output FILE.json)")
    if not want_gui:
        return 0
    return cmd_gui(project, a.viewport, a.quit_after, a.demo, imported, api, a)


def blender_import_say(line):
    print("  faces: " + line, flush=True)


def report_import(path, report, imported):
    """Tells what an importer made (its return value: anything with .sprites, .levels and .notes lists, or None) and records it in `imported`."""
    if report is None:
        return
    sprites, levels = list(getattr(report, "sprites", None) or []), list(getattr(report, "levels", None) or [])
    imported[0].extend(sprites)
    imported[1].extend(levels)
    summary = report.summary() if hasattr(report, "summary") else "%d sprite(s), %d level(s)" % (len(sprites), len(levels))
    print("%s: %s" % (path, summary))
    for note in getattr(report, "notes", None) or []:
        print("  note:", note)


def build_parser(api):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", metavar="FILE", help="a project .json (default: the demo project) and/or files to import into it: .blend%s" % "".join(", " + e for e in api.extensions() if e != ".blend"))
    ap.add_argument("--plugin", action="append", default=[], metavar="FILE.py|DIR", help="load a Python plugin (a file, or the .py files of a folder); repeatable. See prowl_editor/plugins.py")
    ap.add_argument("--output", "-o", metavar="OUT.json", help="save the project here after importing (the editor still opens on it)")
    ap.add_argument("--no-gui", action="store_true", help="do the imports (and --output) and exit without opening the editor")
    ap.add_argument("--demo", choices=["coins", "slime", "slime-rust"], help="open a built-in project: 'slime' is Samples/SlimeJumpDestruct, played in the viewport; 'slime-rust' is SlimeJump in Rust (press F5 to build it)")
    ap.add_argument("--viewport", action="store_true", help="also open the engine's SDL2 window")
    ap.add_argument("--export-ascii", metavar="DIR", help="no GUI: write sprites/ and levels/ text files of the project into DIR")
    ap.add_argument("--import-ascii", nargs="?", const="", metavar="OUT.json", help="build a project from --sprites and --levels text files (added to the project given, if any), save it as OUT.json (if given) and open it in the editor; --no-gui only writes the file")
    ap.add_argument("--import-unity", metavar="OUT.json", help="no GUI: import the 2D sprites and scenes of the --unity folders (or PNG files) into OUT.json (added to it if it exists)")
    ap.add_argument("--cell", type=float, metavar="UNITS", help="with --import-unity: the grid cell for scenes, in world units (default: the size of the most common sprite)")
    ap.add_argument("--no-scenes", action="store_true", help="with --import-unity: import the sprites only, no levels from scenes")
    ap.add_argument("--unity", nargs="*", default=[], metavar="DIR", help="a Unity project folder, any folder of PNGs, or a PNG file")
    ap.add_argument("--sprites", nargs="*", default=[], metavar="FILE.txt")
    ap.add_argument("--levels", nargs="*", default=[], metavar="FILE.txt")
    ap.add_argument("--gpu-physics", nargs="?", const="auto", choices=["auto", "wgpu", "interp"], metavar="BACKEND",
                    help="play levels on the GPU physics engine (circles/particles from crustos/gpu-physics-engine, kernels compiled by Crust to SPIR-V) instead of Box2D for the balls; BACKEND: auto (wgpu, else the slow reference interpreter), wgpu, interp. See GPU.md")
    ap.add_argument("--gpu-script", action="append", default=[], metavar="FILE.cs", help="with --gpu-physics: a C# [GpuKernel] script run on the GPU on every ball each step; repeatable")
    ap.add_argument("--gpu-kernels", metavar="DIR", help="with --gpu-physics: the compiled kernels (default gpu/spirv, or $PROWL_GPU_KERNELS)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--screenshots", metavar="DIR")
    ap.add_argument("--quit-after", type=float, metavar="SECONDS", help=argparse.SUPPRESS)
    api.apply_arguments(ap)                                  # the Blender options and the plugins' own
    return ap


def main():
    from prowl_editor import blender_import, emoji_faces, plugins
    from prowl_editor.model import ProjectError
    try:
        pre = argparse.ArgumentParser(add_help=False, allow_abbrev=False)          # the plugins are loaded first: they add options the real parse needs
        pre.add_argument("--plugin", action="append", default=[])
        api = plugins.Prowl(ROOT)
        blender_import.register(api)
        emoji_faces.register(api)
        plugins.load_plugins(pre.parse_known_args()[0].plugin, api)
        a = build_parser(api).parse_intermixed_args()          # files and options in any order
        if a.selftest:
            return cmd_selftest()
        if a.export_ascii:
            return cmd_export_ascii(a.export_ascii, a.inputs[0] if a.inputs else None)
        if a.import_unity:
            return cmd_import_unity(a.import_unity, a.unity, not a.no_scenes, a.cell)
        if a.screenshots:
            return cmd_screenshots(a.screenshots, a.inputs[0] if a.inputs else None, a.demo)
        return cmd_open(a, api)
    except Exception as e:                        # a bad file is a message, not a traceback
        if isinstance(e, (ProjectError, OSError)):
            print("prowl.py: %s" % e, file=sys.stderr)
            if getattr(e, "unexpected", False) and e.__cause__ is not None:        # a bug in a plugin: its traceback is what its author needs
                traceback.print_exception(type(e.__cause__), e.__cause__, e.__cause__.__traceback__)
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main())
