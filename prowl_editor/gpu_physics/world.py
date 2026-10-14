"""The GPU world: circles stepped by the gpu-physics-engine pipeline.

One step (Prowl's frame order; the engine's own is the same without gravity,
tiles and scripts):

    scripts          user kernels (script.py), each bound by parameter name
    integrate_world  Verlet step, gravity, damping, world box
    grid             build_cell_ids_array: every circle into the (up to 4) cells it touches
    radix sort       the (cell id, circle) pairs by cell id: 4 passes of 8 bits
    collision cells  count / prefix-sum / build: the cells holding two or more pairs
    solver           4 passes, one per cell colour (cells of one colour are two apart,
                     so they can be solved in parallel without touching each other)
    tile_collide     push circles out of the level's solid tiles

Positions are world units, y up, interleaved (x, y) f32 -- the layout of the
engine's array<vec2<f32>>. A circle's handle is its index; handles are stable
because the optional particle re-ordering of the Rust engine is not used.
"""
import struct

from .kernels import Kernels
from .bodies import BodiesMixin

NUM_BLOCKS_PER_WORKGROUP = 45          # the engine's radix-sort constant
RADIX_WG = 256
CELL_SIZE_MULTIPLIER = 2.2            # engine: cell size = largest radius * 2.2
MAX_CELLS = 4                          # a circle touches at most 2^2 cells
PREFIX_LIMIT = 256 * 256


def _ceil_div(a, b):
    return (a + b - 1) // b


class GpuWorld(BodiesMixin):
    host_sort = None  # None: follow the backend (host sort on "interp" only)

    def __init__(self, backend, capacity=4096, world=(64.0, 36.0), gravity=(0.0, -18.0),
                 damping=0.999, max_radius=0.5, kernels=None, kernel_dir=None,
                 max_joints=None, max_sensors=64, max_rays=256, iterations=2, friction=0.15, sand_damping=0.985, bounce_loss=0.6):
        self.b = backend
        if self.host_sort is None:
            self.host_sort = backend.name == "interp"
        self.k = kernels or Kernels(backend, kernel_dir)
        self.capacity = int(capacity)
        self.world = (float(world[0]), float(world[1]))
        self.gravity = (float(gravity[0]), float(gravity[1]))
        self.damping = float(damping)
        self.max_radius = float(max_radius)
        self.n = 0
        self.steps = 0
        self.tiles_dims = (0, 0)
        self.scripts = []
        self.iterations = int(iterations)       # collision + joint rounds per step
        self.friction = float(friction)          # share of a circle's sliding speed a touched tile removes per step
        self.bounce_loss = float(bounce_loss)    # share of the speed a circle leaving a tile loses (0: elastic)
        self.sand_damping = float(sand_damping)  # velocity kept per step by sand (tag 1); balls use `damping`
        cap = self.capacity
        b = self.b
        # particle state
        self.positions = b.alloc(8 * cap)
        self.previous = b.alloc(8 * cap)
        self.radius = b.alloc(4 * cap)
        self.tags = b.alloc(4 * cap)                       # one u32 per circle for scripts / the game
        # grid: (cell id, circle id) pairs and the sort scratch
        pairs = MAX_CELLS * cap
        self.cell_ids = b.alloc(4 * pairs)
        self.object_ids = b.alloc(4 * pairs)
        self.sort_keys_b = b.alloc(4 * pairs)
        self.sort_payload_b = b.alloc(4 * pairs)
        wgs = _ceil_div(_ceil_div(pairs, NUM_BLOCKS_PER_WORKGROUP), RADIX_WG)
        self.histogram = b.alloc(4 * RADIX_WG * max(1, wgs))
        # collision cells
        self.chunks_cap = _ceil_div(pairs, 4)
        self.chunk_counts = b.alloc(4 * max(256, self.chunks_cap))
        self.collision_cells = b.alloc(4 * max(4, pairs))
        self.indirect = b.alloc(16, indirect=True)
        self.cell_uniform = b.alloc(16)
        self.sums = []                                     # prefix-sum block sums, per level
        n = self.chunks_cap
        while True:
            blocks = _ceil_div(n, 256)
            self.sums.append(b.alloc(4 * max(256, blocks)))
            if n < PREFIX_LIMIT:
                break
            n = blocks
        # bodies, joints, queries
        self.groups = b.alloc(4 * cap)                     # body id per circle (0: a free circle)
        self.owner = []                                    # python mirror of groups, per circle
        self.bodies = {}                                   # id -> Body
        self._next_body = 1
        self.joints = {}                                   # id -> [a, b, flags, rest, stiffness, ax, ay]
        self._next_joint = 1
        self._joint_batches = []                           # [(first, count)] per colour
        self._joints_dirty = False
        self.max_joints = int(max_joints or 4 * cap)
        self.joint_i = b.alloc(16 * self.max_joints)
        self.joint_f = b.alloc(16 * self.max_joints)
        self.max_sensors = int(max_sensors)
        self.sensor_f = b.alloc(16 * self.max_sensors)
        self.sensor_mask = b.alloc(4 * self.max_sensors)
        self.sensor_counts = b.alloc(4 * self.max_sensors)
        self.sensors = []                                  # [(x, y, hw, hh, mask)]
        self.sensor_last = []
        self.events = []                                   # (sensor, count, previous count) that changed this step
        self.max_rays = int(max_rays)
        self.ray_f = b.alloc(32 * self.max_rays)
        self.hit_f = b.alloc(16 * self.max_rays)
        self.hit_ids = b.alloc(4 * self.max_rays)
        # level, tiles, input
        self.tiles = b.alloc(16)
        self.input = b.alloc(4 * 520)
        self._tile_cells = (0, 0)

    # ---------------------------------------------------------------- circles
    @property
    def cell_size(self):
        return self.max_radius * CELL_SIZE_MULTIPLIER

    def add_circle(self, x, y, radius=0.5, vx=0.0, vy=0.0, dt=1 / 60.0, tag=0, group=0):
        """Adds a free circle with velocity (vx, vy) (units/second); returns its index.
        Indices change when circles are removed: keep a body id (add_ball, add_box, ...) instead."""
        if self.n >= self.capacity:
            raise OverflowError("GPU world is full (%d circles)" % self.capacity)
        i = self.n
        self.b.write(self.positions, struct.pack("<ff", x, y), 8 * i)
        self.b.write(self.previous, struct.pack("<ff", x - vx * dt, y - vy * dt), 8 * i)
        self.b.write(self.radius, struct.pack("<f", radius), 4 * i)
        self.b.write(self.tags, struct.pack("<I", tag), 4 * i)
        self.b.write(self.groups, struct.pack("<I", group), 4 * i)
        self.owner.append(group)
        self.max_radius = max(self.max_radius, radius)
        self.n += 1
        return i

    def set_circle(self, i, x=None, y=None, vx=None, vy=None, dt=1 / 60.0):
        """Teleports / re-launches circle i (None keeps that part)."""
        cx, cy = self.get_position(i)
        px, py = struct.unpack("<ff", self.b.read(self.previous, 8 * i, 8))
        nx = cx if x is None else x
        ny = cy if y is None else y
        ox = (cx - px) / dt if vx is None else vx
        oy = (cy - py) / dt if vy is None else vy
        self.b.write(self.positions, struct.pack("<ff", nx, ny), 8 * i)
        self.b.write(self.previous, struct.pack("<ff", nx - ox * dt, ny - oy * dt), 8 * i)

    def remove_circle(self, i):
        """Removes circle i by moving the last circle into its slot (joints and bodies
        that named the last circle follow it). Returns the old index that moved, or None.
        A circle that belongs to a body or has joints: use remove_body / remove_joint."""
        if self.owner[i]:
            raise ValueError("circle %d belongs to body %d; use remove_body" % (i, self.owner[i]))
        if any(i in (j[0], j[1]) for j in self.joints.values()):
            raise ValueError("circle %d has joints; remove them first" % i)
        return self._swap_remove(i)

    def _swap_remove(self, i):
        last = self.n - 1
        moved = None
        if i != last:
            for buf, w in ((self.positions, 8), (self.previous, 8), (self.radius, 4), (self.tags, 4), (self.groups, 4)):
                self.b.write(buf, self.b.read(buf, w * last, w), w * i)
            self.owner[i] = self.owner[last]
            moved = last
            for j in self.joints.values():
                if j[0] == last:
                    j[0] = i
                if j[1] == last:
                    j[1] = i
            body = self.bodies.get(self.owner[i])
            if body is not None:
                body.circles[body.circles.index(last)] = i
            self._joints_dirty = True
        self.owner.pop()
        self.n -= 1
        return moved

    def get_position(self, i):
        return struct.unpack("<ff", self.b.read(self.positions, 8 * i, 8))

    def read_positions(self):
        """[(x, y)] for every circle."""
        raw = self.b.read(self.positions, 0, 8 * self.n)
        v = struct.unpack("<%df" % (2 * self.n), raw)
        return [(v[2 * i], v[2 * i + 1]) for i in range(self.n)]

    def read_velocities(self, dt=1 / 60.0):
        cur = struct.unpack("<%df" % (2 * self.n), self.b.read(self.positions, 0, 8 * self.n))
        prv = struct.unpack("<%df" % (2 * self.n), self.b.read(self.previous, 0, 8 * self.n))
        return [((cur[2 * i] - prv[2 * i]) / dt, (cur[2 * i + 1] - prv[2 * i + 1]) / dt) for i in range(self.n)]

    def read_radii(self):
        return list(struct.unpack("<%df" % self.n, self.b.read(self.radius, 0, 4 * self.n)))

    # ------------------------------------------------------------------ level
    def set_tiles(self, width, height, solid):
        """The level's solid tiles: `solid(tx, ty)` -> bool, tile (tx, ty) covering
        [tx, tx+1) x [ty, ty+1) in world units, y up."""
        cells = [1 if solid(x, y) else 0 for y in range(height) for x in range(width)]
        self.set_tile_grid(width, height, cells)

    def set_tile_grid(self, width, height, cells):
        data = struct.pack("<%dI" % len(cells), *cells)
        if len(cells) * 4 > (self.tiles.nbytes):
            self.tiles = self.b.alloc(len(data))
        self.b.write(self.tiles, data)
        self.tiles_dims = (int(width), int(height))

    # ---------------------------------------------------------------- scripts
    def add_script(self, script):
        self.scripts.append(script)
        return script

    def clear_scripts(self):
        self.scripts = []

    # ------------------------------------------------------------------- step
    def _bind(self, entry, **by_name):
        """{binding: Buf} for a kernel entry from {parameter name: Buf}."""
        info = self.k.iface(entry)
        out = {}
        for buf in info["buffers"]:
            if buf["name"] not in by_name:
                raise KeyError("%s: no buffer for parameter %r" % (entry, buf["name"]))
            out[buf["binding"]] = by_name[buf["name"]]
        return out

    def _run(self, entry, items, params, **by_name):
        prog = self.k.entry(entry)
        local = prog.iface[entry]["local_size"][0]
        self.b.dispatch(prog, entry, (_ceil_div(items, local), 1, 1), self._bind(entry, **by_name), params)

    def radix_sort(self, keys, payload, count, keys_b=None, payload_b=None):
        """Sorts the first `count` (key, payload) pairs of two u32 buffers by key,
        ascending and stable, in place (4 passes through the scratch buffers)."""
        if count <= 1:
            return
        if self.host_sort and hasattr(keys, "data"):
            # reference interpreter only: the real kernels take ~30 s per sort there
            kv = struct.unpack_from("<%dI" % count, keys.data, 0)
            pv = struct.unpack_from("<%dI" % count, payload.data, 0)
            order = sorted(range(count), key=kv.__getitem__)
            struct.pack_into("<%dI" % count, keys.data, 0, *[kv[i] for i in order])
            struct.pack_into("<%dI" % count, payload.data, 0, *[pv[i] for i in order])
            return
        keys_b = keys_b or self.sort_keys_b
        payload_b = payload_b or self.sort_payload_b
        threads = _ceil_div(count, NUM_BLOCKS_PER_WORKGROUP)
        wgs = _ceil_div(threads, RADIX_WG)
        a = (keys, payload)
        z = (keys_b, payload_b)
        for pas in range(4):
            params = struct.pack("<4I", count, pas * 8, wgs, NUM_BLOCKS_PER_WORKGROUP)
            self._run("build_histogram", threads, params, keys_a=a[0], histogram=self.histogram)
            self._run("scatter_keys", threads, params, keys_a=a[0], histogram=self.histogram,
                      payload_a=a[1], keys_b=z[0], payload_b=z[1])
            a, z = z, a

    def prefix_sum(self, data, count, level=0):
        """Inclusive prefix sum of the first `count` u32 of `data`, in place."""
        if count <= 0:
            return
        sums = self.sums[level]
        blocks = _ceil_div(count, 256)
        p = struct.pack("<I", count)
        self._run("prefix_sum_of_each_block", count, p, data=data, block_sums=sums)
        if count >= PREFIX_LIMIT:
            self.prefix_sum(sums, blocks, level + 1)
        else:
            self._run("prefix_sum_of_the_block_sums", 256, b"", block_sums=sums)
        self._run("add_block_prefix_sums_to_the_buffer", count, p, data=data, block_sums=sums)

    def build_cells(self, n):
        """grid + sort + collision cells for the first n circles. Returns nothing;
        collision_cells / indirect / chunk_counts hold the result."""
        pairs = MAX_CELLS * n
        self._run("build_cell_ids_array", n, struct.pack("<fI", self.cell_size, n),
                  positions=self.positions, cell_ids=self.cell_ids,
                  object_ids=self.object_ids, radius=self.radius)
        self.radix_sort(self.cell_ids, self.object_ids, pairs)
        chunks = _ceil_div(pairs, 4)
        self.b.write(self.cell_uniform, struct.pack("<II", chunks, pairs))
        self._run("count_objects_for_each_chunk", chunks, b"", chunk_obj_count=self.chunk_counts,
                  uniform_data=self.cell_uniform, cell_ids=self.cell_ids)
        self.prefix_sum(self.chunk_counts, chunks)
        self._run("build_collision_cells_array", chunks, b"", chunk_obj_count=self.chunk_counts,
                  collision_cells=self.collision_cells, indirect_args=self.indirect,
                  uniform_data=self.cell_uniform, cell_ids=self.cell_ids)

    def solve(self):
        prog = self.k.entry("solve_collisions_grouped")
        binds = self._bind("solve_collisions_grouped", chunk_obj_count=self.chunk_counts,
                           collision_cells=self.collision_cells, cell_ids=self.cell_ids,
                           object_ids=self.object_ids, positions=self.positions,
                           radius=self.radius, uniform_data=self.cell_uniform, groups=self.groups)
        for color in (1, 2, 3, 4):
            self.b.dispatch_indirect(prog, "solve_collisions_grouped", self.indirect, binds,
                                     struct.pack("<I", color))

    def tile_collide(self):
        w, h = self.tiles_dims
        if w and h and self.n:
            self._run("tile_collide", self.n, struct.pack("<3I", w, h, self.n),
                      positions=self.positions, radius=self.radius, tiles=self.tiles)

    def tile_friction(self):
        w, h = self.tiles_dims
        if w and h and self.n and (self.friction > 0 or self.bounce_loss > 0):
            self._run("tile_friction", self.n, struct.pack("<3Iff", w, h, self.n, self.friction, self.bounce_loss),
                      positions=self.positions, previous_positions=self.previous, radius=self.radius,
                      tiles=self.tiles)

    def step(self, dt=1 / 60.0, input=None):
        """Advances the world one tick of `dt` seconds. `input` is a GpuInput.
        Order: input, scripts, expire shards, integrate, `iterations` x (circle collisions,
        joints, tiles), tile friction, sensors (their changes land in self.events)."""
        self.events = []
        self._expire(dt)
        n = self.n
        if n == 0:
            self.steps += 1
            return
        if input is not None:
            input.tick(dt, n)
            self.b.write(self.input, input.pack())
        for s in self.scripts:
            s.run(self, dt)
        self._run("integrate_tagged", n,
                  struct.pack("<7fI", dt, self.gravity[0], self.gravity[1], self.damping, self.sand_damping,
                              self.world[0], self.world[1], n),
                  positions=self.positions, previous_positions=self.previous, radius=self.radius, tags=self.tags)
        self.build_cells(n)
        for _ in range(max(1, self.iterations)):
            self.solve()
            self.solve_joints()
            self.tile_collide()
        self.tile_friction()
        self._run_sensors()
        self.b.flush()
        self.steps += 1

    def close(self):
        self.b.close()
