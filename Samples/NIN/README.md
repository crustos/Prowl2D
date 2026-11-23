# NIN: a mud music video (work in progress)

A parody music-video cutscene for the levelang scene engine, to a Nine Inch Nails track you supply. Original character only:
the frontman is a new design (`kmj/singer.kmj`), not a likeness of anyone real. The track itself is not stored here.

Done so far:

- the **layer** support in the .kmj language (`tools/kaomojilang/SPEC.md`, "Layers"): `layer name(clip=..., opacity=...)` sections,
  per-call `layers={'mud': {'shift': (0, rows), ...}}`;
- `kmj/singer.kmj`: the frontman in a sewer, side view, leaning far forward over a mic stand tilted 45 degrees, both hands on the mic, legs spread.
  A big pipe over his back pours mud. The whole mud story is **declared in the file** with CSS `@keyframes` on the layers (`pour`, `spread`,
  `cover`, `hang`, `fall`): `singer(t=seconds)` is the picture at that time of a 60 second story (the pipe pours at 3s, a puddle spreads, the
  mud climbs him, drips hang from 30s, drops fall from 40s). In the video the tile plays it on the song's clock:
  `kmj("kmj/singer.kmj", "singer", fps=24, seconds=<song length>, speed=60 / <song length>)`. To time a moment to the music, change the
  percentages of the keyframes (or give a layer its own `animation="cover 20s ease-in 75s forwards"` per call).

Next: `analyze_audio.py` on the track (as for Window Licker), `video.lvl` and the shots.

## Scene 1: the stage (`stage.lvl`)

A stage at the mouth of a sewer, in the rain. The tunnel drains over a lip into a ditch full of muddy water; the band and the audience are mud people covered in worms.

```sh
cd Samples/NIN
python3 make_assets.py                                   # draws svg/: the crowd and band frames (artlib/💩.py), mud, falls, rain, worms, the wall, the pipes (artlib/🚽.py)
python3 ../../tools/levelang scene stage.lvl --sheet /tmp/stage.png --at 0,10,15,21
python3 ../../tools/levelang export-html stage.lvl -o stage.html
```

The toilet and its pipes (`artlib/🚽.py`) hang on the wall over the stage; its spout is at x 36, y 36 where the singer's pipe will be attached. The audience is three rows (back rows smaller, higher and hazier)
of six figures each (`artlib/💩.py`, 8 frames of dancing per figure). `test.lvl` (from `gen_test.py`) is the plain stage with random cuts, for trying a song in the HTML player.
