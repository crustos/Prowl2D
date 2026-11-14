"""levelang source  ->  plain Python source.

This is a deliberately small, line-oriented rewriter (no full grammar). It never changes
the number of lines, so Python tracebacks point at the right line of your .lvl file.

What it rewrites
----------------
1. Emoji in code            ``🧱*W``                 ->  ``tile_BRICK*W``
2. Art functions            ``def reef(a, b):`` + rows of emoji
                            ->  ``def reef(a, b, x=0, y=0): return __art__(x, y, [...])``
3. Tile definitions         ``def 🟦 -> fill.blue, solid:`` + optional ASCII pattern / SVG body
                            ->  ``tile_LARGE_BLUE_SQUARE = __tile__(...)``

Everything else is passed through (with emoji mangled outside strings and comments).

Art coordinates
---------------
Art is WYSIWYG in a monospace editor: an emoji is 2 cells wide, any other character 1 cell,
and one tile is 2 cells wide (1 cell in pure-ASCII art). So two spaces == one empty tile,
and ``a(`` is exactly one tile, which is why the examples line up. Column 0 is the column
of the ``def`` keyword.
"""
from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass, field

from .emoji import SymbolTable, char_width, cluster_width, scan_cluster


class LevelangSyntaxError(SyntaxError):
    pass


@dataclass
class Translation:
    python: str
    symbols: dict  # mangled name -> emoji glyph
    tiles: set = field(default_factory=set)  # every name that denotes a tile
    filename: str = "<levelang>"


# ----------------------------------------------------------------------------- code mangling


def split_comment(line: str) -> tuple[str, str]:
    """Split ``code  # comment`` while respecting simple string literals."""
    quote = None
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == "#":
            return line[:i], line[i:]
        i += 1
    return line, ""


class CodeMangler:
    """Replaces emoji clusters with identifiers, skipping strings and comments.
    Stateful so triple-quoted strings can span lines."""

    def __init__(self, symbols: SymbolTable) -> None:
        self.symbols = symbols
        self.triple: str | None = None

    @property
    def in_string(self) -> bool:
        return self.triple is not None

    def line(self, s: str) -> str:
        out: list[str] = []
        i, n = 0, len(s)
        while i < n:
            if self.triple:
                end = s.find(self.triple, i)
                if end < 0:
                    out.append(s[i:])
                    break
                out.append(s[i : end + 3])
                i = end + 3
                self.triple = None
                continue
            c = s[i]
            if c == "#":
                out.append(s[i:])
                break
            if c in "'\"":
                if s[i : i + 3] in ('"""', "'''"):
                    self.triple = s[i : i + 3]
                    out.append(self.triple)
                    i += 3
                    continue
                j = i + 1
                while j < n and s[j] != c:
                    j += 2 if s[j] == "\\" else 1
                out.append(s[i : j + 1])
                i = j + 1
                continue
            e = scan_cluster(s, i)
            if e > i:
                if out and (out[-1][-1:].isalnum() or out[-1][-1:] == "_"):
                    out.append(" ")
                out.append(self.symbols.name_for(s[i:e]))
                nxt = s[e : e + 1]
                if nxt and (nxt.isalnum() or nxt == "_" or scan_cluster(s, e) > e):
                    out.append(" ")
                i = e
                continue
            out.append(c)
            i += 1
        return "".join(out)


# ----------------------------------------------------------------------------- art rows


@dataclass
class _Tok:
    kind: str  # 'tile' | 'anchor' | 'char'
    cell: int
    text: str
    width: int = 1  # cells
    name: str = ""  # anchor name


_CALL_RE = re.compile(r"[A-Za-z_]\w*\(")


def _scan_art_row(row: str) -> list[_Tok]:
    toks: list[_Tok] = []
    stack: list[tuple[str, int]] = []
    cell = i = 0
    n = len(row)
    while i < n:
        ch = row[i]
        e = scan_cluster(row, i)
        if e > i:
            cl = row[i:e]
            w = cluster_width(cl)
            toks.append(_Tok("tile", cell, cl, w))
            cell += w
            i = e
            continue
        if ch == " ":
            cell += 1
            i += 1
            continue
        m = _CALL_RE.match(row, i)
        if m and (i == 0 or not (row[i - 1].isalnum() or row[i - 1] == "_")):
            stack.append((m.group(0)[:-1], cell))
            cell += len(m.group(0))
            i = m.end()
            continue
        if ch == ")" and stack:
            name, start = stack.pop()
            cell += 1
            i += 1
            toks.append(_Tok("anchor", start, "", cell - start, name))
            continue
        toks.append(_Tok("char", cell, ch, max(char_width(ch), 1)))
        cell += max(char_width(ch), 1)
        i += 1
    if stack:
        raise LevelangSyntaxError(f"unclosed section anchor '{stack[-1][0]}(' in art row: {row.strip()!r}")
    toks.sort(key=lambda t: t.cell)
    return toks


def _compile_art(rows: list[str], symbols: SymbolTable, tiles: set) -> list[str]:
    scanned = [_scan_art_row(r) for r in rows]
    wide = any(t.kind == "tile" and t.width == 2 for toks in scanned for t in toks)
    step = 2 if wide else 1  # cells per tile
    out = []
    for toks in scanned:
        ents = []
        for t in toks:
            col = t.cell // step
            if t.kind == "tile":
                name = symbols.name_for(t.text)
                tiles.add(name)
                ents.append(f"({col}, {name})")
            elif t.kind == "anchor":
                w = max(1, -(-t.width // step))
                ents.append(f"({col}, __anchor__({t.name}, {w}))")
            else:
                ents.append(f"({col}, {t.text!r})")
        out.append("[" + ", ".join(ents) + "],")
    return out


# ----------------------------------------------------------------------------- translator

# def 🟦 -> fill.blue, stroke.white:
_ARROW_RE = re.compile(r"^(?P<indent>[ \t]*)def[ \t]+(?P<name>[^\s()]+?)[ \t]*->[ \t]*(?P<attrs>.*?)[ \t]*:[ \t]*$")
# def reef(a, b):
_DEF_RE = re.compile(r"^(?P<indent>[ \t]*)def[ \t]+(?P<name>[^\s(]+)[ \t]*\((?P<params>.*)\)[ \t]*:[ \t]*$")
_SVG_FLAG_RE = re.compile(r"(?<![\w.])svg(?![\w(])")


def _indent_width(line: str) -> int:
    return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())


class _Translator:
    def __init__(self, source: str, filename: str) -> None:
        self.filename = filename
        # editors and chat apps love to sneak in non-breaking / exotic spaces; they are just spaces
        source = re.sub(r"[\u00a0\u2000-\u200a\u202f\u205f]", " ", source)
        self.lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.symbols = SymbolTable()
        self.tiles: set[str] = set()
        self.mg = CodeMangler(self.symbols)
        self.out: list[str] = []

    # -- helpers
    def _err(self, msg: str, lineno: int) -> LevelangSyntaxError:
        e = LevelangSyntaxError(msg)
        e.filename, e.lineno, e.text = self.filename, lineno + 1, self.lines[lineno]
        return e

    def _mangle_name(self, name: str) -> tuple[str, str]:
        """-> (python identifier, glyph or '')"""
        e = scan_cluster(name, 0)
        if e > 0:
            if e != len(name):
                raise LevelangSyntaxError(f"tile names must be one emoji or a plain identifier: {name!r}")
            return self.symbols.name_for(name), name
        return name, ""

    def _parses_as_suite(self, cand: list[str]) -> bool:
        mg = CodeMangler(SymbolTable())
        src = "def _f():\n" + "\n".join(mg.line(l) for l in cand) + "\n"
        try:
            ast.parse(src)
            return True
        except SyntaxError:
            return False

    def _find_art(self, i: int, hindent: int):
        """Decide whether the def at line i has an art body. -> (start, end, rows) or None."""
        lines, n = self.lines, len(self.lines)
        cand, j = [], i + 1
        while j < n:
            l = lines[j]
            if l.strip() and _indent_width(l) <= hindent:
                break
            cand.append(l)
            j += 1
        if any(l.strip() for l in cand) and self._parses_as_suite(cand):
            return None  # an ordinary Python function body
        k = i + 1
        while k < n and not lines[k].strip():
            k += 1
        start = k
        while k < n and lines[k].strip():
            k += 1
        if start == k:
            return None
        rows = []
        for r in lines[start:k]:
            r = r.expandtabs(4)
            rows.append(r[hindent:] if not r[:hindent].strip() else r)
        return start, k, rows

    @staticmethod
    def _add_cursor_params(params: str, lineno: int) -> str:
        params = params.strip().rstrip(",").strip()
        if "**" in params:
            raise LevelangSyntaxError(f"line {lineno + 1}: art functions can't take **kwargs")
        names = set()
        for p in params.split(","):
            p = p.strip().lstrip("*")
            if p:
                names.add(re.split(r"[=:\s]", p, maxsplit=1)[0])
        extra = [f"{n}=0" for n in ("x", "y") if n not in names]
        if not extra:
            return params
        # with *args present the new params simply become keyword-only, which is fine
        return (params + ", " if params else "") + ", ".join(extra)

    # -- the two special def forms
    def _arrow_def(self, i: int, m: re.Match, comment: str) -> int:
        lines, n = self.lines, len(self.lines)
        indent = m["indent"]
        pyname, glyph = self._mangle_name(m["name"])
        self.tiles.add(pyname)
        attrs_src = m["attrs"]
        attrs_py = CodeMangler(self.symbols).line(attrs_src)
        no_strings = re.sub(r"\"[^\"]*\"|'[^']*'", '""', split_comment(attrs_src)[0])  # svg("svg/x.svg") is a call, not the bare flag
        is_svg = bool(_SVG_FLAG_RE.search(no_strings))
        head = f"{indent}{pyname} = __tile__({pyname!r}, {glyph!r}, [{attrs_py}]"
        j = i + 1
        if is_svg and j < n and lines[j].lstrip().startswith("<"):
            body = []
            while j < n:
                body.append(lines[j])
                j += 1
                if "</svg>" in body[-1]:
                    break
            else:
                raise self._err("SVG body is missing its closing </svg>", i)
            last = body[-1]
            body[-1] = last[: last.index("</svg>") + 6] + '""")'
            self.out.append(head + ', svg=r"""')
            self.out.extend(body)
            return j
        # ASCII pattern body: the lines up to the next blank line
        k = j
        while k < n and lines[k].strip():
            k += 1
        pat = lines[j:k]
        if not pat:
            self.out.append(head + ")" + (("  " + comment) if comment else ""))
            return j
        dedented = textwrap.dedent("\n".join(pat).expandtabs(4)).split("\n")
        self.out.append(head + ", pattern=(" + (("  " + comment) if comment else ""))
        for idx, row in enumerate(dedented):
            self.out.append(f"{indent}    {row.rstrip()!r}," + ("))" if idx == len(dedented) - 1 else ""))
        return k

    def _art_def(self, i: int, m: re.Match, comment: str, art) -> int:
        start, end, rows = art
        indent = m["indent"]
        name = CodeMangler(self.symbols).line(m["name"])
        params = self._add_cursor_params(CodeMangler(self.symbols).line(m["params"]), i)
        self.out.append(f"{indent}def {name}({params}): return __art__(x, y, [" + (("  " + comment) if comment else ""))
        self.out.extend([""] * (start - i - 1))
        compiled = _compile_art(rows, self.symbols, self.tiles)
        compiled[-1] += "])"
        self.out.extend(compiled)
        return end

    # -- main loop
    def run(self) -> Translation:
        lines, n = self.lines, len(self.lines)
        i = 0
        while i < n:
            raw = lines[i]
            if self.mg.in_string:
                self.out.append(self.mg.line(raw))
                i += 1
                continue
            code, comment = split_comment(raw)
            m = _ARROW_RE.match(code)
            if m:
                i = self._arrow_def(i, m, comment)
                continue
            m = _DEF_RE.match(code)
            if m:
                art = self._find_art(i, _indent_width(raw))
                if art is not None:
                    i = self._art_def(i, m, comment, art)
                    continue
            self.out.append(self.mg.line(raw))
            i += 1
        self.tiles |= set(self.symbols.glyphs)
        return Translation("\n".join(self.out), dict(self.symbols.glyphs), self.tiles, self.filename)


def translate(source: str, filename: str = "<levelang>") -> Translation:
    """Rewrite levelang source as Python source (same number of lines)."""
    return _Translator(source, filename).run()
