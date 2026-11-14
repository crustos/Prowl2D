"""A tiny bot that "plays" a level so the preview GIF shows the layout in use.

Mode 'swim' (free movement in 8 directions, no gravity). It walks spawn -> every reachable
item (nearest first) -> goal, never entering solid or hazard cells and keeping a little
distance from hazards when it can. Platformer physics (gravity, jumps) is a later mode.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from .runtime import Level, Placed

_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


@dataclass
class Plan:
    points: list = field(default_factory=list)  # [(cx, cy)] grid cells, consecutive cells are adjacent
    collects: list = field(default_factory=list)  # [(index into points, Placed item)]
    start: tuple | None = None
    goal: tuple | None = None
    notes: list = field(default_factory=list)


def plan(level: Level, start: tuple | None = None, goal: tuple | None = None, hazard_margin: float = 5.0) -> Plan:
    x0, y0, x1, y1 = level.bounds()
    solid = {(p.x, p.y) for p in level.placements if p.tile.has("solid")}
    hazard = {(p.x, p.y) for p in level.placements if p.tile.has("hazard")}
    near = {(hx + dx, hy + dy) for hx, hy in hazard for dx, dy in _DIRS}
    blocked = solid | hazard
    out = Plan()

    def free(c):
        return x0 <= c[0] <= x1 and y0 <= c[1] <= y1 and c not in blocked

    def dijkstra(src):
        dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
        while pq:
            d, c = heapq.heappop(pq)
            if d > dist.get(c, 1e18):
                continue
            for dx, dy in _DIRS:
                n = (c[0] + dx, c[1] + dy)
                if not free(n):
                    continue
                if dx and dy and not (free((c[0] + dx, c[1])) and free((c[0], c[1] + dy))):
                    continue  # no cutting corners
                nd = d + (1.4142 if dx and dy else 1.0) + (hazard_margin if n in near else 0.0)
                if nd < dist.get(n, 1e18):
                    dist[n], prev[n] = nd, c
                    heapq.heappush(pq, (nd, n))
        return dist, prev

    def edge_cell(right: bool):
        cols = range(x1, x0 - 1, -1) if right else range(x0, x1 + 1)
        for cx in cols:
            ys = [cy for cy in range(y0, y1 + 1) if free((cx, cy))]
            if ys:
                mid = (y0 + y1) / 2
                return (cx, min(ys, key=lambda v: abs(v - mid)))
        return None

    spawns, goals = level.find("spawn"), level.find("goal")
    start = start or ((spawns[0].x, spawns[0].y) if spawns else edge_cell(False))
    goal = goal or ((goals[0].x, goals[0].y) if goals else edge_cell(True))
    if start is None:
        out.notes.append("no free cell to start in")
        return out
    out.start, out.goal = start, goal
    out.points = [start]
    cur = start
    items = list(level.find("item"))

    def walk_to(target, prev, item=None):
        path, c = [], target
        while c != cur:
            path.append(c)
            c = prev[c]
        path.reverse()
        out.points.extend(path)
        if item is not None:
            out.collects.append((len(out.points) - 1, item))

    while items:
        dist, prev = dijkstra(cur)
        reach = [it for it in items if (it.x, it.y) in dist]
        for it in items:
            if it not in reach:
                out.notes.append(f"item at {(it.x, it.y)} is unreachable")
        if not reach:
            break
        it = min(reach, key=lambda p: dist[(p.x, p.y)])
        walk_to((it.x, it.y), prev, it)
        cur = (it.x, it.y)
        items = [i for i in reach if i is not it]
    if goal is not None:
        dist, prev = dijkstra(cur)
        if goal in dist:
            walk_to(goal, prev)
        else:
            out.notes.append(f"goal {goal} is unreachable")
    return out


def path_length(points) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))
