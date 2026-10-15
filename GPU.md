# GPU physics in Prowl2D

An alternative to Box2D-Packed for the balls in play mode, built on
[gpu-physics-engine](https://github.com/crustos/gpu-physics-engine) (circle solver: grid, radix sort,
collision cells, coloured solver) whose compute shaders are written in Rust and compiled to SPIR-V by
[Crust](https://github.com/brentharts/crust). User scripts in a C# subset run on the GPU as well.

    python3 prowl.py --gpu-physics --viewport           # or the Physics menu > GPU physics
    python3 prowl.py --gpu-physics=wgpu --gpu-script gpu/scripts/Magnet.cs --viewport

Options: `--gpu-physics[=auto|wgpu|interp]`, `--gpu-script FILE.cs` (repeatable), `--gpu-kernels DIR`
(default `gpu/spirv`, or `$PROWL_GPU_KERNELS`). Write `--gpu-physics=auto` (with `=`) when a project file
follows on the command line. In the editor: **Physics > GPU physics** and **Physics > Add GPU script**;
the change restarts a level that is being played.

## Needs

* `pip install wgpu==0.32.0` and a Vulkan/Metal/D3D12 driver for the `wgpu` backend.
* Crust (`$CRUST_DIR`, `../crust`, `./crust` or `~/crust`): reads kernel interfaces, compiles scripts, and
  provides the `interp` backend (a reference interpreter: correct but about a second per step, for tests).
* Without a GPU or kernels the viewport says so in its status line and keeps the Box2D balls.

The kernels in `gpu/spirv` are prebuilt (params in a storage buffer, so no push-constant feature is needed).
Rebuild with `python3 gpu-physics-engine/build.py --wgsl --out gpu/spirv --crust ../crust` (`--wgsl` also writes the WGSL a browser needs, and implies `--push-buffer`;
it needs `naga`: `cargo install naga-cli --locked`).

## What runs where

| | GPU | stays on Box2D |
|---|---|---|
| balls | dropped by a click | - |
| crates (movable tiles) | rigid clusters of circles, drawn rotated | crates with a script attached |
| shards | a shattered crate's pieces, expire after 2.5 s | - |
| blasts | push GPU circles too (Box2D bodies as before) | - |
| sand | particles: hold **F**, click or drag; 100s of grains | the native cellular sand (**S**) is unchanged |
| ropes, joints | `world.add_rope`, `add_joint`, `pin` | joints a script makes through the engine |
| ray casts | `world.raycast(_many)` against tiles and circles | `p2d_` ray casts of scripts |
| sensors | `world.add_sensor`, counts + enter/exit events | contact callbacks of Box2D bodies |
| level | the solid tiles, re-read after digging | - |
| per-body material, filters | `driver.set_material / set_collision_filter / set_is_trigger` (friction, bounciness, density, gravity scale, drag, categories) | - |
| anything else | - | polygons other than boxes, script-made bodies, sprites, the engine's own scripts |

The two worlds do not collide with each other. This is a hybrid: the GPU engine has only circles,
so everything above is built from circles.

* **Crates** are a grid of circles (at least 2 x 2) held by stiff distance joints. They are rounded at
  the corners, tumble and stack through circle collisions, and have no separate torque model.
* **Joints** are distance constraints between two circles or a circle and a fixed point: rigid, rope
  (only when stretched) or strut (only when squeezed); stiffness below 1 is a spring. Circles of one
  body never collide with each other. They are solved in colour batches, `iterations` rounds a step.
* **Ray casts**: a batch of rays against the tile grid (exact grid walk) and every circle; a hit says
  where, the normal, tile or circle, and the body id. `ignore_body` lets a crate's own ray through.
* **Sensors**: boxes or circles that count the circles inside them (optionally only some tags); changes
  land in `world.events` as `(sensor, count, previous count)`.
* **Sand**: tag-1 circles with their own damping; tiles remove part of their sliding speed (`friction`)
  and of the speed they bounce off with (`bounce_loss`).

Ropes and sensors are used through the driver's `world` (`Magnet`-style scripts do not see them yet):

    w = viewport.driver.world
    w.add_rope(3, 8, 7, 8, segments=12)            # pinned at its first end
    sid = w.add_sensor(10, 2, 1, 1, tags=(0,))      # counts balls in a box
    hit = w.raycast(5, 9, 0, -1)                    # Hit(t, x, y, nx, ny, kind, index, body) or None

* **Material and filtering** (kernels `prowl_material`; rebuild `gpu/spirv` with the gpu-physics-engine to get them, older
  folders just leave these calls returning False): Unity's friction (0.4) and bounciness, density, gravity scale and
  linear drag per body; Box2D's category / mask / group filter; trigger bodies that pass through circles. Friction
  between circles is the geometric mean, bounciness the larger. The first call switches the world to this path;
  worlds that never call it step as before. Joints between bodies (revolute, prismatic, wheel, ...), contact
  begin/end events, ball spin and polygons are in the C runtime of gpu-physics-engine (`gpuphys.c`) and are **not** in this
  Python host yet: they run on the CPU there, so a port would be a second solver.

## In the browser

    python3 tools/export_gpu_web.py --demo --out Build/GpuWeb            # or: export_gpu_web.py MyGame.json --level "first steps"
    python3 -m http.server -d Build/GpuWeb                              # open http://localhost:8000

`export_gpu_web.py` writes a page that plays a level on the engine, in the browser: `level.json` (the cells, the tiles that are used with their solid / movable /
diggable flags, and their sprites as PNGs), the player (`gpu/web/player.js`, Canvas 2D) and the engine in two forms:

* **WebAssembly** (`gpuphys.wasm`): the engine's whole C runtime on the CPU: crates, polygons, joints, contact events, material, filters, ray casts.
* **WebGPU** (`gpuphys_webgpu.js` and `spirv/*.wgsl`): the circle pipeline of this folder's Python host, in JavaScript, on the GPU: thousands of grains.

The page uses WebGPU where the browser has it and WebAssembly where it does not; `?engine=wasm` or `?engine=webgpu` force one. Click drops a ball, **B** a crate, hold **F**
and drag (or the sand tool) for sand, **T** hangs a rope, right click blasts (diggable tiles go, crates shatter into shards), **R** restarts. It plays what the Python
driver plays (crates from movable tiles, shards, balls, sand, ropes, blasts that dig) and not what runs on Box2D: scripts, sprites of the engine, the editor.

`gpu/web` holds the engine's files, copied from gpu-physics-engine: `runtime/wasm/gpuphys.js`, `runtime/wasm/dist/gpuphys.wasm` (build it with `runtime/wasm/build.py`) and
`web/gpuphys_webgpu.js`. `python3 tools/gpu_web_test.py` exports the demo level and plays it on both engines in headless Chromium (WebGPU on SwiftShader: slow, but the real API with the
real WGSL): the crates become crates and land, balls and sand fall and rest, a blast digs. `--shot DIR` keeps the pictures. Headless Chromium on software Vulkan loses the WebGPU device
when a canvas is presented, so the test reads the Canvas 2D page, which draws from the engine's snapshot; the WebGPU engine itself is driven the same way.

## Input

GPU code cannot call `Input2D`. Each step the driver copies keyboard and mouse (what `p2d_set_key` /
`p2d_set_mouse` fed `Input2D`) into one 520-word buffer (`gpuinput.py` has the layout): 512 key words (Input2D key
codes), button mask, mouse x/y in world units, frame, dt, time, count. A script that mentions `Input2D` reads it.

## C# GPU scripts

    [GpuKernel]
    public class Magnet {
        public float Strength = 30f;                       // tunable: GpuScript.params["Strength"]
        public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) {
            if (Input2D.MouseDown(0)) {
                vx += (Input2D.MouseX - x) * Strength * dt;
                vy += (Input2D.MouseY - y) * Strength * dt;
            }
        }
    }

`Update` runs once per ball, in parallel, before the physics step. In scope: `i`, `tag`, `x y vx vy` (world
units, per second; changes are kept), `dt time count WorldWidth WorldHeight`, and the fields. Supported:
`float/int/uint/bool` locals, arithmetic and comparisons, `if/else`, `while`, `for (init; cond; i++)`, casts,
`Mathf.Sqrt/Abs/Min/Max/Clamp/Floor/Sin/Cos`, `Input2D.Key/MouseDown/MouseX/MouseY` and the key constants.
Not supported: `return` in Update (use if/else), `?:`, `continue` in `for`, arrays, other methods or classes.
Write float literals as floats (`2f`): the kernel language does not mix int and float.
The class is translated to a Rust kernel (`GpuScript.rust` shows it) and compiled by Crust; compile errors show up in the
viewport's script report. (This is a small purpose-built translator, not the CCSharp path, which needs the .NET SDK.)

## Status

Verified on Crust's reference interpreter (`prowl_editor/test_gpu_physics.py`, part of `--selftest`). The wgpu
backend is written against wgpu-py 0.32 but has **not been run on a real GPU yet**: expect to fix small things
the first time.
