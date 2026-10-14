"""Finds Crust, whose SPIR-V reader and reference interpreter the backends use.

Crust is looked for in $CRUST_DIR, then beside this checkout (../crust), then
in ~/crust. It is only needed to *read* a compiled kernel's interface (and, for
the interpreter backend, to run it); building new kernels needs it as well."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_done = []


def find():
    cands = [os.environ.get("CRUST_DIR"),
             os.path.join(ROOT, "..", "crust"),
             os.path.join(ROOT, "crust"),
             os.path.expanduser("~/crust")]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "shivyc", "spirv_reader.py")):
            return os.path.abspath(c)
    return None


def ensure():
    """Puts Crust (and its tools/) on sys.path; raises a clear error without it."""
    if _done:
        return _done[0]
    c = find()
    if c is None:
        raise RuntimeError("the GPU physics needs Crust (SPIR-V reader and interpreter): "
                           "set CRUST_DIR or clone https://github.com/brentharts/crust beside this checkout")
    for p in (c, os.path.join(c, "tools")):
        if p not in sys.path:
            sys.path.insert(0, p)
    _done.append(c)
    return c
