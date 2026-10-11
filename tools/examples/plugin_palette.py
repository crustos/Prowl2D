"""An example prowl.py plugin: python3 prowl.py --plugin tools/examples/plugin_palette.py colours.pal --pal-width 4

A .pal file has one colour per line, `name RRGGBB`; each becomes a sprite of that colour. It shows everything a plugin can add:
an option (--pal-width), an importer for a file type (.pal), a hook on the project, and a hook on the editor (a Plugins menu).
"""
from prowl_editor.model import Sprite
from prowl_editor.plugins import ImportResult


def register(prowl):                                     # called once, when prowl.py starts
    prowl.add_argument("--pal-width", type=int, default=2, metavar="PIXELS", help="the width of the sprites made from .pal files")
    prowl.add_importer(".pal", import_pal)               # prowl.py FILE.pal -> import_pal(project, "FILE.pal", args)
    prowl.on_project(report_project)                     # once the project is built
    prowl.on_gui(add_menu)                               # when the editor opens


def import_pal(project, path, args):
    made = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                name, hexcolour = line.split()
                rgb = tuple(int(hexcolour[i:i + 2], 16) for i in (0, 2, 4))
                index = project.palette.add(project.palette.first_free_key(), name, rgb)
                sprite = Sprite(name, args.pal_width, 1)
                sprite.frames = [bytearray([index] * args.pal_width)]
                made.append(project.add_sprite(sprite))
    return ImportResult(sprites=made, notes=["colours are in the palette too"])


def report_project(project, args):
    print("plugin_palette: the project has %d sprites" % len(project.sprites))


def add_menu(studio, main, windows, args):
    menu = main.menuBar().addMenu("&Plugins")
    menu.addAction("Count sprites", lambda: studio.message.emit("%d sprites" % len(studio.project.sprites)))
