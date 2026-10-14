"""The Viewport driver that plays the level on the GPU physics engine.

What the GPU takes over (when it starts): the dropped balls, the crates (movable tiles),
the shards a shattered crate makes, blasts' pushes, sand (hold F and click/drag), the
level's solid tiles as colliders. Ropes and sensors are available through `driver.world`.
Box2D keeps what the circle engine cannot do: crates with a script attached, bodies scripts
make, joints/ray casts/contacts the *scripts* use, and the engine's own sprites. The two
worlds do not collide with each other.

Each step the driver
  1. copies keyboard and mouse from the engine (what Input2D sees) into GpuInput,
  2. steps the GpuWorld (GPU scripts first, then integrate/sort/collide/joints),
  3. writes ball and crate poses into the engine nodes the viewport draws, drops the ones
     whose actor the viewport retired.
Sand and ropes are drawn through `draw(flat)`: the viewport has a node limit they would exceed.
"""
import math
import random

from . import GpuWorld, GpuInput, make_backend
from .bodies import TAG_SAND

TRACKED_KEYS = (list(range(48, 58)) + list(range(65, 91)) + [32, 256, 262, 263, 264, 265, 340, 341, 257])
KEY_SAND = 70                           # F: click or drag spawns sand instead of a ball


class GpuPhysicsDriver:
    BALL_RADIUS = 0.35

    def __init__(self, backend="auto", scripts=(), capacity=4096, kernel_dir=None, gravity=(0.0, -18.0)):
        self.backend_name = backend
        self.sources = list(scripts)       # C# [GpuKernel] sources or file paths
        self.capacity = capacity
        self.kernel_dir = kernel_dir
        self.gravity = gravity
        self.world = None
        self.vp = None
        self.input = GpuInput()
        self.ball_nodes = {}               # body id -> engine node
        self.actors = {}                   # body id -> the viewport's actor dict (crates, shards)
        self.script_errors = []
        self.error = None
        self._cells = None
        self._ring = 0
        self._balls = []                   # ball body ids, oldest first
        self.sand_per_frame = 6
        self.last_event = None

    # ----------------------------------------------------------- viewport hooks
    def start(self, vp):
        from .script import GpuScript, ScriptError
        self.vp, self.lib = vp, vp.engine.lib
        lv = vp.level
        try:
            backend = make_backend(self.backend_name)
            self.world = GpuWorld(backend, capacity=self.capacity, world=(float(lv.width), float(lv.height)),
                                  gravity=self.gravity, max_radius=self.BALL_RADIUS, kernel_dir=self.kernel_dir)
        except Exception as e:             # no GPU / no kernels: the viewport keeps Box2D
            self.world, self.error = None, str(e)
            vp.status = "GPU physics unavailable (%s); using Box2D" % e
            return
        self.input.clear()
        self.ball_nodes, self.actors, self._balls, self._ring, self._cells = {}, {}, [], 0, None
        self.script_errors = []
        for src in self.sources:
            try:
                self.world.add_script(GpuScript(src, backend=backend))
            except ScriptError as e:
                self.script_errors.append(str(e))
        self._sync_tiles()
        taken = self._take_crates()
        vp.status = "play (GPU physics: %s backend; %d crate(s)%s) - click drops a ball, F+click sand" % (
            backend.name, taken, ", %d script(s)" % len(self.world.scripts) if self.world.scripts else "")
        if self.script_errors:
            vp.script_report = "; ".join(e.splitlines()[0] for e in self.script_errors)

    def stop(self):
        if self.world is not None:
            self.world.close()
        self.world = None
        self.ball_nodes, self.actors, self._balls = {}, {}, []

    def _take_crates(self):
        """Movable tiles become GPU boxes; their Box2D bodies are replaced by plain nodes the
        driver moves. Crates with a script stay on Box2D (the script talks to that body)."""
        w, lib, vp = self.world, self.lib, self.vp
        taken = 0
        for a in vp.actors:
            if not a.get("tile") or a.get("script") or a.get("gpu"):
                continue
            x, y = lib.p2d_node_x(a["node"]), lib.p2d_node_y(a["node"])
            try:
                bid = w.add_box(x, y, a["w"], a["h"])
            except OverflowError:
                break
            lib.p2d_destroy_node(a["node"])
            node = lib.p2d_new_node()
            if node < 0:
                w.remove_body(bid)
                break
            lib.p2d_set_pos(node, x, y)
            a["node"], a["gpu"] = node, bid
            self.actors[bid] = a
            taken += 1
        return taken

    def drop_ball(self, vp, wx, wy):
        """Called by Viewport.drop_ball; True when the GPU world took the click."""
        w = self.world
        if w is None:
            return False
        if self.input.key(KEY_SAND):
            w.brush_sand(wx, wy, 0.5, 24, seed=w.steps)
            return True
        if len(self._balls) >= 100:                        # recycle the oldest, like the Box2D balls
            old = self._balls.pop(0)
            node_old = self.ball_nodes.pop(old)
            self.lib.p2d_destroy_node(node_old)
            vp.balls.remove(node_old)
            w.remove_body(old)
        node = self.lib.p2d_new_node()
        if node < 0 or w.n >= w.capacity:
            return False
        self.lib.p2d_set_pos(node, wx, wy)
        bid = w.add_ball(wx, wy, self.BALL_RADIUS)
        self.ball_nodes[bid] = node
        self._balls.append(bid)
        vp.balls.append(node)
        return True

    def shatter(self, vp, actor, pieces=7, speed=4.0):
        w, lib = self.world, self.lib
        if w is None or actor["gpu"] not in w.bodies:
            return False
        bid = actor["gpu"]
        x, y = w.body_position(bid)
        w.remove_body(bid)
        self.actors.pop(bid, None)
        lib.p2d_destroy_node(actor["node"])
        vp.actors.remove(actor)
        if actor.get("cell"):
            vp.cells[actor["cell"][1] * vp.level.width + actor["cell"][0]] = ""
        rng = random.Random(int(x * 100) + int(y * 10))
        for _ in range(pieces):
            size = rng.uniform(0.22, 0.4)
            ox, oy = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)
            node = lib.p2d_new_node()
            if node < 0:
                break
            try:
                sb = w.add_box(x + ox, y + oy, size, size, rng.uniform(0, 3.14),
                               ox * speed * 2 + rng.uniform(-1, 1), oy * speed * 2 + rng.uniform(1, 4), kind="shard")
            except OverflowError:
                lib.p2d_destroy_node(node)
                break
            lib.p2d_set_pos(node, x + ox, y + oy)
            act = {"node": node, "tile": None, "w": size, "h": size, "ttl": 2.5, "gpu": sb,
                   "color": (0.85 - rng.uniform(0, 0.15), 0.6 - rng.uniform(0, 0.15), 0.35)}
            vp.actors.append(act)
            self.actors[sb] = act
        return True

    def blast(self, vp, wx, wy, radius, force):
        return self.world.blast(wx, wy, radius, force) if self.world is not None else 0

    def step(self, dt):
        w = self.world
        if w is None:
            return
        lib, inp = self.lib, self.input
        for k in TRACKED_KEYS:
            inp.keys[k] = 1 if lib.p2d_key_down(k) else 0
        btn = 0
        for b in range(3):
            if lib.p2d_mouse_down(b):
                btn |= 1 << b
        mx, my = lib.p2d_mouse_world_x(), lib.p2d_mouse_world_y()
        inp.set_mouse(mx, my, btn)
        if inp.key(KEY_SAND) and btn & 1:                  # dragging with F held keeps pouring
            w.brush_sand(mx, my, 0.4, self.sand_per_frame, seed=w.steps)
        self._retire_actors()
        self._sync_tiles()
        w.step(dt, inp)
        for sid, count, prev in w.events:
            self.last_event = (sid, count, prev)
        poses = {p.id: p for p in w.read_bodies()}
        for bid, node in self.ball_nodes.items():
            p = poses.get(bid)
            if p is not None:
                lib.p2d_set_pos(node, p.x, p.y)
        for bid, act in self.actors.items():
            p = poses.get(bid)
            if p is not None:
                lib.p2d_set_pos(act["node"], p.x, p.y)
                lib.p2d_set_angle(act["node"], p.angle)

    def draw(self, flat):
        """Appends sand and ropes in the viewport's 12-float instance format."""
        w = self.world
        if w is None or not w.n:
            return
        pos = w.read_positions()
        rad = w.read_radii()
        for i, t in enumerate(w.read_tags()):
            if t == TAG_SAND:
                flat.extend((pos[i][0], pos[i][1], rad[i], rad[i], 0.0, 0.86, 0.74, 0.42, 1.0, 1, 5, 0))
        for p in w.read_bodies():
            if p.kind == "rope":
                for (x0, y0), (x1, y1) in zip(p.points, p.points[1:]):
                    flat.extend(((x0 + x1) / 2, (y0 + y1) / 2, math.hypot(x1 - x0, y1 - y0) / 2 + 0.03, 0.045,
                                 math.atan2(y1 - y0, x1 - x0), 0.62, 0.45, 0.25, 1.0, 0, 5, 0))

    # ------------------------------------------------------------------ helpers
    def _retire_actors(self):
        """Bodies whose actor the viewport removed (shard ttl, a destroyed crate) leave the GPU world."""
        live = {id(a) for a in self.vp.actors}
        for bid in [b for b, a in self.actors.items() if id(a) not in live]:
            self.actors.pop(bid)
            if bid in self.world.bodies:
                self.world.remove_body(bid)

    def _sync_tiles(self):
        vp, lv = self.vp, self.vp.level
        if vp.cells is None or vp.cells == self._cells:
            return
        self._cells = list(vp.cells)
        solid = {k for k, t in vp.project.tiles.items() if t.solid and not t.dynamic}
        W, H = lv.width, lv.height
        grid = [1 if self._cells[(H - 1 - ty) * W + tx] in solid else 0 for ty in range(H) for tx in range(W)]
        self.world.set_tile_grid(W, H, grid)
