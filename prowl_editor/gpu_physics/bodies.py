"""Bodies, joints, ray casts and sensors on top of the circle engine.

Everything is circles: the engine has no polygons. So

  ball    one circle.
  box     a crate: a grid of circles (at least 2 x 2) held in shape by stiff distance
          joints. Rounded at the corners by the circle radius; spins, slides and
          stacks through ordinary circle collisions, with no torque model of its own.
  shard   a small box that expires after `ttl` seconds.
  rope    a chain of small circles joined by distance joints, optionally pinned to a
          fixed point at either end.
  sand    free circles (tag 1) with their own damping; no body object.

Circles of one body carry its id as their *group* and never collide with each other.
Joints are distance constraints (rigid, rope = only when stretched, strut = only when
squeezed), between two circles or a circle and a fixed point; stiffness below 1 is a
spring. They are solved by colour batches (no circle twice in one dispatch).
"""
import math
import random
import struct
from collections import namedtuple

TAG_BALL, TAG_SAND, TAG_CRATE, TAG_SHARD, TAG_ROPE = 0, 1, 2, 3, 4
KIND_TAG = {"ball": TAG_BALL, "box": TAG_CRATE, "shard": TAG_SHARD, "rope": TAG_ROPE}
RIGID, ROPE, STRUT = 0, 1, 2          # joint flags
FIXED = 0xFFFFFFFF
RAY_TILES, RAY_CIRCLES = 1, 2

Hit = namedtuple("Hit", "t x y nx ny kind index body")
BodyPose = namedtuple("BodyPose", "id kind x y angle w h r points")


class Body:
    def __init__(self, bid, kind, circles, w=0.0, h=0.0, cols=1, rows=1, ttl=None):
        self.id, self.kind, self.circles = bid, kind, circles
        self.w, self.h, self.cols, self.rows, self.ttl = w, h, cols, rows, ttl
        self.joints = []


class BodiesMixin:
    # ------------------------------------------------------------------ bodies
    def _body(self, kind, circles, **kw):
        bid = self._next_body
        self._next_body += 1
        for c in circles:
            self.owner[c] = bid
            self.b.write(self.groups, struct.pack("<I", bid), 4 * c)
        self.bodies[bid] = Body(bid, kind, circles, **kw)
        return bid

    def add_ball(self, x, y, radius=0.35, vx=0.0, vy=0.0, dt=1 / 60.0):
        c = self.add_circle(x, y, radius, vx, vy, dt, tag=TAG_BALL)
        return self._body("ball", [c])

    def add_box(self, x, y, w=1.0, h=1.0, angle=0.0, vx=0.0, vy=0.0, dt=1 / 60.0,
                stiffness=1.0, kind="box", ttl=None):
        """A crate of w x h centred at (x, y), turned by `angle` radians. Returns its id."""
        r0 = min(w, h) / 4.0
        rows = max(2, int(round(h / (2 * r0))))
        cols = max(2, int(round(w / (2 * r0))))
        r = min(w / (2.0 * cols), h / (2.0 * rows))
        if self.n + rows * cols > self.capacity:
            raise OverflowError("GPU world is full (%d circles)" % self.capacity)
        ca, sa = math.cos(angle), math.sin(angle)
        circles = []
        for j in range(rows):
            for i in range(cols):
                lx = -w / 2 + r + i * (w - 2 * r) / (cols - 1)
                ly = -h / 2 + r + j * (h - 2 * r) / (rows - 1)
                circles.append(self.add_circle(x + lx * ca - ly * sa, y + lx * sa + ly * ca, r, vx, vy, dt,
                                               tag=KIND_TAG[kind]))
        bid = self._body(kind, circles, w=w, h=h, cols=cols, rows=rows, ttl=ttl)
        pos = [self.get_position(c) for c in circles]
        body = self.bodies[bid]
        for ai in range(len(circles)):
            for bi in range(ai + 1, len(circles)):
                di = abs(ai % cols - bi % cols)
                dj = abs(ai // cols - bi // cols)
                if max(di, dj) <= 2:
                    rest = math.dist(pos[ai], pos[bi])
                    body.joints.append(self._add_joint(circles[ai], circles[bi], RIGID, rest, stiffness))
        return bid

    def add_shards(self, x, y, count=7, size=(0.22, 0.4), speed=4.0, ttl=2.5, seed=None, dt=1 / 60.0):
        """A burst of small boxes flying outward from (x, y), gone after `ttl` seconds."""
        rng = random.Random(seed if seed is not None else int(x * 100) + int(y * 10))
        out = []
        for _ in range(count):
            s = rng.uniform(*size)
            ox, oy = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)
            try:
                out.append(self.add_box(x + ox, y + oy, s, s, rng.uniform(0, 3.14),
                                        ox * speed * 2 + rng.uniform(-1, 1), oy * speed * 2 + rng.uniform(1, 4),
                                        dt, kind="shard", ttl=ttl))
            except OverflowError:
                break
        return out

    def add_rope(self, ax, ay, bx, by, segments=10, radius=0.07, pin_a=True, pin_b=False, stiffness=1.0, slack=1.0):
        """A chain of `segments` + 1 circles from (ax, ay) to (bx, by); an end can be pinned to its point.
        `slack` > 1 makes the rope longer than the distance between the ends."""
        n = segments + 1
        if self.n + n > self.capacity:
            raise OverflowError("GPU world is full (%d circles)" % self.capacity)
        circles = [self.add_circle(ax + (bx - ax) * k / segments, ay + (by - ay) * k / segments, radius,
                                   tag=TAG_ROPE) for k in range(n)]
        bid = self._body("rope", circles)
        seg = math.dist((ax, ay), (bx, by)) / segments * slack
        body = self.bodies[bid]
        for k in range(segments):
            body.joints.append(self._add_joint(circles[k], circles[k + 1], RIGID, seg, stiffness))
        if pin_a:
            body.joints.append(self.pin(circles[0], ax, ay))
        if pin_b:
            body.joints.append(self.pin(circles[-1], bx, by))
        return bid

    def remove_body(self, bid):
        body = self.bodies.pop(bid)
        for jid in body.joints:
            self.joints.pop(jid, None)
        self._joints_dirty = True
        for c in sorted(body.circles, reverse=True):   # highest first: indices below stay valid
            self.owner[c] = 0
            self._swap_remove_body_circle(c, body)

    def _swap_remove_body_circle(self, c, body):
        body.circles.remove(c)
        # joints on other bodies can't name this circle (they would be a joint to a removed body)
        for jid in [k for k, j in self.joints.items() if c in (j[0], j[1])]:
            del self.joints[jid]
        self._swap_remove(c)

    def body_circle(self, bid, k=0):
        return self.bodies[bid].circles[k]

    def body_position(self, bid):
        """Centre of a body (mean of its circles)."""
        pts = [self.get_position(c) for c in self.bodies[bid].circles]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def set_body_velocity(self, bid, vx, vy, dt=1 / 60.0):
        for c in self.bodies[bid].circles:
            self.set_circle(c, vx=vx, vy=vy, dt=dt)

    def read_bodies(self):
        """[BodyPose] for every body, from one read of the positions."""
        pos = self.read_positions()
        rad = self.read_radii()
        out = []
        for body in self.bodies.values():
            pts = [pos[c] for c in body.circles]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            angle = 0.0
            if body.kind in ("box", "shard"):
                (x0, y0), (x1, y1) = pts[0], pts[1]
                angle = math.atan2(y1 - y0, x1 - x0)
            out.append(BodyPose(body.id, body.kind, cx, cy, angle, body.w, body.h, rad[body.circles[0]],
                                pts if body.kind == "rope" else None))
        return out

    # ------------------------------------------------------------------- sand
    def add_sand(self, x, y, radius=0.08, vx=0.0, vy=0.0):
        if self.n >= self.capacity:
            return None
        return self.add_circle(x, y, radius, vx, vy, tag=TAG_SAND)

    def brush_sand(self, x, y, brush=0.5, count=8, radius=0.08, seed=None):
        rng = random.Random(seed)
        made = 0
        for _ in range(count):
            a, d = rng.uniform(0, 6.283), brush * math.sqrt(rng.random())
            if self.add_sand(x + math.cos(a) * d, y + math.sin(a) * d, radius) is not None:
                made += 1
        return made

    # ----------------------------------------------------------------- joints
    def _add_joint(self, a, b, flags, rest, stiffness, ax=0.0, ay=0.0):
        if len(self.joints) >= self.max_joints:
            raise OverflowError("too many joints (%d)" % self.max_joints)
        jid = self._next_joint
        self._next_joint += 1
        self.joints[jid] = [a, b, flags, rest, stiffness, ax, ay]
        self._joints_dirty = True
        return jid

    def add_joint(self, a, b, rest=None, kind="rigid", stiffness=1.0):
        """Distance joint between circles (indices from body_circle) a and b. kind: "rigid",
        "rope" (only pulls) or "strut" (only pushes). rest defaults to the present distance.
        Circles of different bodies still collide; pass bodies' own circles to tie bodies together."""
        if rest is None:
            rest = math.dist(self.get_position(a), self.get_position(b))
        return self._add_joint(a, b, {"rigid": RIGID, "rope": ROPE, "strut": STRUT}[kind], rest, stiffness)

    def pin(self, a, x, y, rest=0.0, kind="rigid", stiffness=1.0):
        """Ties circle a to the fixed point (x, y) at distance `rest` (0: pinned there)."""
        return self._add_joint(a, FIXED, {"rigid": RIGID, "rope": ROPE, "strut": STRUT}[kind], rest, stiffness, x, y)

    def remove_joint(self, jid):
        self.joints.pop(jid, None)
        self._joints_dirty = True

    def _upload_joints(self):
        used = {}                                   # circle -> colours taken
        colour = {}
        for jid, j in self.joints.items():
            ends = [j[0]] if j[1] == FIXED else [j[0], j[1]]
            taken = set()
            for e in ends:
                taken |= used.get(e, set())
            c = 0
            while c in taken:
                c += 1
            colour[jid] = c
            for e in ends:
                used.setdefault(e, set()).add(c)
        order = sorted(self.joints, key=lambda k: colour[k])
        ji, jf = [], []
        batches = []
        for k, jid in enumerate(order):
            a, b, flags, rest, stiff, ax, ay = self.joints[jid]
            ji += [a, b, flags, 0]
            jf += [rest, stiff, ax, ay]
            if not batches or batches[-1][2] != colour[jid]:
                batches.append([k, 0, colour[jid]])
            batches[-1][1] += 1
        self._joint_batches = [(f, c) for f, c, _ in batches]
        if ji:
            self.b.write(self.joint_i, struct.pack("<%dI" % len(ji), *ji))
            self.b.write(self.joint_f, struct.pack("<%df" % len(jf), *jf))
        self._joints_dirty = False

    def solve_joints(self):
        if self._joints_dirty:
            self._upload_joints()
        for first, count in self._joint_batches:
            self._run("solve_joints", count, struct.pack("<2I", first, count), positions=self.positions,
                      radius=self.radius, joint_i=self.joint_i, joint_f=self.joint_f)
            # `first` is a batch offset: the grid is sized by count, the kernel adds `first`

    # ---------------------------------------------------------------- ray casts
    def raycast(self, ox, oy, dx, dy, max_distance=100.0, mask=RAY_TILES | RAY_CIRCLES, ignore_body=0):
        return self.raycast_many([(ox, oy, dx, dy, max_distance)], mask, ignore_body)[0]

    def raycast_many(self, rays, mask=RAY_TILES | RAY_CIRCLES, ignore_body=0):
        """[Hit or None] for rays (ox, oy, dx, dy, max_distance); directions need not be unit.
        Hit.kind is "tile" or "circle"; Hit.body is the body id of a circle hit (0: free circle)."""
        out = []
        for lo in range(0, len(rays), self.max_rays):
            chunk = rays[lo:lo + self.max_rays]
            flat = []
            for ox, oy, dx, dy, mx in chunk:
                d = math.hypot(dx, dy) or 1.0
                flat += [ox, oy, dx / d, dy / d, mx, 0.0, 0.0, 0.0]
            self.b.write(self.ray_f, struct.pack("<%df" % len(flat), *flat))
            w, h = self.tiles_dims
            self._run("raycast", len(chunk), struct.pack("<6I", w, h, self.n, len(chunk), mask, ignore_body),
                      positions=self.positions, radius=self.radius, groups=self.groups, tiles=self.tiles,
                      rays=self.ray_f, hits=self.hit_f, hit_ids=self.hit_ids)
            hv = struct.unpack("<%df" % (4 * len(chunk)), self.b.read(self.hit_f, 0, 16 * len(chunk)))
            ids = struct.unpack("<%dI" % len(chunk), self.b.read(self.hit_ids, 0, 4 * len(chunk)))
            for k, (ox, oy, dx, dy, mx) in enumerate(chunk):
                t, nx, ny, kind = hv[4 * k:4 * k + 4]
                if kind == 0:
                    out.append(None)
                    continue
                d = math.hypot(dx, dy) or 1.0
                px, py = ox + dx / d * t, oy + dy / d * t
                if kind == 1:
                    out.append(Hit(t, px, py, nx, ny, "tile", ids[k], 0))
                else:
                    out.append(Hit(t, px, py, nx, ny, "circle", ids[k], self.owner[ids[k]]))
        return out

    # ----------------------------------------------------------------- sensors
    def add_sensor(self, x, y, half_w, half_h, tags=()):
        """A box sensor; `tags` limits what it counts (TAG_* values; empty: everything)."""
        return self._add_sensor(x, y, half_w, half_h, tags)

    def add_circle_sensor(self, x, y, radius, tags=()):
        return self._add_sensor(x, y, radius, -1.0, tags)

    def _add_sensor(self, x, y, hw, hh, tags):
        if len(self.sensors) >= self.max_sensors:
            raise OverflowError("too many sensors")
        mask = 0
        for t in tags:
            mask |= 1 << t
        self.sensors.append((x, y, hw, hh, mask))
        self.sensor_last.append(0)
        self._sensors_dirty = True
        return len(self.sensors) - 1

    def sensor_count(self, sid):
        return self.sensor_last[sid]

    def _run_sensors(self):
        ns = len(self.sensors)
        if not ns:
            return
        if getattr(self, "_sensors_dirty", True):
            self.b.write(self.sensor_f, struct.pack("<%df" % (4 * ns), *[v for s in self.sensors for v in s[:4]]))
            self.b.write(self.sensor_mask, struct.pack("<%dI" % ns, *[s[4] for s in self.sensors]))
            self._sensors_dirty = False
        self.b.write(self.sensor_counts, bytes(4 * ns))
        if self.n:
            self._run("sensor_count", self.n, struct.pack("<2I", self.n, ns), positions=self.positions,
                      radius=self.radius, tags=self.tags, sensors=self.sensor_f, sensor_mask=self.sensor_mask,
                      sensor_counts=self.sensor_counts)
        counts = struct.unpack("<%dI" % ns, self.b.read(self.sensor_counts, 0, 4 * ns))
        for sid, c in enumerate(counts):
            if c != self.sensor_last[sid]:
                self.events.append((sid, c, self.sensor_last[sid]))
            self.sensor_last[sid] = c

    # --------------------------------------------------------------- lifetimes
    def _expire(self, dt):
        gone = []
        for body in self.bodies.values():
            if body.ttl is not None:
                body.ttl -= dt
                if body.ttl <= 0:
                    gone.append(body.id)
        for bid in gone:
            self.remove_body(bid)
        return gone

    # ------------------------------------------------------------------ blasts
    def read_tags(self):
        return list(struct.unpack("<%dI" % self.n, self.b.read(self.tags, 0, 4 * self.n)))

    def blast(self, x, y, radius=3.5, force=60.0, dt=1 / 60.0):
        """Pushes every circle within `radius` away from (x, y): force falls off linearly to the
        edge (units/second of speed at the centre). Returns the number of circles pushed."""
        if not self.n:
            return 0
        pos = struct.unpack("<%df" % (2 * self.n), self.b.read(self.positions, 0, 8 * self.n))
        prv = list(struct.unpack("<%df" % (2 * self.n), self.b.read(self.previous, 0, 8 * self.n)))
        pushed = 0
        for i in range(self.n):
            dx, dy = pos[2 * i] - x, pos[2 * i + 1] - y
            d = math.hypot(dx, dy)
            if d < radius:
                if d < 1e-4:
                    dx, dy, d = 0.0, 1.0, 1.0
                k = force * (1.0 - d / radius) * dt / d
                prv[2 * i] -= dx * k
                prv[2 * i + 1] -= dy * k
                pushed += 1
        if pushed:
            self.b.write(self.previous, struct.pack("<%df" % (2 * self.n), *prv))
        return pushed
