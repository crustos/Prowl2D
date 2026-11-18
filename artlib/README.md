# artlib: the drawings behind the symbols of the grid language

A symbol in a kaomojilang grid (`𝀎 𝀇 𝀈 𝀓 ...`, any non-letter Unicode character, the Byzantine Musical block works well) is drawn by the
file in this folder that is **named after the symbol**:

| file | for | what it is |
|---|---|---|
| `artlib/𝀓.kmj` | simple things | a drawing (small, easy to read): the `def` named like the symbol, or the only `def` |
| `artlib/𝀎.svg` | complex shapes | any SVG (`path circle ellipse rect line polyline polygon g`, `transform`, `style`). `data-size="4"` or `"4,2"` on the root says how many columns it covers (default: the longer side is 3 columns) |
| `artlib/𝀔.py` | full control | a script with `generate(...)` |
| `artlib/𝀎.svg` + `artlib/𝀎.py` | both | the script gets the svg of the same name: `generate(svg, ...)` |

Of the files for one symbol the `.py` wins, then the `.svg`, then the `.kmj`.

Where a symbol is looked up, first match wins: a `def <symbol>` in the .kmj file itself, an `artlib/` next to the .kmj file (or in a
parent folder), `$KAOMOJI_ARTLIB` (a path list), and this folder. A sample can therefore override a symbol, and never has to carry
the common ones.

## In a drawing

```
def face_example:
              𝀎   ,-----------.
          ,--'                 `--.
         /                         \
        |    𝀇             𝀈        |
        |𝀦                       𝀸  |
        |         𝀔                |
         \         𝀓              /
          `.   𝁼              ,'
            `--.___________,--'
```

The body lines must be indented. A symbol is stamped centered on its character. Numbers still work in the same grid.

* **Symbols** take their parameters by symbol: `face(sizes={'𝀓': (8, 3)}, rotate={'𝀇': 10}, shift={'𝀈': (0, -1)}, scale={'𝀦': 0})`.
  `fill={'𝀓': some_shape}` swaps the drawing for one call.
* **ASCII art** (`\ / | ( ) - _ ^ < > . , ' ` `) is ink: strokes that touch are joined into one line and drawn as a smooth curve, so a
  rough outline flows. A row of the same slash (`\\\`) is one shallow stroke. Parameters for the ink use the key `'ink'`:
  `face(stroke={'ink': navy}, width={'ink': 0.3}, smooth={'ink': 1.0})`. A column cell is 1 wide and 2 tall (like the numbers' rows).

## generate(...)

`generate` declares the parameters it wants, any of:

| parameter | |
|---|---|
| `svg` | the `ArtSvg` of the `.svg` with the same name (or `None`). `svg.recolor({"#2a1a3a": "navy"})`, `svg.with_attrs(data_size="5")` |
| `kmj` | the Shape of the `.kmj` with the same name (or `None`) |
| `ctx` | the context, below |
| `fill stroke width smooth seed` | the figure's parameters for this symbol |

and returns what to draw, one thing or a list:

* an `ArtSvg`, SVG text, or a `Shape`: stamped in the symbol's box;
* `Stroke`s (`from kaomojilang.brush import Stroke, curve, sketch, connect`): drawn in figure coordinates, so a symbol can reach
  its neighbours. `layer="under"` strokes are drawn below the whole figure (the light rough sketch under the dark lines), `"over"`
  above it;
* `None`: draw the `.svg` / `.kmj` as it is.

### ctx

`ctx.char  ctx.index  ctx.at  ctx.size  ctx.angle  ctx.params  ctx.seed`, and

* `ctx.neighbors(within=None, chars=None)`: the other symbols, nearest first, each `Near(char, at, dist, angle, index, size)`;
  `ctx.nearest(chars=...)`;
* `ctx.nearest_ink()`: `(point, line index)` of the ink closest to the symbol, `ctx.ink`: all the ink lines;
* `ctx.forward(near)`: true for one of the two symbols of a pair, so a connection between two symbols is drawn once.

### brush

`curve(a, b, bend=0.25, out_angle=None, in_angle=None)` is a flowing curve that can leave and arrive at given angles,
`sketch(points, passes=3, overshoot=0.12, wobble=0.07, width=0.07, opacity=0.3)` returns light tapered passes: the first is loose and
sails past the ends, the next settle toward the line, like an artist searching for it; `hand(points, err, seed)` is one such wandering line,
`loop(center, rx, ry)` a loose ellipse that runs past where it began, `simplify`, `resample`, `chaikin` the helpers under them, `connect(a, b, ...)` is a dark curve with its sketch passes under it,
`extend(points, amount)` pushes the ends out along their tangents.

The scripts here are ordinary Python (they are part of the repository, like the tools). `.kmj` files keep the safe subset.

## The pencil underdrawing: `rough`

`face(rough=1)` (0 = off, 2 = messy, or `{'amount': 1, 'color': navy, 'seed': 3, 'width': 0.09}`) draws the loose sketch an artist
makes before the dark lines, on the `under` layer (its own Grease Pencil layer). It is planned from the *whole* drawing
(`kaomojilang/underdraw.py`), big to small:

1. **gesture**: one or two loose loops round the main form (the biggest closed outline), or a line of action for a long figure;
2. **construction**: the centre line, and level lines through features that sit side by side (the eyes), running past the form;
   short measured ticks where the other features fall on the centre line;
3. **blocking**: a rough loop for every feature;
4. **contours**: every line is found in stages: a few straight strokes that carry its shape (sailing past the corners), then the
   curve in several short strokes, then tighter strokes close to the final line.

Every stroke is a `brush.hand` line: a slow wander (never per-point jitter), a late or early start, an overshoot, a pencil taper.

## Symbols for the face and the character

| group | symbols |
|---|---|
| eyes | 𝀇 𝀈 (round, with pupil, `.kmj`), 𝀉 happy, 𝀊 sleepy, 𝀋 closed, 𝀌 wink, 𝀍 sparkle, 𝀏 beady dot, 𝀐 big anime eye, 𝀑 cat eye, 𝀒 X |
| brows | 𝀀 arched, 𝀁 flat, 𝀂 𝀃 angry (left, right), 𝀄 𝀅 worried (left, right) |
| noses | 𝀔 hook (`.py`), 𝀕 button, 𝀖 long, 𝀗 snout |
| mouths | 𝀓 smile (`.kmj`), 𝀙 open grin with teeth, 𝀚 frown, 𝀛 small o, 𝀜 smirk, 𝀝 tongue out, 𝀞 flat, 𝀟 fangs, 𝀠 wavy |
| marks | 𝀤 beauty mark, 𝀦 𝀸 cheeks, 𝀧 freckles, 𝀨 sweat drop, 𝀩 scar, 𝀪 bandage, 𝀫 tear, 𝁃 eye bags, 𝁄 stubble (`.py`), 𝁅 forehead wrinkles (`.py`) |
| ears and hair | 𝀬 𝀭 ears, 𝀎 curl (`.svg` + `.py`), 𝀮 spiky tuft, 𝀯 locks of hair (`.py`: they fall and drift outward), 𝀰 bun, 𝀹 beard (`.py`: strands start on the jaw outline), 𝁼 chin (`.py`) |
| costume | 𝀲 round glasses, 𝀳 sunglasses, 𝀴 monocle, 𝀵 top hat, 𝀶 bow tie, 𝀷 heart, 𝀾 halo, 𝀿 crown, 𝁀 moustache, 𝁂 antenna, 𝁆 anger mark, 𝁇 sparkle |
| horns and ears | 𝀺 𝀻 horns, 𝀼 𝀽 cat ears |

These are my assignments of the Byzantine Musical Symbols, one file each: rename a file to change which symbol means what.
`face(scale={'𝀼': 1.6})`, `sizes=...`, `shift=...` adjust any of them per drawing.

## Examples

`tools/kaomojilang/examples/face_artlib.kmj`, and `face_2_artlib.kmj` … `face_9_artlib.kmj`: a kid, a grumpy old man, someone in
sunglasses, a cat, a queen, a tired face, an imp and an angel. The outlines are plain ASCII art, a closed line each.

Try one: `python3 -m kaomojilang tools/kaomojilang/examples/face_5_artlib.kmj --svg out/` (from `tools/`).
