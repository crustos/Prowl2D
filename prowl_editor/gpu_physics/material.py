"""Per-body material, mass and collision filtering: Box2D's fixture settings on the GPU world.

The kernels are the gpu-physics-engine's `prowl_material` (integrate_material,
solve_collisions_filtered, tile_material). A world that never calls `set_material`,
`set_filter` or `set_sensor` steps exactly as before; the first call switches the world to
the material path for good.

Names and units follow Unity's Rigidbody2D / PhysicsMaterial2D / Collider2D:

  friction      Unity's value (0.4 default); the kernel's coefficient is 0.375 of it
  bounciness    0..1; two circles use the larger one, a tile uses the world's `1 - bounce_loss`
  density       scales mass (mass is proportional to a circle's radius, 1 = the plain engine)
  gravity_scale multiplies gravity (0 floats, -1 rises)
  drag          Unity's linear drag: a circle loses `drag * dt` of its speed per second
  category/mask/group   Box2D's categoryBits, maskBits and groupIndex
  sensor        the body collides with nothing (use `add_sensor` regions to count what is inside)

Combining two circles follows Box2D: friction is the geometric mean, bounciness the larger.
Approaches slower than `bounce_threshold` (units per second) do not bounce.
"""
import struct

FRICTION_UNIT = 0.375           # kernel friction per unit of Unity's friction
ALL = 0xFFFFFFFF


class MaterialMixin:
    def _init_material(self, cap):
        b = self.b
        self.use_material = False
        self.bounce_threshold = 1.0                    # units per second
        self.material_buf = b.alloc(20 * cap)          # f32 x5: friction, bounciness, gravity scale, damping, inverse mass
        self.filter_buf = b.alloc(16 * cap)            # u32 x4: category, mask, group (i32), body
        self.omega_buf = b.alloc(4 * cap)              # spin of each circle, zero: balls here do not spin
        b.write(self.omega_buf, bytes(4 * cap))
        self._m_custom = []                            # per circle: friction set by the user
        self._m_mat = []                               # [friction, bounciness, gravity_scale]
        self._m_dens = []
        self._m_drag = []
        self._m_flt = []                               # [category, mask, group]
        self._m_sensor = []
        self._m_dirty = True
        self._m_dt = None
        self._kernel_ok = None

    # hooks the circle store calls ---------------------------------------------------------
    def _mat_add(self):
        self._m_custom.append(False)
        self._m_mat.append([self.friction, 0.0, 1.0])
        self._m_dens.append(1.0)
        self._m_drag.append(0.0)
        self._m_flt.append([1, ALL, 0])
        self._m_sensor.append(False)
        self._m_dirty = True

    def _mat_swap_remove(self, i, last):
        for arr in (self._m_custom, self._m_mat, self._m_dens, self._m_drag, self._m_flt, self._m_sensor):
            arr[i] = arr[last]
            arr.pop()
        self._m_dirty = True

    # public settings ------------------------------------------------------------------
    def has_material_kernels(self):
        """True when the loaded kernel build has prowl_material (older gpu/spirv folders do not)."""
        if self._kernel_ok is None:
            self._kernel_ok = all(e in self.k.by_entry for e in
                                  ("integrate_material", "solve_collisions_filtered", "tile_material"))
        return self._kernel_ok

    def _circles_of(self, body):
        return list(self.bodies[body].circles)

    def set_material(self, body, friction=0.4, bounciness=0.0, density=1.0, gravity_scale=1.0, drag=0.0):
        """Unity's PhysicsMaterial2D + Rigidbody2D settings for every circle of `body`.
        Returns False when the kernels are missing (the body keeps the plain behaviour)."""
        if not self.has_material_kernels():
            return False
        self.use_material = True
        for c in self._circles_of(body):
            self._m_custom[c] = True
            self._m_mat[c] = [FRICTION_UNIT * max(0.0, friction), min(1.0, max(0.0, bounciness)), gravity_scale]
            self._m_dens[c] = density if density > 0 else 1.0
            self._m_drag[c] = max(0.0, drag)
        self._m_dirty = True
        return True

    def set_filter(self, body, category=1, mask=ALL, group=0):
        """Box2D's collision filter for `body`."""
        if not self.has_material_kernels():
            return False
        self.use_material = True
        for c in self._circles_of(body):
            self._m_flt[c] = [category & ALL, mask & ALL, group]
        self._m_dirty = True
        return True

    def set_sensor(self, body, sensor=True):
        """A sensor body passes through everything (it still moves and can be read)."""
        if not self.has_material_kernels():
            return False
        self.use_material = True
        for c in self._circles_of(body):
            self._m_sensor[c] = bool(sensor)
        self._m_dirty = True
        return True

    def set_bounce_threshold(self, speed):
        self.bounce_threshold = max(0.0, float(speed))

    def set_world_material(self, friction=None, bounciness=None):
        """The level's tiles: Unity friction and bounciness (0 default in Unity)."""
        if friction is not None:
            self.friction = FRICTION_UNIT * max(0.0, friction)
        if bounciness is not None:
            self.bounce_loss = 1.0 - min(1.0, max(0.0, bounciness))
        self._m_dirty = True

    # the step ---------------------------------------------------------------------------
    def _upload_material(self, dt):
        n = self.n
        mat, flt = [], []
        tags = struct.unpack("<%dI" % n, self.b.read(self.tags, 0, 4 * n)) if n else ()
        rad = self.read_radii()
        for i in range(n):
            f, e, gs = self._m_mat[i]
            if not self._m_custom[i]:
                f = self.friction
            sand = self.sand_damping / self.damping if tags[i] == 1 else 1.0
            mat.extend((f, e, gs, sand / (1.0 + self._m_drag[i] * dt), 1.0 / (rad[i] * self._m_dens[i])))
            cat, mask, grp = self._m_flt[i]
            if self._m_sensor[i]:
                cat = mask = grp = 0
            flt.extend((cat, mask, grp & ALL, self.owner[i]))
        self.b.write(self.material_buf, struct.pack("<%df" % (5 * n), *mat))
        self.b.write(self.filter_buf, struct.pack("<%dI" % (4 * n), *flt))

    def _material_integrate(self, dt):
        self._run("integrate_material", self.n,
                  struct.pack("<6fI", dt, self.gravity[0], self.gravity[1], self.damping,
                              self.world[0], self.world[1], self.n),
                  positions=self.positions, previous_positions=self.previous, radius=self.radius,
                  material=self.material_buf)

    def _material_solve(self, dt):
        prog = self.k.entry("solve_collisions_filtered")
        binds = self._bind("solve_collisions_filtered", chunk_obj_count=self.chunk_counts,
                           collision_cells=self.collision_cells, cell_ids=self.cell_ids,
                           object_ids=self.object_ids, positions=self.positions, radius=self.radius,
                           uniform_data=self.cell_uniform, filter=self.filter_buf,
                           material=self.material_buf,
                           previous_positions=self.previous)
        for color in (1, 2, 3, 4):
            self.b.dispatch_indirect(prog, "solve_collisions_filtered", self.indirect, binds,
                                     struct.pack("<If", color, self.bounce_threshold * dt))

    def _material_tiles(self, dt):
        w, h = self.tiles_dims
        if w and h and self.n:
            self._run("tile_material", self.n,
                      struct.pack("<3I3f", w, h, self.n, self.friction, 1.0 - self.bounce_loss,
                                  self.bounce_threshold * dt),
                      positions=self.positions, previous_positions=self.previous, radius=self.radius,
                      tiles=self.tiles, material=self.material_buf,
                      omega=self.omega_buf)
