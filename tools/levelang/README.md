# levelang

Write game levels as emoji / ASCII / SVG art mixed with Python. Preview them as GIFs with a bot playing.

```
pip install -e .[svg]                      # Pillow + cairosvg (cairosvg is only needed for SVG tiles)
python -m levelang gif examples/underwater.lvl --seed 7          # -> examples/underwater.gif
python -m levelang gif examples/mario.lvl --view 40x12           # follow camera
python -m levelang translate examples/underwater.lvl             # the generated Python (same line numbers)
python -m levelang translate examples/underwater.lvl --ast       # ... after the AST transformer
python -m levelang json examples/underwater.lvl                  # engine-neutral level data
python3 -m unittest discover -s tests -t .      # from tools/levelang (pytest works too)
```

## Pipeline

```
.lvl source ──parser.py──▶ plain Python ──ast + transform.py──▶ runtime.py ──▶ Level IR ──▶ render/gif.py (+ bot.py)
 (text rewrite,            (valid, readable,    (tile semantics:                 (placements,         (future: Godot / Unity /
  line-preserving)          same line numbers)   rows, random, chance)            tiles, flags)         Tiled exporters read this)
```

## The language

**Emoji are names.** `🧱` becomes `tile_BRICK`, `⛰️` becomes `tile_MOUNTAIN`. An emoji you never define still works:
it draws as the emoji itself (a few get defaults: colored squares are solid, `🪙` is an item).

**Rows.** A bare tile expression is a row placed at the cursor `x, y`; the cursor then moves down one row.

| you write | meaning |
|---|---|
| `x = 0; y = 6` | move the cursor |
| `🧱*W` | a row of W bricks |
| `(🪨 or 🧱 or None)*50` | 50 cells, each independently one of the three (None = empty) |
| `(🐟*0.03)*W` | each of W cells has a 3% chance of a fish |
| `if 🟩 * 0.1:` | this branch runs 10% of the time |
| `def ⛰️(x, y): ...` | a procedural tile: called wherever ⛰️ is placed, emits relative to `x, y` |

Gotcha: each emitted row moves `y` down, so after `🟨` at `y`, the next row is `y` (already moved), not `y + 1`.

**Art sections.** A `def` whose body is not valid Python is art. Emoji are 2 cells wide, other characters 1,
and a tile is 2 cells, so what you see in a monospace editor is what you get (two spaces = one empty tile).
Column 0 is the column of `def`; the block ends at the first blank line. `x` and `y` params are added for you.

```
def reef(g, x, y):
  🟪🟪🟪🟪
  🟪g( )🟪        ## g( ) = anchor: calls the section passed as `g` here, with x=, y=, w= (width in tiles)
```
In pure-ASCII art one character is one tile; map characters with `legend({'#': 🧱})`.
(A body made only of single-emoji lines is also valid Python; both readings give the same result.)

**Tile definitions** use `->`:

```
def 🟦 -> fill.blue, stroke.white, bg:     ## ASCII pattern body (optional, up to a blank line)
~  ~.~ ~~ ~                                ## repeats across all 🟦 tiles; stroke colours the characters
 ~ ~ ~ ~~~.

def 🪸 -> svg, bg, sway:                   ## SVG body (until </svg>), or svg("coral.svg")
<svg viewBox="0 0 32 32"> ... </svg>
```
Attributes: `fill.<css color>` `stroke.<color>` `svg` `size(w,h)` · flags `solid hazard item spawn goal bg fg` · motion `sway(amount)` `bob` `swim(cells, speed)` (a whale is `swim(14, 1.1)`: long and slow).

## Depth: parallax layers, sizes, and smooth terrain

The grid is for gameplay. Scenery that has no gameplay lives on **layers**, and the blocky tiles can be drawn through a **skin** of smooth curves.

```python
place(🪸, 3, 4, size=(6, 6), flip=True)           # any placement can be bigger, smaller or mirrored (and in a layer, at a fraction of a cell)

with layer("reef_far", parallax=0.2, haze=("#0d3b6e", 0.55)):   # a parallax layer
    place(🐋, 6, 1.5, size=(34, 13.6))                          # whatever is placed inside goes on the layer, not the world

skin(🟨, 🪨, wobble=0.14, outline="#241c45")                    # the sand and rock are drawn rounded and wavy
```

- `layer(name, parallax=0.5, parallax_y=None, over=False, alpha=1, haze=None)`: `parallax` is how much of the camera's movement the layer follows: `1` moves with the world, `0` stays on the
  screen, `0.2` drifts slowly (far away), `1.4` rushes past (foreground). Layer coordinates are cells, like the world's, and they may be fractions; `x = 0, y = 0` line up with the world's when the camera
  is at the top left corner, so a layer needs about `width * (1 + parallax)` cells of scenery to last the whole level. Layers are drawn from the least parallax to the most, all behind the world, except `over=True` ones
  (in front of the world and the player). `haze=(colour, amount)` fogs a layer toward a colour, which is what makes far things look far. Layer tiles animate like any other (`sway`, `bob`, `swim`), and a tall
  `size(1.5, 15)` tile sways more at the top. A layer is never part of the world's cells: the bot, `Level.cs` and `level.cell()` do not see it. Reusing a name adds to the same layer; `with` blocks nest.
  A layer with `parallax=1` is the way to put big, free-placed decoration in the world: it is drawn behind the terrain (and a skin), so the foot of a coral can be buried in the ground.
- `place(tile, x, y, size=(w, h), flip=True)`: size is in cells, overriding the tile's own `size(...)`, so one SVG makes corals of every size.
- `skin(*tiles_or_flags, corner=0.28, smooth=3, wobble=0, outline=None, outline_width=0.07, seed=0, hide=True)`: the cells those tiles (or a flag such as `"solid"`) cover are drawn through a smooth outline:
  every corner of the cells' outline is cut `smooth` times (a staircase becomes a slope, a square corner a curve; `corner` is how much of an edge a cut takes, 0.5 at most), then the outline is nudged by a smooth
  wave of `wobble` cells so a flat floor is not a ruler line. The tiles' own pictures show through the shape, so the sand keeps its texture; the neighbouring tile's picture is carried one cell out so the
  outline never shows a gap, and the level's edge counts as more of the same, so a wall that reaches the picture's edge is not rounded off there. Physics still uses the square cells (the outline strays about
  `wobble` + a corner's cut from them), so keep `wobble` small.
  `levelang.render.skin.skin_loops(...)` gives the outline as polylines in cell units and `path_data(...)` as SVG path data, for an exporter or an engine that draws curves.

## Prowl2D editor: export to a project with layers

    python3 tools/levelang export-project level.lvl -o level.json [--ppc 32] [--tile 16]
    python3 prowl.py level.json

Writes a project for the [editor](../../EDITOR.md): the grid keeps the tiles that mean something to the game (solid, hazard, item, climb, spawn, goal, enemies; one tile per cell, the strongest wins) as small pixel-art
sprites folded into one 255-colour palette; everything that is only a picture (`bg`/`fg` decoration and anything that sways, bobs or swims) and every parallax layer becomes a layer of PNG images at `--ppc` pixels per cell, with
the same positions, sizes, flips, haze, alpha and motion; the `background(top, bottom)` becomes a water gradient layer that stays put across and runs down the level; and a `skin` becomes one image of the whole smooth
terrain on a layer of its own, with the tiles it covers marked `hidden` in the grid (they still collide). The editor draws layers as smooth textured triangles. Its renderer has 63 textures in all, so a level needs
about 40 distinct pictures at most; the exporter warns when it needs more. The sample reef exports to 22 images and 9 sprites, and its solid cells are SlimeJump's walls exactly (a test checks it).

## Game: draw the layers and the skin

`Level.cs` holds the physics only. For a game that draws, `python3 tools/levelang export-scenery FILE.lvl` writes `SceneryData.cs` next to the `.lvl`: the same pictures the editor
export makes (layers, sizes, flips, animation, the smooth skin), packed into ONE atlas (255 colours + air, run-length encoded, so one texture and none of the renderer's 63-texture
limit) and the layers' items as flat float arrays, far to near. `--max-px` (default 128) is the longest side of a picture in the atlas; a skin, being a picture of the whole level,
gets 768. Phases and swim periods are worked out here, so the C# does no hashing and cannot disagree with the editor. A game draws it with `GFX.Triangles`; `Samples/SlimeJumpLevelang`
has the drawing (`Scenery.cs`, `Viewer.cs`). Limits: the atlas is 256 colours, `haze` is a multiplied tint, and the sprites of tiles that stay in the grid (spikes, gems, ...) are not
in it (the sample's viewer draws them as boxes).

## Prowl2D: export to `Level.cs`

The SlimeJump samples (`Samples/SlimeJump*`) keep their level as generated C# data (`Level.cs`: wall rectangles, vines, spikes,
saves, gems, anchors, crumbling tiles, shooters, enemies, spawn, goal; world units, **y up**, one cell = one unit). levelang writes that file:

```
python3 -m levelang export-cs examples/slimejump.lvl -o ../../Samples/SlimeJump/Level.cs --layers-from ../../Samples/SlimeJump/Level.cs
python3 -m levelang from-cs ../../Samples/SlimeJump/Level.cs -o level.lvl      # the other way: an existing Level.cs as editable art
```

| tile attribute | goes to | note |
|---|---|---|
| `solid` | `Walls` (merged into rectangles) | not for `crumbly` tiles |
| `climb` / `hazard` | `Climbs` / `Spikes` (merged) | |
| `crumbly` | `Crumbles`, one per cell | |
| `item` / `save` / `anchor` | `Gems` / `Saves` / `Anchors` | position = the cell's centre |
| `shooter(dx, dy)` | `Shooters` | also mark it `solid`: the game expects the shooter's tile to be in the walls |
| `enemy(kind)` | `Enemies` | 0 = worm, 1 = flyer (see `EnemyCfg.cs`) |
| `spawn` / `goal` | `spawnX/Y` / `goalX/Y` | exactly one of each |
| `at(ax, ay)` | | where an entity stands in its cell (fractions, y up): `at(0.5, 0)` = bottom middle |

`meta(width=64, height=20)` fixes the level size and the origin (top-left cell); without it the bounds of what you placed are the level.
The accessors and helpers in the output are copied verbatim from `Samples/SlimeJump/Level.cs`; `LayerRows()` is copied from `--layers-from`
(each game has its own layer rules). In art, a lone `·` row keeps an otherwise empty row from ending the block.

A complete example: [`Samples/SlimeJumpLevelang`](../../Samples/SlimeJumpLevelang) (the `.lvl`, its `.svg` tiles, the game's `.cs` scripts and the generated `Level.cs`).
From the repo root, `python3 tools/levelang <command>` works too.

Checked by `tests/test_prowl_export.py`: both real levels (`SlimeJump`, `SlimeJumpDestruct`) go Level.cs -> art -> Level.cs with every non-data line identical
and the same spawn, goal, size, entities and wall rectangles (only the order of the rectangles differs). The generated C# has not been compiled or run
(no .NET here); build it with `python3 build.py samples SlimeJump` before relying on it.

## The bot

`bot.py` plans spawn → every reachable item → goal in 8 directions, avoiding solid and hazard cells (and giving
hazards some distance). That's the *swim* mode used by the underwater level. A platformer mode (gravity, jumps)
is the natural next piece, since the Mario-style sample needs it.

## kaomojilang tiles: characters drawn with numbers

[kaomojilang](../kaomojilang/SPEC.md) (vendored in `tools/kaomojilang`, from the geonodes repo; see its VENDORED.md) draws SVG shapes from
numbers placed in text, and animates them (eyes that look and blink, vowel mouths, emotions). A tile can be one of its shapes:

```
def 🗣 -> kmj("face_anim.kmj", "talk", fps=5), size(4, 4), bg:          ## a list of shapes = an animation, cycled at fps

def 🐻 -> kmj("bear.kmj", "bear"), size(4, 4):                           ## a shape def = one picture
def 👁 -> kmj("face_anim.kmj", "eye", scale={10: 0}), size(1, 1):        ## keyword arguments go to the shape def
```

`kmj(file, name, *args, fps=6, **kwargs)`: the file is relative to the `.lvl`; `name` is a shape def (called with the arguments), a shape, or a list of shapes (frames share one canvas, so they line up);
without a name the file's last variable is used. A tile definition body runs to the next blank line, so leave one between `def`s. Size the tile with `size(w, h)` (the picture is fitted to it).
`examples/kaomoji.lvl` places five of them. Needs no Blender: `python -m levelang gif examples/kaomoji.lvl`. The Blender export (`export-blender`) draws the first frame of an animated tile.

## A story: say() and title()

```python
title(34, "Chapter 1", "The girl on the hill")          ## a chapter card, shown when the slime gets to column 34
say(48, "Oh! Hello, little slime.", who="Gelly")          ## a line of dialogue
```

The preview GIF stops the bot at each line for its `seconds` (default 3.5; a title 4.5) and shows it over the picture. `python3 tools/levelang export-story level.lvl -o Story.cs` writes the lines as a C# class
(`Story.Count`, `Story.X(i)`, `Story.Text(i)`, `if` chains: the C build's subset) for a game to print as the player passes them; see `Samples/SlimeJumpRPG`.

## Cutscenes and music videos: scene()

A level is also a stage. `scene("clip", seconds=48, bpm=120)` adds a timeline: `actor()`, `move()`, `warp()`, `show()` / `hide()`, `pose()`, `dance()`, `emote()`, `cam()` / `cut()`, `punch()`, `shake()`, `fade()`, `card()` and `line()`
(all times in seconds, `beat(n)` is n beats of them, places in cells; an actor takes one tile per pose, so a pose is a kaomojilang animation; `size=` draws an actor big, which is how a close-up is made).
`python3 tools/levelang scene clip.lvl -o clip.gif` renders it (a moving, zooming camera with hard cuts, no bot; `--sheet out.png --at b16,b20` writes a contact sheet of moments) and `export-scene` writes `Cutscene.cs`, the same timeline as `if`-chain
functions of time (`ActorX(a, t)`, `Pose(a, t)`, `Visible(a, t)`, `CamX(t)`, `Fade(t)`, `Text(i)` ...) for a game to play. See `Samples/SlimeJumpLoveStory`, which has the call table.

## Blender: grease pencil, animated like the GIF

```sh
python3 tools/levelang export-blender Samples/SlimeJumpLevelang/level.lvl            # -> /tmp/levelang-preview.blend
blender -b /tmp/levelang-preview.blend -a                                            # render it: an mp4 next to the .blend
```

Blender is run headless (`blender -b --python ...`; found on the PATH, `$BLENDER`, `--blender PATH` or the usual install folders; with none, the `bpy` Python module is used if it is
installed). Open the `.blend` and change anything, or render it at any size: the default look is meant to be right as it is (orthographic camera, flat SVG colours, 24 fps, mp4).
Needs Blender 4.3 or newer (grease pencil v3); written and tested against 5.3.

**Our own SVG reader.** Blender's SVG importer is not used. `levelang/svgvec.py` reads each tile's SVG (paths with every command including arcs, shapes, transforms, `style`, opacity,
colours, linear and radial gradients with stops and `href`) into polylines with a fill and a stroke. It uses the standard library only. It says so (and carries on) for what it does not read:
clip paths, masks, filters, text, dashes. `export/blender_scene.py` turns the level into a plain scene description (JSON, `--scene-json PATH` keeps it) and `export/blender_import.py`,
which runs inside Blender, builds it.

**What the .blend holds.**
- `levelang_camera`: orthographic, the height of `--view` (default 32x20 cells, so any render size shows the same height), keyframed to follow the bot, clamped to the level, exactly the GIF's.
- `levelang_bot`: keyframed along the same route (the bot's plan, speed and holds are the GIF's), turning to face where it goes.
- Terrain, standing scenery and every parallax layer as grease pencil objects, stacked far to near. Each parallax layer hangs on an empty `parallax/NAME` whose position is a *driver* on the
  camera, so the depth also works when you move the camera yourself.
- The smooth skin: the covered tiles' own pictures on a layer that is masked by the skin's outline shape, plus the outline.
- Moving things (`swim`, `bob`, `sway`, collected items) are copies of one shared drawing: swimming and bobbing are keyframes (a fish turns over at each end), a gem disappears when the bot
  reaches it, and a swaying plant is a loop of 24 drawings, each copy offset by its own phase with a Time Offset modifier.
- `levelang_backdrop`: the level's sky gradient. Colours are not tone-mapped (the view transform is Standard), a layer's `haze` and `alpha` are baked into its colours.

Options: `-o FILE`, `--res WxH` (the render size saved in the file), `--fps`, `--view WxH`, `--samples`, `--video mp4|png|none`, `--no-bot` (a still camera, only the scenery moves), `--seed`.

**Limits.** A grease pencil fill is one flat colour, so a gradient is cut into 8 bands (opaque ones overlap so no seams show; ones with transparent stops are cut apart). An emoji with no SVG is a
coloured placeholder and a text `pattern` tile is left out (both are raster or font things); the exporter warns once for each. Dashes are drawn solid. Items that are collected hide for good when the bot reaches
them (no respawn). The bot is the one in the GIF: a single route.

## Layout

`parser.py` text → Python · `transform.py` AST pass · `runtime.py` Level IR and helpers · `bot.py` · `render/` (sprites, SVG, GIF) · `svgvec.py` our SVG reader · `scene.py` cutscene timeline · `export/` (Level.cs, Story.cs, Cutscene.cs, editor project, scenery data, `blender*.py`) · `cli.py`
