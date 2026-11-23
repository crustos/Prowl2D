"""CSS animation subset: `@keyframes`, the `animation` property, timing functions and interpolation.

Pure functions, no drawing. `parse_keyframes(css)` reads `@keyframes name { from {...} 50% {...} to {...} }`, `parse_animation(text)`
reads the `animation` shorthand (several, separated by commas), and `animate(...)` gives the value of each animated property at
time `t` (seconds). Values travel as CSS text ("12px", "rotate(30deg)", "0 -5"): `interpolate(kind, a, b, r)` mixes two of them.

What follows CSS: a delay (negative too), `infinite` or N iterations, directions (normal, reverse, alternate, alternate-reverse),
fill modes (none, forwards, backwards, both), the timing function of the animation or of each keyframe (`linear`, `ease`, `ease-in`,
`ease-out`, `ease-in-out`, `cubic-bezier()`, `steps()`, `step-start`, `step-end`), properties missing from a keyframe taking the
value the element has without the animation, and a later animation overriding an earlier one.
"""

import math
import re
from dataclasses import dataclass, field


class AnimError(Exception):
    pass


# ====================================================================================================
# @keyframes
# ====================================================================================================

@dataclass
class Keyframes:
    name: str
    stops: list = field(default_factory=list)       # [(offset 0..1, {property: value}, timing function text or None)], sorted


def _strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _blocks(css, what):
    """[(header, body)] of the `header { body }` blocks at the top level of `css`."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            if css[i:].strip():
                raise AnimError(f"{what}: '{css[i:].strip()[:30]}' is not inside a block")
            break
        depth, k = 1, j + 1
        while k < n and depth:
            depth += (css[k] == "{") - (css[k] == "}")
            k += 1
        if depth:
            raise AnimError(f"{what}: '{{' without '}}' after '{css[i:j].strip()[:30]}'")
        out.append((css[i:j].strip(), css[j + 1:k - 1]))
        i = k
    return out


def declarations(body, what):
    out = {}
    for decl in body.split(";"):
        if not decl.strip():
            continue
        if ":" not in decl:
            raise AnimError(f"{what}: bad declaration '{decl.strip()}'")
        k, v = decl.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


def parse_keyframes(css):
    """{name: Keyframes} of every `@keyframes` block in `css`. Other rules are errors (only keyframes are supported)."""
    found = {}
    for header, body in _blocks(_strip_comments(css), "style"):
        m = re.fullmatch(r"@keyframes\s+([A-Za-z_][\w-]*)", header)
        if not m:
            raise AnimError(f"style: '{header[:40]}' is not supported (only @keyframes blocks are)")
        name, stops = m.group(1), {}
        for sel, decls in _blocks(body, f"@keyframes {m.group(1)}"):
            props = declarations(decls, f"@keyframes {name}")
            timing = props.pop("animation-timing-function", None)
            for s in sel.split(","):
                s = s.strip().lower()
                if s == "from":
                    off = 0.0
                elif s == "to":
                    off = 1.0
                else:
                    pm = re.fullmatch(r"(\d+(?:\.\d+)?|\.\d+)%", s)
                    if not pm or not 0 <= float(pm.group(1)) <= 100:
                        raise AnimError(f"@keyframes {name}: '{s}' is not from, to or a percentage between 0% and 100%")
                    off = float(pm.group(1)) / 100
                old = stops.get(off, ({}, None))
                stops[off] = ({**old[0], **props}, timing or old[1])
        if not stops:
            raise AnimError(f"@keyframes {name} has no keyframes")
        found[name] = Keyframes(name, [(o, p, t) for o, (p, t) in sorted(stops.items())])
    return found


# ====================================================================================================
# animation property
# ====================================================================================================

@dataclass
class Anim:
    name: str
    duration: float = 0.0
    delay: float = 0.0
    iterations: float = 1.0
    direction: str = "normal"
    fill: str = "none"
    timing: str = "ease"


_DIRECTIONS = ("normal", "reverse", "alternate", "alternate-reverse")
_FILLS = ("none", "forwards", "backwards", "both")
_TIMINGS = ("linear", "ease", "ease-in", "ease-out", "ease-in-out", "step-start", "step-end")
_TIME = re.compile(r"([-+]?(?:\d+\.?\d*|\.\d+))(ms|s)")


def _split_top(text, sep):
    """Split on `sep` outside parentheses."""
    out, depth, cur = [], 0, ""
    for c in text:
        depth += (c == "(") - (c == ")")
        if c in sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
    out.append(cur)
    return [p.strip() for p in out if p.strip()]


def _seconds(token):
    m = _TIME.fullmatch(token)
    return None if not m else float(m.group(1)) * (0.001 if m.group(2) == "ms" else 1.0)


def parse_animation(text):
    """[Anim] from the `animation` shorthand (`name 2s ease-in 0.5s infinite alternate both`, several separated by commas)."""
    anims = []
    for one in _split_top(text or "", ","):
        a, times = Anim(""), []
        for tok in _split_top(one, " \t\n"):
            low = tok.lower()
            if _seconds(low) is not None:
                times.append(_seconds(low))
            elif low == "infinite":
                a.iterations = math.inf
            elif re.fullmatch(r"\d+(?:\.\d+)?|\.\d+", low):
                a.iterations = float(low)
            elif low in _DIRECTIONS:
                a.direction = low
            elif low in _FILLS and low != "none":
                a.fill = low
            elif low in _TIMINGS or low.startswith(("cubic-bezier(", "steps(")):
                a.timing = low
            elif low in ("running",):
                pass
            elif low == "paused":
                raise AnimError("animation: animation-play-state is not supported (drive the animation with t)")
            elif low == "none":
                a.name = a.name or "none"
            elif re.fullmatch(r"[A-Za-z_][\w-]*", tok) and not a.name:
                a.name = tok
            else:
                raise AnimError(f"animation: cannot read '{tok}' in '{one}'")
        if len(times) > 2:
            raise AnimError(f"animation: more than two times in '{one}' (duration, delay)")
        if times:
            a.duration = times[0]
        if len(times) > 1:
            a.delay = times[1]
        if a.duration < 0:
            raise AnimError(f"animation: a negative duration in '{one}'")
        if not a.name:
            raise AnimError(f"animation: no @keyframes name in '{one}'")
        if a.name != "none":
            anims.append(a)
    return anims


def animation_from_style(style):
    """[Anim] of the `animation` shorthand and the `animation-*` longhands of a style dict (the longhands win)."""
    base = parse_animation(style["animation"]) if style.get("animation") else []
    long = {k: v for k, v in style.items() if k.startswith("animation-") and k != "animation-timing-function" or k == "animation-timing-function"}
    if not long:
        return base
    names = _split_top(long.get("animation-name", ""), ",") or [a.name for a in base]
    if not names:
        raise AnimError("animation: longhands without animation-name")
    out = []

    def pick(key, i, default, conv):
        vals = _split_top(long.get(key, ""), ",")
        return conv(vals[i % len(vals)]) if vals else default

    def secs(v):
        s = _seconds(v.lower())
        if s is None:
            raise AnimError(f"animation: '{v}' is not a time (1s, 200ms)")
        return s
    for i, n in enumerate(names):
        b = base[i] if i < len(base) else Anim(n)
        out.append(Anim(n, pick("animation-duration", i, b.duration, secs), pick("animation-delay", i, b.delay, secs),
                        pick("animation-iteration-count", i, b.iterations, lambda v: math.inf if v == "infinite" else float(v)),
                        pick("animation-direction", i, b.direction, str.lower), pick("animation-fill-mode", i, b.fill, str.lower),
                        pick("animation-timing-function", i, b.timing, str.lower)))
        if out[-1].direction not in _DIRECTIONS or out[-1].fill not in _FILLS:
            raise AnimError(f"animation: direction or fill-mode not understood in {out[-1]}")
    return out


# ====================================================================================================
# Timing functions and progress
# ====================================================================================================

_BEZIER = {"ease": (.25, .1, .25, 1.), "ease-in": (.42, 0., 1., 1.), "ease-out": (0., 0., .58, 1.), "ease-in-out": (.42, 0., .58, 1.)}


def _bezier(x1, y1, x2, y2):
    def ax(t):
        return 3 * x1 * t * (1 - t) ** 2 + 3 * x2 * t * t * (1 - t) + t ** 3

    def ay(t):
        return 3 * y1 * t * (1 - t) ** 2 + 3 * y2 * t * t * (1 - t) + t ** 3

    def f(x):
        if x <= 0:
            return 0.0 if x < 0 else 0.0
        if x >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if ax(mid) < x:
                lo = mid
            else:
                hi = mid
        return ay((lo + hi) / 2)
    return f


def _steps(n, jump):
    def f(x):
        if jump in ("jump-none",):
            k = math.floor(x * n) if x < 1 else n - 1
            return min(1.0, k / max(1, n - 1)) if n > 1 else 1.0
        if jump in ("start", "jump-start"):
            k = math.ceil(x * n)
            return min(1.0, k / n)
        if jump == "jump-both":
            return min(1.0, (math.floor(x * n) + 1) / (n + 1))
        return min(1.0, math.floor(x * n) / n)         # end / jump-end
    return f


def timing_function(text):
    """The easing function of a CSS timing function (progress 0..1 -> eased progress; steps and bezier overshoot are kept)."""
    t = (text or "ease").strip().lower()
    if t == "linear":
        return lambda x: x
    if t in _BEZIER:
        return _bezier(*_BEZIER[t])
    if t == "step-start":
        return _steps(1, "start")
    if t == "step-end":
        return _steps(1, "end")
    m = re.fullmatch(r"cubic-bezier\(([^)]*)\)", t)
    if m:
        try:
            a, b, c, d = (float(v) for v in re.split(r"[,\s]+", m.group(1).strip()))
        except ValueError:
            raise AnimError(f"timing function '{text}': cubic-bezier needs four numbers") from None
        if not (0 <= a <= 1 and 0 <= c <= 1):
            raise AnimError(f"timing function '{text}': the x values of cubic-bezier must be between 0 and 1")
        return _bezier(a, b, c, d)
    m = re.fullmatch(r"steps\(\s*(\d+)\s*(?:,\s*([a-z-]+)\s*)?\)", t)
    if m:
        n, jump = int(m.group(1)), m.group(2) or "end"
        if n < 1 or jump not in ("start", "end", "jump-start", "jump-end", "jump-none", "jump-both"):
            raise AnimError(f"timing function '{text}' is not valid")
        return _steps(n, jump)
    raise AnimError(f"timing function '{text}' is not supported")


def progress(a, t):
    """Progress 0..1 along the keyframes of animation `a` at time `t` (direction applied, not eased), or None when it does not apply."""
    at = t - a.delay
    D = a.duration
    if at < 0:
        if a.fill not in ("backwards", "both"):
            return None
        it, p = 0, 0.0
    elif D <= 0:
        if a.fill not in ("forwards", "both") and not (a.iterations > 0 and at == 0):
            return None
        it, p = max(0, math.ceil(a.iterations) - 1) if a.iterations != math.inf else 0, 1.0
    else:
        total = D * a.iterations
        if at >= total:
            if a.fill not in ("forwards", "both"):
                return None
            it = math.ceil(a.iterations) - 1
            frac = a.iterations - math.floor(a.iterations)
            p = 1.0 if frac == 0 else frac
        else:
            x = at / D
            it = math.floor(x)
            p = x - it
    forward = {"normal": True, "reverse": False, "alternate": it % 2 == 0, "alternate-reverse": it % 2 == 1}[a.direction]
    return p if forward else 1.0 - p


# ====================================================================================================
# Values
# ====================================================================================================

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?"


def _fmt(v):
    v = round(v, 9)
    return str(int(v)) if v == int(v) and abs(v) < 1e12 else repr(v)


def _num(text, what):
    try:
        return float(text)
    except ValueError:
        raise AnimError(f"{what}: '{text}' is not a number") from None


def _px(text, what):
    m = re.fullmatch(rf"({_NUM})\s*(px)?", text.strip().lower())
    if not m:
        raise AnimError(f"{what}: '{text}' is not a length in px")
    return float(m.group(1))


def _deg(text, what):
    m = re.fullmatch(rf"({_NUM})\s*(deg|rad|turn|grad)?", text.strip().lower())
    if not m:
        raise AnimError(f"{what}: '{text}' is not an angle")
    x, u = float(m.group(1)), m.group(2) or "deg"
    return x if u == "deg" else math.degrees(x) if u == "rad" else x * 360 if u == "turn" else x * 0.9


def _pair(text, what):
    parts = [p for p in re.split(r"[,\s]+", text.strip()) if p]
    vals = [_num(p, what) for p in parts]
    if len(vals) == 1:
        return vals[0], vals[0]
    if len(vals) == 2:
        return vals[0], vals[1]
    raise AnimError(f"{what}: '{text}' must be one number or two")


def _blur(text):
    t = text.strip().lower()
    if t in ("", "none"):
        return 0.0
    m = re.fullmatch(r"blur\(\s*([^)]*?)\s*\)", t)
    if not m:
        raise AnimError(f"filter: '{text}' is not supported (only blur(<n>px))")
    return _px(m.group(1) or "0", "filter: blur()")


# ---- transform lists ---------------------------------------------------------------------------------

def parse_transform(text):
    """[(name, [numbers])] with translate in px, angles in degrees; translateX/Y, scaleX/Y are folded into translate / scale."""
    t = (text or "").strip()
    if t.lower() in ("", "none"):
        return []
    out, pos = [], 0
    for op in re.finditer(r"\s*([a-zA-Z0-9]+)\s*\(([^)]*)\)\s*", t):
        if op.start() != pos:
            break
        pos = op.end()
        name, args = op.group(1).lower(), [a for a in re.split(r"[,\s]+", op.group(2).strip()) if a]
        try:
            if name == "translate" and 1 <= len(args) <= 2:
                out.append(("translate", [_px(args[0], name), _px(args[1], name) if len(args) > 1 else 0.0]))
            elif name == "translatex" and len(args) == 1:
                out.append(("translate", [_px(args[0], name), 0.0]))
            elif name == "translatey" and len(args) == 1:
                out.append(("translate", [0.0, _px(args[0], name)]))
            elif name == "scale" and 1 <= len(args) <= 2:
                s = _num(args[0], name)
                out.append(("scale", [s, _num(args[1], name) if len(args) > 1 else s]))
            elif name == "scalex" and len(args) == 1:
                out.append(("scale", [_num(args[0], name), 1.0]))
            elif name == "scaley" and len(args) == 1:
                out.append(("scale", [1.0, _num(args[0], name)]))
            elif name in ("rotate", "rotatez") and len(args) == 1:
                out.append(("rotate", [_deg(args[0], name)]))
            elif name in ("skewx", "skewy") and len(args) == 1:
                out.append((name.replace("skewx", "skewX").replace("skewy", "skewY"), [_deg(args[0], name)]))
            elif name == "matrix" and len(args) == 6:
                out.append(("matrix", [_num(a, name) for a in args]))
            else:
                raise AnimError(f"transform: '{op.group(1)}({', '.join(args)})' is not supported")
        except AnimError:
            raise
    if t[pos:].strip():
        raise AnimError(f"transform: cannot read '{t[pos:].strip()}'")
    return out


def _matrix_of(fns):
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def mul(m, n):
        a, b, c, d, e, f = m
        A, B, C, D, E, F = n
        return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)
    for name, v in fns:
        if name == "translate":
            n = (1, 0, 0, 1, v[0], v[1])
        elif name == "scale":
            n = (v[0], 0, 0, v[1], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            n = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
        elif name == "skewX":
            n = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == "skewY":
            n = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            n = tuple(v)
        m = mul(m, n)
    return m


def decompose(m):
    """2D matrix -> (tx, ty, angle degrees, skew, sx, sy)  (CSS Transforms: unmatrix)."""
    a, b, c, d, e, f = m
    sx = math.hypot(a, b)
    if sx == 0:
        return e, f, 0.0, 0.0, 0.0, math.hypot(c, d)
    a, b = a / sx, b / sx
    skew = a * c + b * d
    c, d = c - a * skew, d - b * skew
    sy = math.hypot(c, d)
    if sy == 0:
        return e, f, math.degrees(math.atan2(b, a)), 0.0, sx, 0.0
    c, d, skew = c / sy, d / sy, skew / sy
    if a * d < b * c:
        a, b, skew, sx = -a, -b, -skew, -sx
    return e, f, math.degrees(math.atan2(b, a)), skew, sx, sy


def _recompose(tx, ty, angle, skew, sx, sy):
    r = math.radians(angle)
    ca, sa = math.cos(r), math.sin(r)
    # translate * rotate * (skew along x: [1 0 skew 1]) * scale
    a, b, c, d = ca, sa, -sa, ca
    c, d = a * skew + c, b * skew + d
    return (a * sx, b * sx, c * sy, d * sy, tx, ty)


def _show_transform(fns):
    if not fns:
        return "none"
    parts = []
    for name, v in fns:
        if name == "translate":
            parts.append(f"translate({_fmt(v[0])}px, {_fmt(v[1])}px)")
        elif name == "scale":
            parts.append(f"scale({_fmt(v[0])}, {_fmt(v[1])})")
        elif name in ("rotate", "skewX", "skewY"):
            parts.append(f"{name}({_fmt(v[0])}deg)")
        else:
            parts.append(f"matrix({', '.join(_fmt(x) for x in v)})")
    return " ".join(parts)


_IDENTITY = {"translate": [0.0, 0.0], "scale": [1.0, 1.0], "rotate": [0.0], "skewX": [0.0], "skewY": [0.0], "matrix": [1, 0, 0, 1, 0, 0]}


def _lerp(a, b, r):
    return a + (b - a) * r


def lerp_transform(a, b, r):
    fa, fb = parse_transform(a), parse_transform(b)
    if not fa and fb:
        fa = [(n, list(_IDENTITY[n])) for n, _ in fb]
    if not fb and fa:
        fb = [(n, list(_IDENTITY[n])) for n, _ in fa]
    if [n for n, _ in fa] == [n for n, _ in fb]:
        return _show_transform([(n, [_lerp(x, y, r) for x, y in zip(va, vb)]) for (n, va), (_, vb) in zip(fa, fb)])
    da, db = decompose(_matrix_of(fa)), decompose(_matrix_of(fb))
    ang_a, ang_b = da[2], db[2]
    if abs(ang_b - ang_a) > 180:
        ang_b += 360 if ang_b < ang_a else -360
    parts = [_lerp(x, y, r) for x, y in zip(da, db)]
    parts[2] = _lerp(ang_a, ang_b, r)
    return _show_transform([("matrix", list(_recompose(*parts)))])


# ---- transform-origin -------------------------------------------------------------------------------------

def _origin(text):
    parts = (text or "50% 50%").lower().split()
    if len(parts) == 1:
        parts = parts + ["center"] if parts[0] not in ("top", "bottom") else ["center"] + parts
    if len(parts) != 2:
        raise AnimError(f"transform-origin: cannot read '{text}'")
    if parts[0] in ("top", "bottom") or parts[1] in ("left", "right"):
        parts = parts[::-1]
    out = []
    for v, lo, hi in ((parts[0], "left", "right"), (parts[1], "top", "bottom")):
        if v in ("center", lo, hi):
            out.append((50.0 if v == "center" else 0.0 if v == lo else 100.0, "%"))
        else:
            m = re.fullmatch(rf"({_NUM})(%|px)?", v)
            if not m:
                raise AnimError(f"transform-origin: cannot read '{v}'")
            out.append((float(m.group(1)), m.group(2) or "px"))
    return out


def lerp_origin(a, b, r):
    (ax, au), (ay, ayu) = _origin(a)
    (bx, bu), (by, byu) = _origin(b)
    if au != bu or ayu != byu:
        raise AnimError(f"transform-origin: cannot animate between '{a}' and '{b}' (use the same unit, % or px)")
    return f"{_fmt(_lerp(ax, bx, r))}{au} {_fmt(_lerp(ay, by, r))}{ayu}"


# ====================================================================================================
# interpolate / animate
# ====================================================================================================

def interpolate(kind, a, b, r):
    """The value between CSS texts `a` and `b` at ratio `r` (may be outside 0..1 for an overshooting easing)."""
    if kind == "length":
        return f"{_fmt(_lerp(_px(a, 'length'), _px(b, 'length'), r))}px"
    if kind == "number":
        return _fmt(_lerp(_num(a, "number"), _num(b, "number"), r))
    if kind == "angle":
        return f"{_fmt(_lerp(_deg(a, 'angle'), _deg(b, 'angle'), r))}deg"
    if kind == "pair":
        (x0, y0), (x1, y1) = _pair(a, "pair"), _pair(b, "pair")
        return f"{_fmt(_lerp(x0, x1, r))} {_fmt(_lerp(y0, y1, r))}"
    if kind == "filter":
        return f"blur({_fmt(_lerp(_blur(a), _blur(b), r))}px)"
    if kind == "transform":
        return lerp_transform(a, b, r)
    if kind == "origin":
        return lerp_origin(a, b, r)
    raise AnimError(f"cannot animate a '{kind}'")


def animate(style, anims, keyframes, t, kinds, default_timing=None):
    """{property: value} of the properties animated at time `t`.

    `style`: the values of the element without animation (the missing ends of a keyframe come from here), `anims`: [Anim],
    `keyframes`: {name: Keyframes}, `kinds`: {property: kind} the animatable properties (and how they interpolate)."""
    out = {}
    for a in anims:
        kf = keyframes.get(a.name)
        if kf is None:
            raise AnimError(f"animation: no @keyframes named '{a.name}' (have: {', '.join(sorted(keyframes)) or 'none'})")
        p = progress(a, t)
        if p is None:
            continue
        props = []
        for _, d, _ in kf.stops:
            props += [k for k in d if k not in props]
        for prop in props:
            if prop not in kinds:
                raise AnimError(f"@keyframes {a.name}: '{prop}' cannot be animated here (use {', '.join(sorted(kinds))})")
            stops = [(off, d[prop], tm) for off, d, tm in kf.stops if prop in d]
            under = out.get(prop, style.get(prop))
            if under is None:
                raise AnimError(f"@keyframes {a.name}: '{prop}' has no starting value (put it in the style or in a `from` keyframe)")
            if stops[0][0] > 0:
                stops.insert(0, (0.0, under, None))
            if stops[-1][0] < 1:
                stops.append((1.0, under, None))
            k = max(i for i, s in enumerate(stops[:-1]) if stops[i][0] <= p) if p < 1 else len(stops) - 2
            (o0, v0, tm0), (o1, v1, _) = stops[k], stops[k + 1]
            local = 1.0 if o1 == o0 else (p - o0) / (o1 - o0)
            out[prop] = interpolate(kinds[prop], v0, v1, timing_function(tm0 or a.timing)(local))
    return out
