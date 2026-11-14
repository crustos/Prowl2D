"""Level IR  <->  the ``Level.cs`` data file the Samples/SlimeJump* games compile in.

The C# side is a fixed schema (see Samples/SlimeJump/Game.cs): world units with **y up**, one cell = one unit.

    Walls     rects  x y w h      solid ground (a tile with `solid`, unless it is `crumbly`)
    Climbs    rects  x y w h      vines (`climb`)
    Spikes    rects  x y w h      (`hazard`)
    Saves     points x y          (`save`)
    Gems      points x y          (`item`)
    Anchors   points x y          lasso anchors (`anchor`)
    Crumbles  cells  x y w h      crumbling tiles, one per cell (`crumbly`; NOT part of Walls)
    Shooters  x y dx dy           traps; their tile is part of the walls (`solid, shooter(dx, dy)`)
    Enemies   kind x y            (`enemy(kind)`)
    spawn / goal                  (`spawn`, `goal`)

Where an entity stands inside its cell is `at(ax, ay)` (fractions of the cell, y up; default the centre,
`at(0.5, 0)` the bottom middle). Solid, climb and hazard cells are merged into as few rectangles as it takes.

Everything in the file that is not data (accessors, helpers) is copied verbatim from Samples/SlimeJump/Level.cs,
and `LayerRows()` comes from the game you export for (``layers_from=``), since each game has its own layer rules.
"""
from __future__ import annotations

import re
from pathlib import Path

_HERE = Path(__file__).parent
DEFAULT_AT = (0.5, 0.5)
_ARROWS = {(1, 0): "➡️", (-1, 0): "⬅️", (0, 1): "⬆️", (0, -1): "⬇️"}


class ExportError(ValueError):
    pass


# ----------------------------------------------------------------------------- helpers


def fmt(v: float) -> str:
    v = round(float(v), 4)
    return f"{int(v)}f" if v == int(v) else f"{v:.4f}".rstrip("0") + "f"


def merge_rects(cells) -> list[tuple[int, int, int, int]]:
    """Set of (x, y) cells -> rectangles (x, y, w, h), sorted by (y, x). Rows of runs, merged upwards."""
    rows: dict[int, list[int]] = {}
    for x, y in cells:
        rows.setdefault(y, []).append(x)
    runs: dict[int, list[tuple[int, int]]] = {}
    for y, xs in rows.items():
        xs.sort()
        out, start, prev = [], xs[0], xs[0]
        for x in xs[1:]:
            if x != prev + 1:
                out.append((start, prev))
                start = x
            prev = x
        out.append((start, prev))
        runs[y] = out
    rects, open_ = [], {}
    for y in sorted(runs):
        cur = set(runs[y])
        for span, (ys, ye) in list(open_.items()):
            if span not in cur or ye != y - 1:
                rects.append((span[0], ys, span[1] - span[0] + 1, ye - ys + 1))
                del open_[span]
        for span in cur:
            if span in open_:
                open_[span][1] = y
            else:
                open_[span] = [y, y]
    for span, (ys, ye) in open_.items():
        rects.append((span[0], ys, span[1] - span[0] + 1, ye - ys + 1))
    return sorted(rects, key=lambda r: (r[1], r[0]))


def _layer_tail(layers_from: str | None) -> str:
    """The text from the blank line before `// Layer collision matrix` to the end of the class."""
    if layers_from is None:
        return (_HERE / "slimejump_tail.cs").read_text(encoding="utf-8")
    text = Path(layers_from).read_text(encoding="utf-8").replace("\r\n", "\n")
    i = text.find("    // Layer collision matrix")
    if i < 0:
        raise ExportError(f"{layers_from}: no '// Layer collision matrix' block to copy LayerRows from")
    return "\n" + text[i:]


# ----------------------------------------------------------------------------- Level -> Level.cs


def to_level_cs(level, source_name: str = "level.lvl", layers_from: str | None = None) -> tuple[str, list[str]]:
    """-> (Level.cs text, warnings)."""
    warnings: list[str] = []
    meta = level.meta
    if "width" in meta and "height" in meta:
        x0, y0, cols, rows = 0, 0, int(meta["width"]), int(meta["height"])
    else:
        bx0, by0, bx1, by1 = level.bounds()
        x0, y0, cols, rows = bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1
    top = y0 + rows - 1

    def world(p):
        return p.x - x0, top - p.y  # (x, bottom y of the cell), y up

    def at(tile):
        a = tile.params.get("at", DEFAULT_AT)
        if not (isinstance(a, tuple) and len(a) == 2):
            raise ExportError(f"tile {tile.glyph or tile.name}: at(ax, ay) takes two numbers")
        return float(a[0]), float(a[1])

    walls, climbs, spikes = set(), set(), set()
    crumbles, saves, gems, anchors, shooters, enemies, spawns, goals = set(), set(), set(), set(), set(), set(), set(), set()
    for p in level.placements:
        t = p.tile
        wx, wy = world(p)
        if not (0 <= wx < cols and 0 <= wy < rows):
            warnings.append(f"{t.glyph or t.name} at ({p.x}, {p.y}) is outside the {cols}x{rows} level: ignored")
            continue
        ax, ay = at(t)
        pos = (wx + ax, wy + ay)
        if t.has("solid") and not t.has("crumbly"):
            walls.add((wx, wy))
        if t.has("climb"):
            climbs.add((wx, wy))
        if t.has("hazard"):
            spikes.add((wx, wy))
        if t.has("crumbly"):
            crumbles.add((wx, wy))
        if t.has("save"):
            saves.add(pos)
        if t.has("item"):
            gems.add(pos)
        if t.has("anchor"):
            anchors.add(pos)
        if t.has("spawn"):
            spawns.add(pos)
        if t.has("goal"):
            goals.add(pos)
        if "shooter" in t.params:
            d = t.params["shooter"]
            if not (isinstance(d, tuple) and len(d) == 2):
                raise ExportError(f"tile {t.glyph or t.name}: shooter(dx, dy) takes the direction it shoots")
            if not t.has("solid"):
                warnings.append(f"shooter {t.glyph or t.name} at ({p.x}, {p.y}) is not `solid`: the game expects the shooter's tile to be part of the walls")
            shooters.add((pos[0], pos[1], float(d[0]), float(d[1])))
        if "enemy" in t.params:
            k = t.params["enemy"]
            if isinstance(k, bool) or not isinstance(k, int):
                raise ExportError(f"tile {t.glyph or t.name}: enemy(kind) takes an integer kind (0 = worm, 1 = flyer)")
            enemies.add((k, pos[0], pos[1]))
    if len(spawns) != 1:
        raise ExportError(f"a level needs exactly one `spawn` tile (found {len(spawns)})")
    if len(goals) != 1:
        raise ExportError(f"a level needs exactly one `goal` tile (found {len(goals)})")
    (sx, sy), (gx, gy) = next(iter(spawns)), next(iter(goals))

    head = (_HERE / "slimejump_head.cs").read_text(encoding="utf-8")
    out = [f"// GENERATED by levelang from {source_name}: edit that file, not this one", head.rstrip("\n")]
    L = out.append
    L(f"        spawnX = {fmt(sx)}; spawnY = {fmt(sy)};")
    L(f"        goalX = {fmt(gx)}; goalY = {fmt(gy)};")
    L("        minY = 0f;")
    L(f"        minX = 0f; maxX = {fmt(cols)}; maxY = {fmt(rows)};")

    def block(name: str, stride: int, items: list[tuple], one=lambda r: r):
        L(f"        {name} = new float[{max(len(items), 1) * stride}]; {_COUNT[name]} = {len(items)};")
        setter = f"Set{stride}"
        for i, r in enumerate(items):
            L(f"        {setter}({name}, {i}, " + ", ".join(fmt(v) for v in one(r)) + ");")

    block("Walls", 4, merge_rects(walls))
    block("Climbs", 4, merge_rects(climbs))
    block("Spikes", 4, merge_rects(spikes))
    block("Saves", 2, sorted(saves))
    block("Gems", 2, sorted(gems))
    block("Anchors", 2, sorted(anchors))
    block("Crumbles", 4, [(x, y, 1, 1) for x, y in sorted(crumbles)])
    block("Shooters", 4, sorted(shooters))
    en = sorted(enemies, key=lambda e: (e[1], e[2], e[0]))
    L(f"        Enemies = new float[{max(len(en), 1) * 3}]; EnemyCount = {len(en)};")
    for i, (k, x, y) in enumerate(en):
        L(f"        Enemies[{i * 3}] = {k}; Enemies[{i * 3 + 1}] = {fmt(x)}; Enemies[{i * 3 + 2}] = {fmt(y)};")
    L("    }")
    return "\n".join(out) + "\n" + _layer_tail(layers_from), warnings


_COUNT = {"Walls": "WallCount", "Climbs": "ClimbCount", "Spikes": "SpikeCount", "Saves": "SaveCount", "Gems": "GemCount",
          "Anchors": "AnchorCount", "Crumbles": "CrumblyCount", "Shooters": "ShooterCount"}


# ----------------------------------------------------------------------------- Level.cs -> data


def _f(s: str) -> float:
    return float(s.rstrip("f"))


def parse_level_cs(text: str) -> dict:
    """The data of an existing Level.cs, as python lists (the inverse of to_level_cs)."""

    def array(name: str, stride: int) -> list[tuple]:
        m = re.search(rf"{name} = new float\[\d+\]; \w+ = (\d+);", text)
        if not m:
            raise ExportError(f"Level.cs has no {name} array")
        n = int(m[1])
        rows = {}
        for mm in re.finditer(rf"Set{stride}\({name}, (\d+), ([^)]*)\);", text):
            rows[int(mm[1])] = tuple(_f(v.strip()) for v in mm[2].split(","))
        if len(rows) != n:
            raise ExportError(f"{name}: count says {n}, found {len(rows)} entries")
        return [rows[i] for i in range(n)]

    def pair(a: str, b: str, src: str = text) -> tuple[float, float]:
        m = re.search(rf"{a} = ([\d.]+)f; {b} = ([\d.]+)f;", src)
        if not m:
            raise ExportError(f"Level.cs: no `{a} = ...; {b} = ...;`")
        return _f(m[1]), _f(m[2])

    vals = {int(i): _f(v) for i, v in re.findall(r"Enemies\[(\d+)\] = ([\d.]+)f?;", text)}
    en = [(int(vals[i * 3]), vals[i * 3 + 1], vals[i * 3 + 2]) for i in range(len(vals) // 3)]
    return {
        "spawn": pair("spawnX", "spawnY"), "goal": pair("goalX", "goalY"),
        "size": (int(_f(re.search(r"maxX = ([\d.]+f)", text)[1])), int(_f(re.search(r"maxY = ([\d.]+f)", text)[1]))),
        "walls": array("Walls", 4), "climbs": array("Climbs", 4), "spikes": array("Spikes", 4),
        "saves": array("Saves", 2), "gems": array("Gems", 2), "anchors": array("Anchors", 2),
        "crumbles": array("Crumbles", 4), "shooters": array("Shooters", 4), "enemies": en,
    }


# ----------------------------------------------------------------------------- Level.cs -> levelang art


def level_cs_to_lvl(text: str, name: str = "level") -> str:
    """Turn an existing Level.cs into levelang art (one emoji per cell), so a level can be edited as a picture."""
    d = parse_level_cs(text)
    W, H = d["size"]
    cells: dict[tuple[int, int], str] = {}
    used: dict[str, str] = {}  # emoji -> tile definition line

    def cell_of(x, y):
        return int(x // 1), int(y // 1)

    def offsets(points):  # one `at` per tile type; a mixed set can't be drawn with one emoji
        offs = {(round(x % 1, 4), round(y % 1, 4)) for x, y in points}
        if len(offs) > 1:
            raise ExportError(f"entities of one kind stand at different places inside their cells: {sorted(offs)}")
        return offs.pop() if offs else DEFAULT_AT

    def define(emoji, attrs, at=None):
        a = [attrs] + ([f"at({at[0]:g}, {at[1]:g})"] if at and at != DEFAULT_AT else [])
        used[emoji] = f"def {emoji} -> {', '.join(a)}:"

    def paint(rects, emoji):
        for x, y, w, h in rects:
            for i in range(int(w)):
                for j in range(int(h)):
                    cells[(int(x) + i, int(y) + j)] = emoji

    # terrain first, entities on top
    paint(d["walls"], "🧱")
    paint(d["climbs"], "🪜")
    paint(d["spikes"], "🔺")
    paint(d["crumbles"], "🟫")
    if d["walls"]:
        define("🧱", "fill.sienna, solid")
    if d["climbs"]:
        define("🪜", "fill.forestgreen, climb")
    if d["spikes"]:
        define("🔺", "fill.crimson, hazard")
    if d["crumbles"]:
        define("🟫", "fill.peru, crumbly")
    for emoji, key, attrs, color in (("💎", "gems", "item", "deepskyblue"), ("🚩", "saves", "save", "orange"), ("⚓", "anchors", "anchor", "gold")):
        pts = [(x, y) for x, y in d[key]]
        if pts:
            define(emoji, f"fill.{color}, {attrs}", offsets(pts))
            for x, y in pts:
                cells[cell_of(x, y)] = emoji
    for kind, emoji, color in ((0, "🪱", "violet"), (1, "🦇", "slateblue")):
        pts = [(x, y) for k, x, y in d["enemies"] if k == kind]
        if pts:
            define(emoji, f"fill.{color}, enemy({kind})", offsets(pts))
            for x, y in pts:
                cells[cell_of(x, y)] = emoji
    for kind, *_ in d["enemies"]:
        if kind not in (0, 1):
            raise ExportError(f"enemy kind {kind}: the converter knows kinds 0 and 1")
    for dirv, emoji in _ARROWS.items():
        pts = [(x, y) for x, y, dx, dy in d["shooters"] if (dx, dy) == dirv]
        if pts:
            define(emoji, f"fill.dimgray, solid, shooter({dirv[0]}, {dirv[1]})", offsets(pts))
            for x, y in pts:
                cells[cell_of(x, y)] = emoji
    if any((dx, dy) not in _ARROWS for _, _, dx, dy in d["shooters"]):
        raise ExportError("the converter handles shooters that shoot along an axis")
    define("🐸", "fill.limegreen, spawn", offsets([d["spawn"]]))
    cells[cell_of(*d["spawn"])] = "🐸"
    define("🏁", "fill.white, goal", offsets([d["goal"]]))
    cells[cell_of(*d["goal"])] = "🏁"

    rows = []
    for r in range(H):
        wy = H - 1 - r
        line = "".join(cells.get((wx, wy), "  ") for wx in range(W)).rstrip()
        rows.append(line or "·")  # `·` keeps an empty row inside the art block
    out = [f"## {name}: converted from a Level.cs by `levelang from-cs`. One emoji per cell, 2 spaces = air, y up in the game.", f"meta(width={W}, height={H})", ""]
    for line in used.values():
        out += [line, ""]
    out += [f"def {name}():"] + rows + ["", f"{name}()", ""]
    return "\n".join(out)
