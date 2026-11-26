# AphexNIN: Window Licker in the sewer

`Samples/NIN2` (the sewer stage, rain, mud, the hunched band, speakers, synths with blinking lights) meets `Samples/SlimeJumpWindowLicker` (the white-suited hero, THE grin that everyone gets, the rooms of faces). The new part is the girls:

- **Mud girls** (`artlib/👯.py`): the pastel blob girls of Window Licker in bikinis and bows, covered in mud (handprints, drips, boots, worms, pigtails of matted mud that whip), most of them already wearing the grin, one half way there, one not yet. They fill the pit (every other one throws mud), the back rows are simpler, and bigger, faster ones dance on every speaker.
- **The hero** (muddied) dances on top of the biggest speaker, above the guitarist who smashes his guitar on it.
- **Rooms** above the stage: a girl's face chewing on a sunburst, the hero's face under a cap of mud, the ring of faces, the wall of televisions. The camera cuts to them, filling the frame, a few times a take (`rooms=` in `chaos()`).

`make_assets.py` draws nothing twice: it imports the drawing code of both parent samples and writes everything into its own `svg/` (the parents' files are not touched).

```
python3 make_assets.py
python3 ../../tools/levelang export-html stage.lvl -o aphexnin_chaos.html
```

Open the page and it plays take after take by itself; `r` skips to the next seed, `#chaos=7` starts at seed 7, `&clean` hides the label, `#grid=3x2&chaos=100` shows six takes at once.
