# NIN2: the sewer stage, with more detail

Same scene as `Samples/NIN` (a stage at the mouth of a sewer, rain, mud, worms) with more going on:

- **The band is hunched over**, heads down under whipping curtains of muddy hair, banging 4 times a second (16 frames, `hunch=0.9, cycles=4` in `artlib/💩.py`).
- **The crowd bangs faster** (12 frames, 3 bangs a loop, bent over), and every other person winds up and **throws mud**. The page adds **volleys of mud**: balls arc from the pit into the crowd, at the band and onto the stage, and splat (`throw=` in `chaos()`).
- **Speakers everywhere** (`artlib/🔊.py`): cones that throb, cabinets that shake. The biggest wall is at the left edge, with the guitarist standing in front of its big woofer for **feedback** (rings and lightning flaring around it). He **smashes his guitar on the speaker** (`smash_at=`).
- **Synths, a drum machine and a rack** (`artlib/🎛.py`): blinking LEDs, running step sequencers, turning knobs, sliding faders, scopes, VU needles, swaying patch cables, and hunched mud players whose hands work the controls. The camera cuts to **close-ups of the hands** (`rigs=`).
- A low drifting **fog**.

```
python3 make_assets.py                                        # draws svg/ (run from this folder)
python3 ../../tools/levelang export-html stage.lvl -o nin2_chaos.html
```

Open the page and it plays take after take by itself; `r` skips to the next seed, `#chaos=7` starts at seed 7, `&clean` hides the label, `#grid=3x2&chaos=100` shows six takes at once.
