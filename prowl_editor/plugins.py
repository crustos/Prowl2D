"""plugins.py: plugins for prowl.py (no Qt, so the command line can use it too).

A plugin is a Python file (or a folder of them) given to prowl.py with --plugin:

    python3 prowl.py --plugin my_tool.py --plugin more_plugins/ project.json

It is imported when prowl.py starts. If it defines `register(prowl)`, that is called with a `Prowl` object, which is how it adds things:

    def register(prowl):
        prowl.add_argument("--stars", type=int, default=0, help="add N star sprites")      # a command-line option (shown by --help)
        prowl.add_importer(".tmx", import_tmx)                                              # prowl.py level.tmx   -> import_tmx(project, "level.tmx", args)
        prowl.on_project(add_stars)                                                         # add_stars(project, args), once the project is built, before it is saved or opened
        prowl.on_gui(add_menu)                                                              # add_menu(studio, main_window, windows, args), when the editor opens

An importer adds sprites / levels to the project it is given and may return an `ImportResult` (below; anything with `sprites`, `levels` and `notes` lists will do:
the ones it added, and lines to tell the user), which prowl.py reports and uses to select what was imported in the editor; returning None is fine. `args` is the argparse namespace of the whole command line, so a
plugin reads its own options (and the built-in ones) from it. A plugin that has no `register` is just run: its top-level code is the plugin.

The plugin's folder is on sys.path while it loads, so it can import its sibling modules. Errors in a plugin stop prowl.py with the plugin's name and the traceback.
"""
import importlib.util
import os
import re
import sys

from .model import ProjectError


BUILTIN = "prowl.py"             # the "plugin" of what prowl.py registers itself (the .blend importer): its errors are not blamed on a plugin


class PluginError(ProjectError):
    """A plugin could not be loaded or failed; the message says which. `unexpected` is True when it is a bug in the plugin (an exception that is not a
    ProjectError), where prowl.py shows the traceback too."""

    def __init__(self, message, unexpected=False):
        super().__init__(message)
        self.unexpected = unexpected


def _blame(owner, what, e):
    """The PluginError for exception `e` raised by `owner`'s code."""
    if isinstance(e, PluginError):
        return e
    if isinstance(e, ProjectError):
        return PluginError("plugin %s: %s" % (owner, e))
    return PluginError("plugin %s %s: %s: %s" % (owner, what, type(e).__name__, e), unexpected=True)


class ImportResult:
    """What an importer returns: the Sprites and Levels it added to the project, and notes (what was skipped, scaled...) for the user."""

    def __init__(self, sprites=(), levels=(), notes=()):
        self.sprites, self.levels, self.notes = list(sprites), list(levels), list(notes)

    def summary(self):
        return "%d sprite%s, %d level%s" % (len(self.sprites), "" if len(self.sprites) == 1 else "s", len(self.levels), "" if len(self.levels) == 1 else "s")


class Prowl:
    """What a plugin's register(prowl) receives."""

    def __init__(self, root):
        self.root = root                    # the Prowl2D folder (where prowl.py is)
        self.plugins = []                   # the names of the plugins loaded so far
        self._current = BUILTIN             # whose register() is running: what a failure is blamed on
        self._arguments = []                # (owner, names, kwargs)
        self._importers = {}                # ".ext" -> (owner, fn)
        self._project_hooks = []            # (owner, fn)
        self._gui_hooks = []

    # ---- what a plugin calls
    def add_argument(self, *names, **kwargs):
        """A command-line option for prowl.py, with argparse's add_argument arguments."""
        self._arguments.append((self._current, names, kwargs))

    def add_importer(self, ext, fn, help=""):
        """prowl.py FILE.ext calls fn(project, path, args) for every positional file whose extension is `ext` (with the dot, any case)."""
        ext = ext.lower() if ext.startswith(".") else "." + ext.lower()
        if ext in (".json", ".py"):
            raise PluginError("plugin %s: %s files are projects and plugins already, an importer cannot take them" % (self._current, ext))
        if ext in self._importers:
            raise PluginError("plugin %s: %s files are already imported by %s" % (self._current, ext, self._importers[ext][0]))
        self._importers[ext] = (self._current, fn)

    def on_project(self, fn):
        """fn(project, args) runs once the project is built (loaded, and everything given on the command line imported into it)."""
        self._project_hooks.append((self._current, fn))

    def on_gui(self, fn):
        """fn(studio, main_window, windows, args) runs when the editor opens, to add menus, windows, ..."""
        self._gui_hooks.append((self._current, fn))

    # ---- what prowl.py calls
    def importer_for(self, path):
        entry = self._importers.get(os.path.splitext(path)[1].lower())
        return entry[1] if entry else None

    def extensions(self):
        return sorted(self._importers)

    def apply_arguments(self, parser):
        for owner, names, kwargs in self._arguments:
            try:
                parser.add_argument(*names, **kwargs)
            except Exception as e:           # argparse.ArgumentError for a duplicate flag, TypeError for a bad keyword
                raise PluginError("plugin %s: cannot add option %s: %s" % (owner, " / ".join(names), e))

    def run_importer(self, path, project, args):
        return self._call(self._importers[os.path.splitext(path)[1].lower()][0], self.importer_for(path), project, path, args)

    def run_project_hooks(self, project, args):
        for owner, fn in self._project_hooks:
            self._call(owner, fn, project, args)

    def run_gui_hooks(self, studio, main, windows, args):
        for owner, fn in self._gui_hooks:
            self._call(owner, fn, studio, main, windows, args)

    @staticmethod
    def _call(owner, fn, *a):
        if owner == BUILTIN:
            return fn(*a)
        try:
            return fn(*a)
        except Exception as e:
            raise _blame(owner, "failed", e) from e


def plugin_files(path):
    """The .py files a --plugin argument stands for: the file itself, or the .py files of a folder (sorted, not those starting with an underscore)."""
    if os.path.isdir(path):
        names = sorted(n for n in os.listdir(path) if n.endswith(".py") and not n.startswith("_"))
        if not names:
            raise PluginError("plugin folder %s has no .py files" % path)
        return [os.path.join(path, n) for n in names]
    if not os.path.isfile(path):
        raise PluginError("plugin %s does not exist" % path)
    if not path.endswith(".py"):
        raise PluginError("plugin %s is not a .py file" % path)
    return [path]


def load_plugins(paths, prowl):
    """Imports every plugin of `paths` and calls its register(prowl). Returns `prowl`."""
    for given in paths:
        for path in plugin_files(given):
            name = os.path.splitext(os.path.basename(path))[0]
            module_name = "prowl_plugin_" + re.sub(r"\W", "_", name)
            if module_name in sys.modules:
                raise PluginError("plugin %s: another plugin with the same file name is already loaded" % path)
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            folder = os.path.dirname(os.path.abspath(path))
            if folder not in sys.path:                    # and it stays there, for the imports its hooks make later
                sys.path.insert(0, folder)
            prowl._current = name
            try:
                spec.loader.exec_module(module)
                register = getattr(module, "register", None)
                if callable(register):
                    register(prowl)
            except Exception as e:
                raise _blame(path, "failed to load", e) from e
            finally:
                prowl._current = BUILTIN
            prowl.plugins.append(name)
    return prowl
