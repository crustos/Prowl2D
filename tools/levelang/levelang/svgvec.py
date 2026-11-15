"""svgvec.py: our own SVG reader. An SVG goes in, flat vector shapes come out (polylines with a fill and a stroke), ready for a vector renderer such as Blender's grease pencil.

Why not Blender's own SVG import: it makes a mess of gradients, opacity and nested transforms, and cannot be driven from the level's data. This reads the SVG once, here, in plain Python
(standard library only, so it also runs inside Blender's bundled Python), and everything after it works on the same simple shapes.

What it reads: svg (viewBox, width, height), g, defs, use, rect (rx, ry), circle, ellipse, line, polyline, polygon, path (M L H V C S Q T A Z, absolute and relative), transform
(translate, scale, rotate, skewX, skewY, matrix), style="" and the presentation attributes (fill, stroke, stroke-width, stroke-linecap, stroke-linejoin, opacity, fill-opacity,
stroke-opacity, fill-rule, display), colours (#rgb, #rrggbb, #rrggbbaa, rgb(), rgba(), hsl(), names), and linearGradient / radialGradient (stops, objectBoundingBox or userSpaceOnUse,
gradientTransform, href). What it does not read (and says so in `Vector.warnings`): clipPath, mask, filter, text, image, dashes, <style> sheets, markers, patterns.

Coordinates come out in the viewBox's own units (y down), with every transform applied; a stroke's width is scaled by the transform that carried it.
"""
from __future__ import annotations

import colorsys
import math
import re
import xml.etree.ElementTree as ET

NAMED = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff", "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080",
    "pink": "#ffc0cb", "gray": "#808080", "grey": "#808080", "brown": "#a52a2a", "cyan": "#00ffff", "magenta": "#ff00ff", "lime": "#00ff00", "navy": "#000080",
    "teal": "#008080", "maroon": "#800000", "olive": "#808000", "silver": "#c0c0c0", "aqua": "#00ffff", "fuchsia": "#ff00ff", "gold": "#ffd700", "coral": "#ff7f50",
    "salmon": "#fa8072", "tan": "#d2b48c", "beige": "#f5f5dc", "ivory": "#fffff0", "khaki": "#f0e68c", "crimson": "#dc143c", "indigo": "#4b0082", "violet": "#ee82ee",
    "turquoise": "#40e0d0", "skyblue": "#87ceeb", "lightblue": "#add8e6", "darkblue": "#00008b", "lightgreen": "#90ee90", "darkgreen": "#006400", "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3", "darkgray": "#a9a9a9", "darkgrey": "#a9a9a9", "dimgray": "#696969", "orchid": "#da70d6", "plum": "#dda0dd", "sienna": "#a0522d",
    "chocolate": "#d2691e", "peru": "#cd853f", "wheat": "#f5deb3", "linen": "#faf0e6", "lavender": "#e6e6fa", "mintcream": "#f5fffa", "transparent": "#00000000",
}

SKIPPED = {"clippath", "mask", "filter", "text", "image", "marker", "pattern", "style", "script", "foreignobject", "title", "desc", "metadata", "symbol"}
NS = re.compile(r"^\{[^}]*\}")


class Paint:
    """What a shape is filled or stroked with: a flat colour or a gradient."""

    def __init__(self, kind="color", rgba=(0.0, 0.0, 0.0, 1.0), gradient=None):
        self.kind = kind                # 'color' | 'linear' | 'radial'
        self.rgba = rgba                # for a colour; for a gradient the average of its stops (what a renderer without gradients uses)
        self.gradient = gradient        # {'stops': [(offset, (r, g, b, a))], 'p': (x1, y1, x2, y2) | (cx, cy, r), 'units': 'box'|'user', 'matrix': (a, b, c, d, e, f)}

    def __repr__(self):
        return "Paint(%s %s)" % (self.kind, tuple(round(v, 3) for v in self.rgba))


class Shape:
    def __init__(self):
        self.subpaths: list[tuple[list[tuple[float, float]], bool]] = []   # (points, closed)
        self.fill: Paint | None = None
        self.stroke: Paint | None = None
        self.fill_opacity = 1.0         # fill-opacity times the opacity of everything it sits in
        self.stroke_opacity = 1.0
        self.stroke_width = 0.0
        self.linecap = "butt"
        self.linejoin = "miter"
        self.even_odd = False

    def bbox(self):
        xs = [p[0] for pts, _ in self.subpaths for p in pts]
        ys = [p[1] for pts, _ in self.subpaths for p in pts]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else (0.0, 0.0, 0.0, 0.0)


class Vector:
    def __init__(self):
        self.viewbox = (0.0, 0.0, 1.0, 1.0)     # min x, min y, width, height
        self.shapes: list[Shape] = []
        self.warnings: list[str] = []


# ---- colours ---------------------------------------------------------------------------------------------------------------------------------

def parse_color(text, current=None):
    """(r, g, b, a) in 0..1, or None for `none`. Raises ValueError for something it cannot read."""
    t = (text or "").strip().lower()
    if t in ("", "none"):
        return None
    if t == "currentcolor":
        return current if current is not None else (0.0, 0.0, 0.0, 1.0)
    t = NAMED.get(t, t)
    if t.startswith("#"):
        h = t[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
            raise ValueError("bad colour " + text)
        v = [int(h[i:i + 2], 16) / 255.0 for i in range(0, len(h), 2)]
        return (v[0], v[1], v[2], v[3] if len(v) == 4 else 1.0)
    m = re.fullmatch(r"(rgba?|hsla?)\(([^)]*)\)", t)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(2).strip()) if p]
        if len(parts) < 3:
            raise ValueError("bad colour " + text)

        def num(s, scale=1.0):
            return float(s[:-1]) / 100.0 if s.endswith("%") else float(s) / scale

        a = num(parts[3]) if len(parts) > 3 else 1.0
        if m.group(1).startswith("rgb"):
            return (min(max(num(parts[0], 255.0), 0.0), 1.0), min(max(num(parts[1], 255.0), 0.0), 1.0), min(max(num(parts[2], 255.0), 0.0), 1.0), min(max(a, 0.0), 1.0))
        h = float(parts[0].rstrip("deg")) / 360.0 % 1.0
        r, g, b = colorsys.hls_to_rgb(h, num(parts[2]), num(parts[1]))
        return (r, g, b, min(max(a, 0.0), 1.0))
    raise ValueError("bad colour " + text)


# ---- transforms (affine, as (a, b, c, d, e, f): x' = a x + c y + e, y' = b x + d y + f) ---------------------------------------------------------

IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mul(m, n):
    """m after n: apply n first."""
    return (m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
            m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5])


def apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def scale_of(m):
    return math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))


def parse_transform(text):
    m = IDENT
    for name, args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", args)]
        name = name.lower()
        if name == "translate" and v:
            t = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale" and v:
            t = (v[0], 0.0, 0.0, v[1] if len(v) > 1 else v[0], 0.0, 0.0)
        elif name == "rotate" and v:
            a = math.radians(v[0])
            c, s = math.cos(a), math.sin(a)
            t = (c, s, -s, c, 0.0, 0.0)
            if len(v) >= 3:
                t = mul(mul((1.0, 0.0, 0.0, 1.0, v[1], v[2]), t), (1.0, 0.0, 0.0, 1.0, -v[1], -v[2]))
        elif name == "skewx" and v:
            t = (1.0, 0.0, math.tan(math.radians(v[0])), 1.0, 0.0, 0.0)
        elif name == "skewy" and v:
            t = (1.0, math.tan(math.radians(v[0])), 0.0, 1.0, 0.0, 0.0)
        elif name == "matrix" and len(v) == 6:
            t = tuple(v)
        else:
            continue
        m = mul(m, t)
    return m


# ---- paths -----------------------------------------------------------------------------------------------------------------------------------

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_TOKEN = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _cubic(p0, p1, p2, p3, step):
    length = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
    n = max(4, min(64, int(math.ceil(length / step))))
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1.0 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def _arc(p0, rx, ry, rot, large, sweep, p1, step):
    """SVG endpoint arc -> points (the standard F.6.5 conversion to a centre form)."""
    if p0 == p1:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [p1]
    phi = math.radians(rot)
    c, s = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1, y1 = c * dx + s * dy, -s * dx + c * dy
    lam = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry)
    if lam > 1:
        k = math.sqrt(lam)
        rx, ry = rx * k, ry * k
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co * rx * y1 / ry, -co * ry * x1 / rx
    cx, cy = c * cxp - s * cyp + (p0[0] + p1[0]) / 2.0, s * cxp + c * cyp + (p0[1] + p1[1]) / 2.0

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1 - cxp) / rx, (y1 - cyp) / ry)
    dt = ang((x1 - cxp) / rx, (y1 - cyp) / ry, (-x1 - cxp) / rx, (-y1 - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(4, min(96, int(math.ceil(abs(dt) * max(rx, ry) / step))))
    out = []
    for i in range(1, n + 1):
        a = t1 + dt * i / n
        ex, ey = rx * math.cos(a), ry * math.sin(a)
        out.append((c * ex - s * ey + cx, s * ex + c * ey + cy))
    out[-1] = p1
    return out


def parse_path(d, step=1.0):
    """The path's subpaths as [(points, closed)], curves flattened so that no segment is much longer than `step` (in the path's own units)."""
    subs = []
    cur = []
    closed_pending = False
    tokens = [(m.group(1), m.group(2)) for m in _TOKEN.finditer(d or "")]
    i = 0
    cmd = None
    x = y = sx = sy = 0.0
    last_c2 = last_q = None
    prev = None

    def flush(closed):
        nonlocal cur
        if len(cur) >= 2 or (cur and closed):
            subs.append((cur, closed))
        cur = []

    while i < len(tokens):
        if tokens[i][0]:
            cmd = tokens[i][0]
            i += 1
            if cmd in "Zz":
                if cur:
                    flush(True)
                x, y = sx, sy
                last_c2 = last_q = None
                prev = "Z"
                continue
        if cmd is None:
            break
        up = cmd.upper()
        n = ARGS[up]
        vals = []
        while i < len(tokens) and tokens[i][1] is not None and len(vals) < n:
            vals.append(float(tokens[i][1]))
            i += 1
        if len(vals) < n:
            break
        rel = cmd.islower()
        if up == "M":
            if cur:
                flush(False)
            nx, ny = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
            x, y, sx, sy = nx, ny, nx, ny
            cur = [(x, y)]
            cmd = "l" if rel else "L"
            last_c2 = last_q = None
        else:
            if not cur:
                cur = [(x, y)]                      # a command after Z starts from the last start point
            if up == "L":
                x, y = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
                cur.append((x, y))
                last_c2 = last_q = None
            elif up == "H":
                x = x + vals[0] if rel else vals[0]
                cur.append((x, y))
                last_c2 = last_q = None
            elif up == "V":
                y = y + vals[0] if rel else vals[0]
                cur.append((x, y))
                last_c2 = last_q = None
            elif up in ("C", "S"):
                if up == "C":
                    c1 = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
                    c2 = (x + vals[2], y + vals[3]) if rel else (vals[2], vals[3])
                    e = (x + vals[4], y + vals[5]) if rel else (vals[4], vals[5])
                else:
                    c1 = (2 * x - last_c2[0], 2 * y - last_c2[1]) if last_c2 else (x, y)
                    c2 = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
                    e = (x + vals[2], y + vals[3]) if rel else (vals[2], vals[3])
                cur.extend(_cubic((x, y), c1, c2, e, step))
                x, y = e
                last_c2, last_q = c2, None
            elif up in ("Q", "T"):
                if up == "Q":
                    q = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
                    e = (x + vals[2], y + vals[3]) if rel else (vals[2], vals[3])
                else:
                    q = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q else (x, y)
                    e = (x + vals[0], y + vals[1]) if rel else (vals[0], vals[1])
                c1 = (x + 2.0 / 3.0 * (q[0] - x), y + 2.0 / 3.0 * (q[1] - y))
                c2 = (e[0] + 2.0 / 3.0 * (q[0] - e[0]), e[1] + 2.0 / 3.0 * (q[1] - e[1]))
                cur.extend(_cubic((x, y), c1, c2, e, step))
                x, y = e
                last_q, last_c2 = q, None
            elif up == "A":
                e = (x + vals[5], y + vals[6]) if rel else (vals[5], vals[6])
                cur.extend(_arc((x, y), vals[0], vals[1], vals[2], vals[3] != 0, vals[4] != 0, e, step))
                x, y = e
                last_c2 = last_q = None
    if cur:
        flush(False)
    return subs


# ---- the document ----------------------------------------------------------------------------------------------------------------------------

def _num(s, default=0.0):
    m = _NUM.search(s or "")
    return float(m.group(0)) if m else default


def _style(el):
    out = {}
    for k, v in el.attrib.items():
        out[NS.sub("", k)] = v
    for part in (el.attrib.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


INHERITED = ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill-opacity", "stroke-opacity", "fill-rule", "color")


def parse(svg_text, step_fraction=1.0 / 80.0):
    """An SVG's text -> Vector. `step_fraction`: the longest a flattened segment of a curve is, as a fraction of the viewBox's larger side."""
    out = Vector()
    try:
        root = ET.fromstring(svg_text.strip())
    except ET.ParseError as e:
        raise ValueError("not an SVG: %s" % e)
    if NS.sub("", root.tag).lower() != "svg":
        raise ValueError("not an SVG: the root is <%s>" % NS.sub("", root.tag))
    vb = root.attrib.get("viewBox")
    if vb:
        v = [float(x) for x in _NUM.findall(vb)]
        if len(v) == 4 and v[2] > 0 and v[3] > 0:
            out.viewbox = tuple(v)
    else:
        out.viewbox = (0.0, 0.0, _num(root.attrib.get("width"), 100.0), _num(root.attrib.get("height"), 100.0))
    step = max(out.viewbox[2], out.viewbox[3]) * step_fraction

    ids = {}
    for el in root.iter():
        if "id" in el.attrib:
            ids[el.attrib["id"]] = el
    warned = set()

    def warn(msg):
        if msg not in warned:
            warned.add(msg)
            out.warnings.append(msg)

    gradient_cache = {}

    def gradient(gid):
        if gid in gradient_cache:
            return gradient_cache[gid]
        el = ids.get(gid)
        res = None
        if el is not None and NS.sub("", el.tag).lower() in ("lineargradient", "radialgradient"):
            chain, seen, cur = [], set(), el
            while cur is not None and id(cur) not in seen:       # href chains: attributes and stops come from the first that has them
                seen.add(id(cur))
                chain.append(cur)
                href = cur.attrib.get("{http://www.w3.org/1999/xlink}href") or cur.attrib.get("href")
                cur = ids.get(href[1:]) if href and href.startswith("#") else None

            def attr(name, default=None):
                for c in chain:
                    if name in c.attrib:
                        return c.attrib[name]
                return default

            stops = []
            for c in chain:
                stops = [s for s in c if NS.sub("", s.tag).lower() == "stop"]
                if stops:
                    break
            cols = []
            for s in stops:
                st = _style(s)
                off = st.get("offset", "0")
                off = float(off[:-1]) / 100.0 if off.endswith("%") else float(off)
                try:
                    col = parse_color(st.get("stop-color", "black")) or (0.0, 0.0, 0.0, 0.0)
                except ValueError:
                    col = (0.0, 0.0, 0.0, 1.0)
                a = col[3] * float(st.get("stop-opacity", 1))
                cols.append((min(max(off, cols[-1][0] if cols else 0.0), 1.0), (col[0], col[1], col[2], a)))
            if cols:
                linear = NS.sub("", el.tag).lower() == "lineargradient"
                units = "user" if attr("gradientUnits") == "userSpaceOnUse" else "box"

                def coord(name, default):
                    v = attr(name)
                    if v is None:
                        return default
                    return float(v[:-1]) / 100.0 if v.endswith("%") else _num(v, default)

                p = (coord("x1", 0.0), coord("y1", 0.0), coord("x2", 1.0), coord("y2", 0.0)) if linear else (coord("cx", 0.5), coord("cy", 0.5), coord("r", 0.5))
                avg = tuple(sum(c[1][k] for c in cols) / len(cols) for k in range(4))
                res = Paint("linear" if linear else "radial", avg, {"stops": cols, "p": p, "units": units, "matrix": parse_transform(attr("gradientTransform", ""))})
        gradient_cache[gid] = res
        return res

    def paint(value, current, what):
        v = (value or "").strip()
        m = re.fullmatch(r"url\(\s*#([^)\s]+)\s*\)\s*(.*)", v)
        if m:
            g = gradient(m.group(1))
            if g is not None:
                return g
            if m.group(2):
                v = m.group(2)
            else:
                warn("a %s refers to a gradient or pattern that is not there or not supported (#%s)" % (what, m.group(1)))
                return None
        try:
            c = parse_color(v, current)
        except ValueError:
            warn("colour %r not understood" % v)
            return None
        return Paint("color", c) if c is not None else None

    def shape(el, tag, st, m, op):
        sh = Shape()
        scale = scale_of(m)
        subs = []
        a = el.attrib
        if tag == "path":
            subs = parse_path(a.get("d", ""), step)
        elif tag == "rect":
            x, y, w, h = _num(a.get("x")), _num(a.get("y")), _num(a.get("width")), _num(a.get("height"))
            rx, ry = a.get("rx"), a.get("ry")
            rx = _num(rx) if rx is not None else (_num(ry) if ry is not None else 0.0)
            ry = _num(ry) if a.get("ry") is not None else rx
            rx, ry = min(rx, w / 2.0), min(ry, h / 2.0)
            if w <= 0 or h <= 0:
                return None
            if rx <= 0 or ry <= 0:
                subs = [([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True)]
            else:
                d = "M%g %g H%g A%g %g 0 0 1 %g %g V%g A%g %g 0 0 1 %g %g H%g A%g %g 0 0 1 %g %g V%g A%g %g 0 0 1 %g %gZ" % (
                    x + rx, y, x + w - rx, rx, ry, x + w, y + ry, y + h - ry, rx, ry, x + w - rx, y + h, x + rx, rx, ry, x, y + h - ry, y + ry, rx, ry, x + rx, y)
                subs = parse_path(d, step)
        elif tag in ("circle", "ellipse"):
            cx, cy = _num(a.get("cx")), _num(a.get("cy"))
            rx, ry = (_num(a.get("r")),) * 2 if tag == "circle" else (_num(a.get("rx")), _num(a.get("ry")))
            if rx <= 0 or ry <= 0:
                return None
            n = max(12, min(96, int(math.ceil(2 * math.pi * max(rx, ry) / step))))
            subs = [([(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)], True)]
        elif tag == "line":
            subs = [([(_num(a.get("x1")), _num(a.get("y1"))), (_num(a.get("x2")), _num(a.get("y2")))], False)]
        elif tag in ("polyline", "polygon"):
            v = [float(q) for q in _NUM.findall(a.get("points", ""))]
            pts = list(zip(v[0::2], v[1::2]))
            if len(pts) >= 2:
                subs = [(pts, tag == "polygon")]
        local = [p for pts, _ in subs for p in pts]
        local_box = (min(p[0] for p in local), min(p[1] for p in local), max(p[0] for p in local), max(p[1] for p in local)) if local else (0.0, 0.0, 0.0, 0.0)
        sh.subpaths = [([apply(m, px, py) for px, py in pts], closed) for pts, closed in subs]
        sh.subpaths = [s for s in sh.subpaths if len(s[0]) >= 2]
        if not sh.subpaths:
            return None
        current = parse_color(st.get("color", "black"))
        fill_value = st.get("fill", "black")
        sh.fill = paint(fill_value, current, "fill")
        sh.stroke = paint(st.get("stroke", "none"), current, "stroke")
        sh.fill_opacity = max(0.0, min(1.0, float(st.get("fill-opacity", 1)))) * op
        sh.stroke_opacity = max(0.0, min(1.0, float(st.get("stroke-opacity", 1)))) * op
        sh.stroke_width = _num(st.get("stroke-width"), 1.0) * scale
        sh.linecap = st.get("stroke-linecap", "butt")
        sh.linejoin = st.get("stroke-linejoin", "miter")
        sh.even_odd = st.get("fill-rule") == "evenodd"
        if st.get("stroke-dasharray", "none") not in ("none", ""):
            warn("stroke-dasharray is drawn solid")
        if sh.stroke is None or sh.stroke_width <= 0:
            sh.stroke = None
        if sh.fill is None and sh.stroke is None:
            return None
        if sh.fill is not None and sh.fill.kind != "color":
            g = sh.fill.gradient
            sh.fill.gradient = dict(g)
            sh.fill.gradient["bbox"] = local_box          # the shape's box in its own (untransformed) coordinates: objectBoundingBox units are measured on it
            sh.fill.gradient["matrix_total"] = m
        return sh

    def walk(el, inherited, m, op, depth=0):
        tag = NS.sub("", el.tag).lower()
        if tag in SKIPPED:
            if tag in ("clippath", "mask", "filter", "text", "image", "marker", "pattern"):
                warn("<%s> is not supported and is left out" % tag)
            return
        if tag == "defs" or depth > 24:
            return
        st = dict(inherited)
        for k, v in _style(el).items():
            if k in INHERITED or k in ("opacity", "display", "stroke-dasharray", "transform", "visibility"):
                st[k] = v
        if st.get("display") == "none" or st.get("visibility") == "hidden":
            return
        own = el.attrib.get("transform") or _style(el).get("transform")
        m2 = mul(m, parse_transform(own)) if own else m
        op2 = op * max(0.0, min(1.0, float(_style(el).get("opacity", 1)))) if tag != "svg" else op
        passed = {k: st[k] for k in INHERITED + ("stroke-dasharray",) if k in st}
        if tag in ("svg", "g", "a", "switch"):
            for child in el:
                walk(child, passed, m2, op2, depth + 1)
        elif tag == "use":
            href = el.attrib.get("{http://www.w3.org/1999/xlink}href") or el.attrib.get("href")
            target = ids.get(href[1:]) if href and href.startswith("#") else None
            if target is not None:
                mu = mul(m2, (1.0, 0.0, 0.0, 1.0, _num(el.attrib.get("x")), _num(el.attrib.get("y"))))
                if NS.sub("", target.tag).lower() == "symbol":
                    for child in target:
                        walk(child, passed, mu, op2, depth + 1)
                else:
                    walk(target, passed, mu, op2, depth + 1)
        elif tag in ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon"):
            sh = shape(el, tag, st, m2, op2)
            if sh is not None:
                out.shapes.append(sh)
        else:
            warn("<%s> is not supported and is left out" % tag)

    walk(root, {}, IDENT, 1.0)
    return out


# ---- what a renderer without gradients does with one ----------------------------------------------------------------------------------------------

def gradient_at(paint_, t):
    """The colour of a gradient at t (0..1 along it)."""
    stops = paint_.gradient["stops"]
    if t <= stops[0][0]:
        return stops[0][1]
    for (o0, c0), (o1, c1) in zip(stops, stops[1:]):
        if t <= o1:
            f = 0.0 if o1 == o0 else (t - o0) / (o1 - o0)
            return tuple(c0[k] + (c1[k] - c0[k]) * f for k in range(4))
    return stops[-1][1]


def gradient_axis(paint_):
    """For a linear gradient, (x0, y0, dx, dy) in the output coordinates (the shape's transforms applied): t = ((x - x0) dx + (y - y0) dy) / (dx² + dy²). For a radial one,
    (cx, cy, r, None). The gradient's units and transform, and the shape's own placement, are folded in."""
    g = paint_.gradient
    m = g["matrix"]
    tot = g["matrix_total"]
    if g["units"] == "box":
        bx0, by0, bx1, by1 = g["bbox"]
        full = mul(tot, mul((bx1 - bx0 or 1e-9, 0.0, 0.0, by1 - by0 or 1e-9, bx0, by0), m))
    else:
        full = mul(tot, m)
    if paint_.kind == "linear":
        x1, y1, x2, y2 = g["p"]
        a = apply(full, x1, y1)
        b = apply(full, x2, y2)
        return (a[0], a[1], b[0] - a[0], b[1] - a[1])
    cx, cy, r = g["p"]
    c = apply(full, cx, cy)
    return (c[0], c[1], r * scale_of(full), None)
