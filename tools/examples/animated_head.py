"""An animated head made with code, for prowl.py --blend-script:

    python3 prowl.py --blend-script tools/examples/animated_head.py --blend-ppu 48 -o cat.json

The head is a collection of layers (head, mouth, eyes), so the project gets four sprites: the whole cat, and each layer, framed alike.
Pick another kind with the first line: monkey, cat, dog, bear, gorilla, alien, frog, ogre.
"""
import prowl_blender as pb

KIND = "cat"

pb.new_scene(frames=12, fps=12)
face = pb.head(KIND, name=KIND, skin=None)
for f in pb.frames():
    face.look(x=pb.sin(f.t), y=0.3 * pb.cos(f.t))
    face.blink(1.0 if f.i == 8 else 0.0)
    face.mouth(0.5 + 0.5 * pb.sin(f.t, 2))
    face.move(rotation=(0, 0, 6 * pb.sin(f.t)))
