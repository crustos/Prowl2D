# kaomojilang (prototype)

Draw SVG / Grease Pencil shapes by *placing numbers and symbols* in text.

```
colors = {0:yellow, 10:white, 20:white, 30:black, 40:black}
sizes  = {30:large, 40:large}
def smooth_face_example(fill=colors, sizes=sizes):
         0
                   1
  7                  2
      10  11  20  21
         30      40
  ...
```

## Pipeline

```
source text ──stage 1──▶ valid Python ──ast.parse──▶ validated tree ──exec──▶ Shapes ──▶ SVG / Grease Pencil
            (line by line)     (stage 2)              (stage 2)
```

* **Stage 1** (`stage1.py`) is a line translator. It never evaluates anything. It keeps a line map, so every
  error points at the *original* line.
* **Stage 2** (`stage2.py`) parses stage 1's output with Python's `ast`, rejects everything outside a small
  safe subset (no imports, attributes, classes, lambdas, `while`, dunder names), and executes it with a
  fixed namespace (colors, sizes, `random()`, `sin`, `cos`, `pi`, `sqrt`, `range` capped at 100 000).
* **Runtime** (`runtime.py`) turns grids into `Shape`s and renders them with the `drawing` package
  (drawsvg), so the same shape gives an SVG file or Grease Pencil strokes.

`python -m kaomojilang FILE --python` prints what stage 1 produced.

## Stage 1 rules

| Input | Becomes |
|---|---|
| a non-ASCII character Python cannot use in a name (`▢`, `‿`, fullwidth parens) in code | `_uXXXX_`, so `def ▢(...)` and `▢(smooth=1)` are valid Python. Strings and comments are left alone |
| the body of a `def` made only of integers | a function returning `__shape__([(number, x, row), ...], name, params, defaults)` |
| a column-0 line that is not Python (not def, assignment, comment, `import`, `for`, ...) | `__kaomoji__(text, label)`; the label is the comment on the next line |
| anything else | Python, passed through (after symbol mangling) |

Triple-quoted strings and bracketed continuations are tracked, so kaomoji inside docstrings are ignored and an
unclosed `(` is reported on the line where it was opened.

### Grid geometry

* `x` = column of the *center* of the number (`10` spans two columns), `y` = row, both relative to the block.
* Rows are multiplied by `ASPECT = 2` (a text row is about twice as tall as a column is wide), so
  four columns by two rows is a square.
* A number used twice in a drawing is an error.

## Shape rules

Numbers form **runs of consecutive values** (`0 1 2 3`, then `10 11`, ...). The first number of a run is
the **id** of the part.

| Run | Part |
|---|---|
| 1 number | dot, or a stamped glyph (below) |
| 2 numbers | line |
| 3+ numbers, odd id | closed polygon (can be filled) |
| 3+ numbers, even id | smooth closed curve (can be filled) |

`smooth` (0..1, default 0.5): every corner is replaced by a cubic going from a point `smooth/2` of the way toward the
previous corner to a point `smooth/2` toward the next one, the corner being the control polygon.
`smooth=1` on a square is a circle, `smooth=0` is the polygon.

### Parameters

`fill`, `stroke` (default black), `width` (default 0.15 columns), `sizes` (dot size, default 1.5 columns),
`smooth`. Each is either a value or a dict `{part id: value, '*': default}`.

* Predefined names: CSS color names (`red`, `yellow`, `none`, ...) and sizes `tiny 0.7`, `small 1`,
  `medium 1.5`, `large 2.5`, `huge 4`.
* A dict passed to a parameter whose *default* is a dict is **overlaid** on it, so
  `face({30: ▢(smooth=random())})` changes the pupils and keeps the other colors.
  A scalar replaces the default.
* A drawing used as a `fill` value of a **single point** is stamped there, stretched to a `size x size`
  box. `▢(...)` is therefore a unit square whose `smooth` goes from square to circle.
* Calling a drawing returns a `Shape`. `shape.to_svg()`, `shape.save_svg(path)`,
  `shape.to_grease_pencil(gp, frame=n)`, and `frames_to_grease_pencil(list_of_shapes, gp)`
  (one keyframe per shape, same framing for all).

### Grease Pencil layers

One layer per part, named `p<id>` (`p0`, `p10`, ...). Smooth shapes become Bezier strokes (4+ anchors, handles),
polygons and lines stay polylines.

## Decisions taken where the example was open

1. Run detection by consecutive numbers (`7` then `10` starts a new part).
2. Dot fill defaults to the stroke color. A dot with a `fill` that is a color is a circle.
3. Overlay semantics for dict arguments (so the pupil animation keeps the face colors).
4. Glyph stamping stretches to a square box (so `▢` is square regardless of its grid aspect).
5. Any column-0 non-Python line is a kaomoji line; bare call statements at top level are therefore not valid
   (use assignments).
6. Line 39 of the original example had an unclosed `(` (`▢(smooth=random(),`); `examples/example.kmj` is the
   corrected version. The unclosed bracket is reported as an error on line 39.

## Symbols and ASCII art in grids (artlib)

A grid body may hold, next to numbers, **symbols** (any non-ASCII character that is not a letter, e.g. the Byzantine Musical
block) and **ASCII art** (`\ / | ( ) - _ ^ < > . , ' backtick`). `def name:` is `def name():`. Body lines must be indented.

* A symbol is a stamp centered on its character, drawn by the file named after it in `artlib/` (`.kmj`, `.svg`, `.py`; the
  `.py` gets the `.svg` of the same name and runs `generate(...)`), or by a `def <symbol>` in the same file. Parameters are
  per symbol (`sizes={'𝀓': 6}`, `rotate=`, `shift=`, `scale=`, `fill={'𝀓': shape}`). See `artlib/README.md`.
* `generate` can return `Stroke`s in figure coordinates (`brush.py`): connecting curves, overshoot, light sketch lines
  (`layer="under"` is drawn below every part, `"over"` above), using `ctx.neighbors()` and `ctx.nearest_ink()`.
* ASCII art is ink: strokes that touch become one smooth open (or closed) curve, parameters under the key `'ink'`. Free ends up to
  1.6 columns apart are joined too (a cell of air), and marks side by side (`'.`) share the way between their neighbours.
* `rough` (a standard parameter: 0 = off, 1 = a normal sketch, 2 = messy, or `{'amount','color','seed','width'}`) adds the loose
  pencil underdrawing on the `under` layer, planned from the whole drawing (`underdraw.py`): gesture loops, centre and level
  lines, blocking loops for features, then each contour found in stages. Strokes are `brush.hand` lines (slow wander, overshoot,
  taper). Tapered strokes are drawn as filled ribbons.
* In Grease Pencil the layers are `under`, `p<id>` (ink `p1000...`, symbols `p2000...`) and `over`.

## Layers

A grid body can be split into **layers**: transparencies laid over the same grid, bottom first.

```
def slimey(rough=0):
    layer body
         ,-------.
        /         \
        \         /
         `-------'
    layer mud(clip=body, opacity=0.9)

        10         12
             14
    layer drips
    30      32
```

* `layer name` or `layer name(options)` starts a layer. Its first line (blank lines count) is its row 0, and x comes from the
  indentation, so the layers register on each other. What comes before the first `layer` line is a layer called `base`.
* Numbers are numbered across the whole drawing: ids are unique, and consecutive numbers (one part) must stay in one layer.
  Ink (ASCII art) is chained per layer. Symbols belong to their layer.
* Options (on the line, and per call with `layers={'mud': {...}}`, the call overriding the line): `clip=body` (or `clip=(body, hat)`) masks the
  layer to the closed shapes of those layers (where they are now, with their own shift; one path, so overlapping shapes keep their
  union); `opacity`, `hidden`, `shift=(columns, rows)`, `scale`, `rotate` (about the centre of the layer, or about `origin=center|top|bottom|left|right|(col, row)`, which also pivots `scale`). A clipped layer adds nothing to the bounding box, so a moving mud level never
  makes the picture jump.
* SVG: one top-level `<g id="layer">` per layer (parts inside as `layer_p<id>`), the clip as a `clipPath`. Grease Pencil: one
  GP layer per kmj layer (named like it); the clip is not applied there (flatten ignores `clip-path`).
* `layers` and `rough` are standard parameters of every drawing.

## HTML templates (placing, rotating, scaling and flipping symbols)

A def whose body has HTML lines is a **template**. Python lines may come before the HTML; `{expr}` inside the HTML is a Python
expression (the def's parameters and variables are in scope, same safe subset as the rest of the language; `{{` `}}` are braces).

```
def foo(x, y):
    <div style="position:absolute; left:{x+10}px; top:{y+50}px; font-size:100px">𝀌</div>
    <div style="position:absolute; left:{x+130}px; top:{y+50}px; font-size:100px; transform:scaleX(-1) rotate(20deg)">𝀌</div>
```

* Every element is a box; its text is a run of symbols (spaces skipped), each drawn like a symbol of a grid (`artlib/`,
  `def <symbol>`, `fill=`...). Elements nest: a child is placed relative to its parent and follows its transform. Document order is
  drawing order.
* `style` properties: `position` (always honoured as `absolute`: `left` and `top` apply whatever its value), `left`, `top`, `width`,
  `height`, `font-size`, `opacity`, `filter`, `transform`, `transform-origin`, `display:none`, `visibility:hidden`. Any other property is an
  error (a typo is not silently ignored); `color` and `z-index` are not supported.
* `opacity` multiplies down the tree. `filter: blur(40px)` (the only filter; px is the standard deviation, as in CSS) blurs the
  element **with its children as one picture**: they are rendered with cairosvg, blurred with Pillow (premultiplied alpha, so
  colours do not bleed) and embedded as one PNG `<image>` at the place of the first of them in the drawing order, 3 sigma of margin
  included in the bounding box. Blurs nested in each other add up. Grease Pencil skips the image (flatten warns).
* `transform`: `translate`, `translateX/Y`, `scale`, `scaleX/Y` (negative = flip), `rotate` (deg, rad, turn, grad), `skewX/Y`, `matrix`,
  multiplied as in CSS; `transform-origin` defaults to `50% 50%` of the element's box (keywords, px and % work).
* Units: 1px = 0.1 grid column, so a drawing renders at the CSS size with the default 10 pixels per column. `font-size` is the longer
  side of a default-size symbol (16px if not given); a symbol with `data-size` keeps its size relative to the others.
* `layer="name"` on an element (inherited by its children) puts it in a layer: `foo(layers={'name': {'shift': (0, -2), 'opacity': 0.5}})`
  as in a grid. Layers are listed in order of first use; elements with no layer go to `base` (drawn first) when others have one.
* A stamped symbol keeps its Grease Pencil layer (`p2000...`); the flip / rotation is a `matrix(...)` on the symbol's SVG group.
* A def is a template when its first non-Python body line looks like `<tag`; ASCII art such as `<---` still draws as ink.
* Example: `examples/fox_html.kmj`.

## Animation (CSS `@keyframes`, driven by `t`)

A drawing is a function of time. Every drawing accepts the standard parameter `t` (seconds): `fox(t=1.25)` is the Shape at that
moment. Without `t` (or `t=None`) nothing is animated, you get the still picture the file describes. Animations come from CSS
`@keyframes` and the `animation` property, on **HTML elements** and on **grid layers**.

```
@keyframes rise {                       # file level: shared by every drawing, static
    from { shift: 0 -62 }
    to   { shift: 0 0 }
}

def mud_scene:
    layer body
        ...
    layer mud(clip=body, shift=(0, -62), animation="rise 30s ease-in forwards")
        ...

def fox(x, period=4):
    <style>
      @keyframes slide { from { left: {x}px } to { left: {x+100}px } }     # in a template: {expr} after a ':' is Python
    </style>
    <div style="left:{x}px; animation: slide {period}s ease-in-out infinite alternate">𝀌</div>
```

* **`@keyframes name { from {..} 40% {..} to {..} }`**: file level (a block starting at column 0, it may span lines, no `{expr}`),
  or inside a `<style>` of a template (where a `{` opens an expression only after a `:`, so `left: {x}px` works and `{ ... }`
  blocks are CSS). Keyframe selectors: `from`, `to`, `N%`, lists (`0%, 100%`). A keyframe may set `animation-timing-function`
  for the interval that follows it. Other CSS rules in `<style>` are errors.
* **`animation`** (shorthand, comma separated for several; the longhands `animation-name/-duration/-delay/-iteration-count/
  -direction/-fill-mode/-timing-function` work on elements too): name, duration (`2s`, `300ms`), delay (negative starts in the
  middle), iteration count (`3`, `infinite`), direction (`normal reverse alternate alternate-reverse`), fill mode (`none forwards
  backwards both`), timing function. A later animation overrides an earlier one for the same property. `animation-play-state` is
  not supported: `t` is the clock.
* **Timing functions**: `linear ease ease-in ease-out ease-in-out cubic-bezier(a,b,c,d) steps(n[, jump-*]) step-start step-end`.
* **What a keyframe can set**: on an element `left top width height font-size opacity transform transform-origin filter: blur()`;
  on a layer `shift` (`cols rows`), `scale` (`sx [sy]`), `rotate` (`30deg`), `opacity`. A property missing from `from` / `to` keeps
  the value the element or layer has without the animation. Transforms interpolate function by function when the lists have the
  same functions (`rotate`, `translate`, `scale`; `scaleX(-1)` passes through 0, as in a browser), and through a decomposed matrix
  otherwise. An animation replaces the whole `transform`: a mirrored element needs `scaleX(-1)` in its keyframes.
* **Layers**: `layer mud(animation="rise 6s ease-in forwards")` (also per call: `layers={'mud': {'animation': '...'}}`). The animated
  values win over the line's and the call's options (like CSS animations over style). Layers move under a clip, so the picture's
  box does not jump; give the video one fixed `bbox`.
* **Frames**: `prog.frames('fox', fps=24, duration=4, **args)` returns the Shapes for `t = k / fps` (frame them with
  `runtime.union_bbox`). In levelang, `kmj("fox.kmj", "fox", fps=24, seconds=240)` is a tile whose frame k is the drawing at
  `t = k / fps`: drawn when asked for (a song-long animation does not sit in memory), one canvas for all frames (`bbox=` to fix it).
* Blurs inside an animation are re-rendered for every frame that changes them. Examples: `examples/fox_html.kmj` (blink, ear twitch,
  breathing shade), `Samples/NIN/kmj/singer.kmj` (the mud story).

## Not done yet (proposals)

* **Kaomoji to shapes.** The 105 kaomoji lines are parsed (`prog.kaomoji`, text + label) but not drawn. A natural
  next step is the same idea as `▢`: a table of eye / mouth / cheek glyphs, each a small numbered drawing, composed
  left to right (`ʘ‿ʘ` = eye `ʘ` + mouth `‿` + eye `ʘ`).
* **Open smooth lines** with 3+ points (today only 2-point lines are open). Proposal: a trailing symbol on the last
  number, e.g. `5~`, or an id range reserved for open shapes.
* Per-point attributes (width taper); animating symbol parameters of a grid (eyes, mouth) with `@keyframes` (layers and HTML elements animate today).
* Nested defs and drawing composition (`place(shape, at=12, size=large)`).

## Additions (face / bear experiments)

- **Parameters** `shift`, `rotate`, `scale` join `fill stroke width sizes smooth`. Each is a value or a dict
  `{id: value, '*': default}`. `shift=(cols, rows)`; `rotate` is clockwise degrees about the part centroid
  (for a stamped point: the glyph's rotation); `scale` is a number or `(sx, sy)`, and `0` hides the part.
- All standard parameters are implicit: a grid shape accepts them even when its `def` doesn't declare them.
- **Sizes** accept a number or `(w, h)`; a one-point part with `(w, h)` is an ellipse.
- **Stamping**: a Shape used as the `fill` of a single point is drawn at its natural size (or `sizes`), with
  stroke width compensated. Hidden parts leave empty keyframes in Grease Pencil so layers don't hold stale drawings.
- **Open runs**: a `~` right after the last number of a run (`2~`) leaves 3+ points open. Odd id: open polyline;
  even id: open smooth curve whose ends are not rounded (smile / frown). `~` anywhere else is an error.
  Ids in a run must be consecutive, so two separate parts need non-consecutive ids (e.g. 11 and 15, not 11 and 12).
- A `def` header must be on one line.
- More CSS colors: tan, wheat, beige, coral, salmon, tomato, crimson, hotpink, violet, indigo, skyblue, ...
- Examples: `face_anim.kmj` (talk, blink, look, mood, emotes), `bear.kmj`.
