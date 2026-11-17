# SlimeJump Window Licker: a love story

A parody music-video cutscene for the levelang scene engine. Original characters, jokes and ending; it only borrows the music-video grammar (long dialogue, stretched limo, dance, morphing faces, beach party, champagne, wedding).

- `video.lvl`: the whole timeline (reads `audio.json`).
- `gen_svg.py` + `art.py`: Python that writes `svg/*.svg`. Run `python3 gen_svg.py`.
- `kmj/`: kaomojilang art (Gelly, Jelly, the frogs, props).
- `analyze_audio.py`: `python3 analyze_audio.py TRACK.mp3 audio.json` (numbers only, the track is not stored here).

Render (preview with your own audio, 8 fps):

    python3 tools/levelang scene Samples/SlimeJumpWindowLicker/video.lvl --fps 8 --tile 20 --mp4 out.mp4 --audio TRACK.mp3
