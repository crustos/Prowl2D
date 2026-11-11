# SlimeJumpGoose

![The bot playing SlimeJumpGoose](slimejump.gif)

*The bot playing the level in about 15 seconds, its scripts all Goose: it climbs the vines, swings across the gap on the lasso and reaches the goal.*

[SlimeJump](../SlimeJump) with its game logic in **Goose** — the Crust subset, lowered to C by `tools/goose2c.py` and linked into the engine library; no Goose compiler, no C++ compiler.
It is [SlimeJumpRust](../SlimeJumpRust) ported script for script: the same level, sprites, controls and scripts (`prowl_editor/slime_goose.py`):

    python3 prowl.py --demo slime-goose     # open it; press F5 (Build) in the Scripts window, then play in the viewport

Controls: arrows or A/D walk, space / up / W jump (let go early for a short hop; keep it held to climb vines), **left mouse button** shoots the blaster at the pointer,
**right mouse button** throws the lasso (it catches on walls and anchors; W / S reel in and out, A / D pump the swing, letting go of the button lets go of the rope), **T** switches the bot on and off.
What each script does is in [SlimeJumpRust's README](../SlimeJumpRust/README.md); the table of node tags and globals there holds here too, since the scripts talk the same way.

## What Goose looks like as a script

    // script(max_instances = 32)
    struct Gem {
        node: i32,
        state: i32,
        home_y: f32,
    }

    fn start(g: Gem&) { g.home_y = node_y(g.node); }

    fn fixed_update(g: Gem&) {
        let s = (get_global(21) as i32) - 1;
        if s < 0 { return; }
        ...
    }

| | Rust (`SlimeJumpRust`) | Goose |
|---|---|---|
| marks a script | `#[script(max_instances = 32)]` | the comment `// script(max_instances = 32)` on the line above the struct (Goose has no attributes, and ignores comments) |
| callbacks | methods of `impl Gem`, `&mut self` | functions whose first parameter is the struct by reference: `fn fixed_update(g: Gem&)`; the others (`on_trigger_enter_2d(g: Gem&, other: i32)`) are named the same, in snake_case |
| constants | `const DT: f32 = 0.0166;` | `let DT: f32 = 0.0166;` |
| casts | `x as i32` | `x as i32` |
| locals | `let mut a: f32 = 0.0;` | `var a: f32 = 0.0;` (a float or integer literal with nothing to give it a type is 64 bits in Goose, so `let dy: f32 = 0.0;` says what it is) |
| float arithmetic | Crust lowers a literal like `0.9` as a C `double`, so `x * 0.9` is computed in double precision | `f32` stays 32 bits, as Goose's spec says |

The engine's calls are `extern fn`s, which the build writes after the script (`tools/script_native.py`: `goose_prelude`), in the plain-C shape Goose's interop allows: `fn set_pos(node: i32, x: f32, y: f32)`, `fn node_x(node: i32) -> f32`.
Every callback the script has is an `export fn` the build writes in the same way (`goose_glue`), which keeps the script's instances in an array of its capacity and calls the callback on one of them.
The Goose is lowered to C with `goose2c --lib`, compiled with the rest, and linked into the library.

## Tests

`prowl_editor/test_goose_scripts.py` checks the language and the scanner, that an error in a script is reported at its line in the editor's problems list, that all 13 scripts lower and compile,
and that **the Goose scripts do what the Rust ones do**: both builds run under a driver that moves the nodes, presses keys and changes the globals at random, against a stub engine that logs every call it gets,
and the two logs must agree (a float to within its last digit). `SlimeJumpInGoose` in `prowl_editor/test_engine.py` builds the scripts with the editor's own Build and plays them in the viewport,
running every test of `SlimeJumpInRust` (walking and jumping, spikes, pit and worms, gems and checkpoints, climbing, the blaster, the lasso, turret arrows, crumbly platforms, and the bot playing the whole level to the goal).

The GIF is recorded from the viewport (the same engine library, bot on, camera following the slime):

    python3 build.py so
    xvfb-run -a python3 tools/slime_goose_gif.py          # writes Samples/SlimeJumpGoose/slimejump.gif
