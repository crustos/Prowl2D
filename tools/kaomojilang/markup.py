"""A minimal HTML + CSS subset for placing, rotating, scaling and flipping symbols.

A def whose body has HTML lines is a *template*: `{expr}` is a Python expression (the def's parameters and its own
assignments are in scope; `{{` and `}}` are literal braces), and the HTML is laid out into stamped symbols.

    def foo(x, y):
        <div style="position:absolute; left:{x+10}px; top:{y+50}px; font-size:100px; transform:scaleX(-1) rotate(20deg)">𝀌</div>

Supported
---------
* Elements: any tag is a box (`div`, `span`, ...). Text inside is a run of symbols laid out left to right (each one is drawn by
  `artlib/`, a `def <symbol>` or the standard parameters, like a symbol in a grid). Spaces are skipped. Elements nest: a child
  is placed relative to its parent and follows its transform.
* Attribute `layer="name"` (inherited by children) puts the element in a layer of the drawing (`layers={'name': {...}}` per call).
* `style="..."` properties: `position` (left/top apply to every position value, so write `absolute`), `left`, `top`, `width`,
  `height`, `font-size`, `opacity`, `transform`, `transform-origin`, `display:none`, `visibility:hidden`.
  Anything else is an error, so a typo does not go unnoticed.
* `transform`: `translate(x[, y])`, `translateX`, `translateY`, `scale(sx[, sy])`, `scaleX`, `scaleY`, `rotate(a)`,
  `skewX`, `skewY`, `matrix(a, b, c, d, e, f)`, in that order of application as in CSS (the last is applied first to the
  element). Angles: deg, rad, turn, grad. `transform-origin`: `50% 50%` (default), keywords, or px.
* Units: 1px = 0.1 grid column, so the drawing is the size of the CSS at the default 10 pixels per column. A symbol's
  longer side is the `font-size` (16px by default), a symbol with its own `data-size` keeps its proportion to the others.
"""

import ast
import math
import re
from html.parser import HTMLParser

from . import anim, artlib
from .stage1 import mangle_symbols

PX = 0.1                    # grid columns per CSS pixel
DEFAULT_FONT = 16.0
IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


class HtmlError(Exception):
    pass


# ====================================================================================================
# Affine matrices (a, b, c, d, e, f): x' = a x + c y + e, y' = b x + d y + f
# ====================================================================================================

def mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def move(x, y):
    return (1.0, 0.0, 0.0, 1.0, x, y)


def apply(m, x, y):
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


# ====================================================================================================
# {expr} substitution
# ====================================================================================================

_NODES = (ast.Expression, ast.Call, ast.keyword, ast.Name, ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.ListComp,
          ast.comprehension, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp, ast.Subscript, ast.Slice, ast.Starred,
          ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context, ast.GeneratorExp)


def _check(tree, text):
    for node in ast.walk(tree):
        if not isinstance(node, _NODES):
            raise HtmlError(f"{{{text}}}: {type(node).__name__} is not allowed in a template expression")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise HtmlError(f"{{{text}}}: name '{node.id}' is reserved")
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise HtmlError(f"{{{text}}}: only plain functions can be called")


def _show(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return str(int(v)) if v == int(v) and abs(v) < 1e15 else f"{v:.6g}"
    return str(v)


def _evaluate(text, g):
    code, _ = mangle_symbols(text)
    try:
        tree = ast.parse(code, mode="eval")
        _check(tree, text)
        return _show(eval(compile(tree, "<template>", "eval"), g))
    except HtmlError:
        raise
    except Exception as e:
        raise HtmlError(f"{{{text}}}: {type(e).__name__}: {e}") from None


def _closing(text, i, line):
    """Index after the `}` matching the `{` at text[i]."""
    depth, j = 1, i + 1
    while j < len(text) and depth:
        depth += (text[j] == "{") - (text[j] == "}")
        j += 1
    if depth:
        raise HtmlError(f"line {line} of the template: '{{' without '}}'")
    return j


def _plain(text, g, line0):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        line = line0 + text.count("\n", 0, i)
        if c == "{" and text[i + 1:i + 2] == "{":
            out.append("{")
            i += 2
        elif c == "}" and text[i + 1:i + 2] == "}":
            out.append("}")
            i += 2
        elif c == "{":
            j = _closing(text, i, line)
            out.append(_evaluate(text[i + 1:j - 1].strip(), g))
            i = j
        elif c == "}":
            raise HtmlError(f"line {line} of the template: single '}}' (write '}}}}' for a brace)")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _css(text, g, line0):
    """Inside <style>, braces are CSS blocks; a `{` opens an expression only after a `:` in a value (`left: {x}px`)."""
    out, i, n, colon = [], 0, len(text), False
    while i < n:
        c = text[i]
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(text[i:j])
            i = j
            continue
        if c == "{" and colon:
            j = _closing(text, i, line0 + text.count("\n", 0, i))
            out.append(_evaluate(text[i + 1:j - 1].strip(), g))
            i = j
            continue
        if c == ":":
            colon = True
        elif c in "{};":
            colon = False
        out.append(c)
        i += 1
    return "".join(out)


_STYLE_BLOCK = re.compile(r"(<style\b[^>]*>)(.*?)(</style\s*>)", re.S | re.I)


def substitute(template, scope, ns):
    """Replace every `{expr}` by its value; `{{` and `}}` are braces. Inside <style> a `{` is a CSS block (see `_css`)."""
    g = dict(ns)
    g.update(scope)
    out, pos = [], 0
    for m in _STYLE_BLOCK.finditer(template):
        out.append(_plain(template[pos:m.start()], g, 1 + template.count("\n", 0, pos)))
        out.append(m.group(1))
        out.append(_css(m.group(2), g, 1 + template.count("\n", 0, m.start(2))))
        out.append(m.group(3))
        pos = m.end()
    out.append(_plain(template[pos:], g, 1 + template.count("\n", 0, pos)))
    return "".join(out)


# ====================================================================================================
# Parsing
# ====================================================================================================

class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.children = []                         # Node | str


VOID = {"br", "hr", "img", "meta", "input", "link"}


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is self.root:
            raise HtmlError(f"</{tag}> closes nothing")
        self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(text):
    p = _Parser()
    p.feed(text)
    p.close()
    if p.cur is not p.root:
        raise HtmlError(f"<{p.cur.tag}> is never closed")
    return p.root


# ====================================================================================================
# CSS
# ====================================================================================================

STYLE_KEYS = ("position", "left", "top", "width", "height", "font-size", "opacity", "transform", "transform-origin", "display", "visibility", "filter",
              "animation", "animation-name", "animation-duration", "animation-delay", "animation-iteration-count", "animation-direction",
              "animation-fill-mode", "animation-timing-function")


ANIMATABLE = {"left": "length", "top": "length", "width": "length", "height": "length", "font-size": "length", "opacity": "number",
              "transform": "transform", "transform-origin": "origin", "filter": "filter"}


def parse_style(text, tag):
    style = {}
    for decl in re.split(r";", text or ""):
        if not decl.strip():
            continue
        if ":" not in decl:
            raise HtmlError(f"<{tag}>: bad style declaration '{decl.strip()}'")
        k, v = decl.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k not in STYLE_KEYS:
            raise HtmlError(f"<{tag}>: the style property '{k}' is not supported (use {', '.join(STYLE_KEYS)})")
        style[k] = v
    return style


def length(v, what, allow_percent=False):
    """CSS length in px (or a number) -> grid columns. `50%` -> ('%', 0.5) when allowed."""
    v = v.strip().lower()
    m = re.fullmatch(r"([-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)\s*(px)?", v)
    if m:
        return float(m.group(1)) * PX
    m = re.fullmatch(r"([-+]?(?:\d+\.?\d*|\.\d+))\s*%", v)
    if m and allow_percent:
        return ("%", float(m.group(1)) / 100)
    raise HtmlError(f"{what}: '{v}' is not a length in px")


def angle(v):
    m = re.fullmatch(r"([-+]?(?:\d+\.?\d*|\.\d+))\s*(deg|rad|turn|grad)?", v.strip().lower())
    if not m:
        raise HtmlError(f"transform: '{v}' is not an angle (deg, rad, turn, grad)")
    x, unit = float(m.group(1)), m.group(2) or "deg"
    return x if unit == "deg" else math.degrees(x) if unit == "rad" else x * 360 if unit == "turn" else x * 0.9


def transform_matrix(text):
    """The matrix of a `transform` value (in grid columns), operations applied as CSS does: left to right multiplication."""
    m = IDENT
    pos = 0
    text = (text or "").strip()
    if text.lower() == "none":
        return m
    for op in re.finditer(r"\s*([a-zA-Z0-9]+)\s*\(([^)]*)\)\s*", text):
        if op.start() != pos:
            break
        pos = op.end()
        name, args = op.group(1), [a for a in re.split(r"[,\s]+", op.group(2).strip()) if a]

        def num(a):
            try:
                return float(a)
            except ValueError:
                raise HtmlError(f"transform: {name}() takes numbers, got '{a}'") from None
        lname = name.lower()
        if lname == "translate" and 1 <= len(args) <= 2:
            t = move(length(args[0], "translate"), length(args[1], "translate") if len(args) > 1 else 0.0)
        elif lname == "translatex" and len(args) == 1:
            t = move(length(args[0], "translateX"), 0.0)
        elif lname == "translatey" and len(args) == 1:
            t = move(0.0, length(args[0], "translateY"))
        elif lname == "scale" and 1 <= len(args) <= 2:
            sx = num(args[0])
            t = (sx, 0.0, 0.0, num(args[1]) if len(args) > 1 else sx, 0.0, 0.0)
        elif lname == "scalex" and len(args) == 1:
            t = (num(args[0]), 0.0, 0.0, 1.0, 0.0, 0.0)
        elif lname == "scaley" and len(args) == 1:
            t = (1.0, 0.0, 0.0, num(args[0]), 0.0, 0.0)
        elif lname in ("rotate", "rotatez") and len(args) == 1:
            r = math.radians(angle(args[0]))
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0.0, 0.0)
        elif lname == "skewx" and len(args) == 1:
            t = (1.0, 0.0, math.tan(math.radians(angle(args[0]))), 1.0, 0.0, 0.0)
        elif lname == "skewy" and len(args) == 1:
            t = (1.0, math.tan(math.radians(angle(args[0]))), 0.0, 1.0, 0.0, 0.0)
        elif lname == "matrix" and len(args) == 6:
            a, b, c, d, e, f = (num(a) for a in args)
            t = (a, b, c, d, e * PX, f * PX)
        else:
            raise HtmlError(f"transform: '{name}({', '.join(args)})' is not supported "
                            "(translate, translateX/Y, scale, scaleX/Y, rotate, skewX/Y, matrix)")
        m = mul(m, t)
    if text[pos:].strip():
        raise HtmlError(f"transform: cannot read '{text[pos:].strip()}'")
    return m


def blur_of(text):
    """`filter: blur(40px)` -> sigma in grid columns (0 for none). Only blur() is supported."""
    t = (text or "").strip()
    if not t or t.lower() == "none":
        return 0.0
    m = re.fullmatch(r"blur\(\s*([^)]*?)\s*\)", t, re.I)
    if not m:
        raise HtmlError(f"filter: '{t}' is not supported (only blur(<n>px))")
    v = length(m.group(1) or "0", "filter: blur()")
    if v < 0:
        raise HtmlError("filter: blur() cannot be negative")
    return v


def origin_of(text, w, h):
    """transform-origin -> (x, y) in the frame of the box."""
    parts = (text or "50% 50%").split()
    if len(parts) == 1:
        parts = parts + ["center"] if parts[0] not in ("top", "bottom") else ["center"] + parts
    if len(parts) != 2:
        raise HtmlError(f"transform-origin: cannot read '{text}'")
    if parts[0] in ("top", "bottom") or parts[1] in ("left", "right"):
        parts = parts[::-1]

    def one(v, size, lo, hi):
        if v == "center":
            return size / 2
        if v == lo:
            return 0.0
        if v == hi:
            return size
        q = length(v, "transform-origin", allow_percent=True)
        return q[1] * size if isinstance(q, tuple) else q
    return one(parts[0], w, "left", "right"), one(parts[1], h, "top", "bottom")


# ====================================================================================================
# Layout: the tree -> symbol cells
# ====================================================================================================

ANIM_DEFAULTS = {"left": "0px", "top": "0px", "width": "0px", "height": "0px", "opacity": "1", "transform": "none",
                "transform-origin": "50% 50%", "filter": "none"}


def layout(root, name, natural, t=None, keyframes=None):
    """Cells [("sym", char, x, row, layer, extra)] in document order. `natural(char)` is the natural size of a symbol."""
    cells, layers, groups = [], [], []

    def walk(node, world, font, layer, op, blur):
        for child in node.children:
            if isinstance(child, str):
                continue
            if child.tag == "style":
                continue
            style = parse_style(child.attrs.get("style"), child.tag)
            if t is not None and any(k.startswith("animation") for k in style):
                style = dict(style)
                style.setdefault("font-size", f"{font / PX:g}px")
                style.update(anim.animate({**{k: ANIM_DEFAULTS.get(k) for k in ANIMATABLE if ANIM_DEFAULTS.get(k)}, **style},
                                          anim.animation_from_style(style), keyframes or {}, t, ANIMATABLE))
            if style.get("display") == "none" or style.get("visibility") == "hidden":
                continue
            lay = child.attrs.get("layer") or child.attrs.get("data-layer") or layer
            if lay and lay not in layers:
                layers.append(lay)
            fs = length(style["font-size"], f"<{child.tag}> font-size") if "font-size" in style else font
            if "font-size" in style and fs <= 0:
                raise HtmlError(f"<{child.tag}>: font-size must be positive")
            try:
                own = float(style.get("opacity", 1))
            except ValueError:
                raise HtmlError(f"<{child.tag}>: opacity '{style['opacity']}' is not a number") from None
            opacity = op * min(1.0, max(0.0, own))
            sigma = blur_of(style.get("filter"))
            group = blur                                           # (id, sigma) of the outermost filter around this element
            if sigma > 0:
                if blur is None:
                    groups.append(1)
                    group = (len(groups), sigma)
                else:
                    group = (blur[0], math.hypot(blur[1], sigma))
            left = length(style["left"], f"<{child.tag}> left") if "left" in style else 0.0
            top = length(style["top"], f"<{child.tag}> top") if "top" in style else 0.0
            # the text of this element: a run of symbols
            glyphs, x = [], 0.0
            for piece in child.children:
                if isinstance(piece, str):
                    for ch in piece:
                        if ch.isspace():
                            continue
                        nat = natural(ch)
                        k = fs / artlib.DEFAULT_SIZE
                        w, h = nat[0] * k, nat[1] * k
                        glyphs.append((ch, x, w, h))
                        x += w
            bw = x if glyphs else (length(style["width"], f"<{child.tag}> width") if "width" in style else 0.0)
            bh = max((g[3] for g in glyphs), default=(length(style["height"], f"<{child.tag}> height") if "height" in style else 0.0))
            if glyphs and "width" in style:
                bw = length(style["width"], f"<{child.tag}> width")
            if glyphs and "height" in style:
                bh = length(style["height"], f"<{child.tag}> height")
            ox, oy = origin_of(style.get("transform-origin"), bw, bh)
            local = mul(mul(move(left + ox, top + oy), transform_matrix(style.get("transform"))), move(-ox, -oy))
            m = mul(world, local)
            for ch, gx, gw, gh in glyphs:
                cx, cy = apply(m, gx + gw / 2, gh / 2)
                cells.append(("sym", ch, cx, cy / 2.0, lay or "", {"box": (gw, gh), "linear": m[:4], "opacity": opacity, "at": (cx, cy), "blur": group}))
            walk(child, m, fs, lay, opacity, group)
    walk(root, IDENT, DEFAULT_FONT * PX, "", 1.0, None)
    return cells, layers


def _styles(node):
    """The text of every <style> element of the tree."""
    for c in node.children:
        if isinstance(c, Node):
            if c.tag == "style":
                yield "".join(x for x in c.children if isinstance(x, str))
            else:
                yield from _styles(c)


def build_html(template, name, scope, params, defaults, env):
    """`__html__`: called by the code generated for a def whose body is HTML. Returns a Shape."""
    from . import runtime
    try:
        text = substitute(template, scope, env.ns)
        root = parse(text)
        keyframes = dict(getattr(env, "keyframes", {}) or {})
        for style in _styles(root):
            keyframes.update(anim.parse_keyframes(style))
    except (HtmlError, anim.AnimError) as e:
        raise runtime.ShapeError(f"{name}: {e}") from None
    p = runtime.merged_params(params, defaults)
    t = runtime.time_of(name, p.get("t"))

    def natural(ch):
        dirs = env.dirs()
        try:
            return runtime.symbol_source(name, ch, runtime.pick(p.get("fill"), ch, None), env, dirs)[2]
        except artlib.ArtError as e:
            raise runtime.ShapeError(f"{name}: symbol {ch!r}: {e}") from None
    try:
        cells, layers = layout(root, name, natural, t, keyframes)
    except (HtmlError, anim.AnimError) as e:
        raise runtime.ShapeError(f"{name}: {e}") from None
    if layers:
        cells = [(c[0], c[1], c[2], c[3], c[4] or "base", c[5]) for c in cells]
        if any(c[4] == "base" for c in cells):
            layers = ["base"] + [n for n in layers if n != "base"]
    shape = runtime.Shape(name, [])
    shape.layers = runtime._layer_options(name, [(n, {}) for n in layers], p.get("layers"), t, keyframes)
    runtime._add_cells(shape, cells, p, name, env, runtime.ASPECT)
    return shape
