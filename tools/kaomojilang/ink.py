"""ASCII art as ink: `\\ / | ( ) - _ ^ < >` in a grid are small strokes; strokes that touch are joined into one line,
and the line is drawn as a smooth curve (so a rough ASCII outline becomes a flowing one).

A character cell is 1 column wide and 2 units tall (a text row is twice as tall as a column is wide). The strokes of a
cell are given relative to its centre, x in -0.5..0.5, y in -1..1. A run of the same slash in a row (`\\\\\\`) is ONE
shallow stroke over the whole run, the way ASCII artists use it.
"""

import math

TOL = 0.75            # strokes whose ends are closer than this (in columns) are joined
GAP = 1.6             # a free end also reaches another free end this far (rough ASCII art: a cell of air in an outline is still one line)

SHAPES = {
    "\\": [(-0.5, -1.0), (0.5, 1.0)],
    "/": [(-0.5, 1.0), (0.5, -1.0)],
    "|": [(0.0, -1.0), (0.0, 1.0)],
    "-": [(-0.5, 0.0), (0.5, 0.0)],
    "_": [(-0.5, 0.95), (0.5, 0.95)],
    "(": [(0.3, -1.0), (-0.12, -0.45), (-0.25, 0.0), (-0.12, 0.45), (0.3, 1.0)],
    ")": [(-0.3, -1.0), (0.12, -0.45), (0.25, 0.0), (0.12, 0.45), (-0.3, 1.0)],
    "^": [(-0.5, 0.5), (0.0, -0.7), (0.5, 0.5)],
    "<": [(0.5, -1.0), (-0.5, 0.0), (0.5, 1.0)],
    ">": [(-0.5, -1.0), (0.5, 0.0), (-0.5, 1.0)],
}
LOW, HIGH = ".,", "'`"            # marks that sit low or high in their cell: they bend toward the strokes next to them
FLEX = LOW + HIGH
DOTS = {}


def _runs(cells):
    """Merge a row of the same slash into one stroke: [(char, x_first, x_last, y)]."""
    rows = {}
    for c, x, y in cells:
        rows.setdefault((c, y), []).append(x)
    out = []
    for (c, y), xs in rows.items():
        xs.sort()
        run = [xs[0]]
        for x in xs[1:]:
            if c in "\\/" and abs(x - run[-1] - 1.0) < 1e-6:
                run.append(x)
            else:
                out.append((c, run[0], run[-1], y))
                run = [x]
        out.append((c, run[0], run[-1], y))
    return out


def _edge(c, side):
    """y (relative to the centre) where the stroke of `c` meets the next cell on `side` (-1 left, 1 right); None if it does not reach it."""
    pts = SHAPES.get(c)
    if not pts:
        return None
    p = min(pts, key=lambda q: q[0]) if side == -1 else max(pts, key=lambda q: q[0])
    return p[1] if abs(p[0]) >= 0.45 else None


def _flex(c, x, y, occ, flex=()):
    """The marks . , ' and the backtick bend toward their neighbours: `,-'` rises, `-.` falls, `.______.` dips and comes back up.
    Marks side by side (`'.`) share the way between the strokes at the two ends of the run, a little each."""
    xs = {fx for fx, fy in flex if fy == y}
    x0 = x
    while x0 - 1.0 in xs:
        x0 -= 1.0
    x1 = x
    while x1 + 1.0 in xs:
        x1 += 1.0
    count = int(round(x1 - x0)) + 1
    k = int(round(x - x0))
    left, right = occ.get((x0 - 1.0, y)), occ.get((x1 + 1.0, y))
    yl = _edge(left, 1) if left else None
    yr = _edge(right, -1) if right else None
    free = 0.8 if c in LOW else -0.8
    if yl is None and yr is None:
        if count > 1:                                    # a run of marks with nothing at its ends: a slight line
            return [(-0.5, free * 0.7), (0.5, free * 0.7)]
        return [(-0.3, free), (0.3, free * 0.6)] if c in LOW else [(-0.3, free * 0.6), (0.3, free)]
    a0 = yl if yl is not None else yr + free
    b0 = yr if yr is not None else yl + free
    return [(-0.5, a0 + (b0 - a0) * k / count), (0.5, a0 + (b0 - a0) * (k + 1) / count)]


def strokes(cells, aspect=2.0):
    """`cells` = [(char, x, row)] -> (segments, dots): segments are point lists, dots are (x, y) centres."""
    segs, dots = [], []
    plain = [(c, x, row * aspect) for c, x, row in cells if c in SHAPES or c in FLEX]
    occ = {(x, y): c for c, x, y in plain if c in SHAPES}
    flex = {(x, y) for c, x, y in plain if c in FLEX}
    for c, x0, x1, y in _runs(plain):
        if c in FLEX:
            segs.append([(x0 + px, y + py) for px, py in _flex(c, x0, y, occ, flex)])
            continue
        if c in "\\/" and x1 > x0:                       # a run of slashes: one shallow stroke
            left, right = x0 - 0.5, x1 + 0.5
            segs.append([(left, y - 1.0), (right, y + 1.0)] if c == "\\" else [(left, y + 1.0), (right, y - 1.0)])
            continue
        segs.append([(x0 + px, y + py) for px, py in SHAPES[c]])
    return segs, dots


def _near(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def chains(segs):
    """Join strokes whose ends touch: [(points, closed)]."""
    n = len(segs)
    ends = [(i, e) for i in range(n) for e in (0, 1)]

    def pt(i, e):
        return segs[i][0] if e == 0 else segs[i][-1]

    pairs = []
    for a in range(len(ends)):
        for b in range(a + 1, len(ends)):
            (i, e), (j, f) = ends[a], ends[b]
            if i == j:
                continue
            d = _near(pt(i, e), pt(j, f))
            if d <= GAP:
                pairs.append((d, ends[a], ends[b]))
    pairs.sort(key=lambda t: t[0])
    link = {}
    for d, a, b in pairs:                            # touching ends first, then (only free ends) the gaps
        if d <= TOL and a not in link and b not in link:
            link[a], link[b] = b, a
    for d, a, b in pairs:
        if d > TOL and a not in link and b not in link:
            link[a], link[b] = b, a
    done, out = set(), []

    def walk(i, e):
        """Start at the end `e` of segment i, go to its other end, and follow the links."""
        pts, closed = [], False
        while True:
            done.add(i)
            seg = segs[i] if e == 0 else segs[i][::-1]
            if pts:
                mid = ((pts[-1][0] + seg[0][0]) / 2, (pts[-1][1] + seg[0][1]) / 2)
                pts[-1] = mid
                pts.extend(seg[1:])
            else:
                pts.extend(seg)
            far = (i, 1 - e)
            nxt = link.get(far)
            if nxt is None:
                break
            if nxt[0] in done:
                closed = nxt[0] == start_seg
                break
            i, e = nxt
        return pts, closed

    for i in range(n):                               # open chains first: they start at a free end
        if i in done:
            continue
        for e in (0, 1):
            if (i, e) not in link:
                start_seg = i
                out.append(walk(i, e))
                break
    for i in range(n):                               # what is left is loops
        if i not in done:
            start_seg = i
            out.append(walk(i, 0))
    return [(simplify(p), c) for p, c in out]


def simplify(pts, eps=0.06):
    """Drop points that lie on the line between their neighbours (a stack of `|` is one straight line)."""
    if len(pts) < 3:
        return pts
    keep = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = keep[-1], pts[i], pts[i + 1]
        cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        length = _near(a, c) or 1.0
        if cross / length > eps:
            keep.append(b)
    keep.append(pts[-1])
    return keep
