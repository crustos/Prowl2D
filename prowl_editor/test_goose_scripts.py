"""Goose as a script language (languages.py, tools/script_langs.py, tools/script_native.py) and Samples/SlimeJumpGoose.

Without the engine library (it needs a .NET SDK to build), what can be checked is: the language's marker, the scanner, the way a build error is reported, that every Goose script of
the sample lowers and compiles with the engine's calls and the glue, and that the Goose scripts do what the Rust ones do. That last one runs the callbacks of both builds under a
driver and a stub engine (test_stub_engine.c) that logs each engine call: the two logs must agree, a float to within the last digit (Crust lowers Rust's `0.375 * 0.9` in double
precision, Goose keeps `f32` arithmetic in 32 bits, as its spec says). It needs gcc and Crust (the sibling folder `crust`, or $CRUST_HOME); without them it is skipped.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "ccsharp"))

from prowl_editor import languages, scriptbuild   # noqa: E402
import script_langs                               # noqa: E402
import script_native                              # noqa: E402

GOOSE_DIR = os.path.join(ROOT, "Samples", "SlimeJumpGoose")
RUST_DIR = os.path.join(ROOT, "Samples", "SlimeJumpRust")
ENGINE_CS = os.path.join(ROOT, "Native", "Engine2D", "Engine.cs")


def crust_ready():
    home = script_native.crust_home()
    return shutil.which("gcc") is not None and os.path.exists(os.path.join(home, "tools", "goose2c.py"))


class TestLanguage(unittest.TestCase):
    def test_goose_is_one_of_the_languages(self):
        g = languages.get("goose")
        self.assertEqual((g.name, g.ext), ("Goose", ".goose"))
        self.assertIs(languages.by_extension("Samples/SlimeJumpGoose/Slime.goose"), g)
        self.assertEqual(script_langs.language_of("x.goose"), "goose")
        self.assertIn("goose", script_langs.BUILT)

    def test_the_template_is_a_script_that_scans_and_has_a_callback(self):
        g = languages.get("goose")
        text = g.new_text("Spinner")
        self.assertEqual(g.classes(text), ["Spinner"])
        d = tempfile.mkdtemp()
        p = os.path.join(d, "Spinner.goose")
        with open(p, "w") as f:
            f.write(text)
        (s,) = script_langs.scan_file(p)
        self.assertEqual((s["name"], s["capacity"], s["callbacks"], s["language"]), ("Spinner", 16, ["Update"], "goose"))

    def test_the_marker_is_only_a_marker_directly_above_a_struct(self):
        g = languages.get("goose")
        text = ("// script(max_instances = 4)\n\n// a note\nroot struct A { node: i32 }\n"
                "/* // script(max_instances = 2)\nstruct Hidden { node: i32 } */\nstruct NoMarker { node: i32 }\n")
        self.assertEqual(g.classes(text), ["A"])


class TestScanner(unittest.TestCase):
    def scan(self, text):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "T.goose")
        with open(p, "w") as f:
            f.write(text)
        return script_langs.scan_file(p)

    def refused(self, text):
        with self.assertRaises(script_langs.GenError) as c:
            self.scan(text)
        return str(c.exception)

    def test_callbacks_are_the_functions_that_take_the_struct_by_reference(self):
        (s,) = self.scan("// script(max_instances = 8)\nstruct G { node: i32 }\nfn start(s: G&) {}\n"
                         "fn on_trigger_enter_2d(s: G&, other: i32) {}\nfn update(x: i32) {}\n")
        self.assertEqual(s["callbacks"], ["Start", "OnTriggerEnter2D"])           # (update(x: i32) is another type's function)

    def test_a_struct_taken_by_value_would_change_a_copy(self):
        self.assertIn("by reference", self.refused("// script(max_instances = 8)\nstruct G { node: i32 }\nfn update(s: G) {}\n"))

    def test_a_script_needs_a_node_field_and_a_capacity(self):
        self.assertIn("node: i32", self.refused("// script(max_instances = 8)\nstruct G { n: i32 }\n"))
        self.assertIn("integer literal", self.refused("// script(max_instances = x)\nstruct G { node: i32 }\n"))
        self.assertIn("above a struct", self.refused("// script(max_instances = 3)\nfn f() {}\n"))

    def test_lifecycle_callbacks_take_nothing_and_collisions_take_the_other_node(self):
        self.assertIn("no parameters", self.refused("// script(max_instances = 3)\nstruct G { node: i32 }\nfn start(s: G&, k: i32) {}\n"))
        self.assertIn("other node", self.refused("// script(max_instances = 3)\nstruct G { node: i32 }\nfn on_trigger_enter_2d(s: G&) {}\n"))


class TestDiagnostics(unittest.TestCase):
    def test_a_goose_error_is_placed_at_the_scripts_own_line(self):
        (d,) = scriptbuild.parse_diagnostics("/tmp/work/native/Slime.goose:251: error: unknown name 'SCRIPT_BULLET'")
        self.assertEqual((d.script, d.line, d.severity), ("Slime", 251, "error"))
        self.assertIn("SCRIPT_BULLET", d.message)


@unittest.skipUnless(crust_ready(), "needs gcc and Crust (the sibling folder `crust` or $CRUST_HOME)")
class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import prowl2d_so
        cls.api = prowl2d_so.parse_api(ENGINE_CS)
        cls.work = tempfile.mkdtemp(prefix="goose_scripts_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def build_dir(self, folder, ext, builder):
        native = os.path.join(self.work, "native_" + ext.strip("."))
        os.makedirs(native, exist_ok=True)
        scripts = []
        for f in sorted(glob.glob(os.path.join(folder, "*" + ext))):
            scripts += script_langs.scan_file(f)
        ids = {s["name"]: i for i, s in enumerate(scripts)}
        objs = [builder(s, s["where"].rsplit(":", 1)[0], native, self.work, "gcc", self.api, ids) for s in scripts]
        return scripts, objs

    def test_every_script_of_the_sample_lowers_and_compiles_and_keeps_only_its_glue_global(self):
        scripts, objs = self.build_dir(GOOSE_DIR, ".goose", script_native.build_goose)
        self.assertEqual(sorted(s["name"] for s in scripts), sorted(slime_scripts()))
        for s, obj in zip(scripts, objs):
            syms = subprocess.run(["nm", "-g", "--defined-only", obj], capture_output=True, text=True).stdout.split()
            names = sorted(x for x in syms if x.startswith("p2dn_") or x.startswith("gs_") or x.startswith("p2d_"))
            self.assertEqual(names, sorted(script_native.glue_names(s)), s["name"])

    def test_a_script_that_does_not_fit_the_subset_is_refused_with_its_line(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "Oops.goose")
        with open(p, "w") as f:
            f.write("// script(max_instances = 2)\nstruct Oops {\n    node: i32,\n}\n\nfn start(o: Oops&) {\n    set_pos(o.node, 1.0, undefined_thing);\n}\n")
        (s,) = script_langs.scan_file(p)
        with self.assertRaises(script_native.Failed) as c:
            script_native.build_goose(s, p, d, self.work, "gcc", self.api, {})
        (diag,) = scriptbuild.parse_diagnostics(c.exception.args[0])
        self.assertEqual((diag.script, diag.line), ("Oops", 7))

    def test_the_goose_scripts_do_what_the_rust_scripts_do(self):
        rs_scripts, rs_objs = self.build_dir(RUST_DIR, ".rs", script_native.build_rust)
        gs_scripts, gs_objs = self.build_dir(GOOSE_DIR, ".goose", script_native.build_goose)
        self.assertEqual([(s["name"], s["capacity"], s["callbacks"]) for s in rs_scripts], [(s["name"], s["capacity"], s["callbacks"]) for s in gs_scripts])
        d = tempfile.mkdtemp(prefix="goose_vs_rust_")
        with open(os.path.join(d, "driver.c"), "w") as f:
            f.write(driver_c(gs_scripts))
        shutil.copy(os.path.join(HERE, "test_stub_engine.c"), os.path.join(d, "stub.c"))
        logs = {}
        for tag, objs in (("rust", rs_objs), ("goose", gs_objs)):
            exe = os.path.join(d, tag)
            r = subprocess.run(["gcc", "-w", "-o", exe, os.path.join(d, "driver.c"), os.path.join(d, "stub.c")] + objs + ["-lm"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[:2000])
            log = os.path.join(d, tag + ".log")
            subprocess.run([exe, log], check=True, timeout=120)
            with open(log) as f:
                logs[tag] = f.read().splitlines()
        a, b = logs["rust"], logs["goose"]
        self.assertGreater(len(a), 10000)                         # (the driver exercised the scripts: that many engine calls)
        self.assertEqual(len(a), len(b))
        num = re.compile(r"-?\d+\.\d+")
        for i, (x, y) in enumerate(zip(a, b)):
            if x == y:
                continue
            xs, ys = num.findall(x), num.findall(y)
            ok = num.sub("#", x) == num.sub("#", y) and len(xs) == len(ys) and all(abs(float(p) - float(q)) <= 2e-3 for p, q in zip(xs, ys))
            self.assertTrue(ok, "line %d differs:\n  rust : %s\n  goose: %s" % (i + 1, x, y))


def slime_scripts():
    from prowl_editor.slime_rust import SCRIPTS
    return SCRIPTS


def driver_c(scripts):
    """A C driver that, for every script and six seeds, runs its Start and then 160 frames of FixedUpdate and the other callbacks while it moves the nodes, presses keys, and
    changes the globals and tags at random (a fixed generator: both builds see the same), logging every engine call."""
    L = ["#include <stdio.h>", "void stub_seed(unsigned); void stub_log(FILE*); void stub_reset(void); void stub_node(int,float,float); void stub_key(int,int);",
         "void stub_mouse(int,int); void stub_global(int,float); void stub_tag(int,int);"]
    for s in scripts:
        L.append("void p2dn_%s_Reset(int);" % s["name"])
        for cb in s["callbacks"]:
            L.append("void p2dn_%s_%s(int,int);" % (s["name"], cb))
    L += ["static unsigned r = 1; static unsigned rd(void) { r = r * 1103515245u + 12345u; return (r >> 8) & 0xffff; }",
          "static float rf(float lo, float hi) { return lo + (hi - lo) * (rd() % 1000) / 1000.0f; }",
          "int main(int argc, char **argv) {", "  FILE *f = fopen(argv[1], \"w\"); stub_log(f);"]
    for si, s in enumerate(scripts):
        n = s["name"]
        L += ["  for (unsigned seed = 1; seed <= 6; seed++) {",
              "    r = seed * 7919u + %d; stub_reset(); stub_seed(seed);" % si,
              "    for (int n = 1; n < 6; n++) stub_node(n, rf(8, 12), rf(3, 6));",
              "    fprintf(f, \"== %s seed %%u\\n\", seed);" % n,
              "    stub_global(21, 2); p2dn_%s_Reset(0);" % n]
        if "Start" in s["callbacks"]:
            L.append("    p2dn_%s_Start(0, 3);" % n)
        L += ["    for (int fr = 0; fr < 160; fr++) {",
              "      for (int k = 1; k < 6; k++) if (rd() % 5 == 0) stub_node(k, rf(8, 12), rf(3, 6));",
              "      { int keys[6] = {263, 262, 32, 265, 83, 84}; for (int k = 0; k < 6; k++) if (rd() % 4 == 0) stub_key(keys[k], rd() % 2); }",
              "      if (rd() % 6 == 0) stub_mouse(0, rd() % 2);",
              "      if (rd() % 6 == 0) stub_mouse(2, rd() % 2);",
              "      if (rd() % 9 == 0) stub_global(6, rd() % 2);",
              "      if (rd() % 7 == 0) { stub_global(7, rf(-1, 1)); stub_global(8, rd() % 2); stub_global(9, rd() % 2); stub_global(12, rd() % 2); stub_global(13, rf(-1, 1));",
              "        stub_global(15, rd() % 2); stub_global(16, rd() % 2); stub_global(18, rd() % 2); stub_global(10, rf(5, 15)); stub_global(11, rf(2, 7)); }",
              "      if (rd() % 11 == 0) { stub_global(0, rd() % 3); stub_global(1, rd() % 3); }",
              "      if (rd() % 8 == 0) stub_tag(rd() % 5 + 1, (int[]){1, 2, 3, 4, 5, 7, 9, 99}[rd() % 8]);"]
        for cb in s["callbacks"]:
            if cb != "Start":
                L.append("      p2dn_%s_%s(0, 3);" % (n, cb))
        L += ["    }", "  }"]
    L += ["  fclose(f); return 0; }"]
    return "\n".join(L)


if __name__ == "__main__":
    unittest.main()
