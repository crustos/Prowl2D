# prowl.py — the dotnet-free 2D editor

PyQt5 editor (floating windows) over the engine, which is the C# runtime translated to C and loaded with ctypes.

    python3 build.py so            # builds /tmp/libprowl2d.so (+ libprowl2d.h); PROWL2D_LIB overrides the path
    python3 prowl.py [project.json] [scene.blend …] [--viewport]
    python3 prowl.py --demo slime  # Samples/SlimeJumpDestruct, played in the viewport
    python3 prowl.py --export-ascii DIR project.json
    python3 prowl.py --import-ascii [OUT.json] --sprites a.txt … --levels b.txt …   # builds the project, saves it as OUT.json, opens the editor on it
    python3 prowl.py --no-gui -o OUT.json …                                          # any of the imports without opening the editor (for scripts)
    python3 prowl.py scene.blend                     # Blender collections as sprites (see Blender, below)
    python3 prowl.py --plugin tool.py …              # your own options, importers and editor hooks (see Plugins, below)
    python3 prowl.py --selftest    # model, GUI (offscreen), engine tests; run under xvfb-run for the viewport tests

Windows: Project (File menu), Palette, Sprite editor, Level editor, Effects, Lights, and the engine's own SDL2 viewport (P play, R reset, Home fit, wheel zoom, right-drag pan).

## Importing and the command line
`--import-ascii` builds a project from ASCII-art sprites and emoji levels and **opens the editor on it** (the first imported sprite and level are selected); with `OUT.json` it also saves it
there first. Give a project too (`prowl.py game.json --import-ascii --sprites more.txt`) to add to it. With `--no-gui` it only writes the file, as it did before the editor opened. If the machine
has no display (or no PyQt5) and the project was saved, the editor is skipped with a note; if nothing was saved, prowl.py stops before doing any work and asks for `--output FILE.json`.
The positional files and the options can come in any order. `--output` / `-o` saves the project after any import, `--no-gui` skips the editor; both work with Blender files and plugins.

## Blender
Give prowl.py a `.blend` file, or a Python script that builds a scene, and each **collection** is rendered to a sprite named after it, added to the project the editor opens (a new project named after
the file, unless you give one):

    python3 prowl.py scene.blend                               # sprites in a new project, editor opens
    python3 prowl.py game.json scene.blend -o game.json --no-gui   # added to the project in game.json and saved, no editor
    python3 prowl.py --blend-script tools/examples/blender_sprites.py -o sprites.json    # the script builds the scene; no .blend is needed

Blender runs in the background: it is found on the PATH, in the usual install folders, in `$BLENDER`, or at `--blender PATH` (developed and tested with Blender 5.0; it runs with `--factory-startup`, so your
preferences and add-ons are not loaded). `tools/blender_render_collections.py` runs inside it. The rules:

- Every collection directly under the scene's collection is one sprite, with everything inside it (child collections too, collection instances too). A collection with no geometry (a "Lights" one),
  one switched off for renders or excluded from the view layer is skipped, with a note. `--blend-collections Hero,Coin*` renders only the named ones instead, at any depth (`*` and `?` match).
- The camera is orthographic and looks from `--blend-view` (`front` for a side-scroller, the default; `top` for a top-down game; also `back`, `left`, `right`, `bottom`). The background is transparent.
- All sprites share one scale, so a coin stays smaller than the hero: `--blend-size N` makes the longest side of the biggest collection N pixels (default 32), or `--blend-ppu N` fixes the pixels per
  Blender unit (one unit = one tile at `--blend-ppu 16` is 16 pixels). Each sprite is cropped to what it shows; a sprite is at most 256 pixels a side.
- The scene's own lights are used; a scene with none gets a sun and an ambient light so it is not black. `--blend-engine` is `cycles` (the default, which needs no GPU), `eevee` or `workbench`;
  `--blend-samples` sets the samples (default 16, few: the edges stay hard, like pixel art).
- Sprites use a palette, so the colours of all the renders are folded into at most `--blend-colors` (default 32, 0 for no limit) and added to the project's palette as `blender #rrggbb`.
- A script (`--blend-script`, repeatable) starts in an empty scene, not Blender's cube, and does not have to save anything. An error in it shows Blender's output.
- `--blend-keep DIR` keeps the full-size renders and `manifest.json` in DIR, to see what Blender drew.

- **Animation.** `--blend-frames` (or `--blend-frames 10:40`) renders every frame of the scene's frame range, at the scene's frame rate, as the frames of each sprite. A collection is framed once
  around everything it covers in any frame, so the frames stay aligned; one that does not move keeps a single frame. Put the files before the option, or write `--blend-frames all`.
- **Levels.** A collection whose name starts with `level` (`Level_1`, `level 2`) is a level, not a sprite. Put collection instances in it (Add > Collection Instance, or an Empty with Instancing set to
  Collection): each instanced collection is rendered as a sprite named after it, and each instance becomes a tile at its position, snapped to a grid of `--blend-cell` Blender units (default 1, so a 1 unit tile
  is one cell) with up at the top of the level. A custom property `solid` on a tile's collection makes its tiles solid. Anything in a level that is not an instance is ignored with a note; a tile off its
  cell by more than a quarter, or hidden behind another in the same cell, is reported. The tiles get emoji names like those of the Unity import. Keep the tile collections enabled for renders (excluding them hides them).
  Use `--blend-ppu` with levels (say 16): `--blend-size` sizes the biggest sprite, which would shrink the tiles next to a tall hero.

Importing again adds the sprites again (`hero`, then `hero 2`), and a level that was imported twice is `Level_1`, `Level_1 2`, each pointing at its own sprites.

### Animating with code

A `--blend-script` can animate what it builds, in the same script. `tools/prowl_blender.py` (on Blender's path for scripts) has the small things that make it easy:
`new_scene(frames, fps)`, `frames()` (steps the frames; `f.t` goes 0 to 1 over the loop), `key(ob, location, rotation, scale)`, `collection(name, layers=True)`
and `head(kind)`. The heads come from [zigzag](https://github.com/brentharts/zigzag) (MIT): Blender's Suzanne with some vertices moved (monkey, cat, dog, bear,
gorilla, alien, frog, ogre; emoji work too), so every kind has the same polygons for the same parts. A part is the polygons of one material (skin, eye, pupil,
lids, lip, teeth, ...), made an object of its own; the materials have roles (pupil, eyelids, lower lip) that say how they move. `look(x, y)`, `blink(amount)`,
`mouth(amount)` and `move(...)` keyframe them for the current frame. See `tools/examples/animated_head.py`.

A collection made with `layers=True` (`head()` does) is rendered as a sprite and so is each of its child collections, all framed alike, so the layers lie exactly
over each other in the project. A scene with more than one frame from `new_scene` renders all its frames without `--blend-frames`.

## Plugins
`--plugin FILE.py` (or a folder of `.py` files; repeatable) loads Python plugins when prowl.py starts, so a user can extend the command line without touching prowl.py. A plugin with a
`register(prowl)` function gets an object to add things to; one without is just run. `tools/examples/plugin_palette.py` uses all of it, in 40 lines:

    def register(prowl):
        prowl.add_argument("--pal-width", type=int, default=2)    # a command-line option (listed by --help)
        prowl.add_importer(".pal", import_pal)                     # prowl.py FILE.pal calls import_pal(project, path, args)
        prowl.on_project(lambda project, args: ...)                # once the project is built, before it is saved or opened
        prowl.on_gui(lambda studio, main, windows, args: ...)      # when the editor opens: add menus, select things...

An importer adds sprites and levels to the project and may return `prowl_editor.plugins.ImportResult(sprites=…, levels=…, notes=…)`; prowl.py prints it and selects what was imported.
`args` is the parsed command line, so a plugin reads its own options from it. A plugin's folder is on `sys.path`, so it can import its own helper modules and `prowl_editor` (the model: `Project`,
`Sprite`, `Level`, `asciiart`, `unity_import` ...). A plugin that fails stops prowl.py with its name; a bug in one also shows the traceback. `.json` and `.py` files cannot be given importers.

## Effects
The Effects window (Window menu) holds a level's picture effects as a stack, first to last: Add effect (grouped menu), Up / Down, Duplicate, Remove, Reset, and a check box to switch one off.
The controls of the selected effect are built from the effect registry (Native/Gfx2D/fx/*.fx, generated into prowl_editor/fxdefs.py), so a new .fx file shows up here with no GUI code:
a slider and number box per float, a color button with alpha, a combo box per enum. The viewport applies the stack live, in play mode too. Each change is an undo step
(a slider drag is one). In the project JSON a level has `"effects": [{"effect": "tint", "values": {"amount": 0.5}, "enabled": true}]`; a project naming an unknown effect or
parameter is refused with the place. The same effects run in a game: `gfx_effect(id, params, count)` (`GFX.Effect` in C#) after `gfx_draw`, on the GLES, WebGL2 and WebGPU renderers.

## Lights
The Lights window (and the Lights tool of the level editor) put up to 8 point or spot lights in a level, over an ambient color: `lights` and `lighting` in a level's JSON.
A light has a place in cells (x right, y down from the top edge), a radius in cells, an intensity, a color, and for a spot a direction, cone and edge softness. In the level editor's Lights tool,
click an empty place to add a light, drag one to move it, right-click one to remove it. The viewport lights its picture with them live (before the level's effects), and they stay
where they were put when the camera pans or zooms. Moving a light, or a slider, is one undo step.

## Scripts
The Scripts window (Window menu) is a code editor for the project's scripts. A script is one file in one language: pick C#, C++, Rust or RPython in the Language box, then New script (the file list shows `Name.cs`, `.cpp`, `.rs` or `.py`).
A class is a script when it carries its language's marker, and sprites and the game attach scripts by that class name, whatever the language:

| language | marker | callbacks (all optional) |
|---|---|---|
| C# | `[Script, MaxInstances(16)] class Name` | `Start`, `Update`, `OnCollisionBegin2D`, ... |
| C++ | `PROWL_SCRIPT(16) class Name` (an empty macro) | the same names |
| Rust | `#[script(max_instances = 16)] struct Name` with an `impl` | `start`, `update`, `on_collision_begin_2d`, ... |
| RPython | `@script(max_instances=16) class Name` | `start`, `update`, `on_collision_begin_2d`, ... |

A new script is a template with its marker and an `Update`; the editor colours, and indents (after `{`, or `:` in Python), by the file's language.

Calls the C++, Rust and RPython scripts also have, for scripts that must find each other: `set_tag(node, n)` / `get_tag(node)` (a number on a node, -1 if there is none), `node_alive(node)` and `node_slots()` (how many node slots there are to scan), `set_global(i, v)` / `get_global(i)` (256 numbers all scripts share, zero when a level starts), `set_layer`, `raycast(ox, oy, dx, dy, distance, layer_mask)` with `ray_x()` / `ray_y()` and `overlap_box(cx, cy, hw, hh, layer_mask)` to look around (layer 0 is the walls), `add_box_trigger`, `set_active`, `attach_script(node, SCRIPT_<NAME>)` for nodes a script makes, `key_down`, `mouse_down`, `mouse_world_x/y` and `math_sqrt/sin/cos/atan2`. A node that has a sprite (`add_sprite`) is drawn by the viewport wherever it is. In the viewport, a tile whose sprite has scripts is drawn where its node is (a script that moves it moves the picture) and is gone when the script destroys the node. `Samples/SlimeJumpRust` is a whole game made this way (climbing, blaster, lasso, turrets, crumbly platforms, checkpoints and a bot).

**C++, Rust and RPython are the Crust subsets**, not full languages: C++ is lowered to C by `tools/cpprust.py`, Rust by Crust (`shivyc/crust.py`), RPython by `tools/py2c.py`, and gcc compiles that C (never g++, rustc or CPython). What those front ends do not accept, Build says, at the script's line. Each script becomes an object file linked into `libprowl2d.so` beside the engine, behind a small generated C# script of the same name and capacity (`tools/script_native.py`), so the scene's calls reach it like any other script. A script reaches the engine through node handles (an int), not the C# engine's `Component` and `Node` objects:

| | C++ | Rust | RPython |
|---|---|---|---|
| the node | `int node;` | `node: i32` | `self.node: int = 0` in `__init__` |
| engine calls | `SetPos(node, x, y)`, `NodeX(node)` ... | `set_pos(..)`, `node_x(..)` ... | `set_pos(..)`, `node_x(..)` ... |
| input | `KeyDown(65)`, `MouseDown(0)`, `MouseWorldX()` | `key_down(65)`, `mouse_down(0)`, `mouse_world_x()` | `key_down(65)`, ... |
| collision, trigger | `void OnTriggerEnter2D(int other)` | `fn on_trigger_enter_2d(&mut self, other: i32)` | `def on_trigger_enter_2d(self, other: int)` |
| where a collision was | `HitX()`, `HitY()`, `HitNX()`, `HitNY()`, `HitImpulse()` | `hit_x()` ... | `hit_x()` ... |

The engine calls are the `public static` functions of `Native/Engine2D/Engine.cs` (the same ones `p2d_*` exports), without the host's own (`Init`, `Step`, `Draw`, `Camera`, ...). The scripts' instances live in a pool of the script's capacity; a recycled one starts again from zero (RPython: `__init__` runs when the script is attached and again after a recycle; annotate its fields, `self.x: float = 0.0`, which is what gives them C types).

Build (F5) builds all four languages. `tools/script_langs.py` first checks the other languages' files (the same step runs under `python3 tools/prowl2d_so.py --scripts DIR`, which tells languages apart by the file's extension): a capacity that is not an integer literal of at least 1, a marker with no class after it, a script without its `node` field, a callback that would never be called (not `void`, not public, no `&mut self` or `self`, a lifecycle callback with parameters, a collision callback without `other`), or two scripts of one name (across all languages: sprites and the game attach by name) is an error at its line. What the front ends say (`cpprust:`, Crust's, py2c's) is read into the same problems list, colour codes and all; an error the C compiler gives on the C a front end wrote has no place, because that line is not the script's.

## Project JSON
`{"format":"prowl2d-project","version":1, palette, sprites, tiles, levels}`. Scripts are `"scripts": [{"name": "Spinner", "text": "...", "language": "cpp"}]` (`language` is `csharp` when left out, and is one of `csharp`, `cpp`, `rust`, `rpython`); a project with a script in a language other than C# is written as `"version":2`, so that an editor without languages refuses it instead of reading a Rust script as C#. Sprite frames are rows of palette key letters; `.` is index 0 (transparent).
Recolouring an index recolours every pixel that uses it, so scripts animate by changing one palette entry.

## Sprite ASCII
    # sprite: coin
    # fps: 6
    # palette: Y=#ffd23c O=#e08a1e
    .YY.
    YOOY
    (blank line between frames)
Unknown letters on import are mapped to colours in a dialog (or guessed).

## Level emoji
    # level: first steps
    # empty: ⬛
    # 🧱 = brick (solid) -> brick
    ⬛⬛🪙⬛
    🧱🧱🧱🧱
Emoji names come from Unicode (🧱 → "brick") and link to the sprite with the same name; view as emoji or sprites.

Tiles can be `solid` (static collider), `dynamic` (a movable body, like a crate) and `diggable` (a blast removes it, like dirt); the emoji legend writes them as `# 📦 = crate (dynamic) -> crate`. In the viewport's play mode a click drops a ball and B blasts at the pointer.

Not yet: Unity scene import, generating the player's C#/C from the GUI, WASM window.
