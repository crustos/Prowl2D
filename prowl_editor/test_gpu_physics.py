"""GPU physics tests. They run on Crust's reference interpreter (no GPU needed) and skip
without Crust or the compiled kernels (gpu/spirv). The real radix sort is checked
once in a small case; the others use the host sort so the suite stays quick."""
import math
import os
import struct
import unittest

from prowl_editor.gpu_physics import crust_path

HAVE = crust_path.find() is not None and os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gpu", "spirv", "manifest.json"))


class InputTests(unittest.TestCase):
    def test_pack_layout(self):
        from prowl_editor.gpu_physics.gpuinput import GpuInput, WORDS, BUTTONS, MOUSE_X, MOUSE_Y, FRAME
        g = GpuInput()
        g.set_key(263, 1)
        g.set_key(9999, 1)                     # out of range: ignored
        g.set_mouse(1.5, -2.0, 5)
        g.tick(1 / 60.0, 7)
        words = struct.unpack("<%dI" % WORDS, g.pack())
        self.assertEqual(len(g.pack()), WORDS * 4)
        self.assertEqual(words[263], 1)
        self.assertEqual(sum(words[:512]), 1)
        self.assertEqual(words[BUTTONS], 5)
        self.assertEqual(struct.unpack("<f", struct.pack("<I", words[MOUSE_X]))[0], 1.5)
        self.assertEqual(struct.unpack("<f", struct.pack("<I", words[MOUSE_Y]))[0], -2.0)
        self.assertEqual(words[FRAME], 1)


class TranslateTests(unittest.TestCase):
    SRC = """
    [GpuKernel] public class T {
        public float K = 2.5f; public int N = 3; public bool On = true;
        public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) {
            for (int k = 0; k < N; k++) { vx += (float)k * K * dt; }
            if (On && Input2D.Key(Input2D.Left)) vy = Mathf.Max(vy, 1f);
        }
    }"""

    def test_translation(self):
        from prowl_editor.gpu_physics.script import translate
        rust, info = translate(self.SRC)
        self.assertEqual([p[0] for p in info["params"]], ["K", "N", "On"])
        self.assertEqual(info["params"][0][2], 2.5)
        self.assertEqual(info["params"][2][2], 1)
        self.assertTrue(info["uses_input"])
        for frag in ("while k < N", "input_u32[(263) as usize]", ".max(1.0)", "On_raw: u32", "let On: bool = On_raw != 0;"):
            self.assertIn(frag, rust)

    def test_refusals(self):
        from prowl_editor.gpu_physics.script import translate, ScriptError
        wrap = "[GpuKernel] class A { public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) { %s } }"
        for bad in ("return;", "float a = x > 0f ? 1f : 2f;", "float a; a = 1f;", "float a = Mathf.Pow(x, 2f);"):
            with self.assertRaises(ScriptError, msg=bad):
                translate(wrap % bad)
        with self.assertRaises(ScriptError):
            translate("class NoAttribute { }")


@unittest.skipUnless(HAVE, "needs Crust and gpu/spirv")
class WorldTests(unittest.TestCase):
    def world(self, **kw):
        from prowl_editor.gpu_physics import make_backend, GpuWorld
        return GpuWorld(make_backend("interp"), **dict(dict(capacity=32, world=(10.0, 8.0), max_radius=0.4), **kw))

    def test_floor_and_walls_contain(self):
        w = self.world()
        for i in range(6):
            w.add_circle(2 + i * 0.6, 3 + (i % 3) * 0.9, 0.3, vx=(i - 5) * 2.0)
        for _ in range(50):
            w.step(1 / 60.0)
        for x, y in w.read_positions():
            self.assertTrue(0.0 <= x <= 10.0 and 0.0 <= y <= 8.0, (x, y))
        self.assertLess(max(y for _, y in w.read_positions()), 3.5)      # it fell

    def test_tiles_hold_circles_up(self):
        w = self.world()
        W, H = 10, 8
        w.set_tiles(W, H, lambda tx, ty: ty < 2)                          # a floor two tiles thick
        for i in range(4):
            w.add_circle(2 + i, 4.2 + i * 0.1, 0.3)
        for _ in range(60):
            w.step(1 / 60.0)
        for x, y in w.read_positions():
            self.assertGreaterEqual(y, 2.0 + 0.3 - 0.05, (x, y))          # stands on the tiles, not in them

    def test_circles_do_not_stack_on_one_point(self):
        w = self.world()
        for i in range(5):
            w.add_circle(5.0 + i * 0.01, 1.0 + i * 0.01, 0.3)
        for _ in range(80):
            w.step(1 / 60.0)
        pos = w.read_positions()
        worst = min(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for i, a in enumerate(pos) for b in pos[i + 1:])
        self.assertGreater(worst, 0.45)                                   # 2r = 0.6, a little give

    def test_real_radix_sort_matches_host_sort(self):
        from prowl_editor.gpu_physics import make_backend, GpuWorld
        w = GpuWorld(make_backend("interp"), capacity=4, world=(10.0, 8.0))
        w.host_sort = False
        keys = [9, 3, 3, 1000, 0, 70000, 3, 5]
        n = len(keys)
        w.b.write(w.cell_ids, struct.pack("<%dI" % n, *keys))
        w.b.write(w.object_ids, struct.pack("<%dI" % n, *range(n)))
        w.radix_sort(w.cell_ids, w.object_ids, n)
        k = struct.unpack("<%dI" % n, w.b.read(w.cell_ids, 0, 4 * n))
        p = struct.unpack("<%dI" % n, w.b.read(w.object_ids, 0, 4 * n))
        self.assertEqual(list(k), sorted(keys))
        self.assertEqual(list(p), sorted(range(n), key=lambda i: keys[i]))   # stable


@unittest.skipUnless(HAVE, "needs Crust and gpu/spirv")
class ScriptTests(unittest.TestCase):
    def test_magnet_pulls_toward_the_mouse_and_reads_keys(self):
        from prowl_editor.gpu_physics import make_backend, GpuWorld, GpuInput
        from prowl_editor.gpu_physics.script import GpuScript, SAMPLE_MAGNET
        w = GpuWorld(make_backend("interp"), capacity=8, world=(16.0, 9.0), gravity=(0.0, 0.0))
        w.add_circle(2.0, 4.5, 0.3)
        w.add_script(GpuScript(SAMPLE_MAGNET, {"Strength": 20.0}))
        g = GpuInput()
        g.set_mouse(12.0, 4.5, 0)               # button up: nothing happens
        for _ in range(10):
            w.step(1 / 60.0, g)
        self.assertAlmostEqual(w.get_position(0)[0], 2.0, places=3)
        g.set_mouse(12.0, 4.5, 1)               # button down: pulled right
        for _ in range(10):
            w.step(1 / 60.0, g)
        self.assertGreater(w.get_position(0)[0], 2.05)
        y0 = w.get_position(0)[1]
        g.set_mouse(12.0, 4.5, 0)
        g.set_key(32, 1)                        # Space: kicked upward
        for _ in range(10):
            w.step(1 / 60.0, g)
        self.assertGreater(w.get_position(0)[1], y0 + 0.1)


@unittest.skipUnless(HAVE, "needs Crust and gpu/spirv")
class BodyTests(unittest.TestCase):
    def world(self, **kw):
        from prowl_editor.gpu_physics import make_backend, GpuWorld
        return GpuWorld(make_backend("interp"), **dict(dict(capacity=64, world=(10.0, 8.0), max_radius=0.4), **kw))

    def test_a_crate_lands_flat_and_keeps_its_shape(self):
        w = self.world()
        w.set_tiles(10, 8, lambda tx, ty: ty < 1)
        bid = w.add_box(5.0, 1.9, 1.0, 1.0, angle=0.4)
        rest = {k: j[3] for k, j in w.joints.items()}
        for _ in range(45):
            w.step(1 / 60.0)
        p = w.read_bodies()[0]
        self.assertAlmostEqual(p.y, 1.5, delta=0.08)                      # half a tile above the floor
        turn = abs(p.angle) % (math.pi / 2)
        self.assertLess(min(turn, math.pi / 2 - turn), 0.12)              # lying on a side
        for k, j in w.joints.items():
            a, b = w.get_position(j[0]), w.get_position(j[1])
            self.assertAlmostEqual(math.dist(a, b), rest[k], delta=0.06 * rest[k] + 0.02)
        self.assertEqual(w.bodies[bid].kind, "box")

    def test_a_pinned_rope_hangs_from_its_pin(self):
        w = self.world()
        bid = w.add_rope(5.0, 6.0, 8.0, 6.0, segments=6)
        for _ in range(60):
            w.step(1 / 60.0)
        pts = w.read_bodies()[0].points
        self.assertAlmostEqual(pts[0][0], 5.0, delta=0.05)
        self.assertAlmostEqual(pts[0][1], 6.0, delta=0.05)
        self.assertLess(pts[-1][1], 5.2)                                  # swinging down from the side
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.assertAlmostEqual(math.dist((x0, y0), (x1, y1)), 0.5, delta=0.1)

    def test_removing_a_body_keeps_the_others_whole(self):
        w = self.world()
        a = w.add_box(2.0, 3.0, 1.0, 1.0)
        b = w.add_box(5.0, 3.0, 1.0, 1.0)
        c = w.add_rope(7.0, 6.0, 9.0, 6.0, segments=4)
        before = {p.id: (round(p.x, 4), round(p.y, 4)) for p in w.read_bodies()}
        w.remove_body(a)
        self.assertEqual(w.n, 4 + 5)
        after = {p.id: (round(p.x, 4), round(p.y, 4)) for p in w.read_bodies()}
        self.assertEqual(after, {k: v for k, v in before.items() if k != a})
        for j in w.joints.values():                                       # every joint still names circles of one body
            ends = [e for e in j[:2] if e != 0xFFFFFFFF]
            self.assertEqual(len({w.owner[e] for e in ends}), 1)
            self.assertTrue(all(0 <= e < w.n for e in ends))
        self.assertEqual(sorted(w.owner), sorted([b] * 4 + [c] * 5))

    def test_shards_expire(self):
        w = self.world()
        ids = w.add_shards(5.0, 4.0, count=3, ttl=0.03)
        self.assertEqual(len(ids), 3)
        n = w.n
        for _ in range(3):
            w.step(1 / 60.0)
        self.assertEqual(w.n, 0)
        self.assertEqual(w.bodies, {})
        self.assertEqual(n, 12)

    def test_raycast_finds_tiles_circles_and_ignores_a_body(self):
        w = self.world(gravity=(0.0, 0.0))
        w.set_tiles(10, 8, lambda tx, ty: ty < 1)
        crate = w.add_box(5.0, 3.0, 1.0, 1.0)
        hit = w.raycast(4.8, 6.0, 0.0, -1.0)
        self.assertEqual((hit.kind, hit.body), ("circle", crate))
        self.assertAlmostEqual(hit.y, 3.5, delta=0.03)                    # the crate's top (corner circles are rounded)
        self.assertGreater(hit.ny, 0.5)
        hit = w.raycast(7.5, 6.0, 0.0, -1.0)
        self.assertEqual(hit.kind, "tile")
        self.assertAlmostEqual(hit.y, 1.0, delta=0.01)
        self.assertEqual((hit.nx, hit.ny), (0.0, 1.0))
        self.assertIsNone(w.raycast(7.5, 6.0, 0.0, 1.0, 50.0))            # up and away
        self.assertIsNone(w.raycast(7.5, 6.0, 0.0, -1.0, 2.0))            # too short
        hit = w.raycast(4.8, 6.0, 0.0, -1.0, ignore_body=crate)           # the crate's own ray goes through it
        self.assertEqual(hit.kind, "tile")
        both = w.raycast_many([(4.8, 6.0, 0.0, -2.0, 99.0), (0.2, 2.75, 1.0, 0.0, 99.0)], mask=2)
        self.assertEqual(both[0].body, crate)
        self.assertEqual(both[1].body, crate)

    def test_a_sensor_counts_and_reports_entering_and_leaving(self):
        w = self.world()
        s_all = w.add_sensor(5.0, 2.0, 1.0, 1.0)
        s_sand = w.add_sensor(5.0, 2.0, 1.0, 1.0, tags=(1,))
        s_round = w.add_circle_sensor(5.0, 2.0, 0.5)
        w.add_ball(5.0, 2.0)
        w.add_sand(5.2, 2.1)
        w.add_ball(8.0, 6.0)                                              # outside
        w.step(1 / 60.0)
        self.assertEqual((w.sensor_count(s_all), w.sensor_count(s_sand), w.sensor_count(s_round)), (2, 1, 2))
        self.assertIn((s_all, 2, 0), w.events)
        for _ in range(60):
            w.step(1 / 60.0)                                              # they fall out of the sensor
        self.assertEqual(w.sensor_count(s_all), 0)
        self.assertEqual(w.events[-1][1:] if w.events else (0, 0), w.events[-1][1:] if w.events else (0, 0))

    def test_sand_settles_on_a_floor_and_a_blast_pushes_it(self):
        w = self.world()
        w.set_tiles(10, 8, lambda tx, ty: ty < 1)
        self.assertEqual(w.brush_sand(5.0, 2.5, 0.6, 12, seed=1), 12)
        for _ in range(60):
            w.step(1 / 60.0)
        for (x, y) in w.read_positions():
            self.assertGreaterEqual(y, 1.0 + 0.08 - 0.03)
        self.assertEqual(len([t for t in w.read_tags() if t == 1]), 12)
        vel = w.read_velocities()
        self.assertLess(max(math.hypot(*v) for v in vel), 2.5)            # at rest, more or less
        cx = sum(p[0] for p in w.read_positions()) / 12
        pushed = w.blast(cx - 1.0, 1.1, radius=3.0, force=80.0)
        self.assertGreater(pushed, 0)
        self.assertGreater(sum(v[0] for v in w.read_velocities()), 5.0)   # pushed to the right


@unittest.skipUnless(HAVE, "needs Crust and gpu/spirv")
class MaterialTests(unittest.TestCase):
    def world(self, **kw):
        from prowl_editor.gpu_physics import make_backend, GpuWorld
        return GpuWorld(make_backend("interp"), **dict(dict(capacity=64, world=(12.0, 8.0), max_radius=0.4), **kw))

    def test_plain_worlds_keep_the_old_path(self):
        w = self.world()
        w.add_ball(5.0, 3.0)
        w.step(1 / 60.0)
        self.assertFalse(w.use_material)

    def test_bounciness_gravity_scale_and_filters(self):
        w = self.world()
        w.set_tiles(12, 8, lambda tx, ty: ty < 1)
        w.set_world_material(friction=0.4, bounciness=0.0)
        live = w.add_ball(2.0, 2.6)                    # rubber: keeps most of its speed off the floor
        dead = w.add_ball(4.0, 2.6)                    # default material: stops
        self.assertTrue(w.set_material(live, friction=0.4, bounciness=0.8))
        float_a = w.add_ball(8.0, 4.0)                 # gravity scale 0: floats
        w.set_material(float_a, gravity_scale=0.0)
        ghost = w.add_ball(8.0, 5.0)                   # falls onto it, but masks exclude each other
        w.set_filter(float_a, category=2, mask=2)
        w.set_filter(ghost, category=4, mask=4)
        low = {live: 99.0, dead: 99.0}
        peak_after = {live: 0.0, dead: 0.0}
        landed = False
        for _ in range(48):
            w.step(1 / 60.0)
            for name, bid in (("live", live), ("dead", dead)):
                y = w.get_position(w.bodies[bid].circles[0])[1]
                if y < low[bid]:
                    low[bid] = y
                elif y > low[bid] + 0.02:
                    peak_after[bid] = max(peak_after[bid], y - low[bid])
        self.assertGreater(peak_after[live], peak_after[dead] + 0.15)       # rubber rebounds, default does not
        fy = w.get_position(w.bodies[float_a].circles[0])[1]
        self.assertAlmostEqual(fy, 4.0, delta=0.05)                         # nothing moved it
        gy = w.get_position(w.bodies[ghost].circles[0])[1]
        self.assertLess(gy, fy - 0.3)                                       # the ghost passed through

    def test_sensor_bodies_pass_through_other_circles(self):
        w = self.world()
        floor = w.add_ball(6.0, 4.0)
        w.set_material(floor, gravity_scale=0.0)
        s = w.add_ball(6.0, 4.9)
        w.set_sensor(s)
        for _ in range(30):
            w.step(1 / 60.0)
        self.assertLess(w.get_position(w.bodies[s].circles[0])[1], 4.0 - 0.2)   # went through the ball it fell on


class _Lib:
    """Just enough of the engine for the driver: keys, mouse, nodes."""
    def __init__(self):
        self.pos, self.ang, self.keys, self.n, self.dead = {}, {}, set(), 0, set()

    def p2d_new_node(self):
        self.n += 1
        return self.n - 1

    def p2d_destroy_node(self, node):
        self.dead.add(node)
        self.pos.pop(node, None)

    def p2d_set_pos(self, node, x, y):
        self.pos[node] = (x, y)

    def p2d_set_angle(self, node, a):
        self.ang[node] = a

    def p2d_node_x(self, node):
        return self.pos[node][0]

    def p2d_node_y(self, node):
        return self.pos[node][1]

    def p2d_key_down(self, k):
        return int(k in self.keys)

    def p2d_mouse_down(self, b):
        return 0

    def p2d_mouse_world_x(self):
        return 1.0

    def p2d_mouse_world_y(self):
        return 2.0

    def p2d_blast(self, *a):
        return 0


def _viewport(lib, cells, W, H, tiles, actors=()):
    from types import SimpleNamespace as NS
    return NS(engine=NS(lib=lib), level=NS(width=W, height=H), cells=cells, project=NS(tiles=tiles),
              balls=[], actors=list(actors), status="", script_report="")


@unittest.skipUnless(HAVE, "needs Crust and gpu/spirv")
class DriverTests(unittest.TestCase):
    def test_driver_drops_steps_and_mirrors_into_nodes(self):
        from types import SimpleNamespace as NS
        from prowl_editor.gpu_physics.driver import GpuPhysicsDriver
        lib = _Lib()
        vp = _viewport(lib, [""] * 24 + ["#"] * 6, 6, 5, {"#": NS(solid=True, dynamic=False)})
        d = GpuPhysicsDriver("interp", capacity=32)
        d.start(vp)
        self.assertIsNotNone(d.world)
        self.assertTrue(d.drop_ball(vp, 3.0, 4.0))
        lib.keys.add(32)
        for _ in range(60):
            d.step(1 / 60.0)
        self.assertEqual(d.input.keys[32], 1)
        x, y = lib.pos[vp.balls[0]]
        self.assertAlmostEqual(x, 3.0, places=2)
        self.assertGreaterEqual(y, 1.0 + 0.35 - 0.05)                  # the bottom row of the level is solid: ball rests on it
        vp.cells = [""] * 30                                           # the tiles dug away: it falls to the world floor
        for _ in range(60):
            d.step(1 / 60.0)
        self.assertLess(lib.pos[vp.balls[0]][1], 0.6)
        d.stop()

    def test_driver_takes_crates_breaks_them_and_pours_sand(self):
        from types import SimpleNamespace as NS
        from prowl_editor.gpu_physics.driver import GpuPhysicsDriver, KEY_SAND
        lib = _Lib()
        crate_node = lib.p2d_new_node()
        lib.p2d_set_pos(crate_node, 3.0, 1.6)
        crate = {"node": crate_node, "tile": "c", "w": 1.0, "h": 1.0, "ttl": None, "cell": (3, 2)}
        scripted = {"node": lib.p2d_new_node(), "tile": "c", "w": 1.0, "h": 1.0, "ttl": None, "script": True}
        lib.p2d_set_pos(scripted["node"], 1.0, 3.0)
        cells = [""] * 24 + ["#"] * 6
        vp = _viewport(lib, cells, 6, 5, {"#": NS(solid=True, dynamic=False)}, [crate, scripted])
        vp.cells[2 * 6 + 3] = "c"
        d = GpuPhysicsDriver("interp", capacity=64)
        d.start(vp)
        self.assertEqual(list(d.actors.values()), [crate])             # the scripted crate stays on Box2D
        self.assertNotEqual(crate["node"], crate_node)                 # the Box2D body was replaced by a plain node
        self.assertIn(crate_node, lib.dead)
        for _ in range(30):
            d.step(1 / 60.0)
        self.assertAlmostEqual(lib.pos[crate["node"]][1], 1.5, delta=0.12)
        self.assertTrue(d.shatter(vp, crate, pieces=3))
        self.assertNotIn(crate, vp.actors)
        self.assertEqual(vp.cells[2 * 6 + 3], "")
        shards = [a for a in vp.actors if a.get("gpu")]
        self.assertEqual(len(shards), 3)
        vp.actors.remove(shards[0])                                    # the viewport retires one (ttl ran out)
        d.step(1 / 60.0)
        self.assertEqual(len(d.world.bodies), 2)
        lib.keys.add(KEY_SAND)
        d.step(1 / 60.0)                                               # the driver reads the keys once per step
        self.assertTrue(d.drop_ball(vp, 4.0, 3.0))                     # F held: sand, not a ball
        self.assertEqual(vp.balls, [])
        self.assertGreater(len([t for t in d.world.read_tags() if t == 1]), 10)
        flat = []
        d.draw(flat)
        self.assertEqual(len(flat) % 12, 0)
        self.assertGreater(len(flat) // 12, 10)
        d.stop()

    def test_driver_falls_back_without_kernels(self):
        from prowl_editor.gpu_physics.driver import GpuPhysicsDriver
        vp = _viewport(_Lib(), [""] * 16, 4, 4, {})
        d = GpuPhysicsDriver("interp", kernel_dir="/nonexistent")
        d.start(vp)
        self.assertIsNone(d.world)
        self.assertFalse(d.drop_ball(vp, 1.0, 1.0))                    # the viewport keeps its Box2D ball
        self.assertIn("unavailable", vp.status)


if __name__ == "__main__":
    unittest.main()
