"""slime_goose.py: SlimeJump (Samples/SlimeJump), with its game logic in Goose, as an editor project.

The same level, sprites and scripts as slime_rust.py, with the scripts the Goose files of Samples/SlimeJumpGoose (see slime_rust.py for what each one does). Goose is the Crust
subset that tools/goose2c.py lowers to C, which Build links into the engine library. A Goose script has no attribute to carry its marker, so the line above its struct is a
comment, `// script(max_instances = 16)`; its callbacks are functions that take the struct by reference (`fn fixed_update(s: Slime&)`).
"""
import os

from .model import ScriptFile
from .slime_rust import GAME_SCRIPTS, SCRIPTS, SPRITE_OF, make_slime_rust_project

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(os.path.dirname(HERE), "Samples", "SlimeJumpGoose")


def make_slime_goose_project():
    p = make_slime_rust_project()                       # the level, the sprites and the palette: the same
    p.name = "SlimeJumpGoose"
    p.scripts = []
    for sprite in p.sprites:
        sprite.scripts = []
    for name in SCRIPTS:
        with open(os.path.join(SAMPLE, name + ".goose"), encoding="utf-8") as f:
            p.scripts.append(ScriptFile(name, f.read(), "goose"))
        if name in SPRITE_OF:
            p.sprite(SPRITE_OF[name]).scripts.append(name)
    p.game_scripts = list(GAME_SCRIPTS)
    p.dirty = False
    return p
