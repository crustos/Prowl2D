# SlimeJumpLoveStory

![A music video: a deadpan lane, a beat drop, close-ups on the beat, a crowd of dancing frogs, a wedding, and a twist](intro.gif)

**The opening music video of [`SlimeJumpRPG`](../SlimeJumpRPG)**, made the same way as the level: `.lvl` stages, `.kmj` drawings, and a timeline. Forty-eight seconds at 120 bpm, in the grammar of a music video:
a deadpan opening in a quiet lane, a beat drop, cuts on the beat, close-ups of faces reacting, an escalating absurd dance, and a shock ending. (The characters, jokes and ending are original; the clock is a plain BPM grid you can line up with any track you have the right to use.)

| beats | seconds | what |
|---|---|---|
| 0 - 15 | 0 - 8 | **the lane**, deadpan: Sir Croak interrogates Slime, cutaways to nervous and smug faces, a stretch limo takes its time, shock, and a wink from whoever is inside |
| 16 - 31 | 8 - 16 | **the drop**: white flash, the club, everyone dances, the camera punches and a colour flashes on every beat, and a cut every beat between wide shots and close-ups (Gelly, Slime, Croak winking, smirking, in shades) |
| 32 - 55 | 16 - 28 | **the crowd**: one more Sir Croak steps in every beat until there are seven, the dance doubles in speed, then Slime and Gelly see each other (close-ups: heart eyes, heart eyes, a heartbroken frog), and the camera pushes in on the pair |
| 56 - 85 | 28 - 43 | **the wedding**, which nobody saw coming: a bride and a groom, a close-up of each, "I do", Sir Croak objects and then does not, and the whole hall dances |
| 86 - 96 | 43 - 48 | **the twist**: it was a dream. Slime wakes up in the lane; "you are late for chapter one", and the chapter begins |

## What is in the folder

| file | what |
|---|---|
| `intro.lvl` | the video: the stage (four sets and four close-up rooms) and `scene(...)`, the timeline |
| `level.lvl` | the game level, the same as `SlimeJumpRPG`'s (its `Level.cs` and `Story.cs` are generated from it) |
| `kmj/*.kmj` | the drawings, `SlimeJumpRPG`'s plus new poses (nervous, shock, wink, cool, two dance moves, with and without shades) for the slime, Gelly and Sir Croak, and a stretch limo, a disco ball and a speaker |
| `Cutscene.cs` | **generated** from `intro.lvl`: the timeline as functions of time (about 3000 lines of `if` chains; do not edit) |
| `Game.cs` | `SlimeJumpRPG`'s, with `PlayCutscene()` first |
| `intro.gif` | the preview |

## The sets

One stage, side by side. The camera never travels between them: it **cuts**.

| x | set |
|---|---|
| 0 - 63 | the lane, at dawn (grass, parallax hills, trees, clouds) |
| 64 - 127 | the club: a dark room, a floor that lights up in three colours, a neon heart, two disco balls, speaker stacks |
| 128 - 223 | close-up rooms for Slime, Gelly and Sir Croak: loud flat stripes |
| 224 - 255 | the wedding hall: an arch, a pink aisle |
| 256 - 287 | a close-up room for the bride |

A **close-up** is just an actor drawn big (`size=(21.6, 15.3)`) in its own room, so the face is crisp (the SVG is rasterized at that size). To cut to a face: `close(t, "gelly", "wink")` (a helper in `intro.lvl`: a cut, plus the pose).

## The timeline

```python
scene("clip", seconds=48, fps=12, view=(32, 18), bpm=120)     # beat(16) is the drop: 8 seconds
actor("gelly", GELLY, 95, 15)                                  # one tile per pose; size=(w, h) draws it big
actor("c0", CROAK, 84.6, 15.4); hide("c0", 0)                  # the clones are not on stage yet
cut(beat(16), 94, 14.4, 1.9)                                   # a hard shot change: the camera is there from that beat
dance("gelly", beat(16), beat(40), ["da", "db"], every=1, hop=0.7)   # change pose and hop on every beat
show("c0", beat(32)); punch(beat(32), 0.07); flash(beat(32))   # one more frog, a camera shove, a white flash
warp("slime", beat(56), 236.4, 15.8)                           # jump into another set (it does not turn)
card(...) / line(...) / emote(...) / fade(...) / pose(...) / move(...) / cam(...)
```

| call | does |
|---|---|
| `scene(name, seconds, fps, view, bpm)` | starts the scene; `view` is the window in cells at zoom 1 |
| `beat(n)` | seconds of n beats at the scene's bpm |
| `actor(name, tile or {pose: tile}, x, y, flip, size)` | an actor: the top left corner of its picture, in cells |
| `move(name, t0, t1, x, y, ease, hop)` | walks between two times (`linear` `in` `out` `inout`); it looks where it walks |
| `warp(name, t, x, y)` / `face(name, t, left)` | jumps there at t (a cut) / mirrors the picture |
| `show(name, t)` / `hide(name, t)` | on stage / off stage |
| `pose(name, t, pose)` / `dance(name, t0, t1, poses, every, hop)` | another tile (a kaomojilang animation) / changes pose and hops on the beat |
| `emote(name, t, tile, seconds)` | a picture that pops up and floats over the actor |
| `cut(t, x, y, zoom)` / `cam(t, x, y, zoom, ease)` | a hard cut / the camera centre and zoom, eased between keys |
| `punch(t, amount, seconds)` / `shake(t0, t1, amp)` | the camera zooms in a little and settles back / jitters |
| `fade(t0, t1, from, to, colour)` | a coloured veil (a flash is `fade(t, t + .3, .6, 0)`) |
| `card(t, text, sub)` / `line(t, text, who)` | a title band / a speech box |

## Edit, regenerate, preview, run

```sh
python3 tools/levelang scene        Samples/SlimeJumpLoveStory/intro.lvl --tile 16 -o Samples/SlimeJumpLoveStory/intro.gif    # needs: pip install cairosvg
python3 tools/levelang scene        Samples/SlimeJumpLoveStory/intro.lvl --tile 16 --sheet /tmp/look.png --at b16.3,b21,b44.5,b57   # a contact sheet of some moments (b = beats)
python3 tools/levelang export-scene Samples/SlimeJumpLoveStory/intro.lvl -o Samples/SlimeJumpLoveStory/Cutscene.cs
python3 tools/levelang export-cs    Samples/SlimeJumpLoveStory/level.lvl -o Samples/SlimeJumpLoveStory/Level.cs --layers-from Samples/SlimeJump/Level.cs
python3 tools/levelang export-story Samples/SlimeJumpLoveStory/level.lvl -o Samples/SlimeJumpLoveStory/Story.cs
python3 build.py player Samples/SlimeJumpLoveStory --run     # translate to C, build, play: the cutscene prints, then the bot wins the level
```

The game here is headless (it prints, it does not draw), so `PlayCutscene()` steps the timeline a tenth of a second at a time and prints every line, every emote, and every two seconds the camera, the fade and where each actor is.
A game that draws would ask `Cutscene.ActorX(a, t)`, `ActorY`, `Pose`, `Flip`, `Visible`, `CamX`, `CamY`, `CamZoom`, `Fade` and `FadeColor` for the same numbers every frame; they use the same easings, cuts, punches and shakes as the GIF.

The C player run: `cutscene done: 11 of 11 lines, 22 of 22 emotes, 53 camera jumps`, then the level is won as in `SlimeJumpRPG` (`won=1 frame=2284 deaths=3`, 28 of 28 story lines).
`--verify` (the same run on .NET) needs the .NET 10 SDK and was not run. `python3 -m unittest discover -s tools/levelang/tests -t tools/levelang` fails if `Cutscene.cs` is out of date with `intro.lvl`, a caption overlaps another, a cut is off the half beat, or a close-up spills out of its room.
