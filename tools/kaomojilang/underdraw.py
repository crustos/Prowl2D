"""The underdrawing: the loose pencil sketch an artist makes before the dark lines, planned from the whole figure.

An artist does not trace the final line three times. They look at the whole thing first and work from big to small:

  1. gesture        one or two loose loops for the overall mass (or a line of action for a long figure)
  2. construction   the centre line and the level lines through features that sit side by side (the eyes), measured ticks
                    where the other features fall on the centre line; drawn through the form, past its edges
  3. blocking       a rough loop for every feature
  4. contours       each line found in stages: a few straight strokes that carry its shape (sailing past the corners),
                    then the curve in several short strokes, then tighter strokes close to the final line

Every stroke goes through `brush.hand` (a slow wander, never jitter) and is drawn on the `under` layer, light and thin,
so the dark lines sit on top of it. The planner only needs the geometry of the figure (`plan`), so it works for ASCII
outlines, numbered parts and symbols alike.
"""

import math
import random

from .brush import Stroke, chaikin, dist, hand, loop, path_length, polar, resample, simplify

# (first stage) tuning, in fractions of U = sqrt(width * height) of the figure
ERR = 0.013                 # base wander of the hand
BLOCK_TOL = 0.07            # how far a straight blocking stroke may be from the contour
RUN = 0.32                  # length of a refining stroke
TIGHT_RUN = 0.2             # length of a tight stroke


class Contour:
    def __init__(self, points, closed=False, smooth=0.8):
        self.points, self.closed, self.smooth = list(points), closed, smooth

    def curve(self):
        """The smooth line the final drawing follows (corners rounded the way the renderer rounds them)."""
        return chaikin(self.points, 2 if self.smooth >= 0.1 else 0, self.closed)


class Block:
    """A feature (a symbol, a dot): where it is and how big."""

    def __init__(self, at, size, char=""):
        self.at, self.size, self.char = at, size, char


def _bounds(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _pca_angle(points):
    """Angle (degrees) of the long axis of a point cloud."""
    n = len(points)
    mx, my = sum(p[0] for p in points) / n, sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points)
    syy = sum((p[1] - my) ** 2 for p in points)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points)
    return math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy)), (sxx + syy) / n


class Underdrawing:
    def __init__(self, contours, blocks, amount=1.0, color="black", seed=0, width=0.085):
        self.contours = [c for c in contours if len(c.points) >= 2]
        self.blocks = list(blocks)
        self.amount = max(0.0, float(amount))
        self.color = color
        self.rnd = random.Random(seed)
        self.width = width
        cloud = [p for c in self.contours for p in c.points] or [b.at for b in self.blocks]
        self.cloud = cloud
        if cloud:
            ext = [p for c in self.contours for p in c.points] + [q for b in self.blocks
                                                                    for q in ((b.at[0] - b.size[0] / 2, b.at[1] - b.size[1] / 2),
                                                                              (b.at[0] + b.size[0] / 2, b.at[1] + b.size[1] / 2))]
            self.box = _bounds(ext)
        else:
            self.box = (0, 0, 1, 1)
        w, h = self.box[2] - self.box[0], self.box[3] - self.box[1]
        self.W, self.H = max(w, 0.5), max(h, 0.5)
        self.U = math.sqrt(self.W * self.H)
        self.err = ERR * self.U * self.amount
        self.out = []

    # ---- helpers -----------------------------------------------------------------------------------------------
    def _seed(self):
        return self.rnd.randrange(1 << 30)

    def _add(self, points, width_k=1.0, opacity=0.2, **kw):
        if len(points) >= 2:
            self.out.append(Stroke(points, self.width * width_k, self.color, min(1.0, opacity), "under", taper=kw.pop("taper", 0.8), **kw))

    def _pencil(self, points, err_k, opacity, width_k=1.0, overshoot=0.06, bow=1.0):
        self._add(hand(points, self.err * err_k, self._seed(), bow=bow, overshoot=overshoot), width_k, opacity)

    # ---- 1. gesture --------------------------------------------------------------------------------------------
    def _mass(self):
        """The points of the main form: the biggest closed contour if it holds most of the figure (the head, not its whiskers)."""
        best = None
        for c in self.contours:
            if c.closed and len(c.points) >= 4:
                x0, y0, x1, y1 = _bounds(c.points)
                area = (x1 - x0) * (y1 - y0)
                if best is None or area > best[0]:
                    best = (area, c)
        if best and best[0] >= 0.3 * self.W * self.H:
            return best[1].points
        return self.cloud

    def gesture(self):
        pts = self._mass()
        if len(pts) < 2:
            return
        x0, y0, x1, y1 = _bounds(pts)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = max(x1 - x0, 0.5), max(y1 - y0, 0.5)
        if max(w, h) / min(w, h) > 2.4:                      # a long form: the line of action along it
            ang, _ = _pca_angle(pts)
            half = max(w, h) / 2 * 1.08
            for k, bow in enumerate((1.2, 0.7)):
                a, b = polar((cx, cy), ang + 180, half), polar((cx, cy), ang, half)
                self._pencil([a, b], 2.0 - 0.5 * k, 0.10 + 0.05 * k, 1.3, overshoot=0.05, bow=bow)
            return
        ang, _ = _pca_angle(pts)
        ang = max(-18.0, min(18.0, ang if ang < 90 else ang - 180)) * (1.0 if min(w, h) / max(w, h) < 0.92 else 0.0)
        if w < h:
            ang = 0.0 if abs(ang) < 1 else ang
        for k in range(2):
            grow = 1.03 + 0.035 * k
            self.out.append(Stroke(loop((cx, cy), w / 2 * grow, h / 2 * grow, ang, self.err * (2.2 - 0.7 * k), self._seed(), turns=1.12 + 0.05 * k),
                                   self.width * 1.35, self.color, 0.10 + 0.05 * k, "under", taper=0.85))

    # ---- 2. construction ---------------------------------------------------------------------------------------
    def _levels(self):
        """Groups of features side by side: [(left, right)] pairs that sit at about the same height."""
        found = []
        bs = self.blocks
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, b = (bs[i], bs[j]) if bs[i].at[0] <= bs[j].at[0] else (bs[j], bs[i])
                dx, dy = b.at[0] - a.at[0], b.at[1] - a.at[1]
                wide = max(a.size[0], b.size[0])
                if dx < 1.6 * wide or dx < 0.12 * self.W or abs(dy) > 0.1 * max(self.H, dx):
                    continue
                match = min(a.size[0] * a.size[1], b.size[0] * b.size[1]) / max(a.size[0] * a.size[1], b.size[0] * b.size[1], 1e-6)
                if match < 0.4:
                    continue
                found.append((abs(dy) / dx + (1 - match) * 0.3, a, b))
        found.sort(key=lambda f: f[0])
        levels = []
        for _, a, b in found:                               # the best pair first; one level per height
            y = (a.at[1] + b.at[1]) / 2
            if all(abs(y - (l[0].at[1] + l[1].at[1]) / 2) > 0.1 * self.H for l in levels):
                levels.append((a, b))
            if len(levels) == 3:
                break
        levels.sort(key=lambda l: l[0].at[1] + l[1].at[1])
        return levels

    def construction(self):
        if not self.blocks and not self.contours:
            return
        x0, y0, x1, y1 = self.box
        levels = self._levels()
        mids = [((a.at[0] + b.at[0]) / 2, (a.at[1] + b.at[1]) / 2) for a, b in levels]
        # the centre line: through the middle of the level lines, else of the whole figure; tilted with the features
        if len(mids) >= 2:
            (ax, ay), (bx, by) = mids[0], mids[-1]
            tilt = 0.4 * math.atan2(bx - ax, by - ay)                         # leaning of the axis (damped: features are not exact)
            cx, cy = (sum(m[0] for m in mids) / len(mids), sum(m[1] for m in mids) / len(mids))
        elif mids:
            a, b = levels[0]
            tilt = math.atan2(-(b.at[1] - a.at[1]), b.at[0] - a.at[0])        # perpendicular to the level line
            cx, cy = mids[0]
        else:
            tilt, cx, cy = 0.0, (x0 + x1) / 2, (y0 + y1) / 2
        tilt = max(-0.12, min(0.12, tilt))
        top, bottom = y0 - 0.06 * self.H, y1 + 0.06 * self.H
        sx, sy = math.sin(tilt), math.cos(tilt)
        t0, t1 = (top - cy) / sy, (bottom - cy) / sy
        axis = [(cx + sx * t, cy + sy * t) for t in (t0, (t0 + t1) / 2, t1)]
        self._pencil(axis, 1.1, 0.22, 1.1, overshoot=0.03, bow=0.7)
        self._axis = (cx, cy, sx, sy)
        # level lines: through each pair, curved a little (they wrap the form), running past the pair
        for a, b in levels:
            ya, yb = a.at[1], b.at[1]
            reach = 0.18 * self.W
            p0, p1 = (a.at[0] - reach, ya - (yb - ya) * reach / max(1e-6, b.at[0] - a.at[0])), \
                     (b.at[0] + reach, yb + (yb - ya) * reach / max(1e-6, b.at[0] - a.at[0]))
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.03 * self.W)
            self._pencil([p0, mid, p1], 1.1, 0.2, 1.0, overshoot=0.03, bow=0.6)
        # measured ticks: a short cross line where a feature falls on the centre line
        used = {id(x) for pair in levels for x in pair}
        for b in self.blocks:
            if id(b) in used:
                continue
            t = (b.at[1] - cy) / sy
            ax_x = cx + sx * t
            if abs(b.at[0] - ax_x) < 0.18 * self.W:
                half = 0.07 * self.W
                self._pencil([(ax_x - half, b.at[1]), (ax_x + half, b.at[1] + 0.01 * self.W)], 0.6, 0.2, 0.9, overshoot=0.1, bow=0.4)

    # ---- 3. blocking -------------------------------------------------------------------------------------------
    def blocking(self):
        for b in self.blocks:
            rx, ry = max(b.size[0], 0.6) / 2, max(b.size[1], 0.6) / 2
            for k in range(2 if rx * ry > 3 else 1):
                self.out.append(Stroke(loop(b.at, rx * (1.08 + 0.06 * k), ry * (1.08 + 0.06 * k), 0.0, self.err * 0.7, self._seed(), turns=1.1),
                                       self.width * 0.9, self.color, 0.16 + 0.04 * k, "under", taper=0.85))

    # ---- 4. contours -------------------------------------------------------------------------------------------
    def _runs(self, curve, closed, length, overlap=0.14):
        """The curve in strokes of about `length` (the pencil lifts), neighbours overlapping a little. Start at a random place."""
        total = path_length(curve, closed)
        if total <= length * 1.25:
            return [curve + ([curve[0]] if closed else [])]
        line = resample(curve + ([curve[0]] if closed else []), 0.35)
        if closed:
            r = self.rnd.randrange(len(line) - 1)
            line = line[r:-1] + line[:r] + [line[r]]
        n = len(line)
        per = max(4, int(length / 0.35))
        step = max(2, int(per * (1 - overlap)))
        runs, i = [], 0
        while i < n - 2:
            runs.append(line[i:min(n, i + per + 1)])
            if i + per + 1 >= n:
                break
            i += step
        return runs

    def contour(self, c):
        curve = c.curve()
        length = path_length(curve, c.closed)
        if length < 0.6:
            return
        small = length < 0.25 * self.U
        # a. the few straight strokes that carry the shape, sailing past the corners
        if not small:
            tol = max(0.8, BLOCK_TOL * self.U)
            corners = simplify(curve + ([curve[0]] if c.closed else []), tol, c.closed)
            if c.closed and len(corners) > 2 and corners[0] != corners[-1]:
                corners.append(corners[0])
            for a, b in zip(corners, corners[1:]):
                if dist(a, b) > 0.8:
                    self._pencil([a, b], 1.5, 0.15, 1.15, overshoot=0.08, bow=1.0)
        # b. the curve itself, found in short strokes
        for run in self._runs(curve, c.closed, max(3.0, RUN * self.U)):
            self._pencil(run, 0.85, 0.24, 1.0, overshoot=0.05, bow=0.8)
        # c. tighter strokes close to the line (not after the whole length: the final line covers them)
        for run in self._runs(curve, c.closed, max(2.5, TIGHT_RUN * self.U), 0.2):
            self._pencil(run, 0.35, 0.3, 0.85, overshoot=0.03, bow=0.5)

    # ---- all ---------------------------------------------------------------------------------------------------
    def build(self):
        if self.amount <= 0 or (not self.contours and not self.blocks):
            return []
        self.gesture()
        self.construction()
        self.blocking()
        for c in sorted(self.contours, key=lambda c: -path_length(c.points, c.closed)):
            self.contour(c)
        return self.out


def plan(contours, blocks, amount=1.0, color="black", seed=0, width=0.085):
    """The underdrawing strokes (layer "under") of a figure: contours is [Contour], blocks is [Block]."""
    return Underdrawing(contours, blocks, amount, color, seed, width).build()
