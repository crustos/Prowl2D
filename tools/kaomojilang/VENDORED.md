# Vendored from geonodes

Copied from [crustos/geonodes](https://github.com/crustos/geonodes) (commit e34cebba, `kaomojilang/` and the parts of `drawing/` it uses):

- `kaomojilang/` -> here; `drawing/{flatten,grease}.py` and `drawing/drawsvg/` -> `drawing/`.
- Changed on the way in: `runtime.py` imports `.drawing` instead of `..drawing`; the tests import `kaomojilang` instead of `geonodes.kaomojilang`.
- Left behind: `drawing/nodes.py` (the node-tree drawing mode needs the geonodes library) and the Blender-only integration tests' venv setup.
- `drawing/drawsvg/` is the MIT-licensed drawsvg (see its LICENSE.txt and VENDORED.md).

Blender is not needed to draw or animate SVG. `drawing/grease.py` (and `Shape.to_grease_pencil`) import `bpy` only when called, so they work inside Blender or with the `bpy` pip module.

Run the tests (from `tools/`): `python3 -m pytest kaomojilang/tests` (the Grease Pencil tests are skipped without `bpy`).
Command line: `python3 -m kaomojilang examples/face_anim.kmj --svg out/` (from `tools/kaomojilang`'s parent, `tools/`: `python3 -m kaomojilang kaomojilang/examples/face_anim.kmj --svg out/`).

## Local additions (not in geonodes)

- `artlib.py`, `brush.py`, `ink.py`, `tests/test_artlib.py`, `examples/face_artlib.kmj` and the repository's `artlib/` folder: symbols and ASCII art in grids (see `SPEC.md`, `artlib/README.md`). `stage1.py`, `stage2.py` and `runtime.py` changed to carry them; re-vendoring from geonodes must keep these.
