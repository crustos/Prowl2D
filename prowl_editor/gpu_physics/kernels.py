"""The compiled kernels: gpu/spirv/*.spv and manifest.json.

The files shipped in gpu/spirv are built by the physics engine's build.py with
`--push-buffer` (parameters in a storage buffer, binding 30), which every
backend can run. $PROWL_GPU_KERNELS or the `directory` argument points at
another build; `rebuild()` runs build.py from a gpu-physics-engine checkout
(needs Crust) to refresh them."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_DIR = os.path.join(ROOT, "gpu", "spirv")


class KernelError(RuntimeError):
    pass


def default_dir():
    return os.environ.get("PROWL_GPU_KERNELS") or DEFAULT_DIR


class Kernels:
    """Loads modules on first use. kernels.entry("solve_collisions") -> (Program, name)."""

    def __init__(self, backend, directory=None):
        self.backend = backend
        self.dir = directory or default_dir()
        mpath = os.path.join(self.dir, "manifest.json")
        if not os.path.exists(mpath):
            raise KernelError("no compiled GPU kernels in %s (manifest.json missing); build them with "
                              "gpu-physics-engine/build.py --push-buffer --out %s" % (self.dir, self.dir))
        with open(mpath) as fh:
            man = json.load(fh)
        self.meta = man.pop("_meta", {})
        self.manifest = man
        self.by_entry = {}
        for module, rec in man.items():
            for e in rec["entry_points"]:
                self.by_entry[e["name"]] = module
        self._progs = {}
        if backend.name == "wgpu" and self.meta.get("push_mode") != "buffer":
            raise KernelError("%s was built with push constants; the wgpu backend needs --push-buffer kernels" % self.dir)

    def program(self, module):
        p = self._progs.get(module)
        if p is None:
            with open(os.path.join(self.dir, self.manifest[module]["file"]), "rb") as fh:
                p = self.backend.load(fh.read())
            self._progs[module] = p
        return p

    def entry(self, name):
        mod = self.by_entry.get(name)
        if mod is None:
            raise KernelError("no kernel entry point %r in %s" % (name, self.dir))
        return self.program(mod)

    def iface(self, name):
        return self.entry(name).iface[name]

    def local_size(self, name):
        return self.iface(name)["local_size"][0]


def rebuild(engine_dir, crust_dir=None, out=None):
    """Runs gpu-physics-engine/build.py --push-buffer into `out` (default gpu/spirv)."""
    script = os.path.join(engine_dir, "build.py")
    if not os.path.exists(script):
        raise KernelError("%s is not a gpu-physics-engine checkout (no build.py)" % engine_dir)
    cmd = [sys.executable, script, "--push-buffer", "--out", out or DEFAULT_DIR]
    if crust_dir:
        cmd += ["--crust", crust_dir]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise KernelError("kernel build failed:\n" + p.stdout + p.stderr)
    return p.stdout
