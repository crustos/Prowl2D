"""One animated head for SlimeJumpHeads, rendered by prowl.py --blend-script (see tools/slime_heads/render.py, which runs this for every kind and puts the head on its ASCII body).
The kind comes from the HEAD_KIND environment variable; the animation is a loop of 8 frames: the eyes look about, one blink, the mouth chews."""
import os
import prowl_blender as pb

KIND = os.environ.get("HEAD_KIND", "cat")
FRAMES = 8

pb.new_scene(frames=FRAMES, fps=8)
face = pb.head(KIND, name="head", layers=False)
for f in pb.frames():
    face.look(x=pb.sin(f.t), y=0.4 * pb.cos(f.t))
    face.blink(1.0 if f.i == 5 else 0.0)
    face.mouth(0.5 + 0.5 * pb.sin(f.t, 1, 0.25) if KIND in ("ogre", "gorilla", "dog") else 0.5 * (0.5 + 0.5 * pb.sin(f.t)))
