"""User scripts on the GPU: a C# subset class with a per-entity Update.

    [GpuKernel]
    public class Magnet {
        public float Strength = 30f;          // a tunable parameter (GpuScript.params)
        public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) {
            float dx = Input2D.MouseX - x;
            float dy = Input2D.MouseY - y;
            if (Input2D.MouseDown(0)) {
                vx += dx * Strength * dt;
                vy += dy * Strength * dt;
            }
        }
    }

Update runs once per circle, in parallel, before the physics step. `x, y` are
the position and `vx, vy` the velocity in world units (per second); changes
are written back. Also in scope: `dt`, `time`, `count`, `tag` (the circle's
tag), `WorldWidth`, `WorldHeight`, and `Input2D.Key/MouseDown/MouseX/MouseY`
(read from the block the CPU fills each frame: see gpuinput.py).

The class is translated to a Rust-subset #[kernel] and compiled to SPIR-V by
Crust. Supported: float/int/uint/bool locals, + - * / % compare && || !,
if/else, while, for (init; cond; i++), casts, Mathf.Sqrt/Abs/Min/Max/Clamp/
Floor/Sin/Cos. Not supported: return inside Update (use if/else), `?:`,
arrays, calls to other methods, classes. Float literals should be written as
floats (`2f`, `2.0`): the kernel language does not mix int and float."""
import os
import re
import struct
import subprocess
import sys
import tempfile

from . import crust_path


class ScriptError(RuntimeError):
    pass


TYPES = {"float": "f32", "int": "i32", "uint": "u32", "bool": "bool"}
FMT = {"f32": "f", "i32": "i", "u32": "I", "bool": "I"}
KEYS = {"Left": 263, "Right": 262, "Down": 264, "Up": 265, "Space": 32, "Escape": 256}

# bindings the script kernels use; the world supplies the buffers by parameter name
BINDINGS = (("positions", "&mut [f32]"), ("previous_positions", "&mut [f32]"), ("radius", "&[f32]"),
            ("tags", "&[u32]"), ("input_u32", "&[u32]"), ("input_f32", "&[f32]"))
STD = ("dt", "time", "count", "WorldWidth", "WorldHeight")


# ------------------------------------------------------------ source helpers
def _strip_comments(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def _match(s, i, open_="(", close=")"):
    """Index of the bracket matching s[i] (which is `open_`)."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == open_:
            depth += 1
        elif s[j] == close:
            depth -= 1
            if depth == 0:
                return j
    raise ScriptError("unbalanced %s in script" % open_)


def _split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _call(s, name, fn):
    """Rewrites every `name(args)` with fn(list of already-rewritten args)."""
    pat = re.compile(r"(?<![\w.])" + re.escape(name) + r"\s*\(")
    while True:
        m = pat.search(s)
        if not m:
            return s
        o = m.end() - 1
        c = _match(s, o)
        args = [_expr(a) for a in _split_args(s[o + 1:c])]
        s = s[:m.start()] + fn(args) + s[c + 1:]


def _expr(e):
    """Expression-level C# -> Rust-subset rewriting."""
    e = re.sub(r"\bthis\.", "", e)
    for k, v in KEYS.items():
        e = re.sub(r"\bInput2D\.%s\b" % k, str(v), e)
    e = re.sub(r"\bInput2D\.MouseX\b", "input_f32[513]", e)
    e = re.sub(r"\bInput2D\.MouseY\b", "input_f32[514]", e)
    e = _call(e, "Input2D.Key", lambda a: "(input_u32[(%s) as usize] != 0)" % a[0])
    e = _call(e, "Input2D.MouseDown",
              lambda a: "(((input_u32[512] >> ((%s) as u32)) & 1) != 0)" % a[0])
    one = {"Sqrt": "sqrt", "Abs": "abs", "Floor": "floor", "Sin": "sin", "Cos": "cos"}
    for cs, rs in one.items():
        e = _call(e, "Mathf." + cs, lambda a, rs=rs: "(%s).%s()" % (a[0], rs))
    e = _call(e, "Mathf.Min", lambda a: "(%s).min(%s)" % (a[0], a[1]))
    e = _call(e, "Mathf.Max", lambda a: "(%s).max(%s)" % (a[0], a[1]))
    e = _call(e, "Mathf.Clamp", lambda a: "(%s).clamp(%s, %s)" % (a[0], a[1], a[2]))
    if re.search(r"\bMathf\.|\bInput2D\.", e):
        raise ScriptError("unsupported API in expression: %s" % e.strip())
    # (float)x -> (x as f32)
    e = re.sub(r"\((float|int|uint)\)\s*(\w+(?:\[[^\]]*\])?|\([^()]*\))",
               lambda m: "(%s as %s)" % (m.group(2), TYPES[m.group(1)]), e)
    # 2f / 1.5f / 1e3f -> float literals
    e = re.sub(r"\b(\d+\.\d*|\d*\.\d+|\d+)([eE][+-]?\d+)?[fF]\b",
               lambda m: _flt(m.group(1) + (m.group(2) or "")), e)
    if "?" in e:
        raise ScriptError("the ?: operator is not supported on the GPU; use if/else")
    return e


def _flt(t):
    return t if ("." in t or "e" in t.lower()) else t + ".0"


def _stmt(line):
    """One C# statement (no braces) -> Rust-subset statement."""
    s = line.strip()
    if not s:
        return ""
    m = re.match(r"(float|int|uint|bool)\s+(\w+)\s*=\s*(.*);$", s, re.S)
    if m:
        return "let mut %s: %s = %s;" % (m.group(2), TYPES[m.group(1)], _expr(m.group(3)))
    if re.match(r"(float|int|uint|bool|var)\s+\w+\s*;", s) or s.startswith("var "):
        raise ScriptError("declare locals with an initial value: %s" % s)
    m = re.match(r"(\w+)\s*(\+\+|--)\s*;$", s)
    if m:
        return "%s %s= 1;" % (m.group(1), m.group(2)[0])
    if s.startswith("return"):
        raise ScriptError("`return` inside Update is not supported on the GPU; use if/else")
    return _expr(s)


def _block(src):
    """Statements/blocks of a C# body -> Rust-subset text."""
    out = []
    i, n = 0, len(src)
    while i < n:
        while i < n and src[i].isspace():
            i += 1
        if i >= n:
            break
        if src[i] == "}":
            raise ScriptError("unbalanced } in script")
        m = re.match(r"(else\s+if|if|while|for|else)\b\s*", src[i:])
        if m:
            kw = m.group(1)
            j = i + m.end()
            head = ""
            if kw != "else":
                if src[j] != "(":
                    raise ScriptError("expected ( after %s" % kw)
                c = _match(src, j)
                head = src[j + 1:c]
                j = c + 1
            while j < n and src[j].isspace():
                j += 1
            if j < n and src[j] == "{":
                e = _match(src, j, "{", "}")
                body = _block(src[j + 1:e])
                i = e + 1
            else:                                   # single statement body
                e = src.index(";", j)
                body = _stmt(src[j:e + 1])
                i = e + 1
            if kw in ("if", "else if", "while"):
                out.append("%s %s { %s }" % (kw, _expr(head), body))
            elif kw == "else":
                out.append("else { %s }" % body)
            else:
                parts = [p.strip() for p in head.split(";")]
                if len(parts) != 3:
                    raise ScriptError("for needs init; cond; step")
                init = _stmt(parts[0] + ";")
                step = _stmt(parts[2] + ";") if not re.search(r"[+-]=", parts[2]) else \
                    _expr(parts[2]) + ";"
                if "continue" in body:
                    raise ScriptError("`continue` in for is not supported; use if")
                out.append("{ %s while %s { %s %s } }" % (init, _expr(parts[1]), body, step))
            continue
        if src[i] == "{":
            e = _match(src, i, "{", "}")
            out.append("{ %s }" % _block(src[i + 1:e]))
            i = e + 1
            continue
        e = src.index(";", i)
        out.append(_stmt(src[i:e + 1]))
        i = e + 1
    return " ".join(x for x in out if x)


# --------------------------------------------------------------- translation
def translate(source):
    """C# [GpuKernel] class -> (rust source, info). info: name, entry, params
    [(name, type, default)], uses_input."""
    src = _strip_comments(source)
    m = re.search(r"\[GpuKernel[^\]]*\]\s*(?:public\s+|sealed\s+|static\s+)*class\s+(\w+)[^{]*\{", src)
    if not m:
        raise ScriptError("no [GpuKernel] class found")
    name = m.group(1)
    cend = _match(src, m.end() - 1, "{", "}")
    cbody = src[m.end():cend]
    um = re.search(r"void\s+Update\s*\(([^)]*)\)\s*\{", cbody)
    if not um:
        raise ScriptError("%s has no `void Update(...)` method" % name)
    uend = _match(cbody, um.end() - 1, "{", "}")
    ubody = cbody[um.end():uend]
    rest = cbody[:um.start()] + cbody[uend + 1:]
    params = []
    for fm in re.finditer(r"(?:public\s+|private\s+|readonly\s+)*(float|int|uint|bool)\s+(\w+)\s*(?:=\s*([^;]+))?;", rest):
        ty, fname, init = TYPES[fm.group(1)], fm.group(2), fm.group(3)
        if fname in STD or fname in ("x", "y", "vx", "vy", "i", "tag"):
            raise ScriptError("field %s hides a built-in name" % fname)
        if init is None:
            default = 0
        elif ty == "bool":
            default = 1 if init.strip() == "true" else 0
        else:
            try:
                default = (float if ty == "f32" else int)(re.sub(r"[fF]$", "", init.strip()))
            except ValueError:
                raise ScriptError("field %s: initializer must be a number literal" % fname)
        params.append((fname, ty, default))
    if re.search(r"\b\w+\s*\([^)]*\)\s*\{", rest):
        raise ScriptError("only fields and Update are supported in a GpuKernel class")
    uses_input = "Input2D" in ubody
    body = _block(ubody)
    entry = "script_" + name.lower()
    decl = ["    #[binding(%d)] %s: %s," % (i, n, t) for i, (n, t) in enumerate(BINDINGS)]
    decl += ["    dt: f32,", "    time: f32,", "    count: u32,", "    WorldWidth: f32,", "    WorldHeight: f32,"]
    decl += ["    %s%s: %s," % (n, "_raw" if t == "bool" else "", "u32" if t == "bool" else t)
             for n, t, _ in params]
    unpack = "".join("    let %s: bool = %s_raw != 0;\n" % (n, n) for n, t, _ in params if t == "bool")
    rust = (
        "// generated from %s.cs by prowl_editor.gpu_physics.script\n"
        "#[kernel(local_size = 64)]\nfn %s(\n%s\n) {\n"
        "    let index: u32 = gpu_global_id(0);\n"
        "    if index >= count {\n        return;\n    }\n"
        "%s"
        "    let i: i32 = index as i32;\n"
        "    let tag: u32 = tags[index as usize];\n"
        "    let p: usize = (index * 2) as usize;\n"
        "    let mut x: f32 = positions[p];\n    let mut y: f32 = positions[p + 1];\n"
        "    let mut vx: f32 = (x - previous_positions[p]) / dt;\n"
        "    let mut vy: f32 = (y - previous_positions[p + 1]) / dt;\n"
        "    %s\n"
        "    positions[p] = x;\n    positions[p + 1] = y;\n"
        "    previous_positions[p] = x - vx * dt;\n    previous_positions[p + 1] = y - vy * dt;\n}\n"
    ) % (name, entry, "\n".join(decl), unpack, body)
    return rust, {"name": name, "entry": entry, "params": params, "uses_input": uses_input}


def compile_rust(rust, workdir=None):
    """Rust-subset kernel source -> SPIR-V bytes (params in a storage buffer,
    so the wgpu backend needs no push-constant feature)."""
    crust = crust_path.ensure()
    with tempfile.TemporaryDirectory(dir=workdir) as td:
        src = os.path.join(td, "script.rs")
        out = os.path.join(td, "script.spv")
        with open(src, "w") as fh:
            fh.write(rust)
        env = dict(os.environ, CRUST_SPIRV_PUSH="buffer",
                   PYTHONPATH=crust + os.pathsep + os.environ.get("PYTHONPATH", ""))
        p = subprocess.run([sys.executable, "-m", "shivyc.main", "--target", "spirv", src, "-o", out],
                           cwd=crust, env=env, capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(out):
            msg = re.sub(r"\x1b\[[0-9;]*m", "", p.stdout + p.stderr).strip()
            raise ScriptError("GPU script did not compile:\n" + msg)
        with open(out, "rb") as fh:
            return fh.read()


class GpuScript:
    """A compiled [GpuKernel] script. add it to a GpuWorld with world.add_script."""

    def __init__(self, source, params=None, backend=None):
        if os.path.exists(source) if len(source) < 4096 and "\n" not in source else False:
            with open(source) as fh:
                source = fh.read()
        self.rust, self.info = translate(source)
        self.params = {n: d for n, _, d in self.info["params"]}
        self.params.update(params or {})
        self.time = 0.0
        self.spv = compile_rust(self.rust)
        self.prog = None
        self.backend = None
        if backend is not None:
            self.attach(backend)

    @property
    def name(self):
        return self.info["name"]

    def attach(self, backend):
        if self.backend is backend:
            return
        self.prog = backend.load(self.spv)
        self.backend = backend

    def pack(self, world, dt):
        out = struct.pack("<ffIff", dt, self.time, world.n, world.world[0], world.world[1])
        for n, t, d in self.info["params"]:
            v = self.params.get(n, d)
            out += struct.pack("<" + FMT[t], (1 if v else 0) if t == "bool" else (float(v) if t == "f32" else int(v)))
        return out

    def run(self, world, dt):
        self.attach(world.b)
        self.time += dt
        entry = self.info["entry"]
        iface = self.prog.iface[entry]
        by_name = {"positions": world.positions, "previous_positions": world.previous,
                   "radius": world.radius, "tags": world.tags,
                   "input_u32": world.input, "input_f32": world.input}
        binds = {}
        for buf in iface["buffers"]:
            binds[buf["binding"]] = by_name[buf["name"]]
        local = iface["local_size"][0]
        groups = (world.n + local - 1) // local
        world.b.dispatch(self.prog, entry, (groups, 1, 1), binds, self.pack(world, dt))


SAMPLE_MAGNET = """
[GpuKernel]
public class Magnet {
    public float Strength = 30f;
    public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) {
        float dx = Input2D.MouseX - x;
        float dy = Input2D.MouseY - y;
        if (Input2D.MouseDown(0)) {
            vx += dx * Strength * dt;
            vy += dy * Strength * dt;
        }
        if (Input2D.Key(Input2D.Space)) {
            vy += 40f * dt;
        }
    }
}
"""
