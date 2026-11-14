"""AST pass: gives plain Python expressions their level-language meaning.

The parser output is ordinary Python. Here we walk it with ``ast`` and rewrite the few
constructs whose meaning depends on *tiles*:

    🧱                       (statement)  ->  y = __emit__(🧱, x, y)     place at cursor, move down a row
    🧱 * W                   (tile * int) ->  __rep__(lambda: 🧱, W)      a row of W tiles, re-evaluated per tile
    (🪨 or 🧱 or None)       (``or``)     ->  __pick__(...)               uniform random choice
    🪙 * 0.1                 (tile * flt) ->  __maybe__(lambda: 🪙, 0.1)  tile with 10% probability
    if 🟩 * 0.1: ...         (as a test)  ->  if __roll__(0.1): ...      10% chance the branch runs

"Tile" means a name the parser knows is a tile (every emoji, every ``def X -> ...``), so normal
Python such as ``a or b`` or ``n * 2`` is left alone.

Functions that emit get ``x`` and ``y`` parameters added if they don't declare them.
"""
from __future__ import annotations

import ast


def _call(name: str, *args: ast.expr) -> ast.Call:
    return ast.Call(func=ast.Name(name, ast.Load()), args=list(args), keywords=[])


def _lambda(body: ast.expr) -> ast.Lambda:
    return ast.Lambda(
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=body,
    )


class LevelTransformer(ast.NodeTransformer):
    def __init__(self, tiles: set[str]) -> None:
        self.tiles = tiles
        self._emits: list[bool] = [False]  # one flag per enclosing function

    # ---- classification -------------------------------------------------------------
    def is_tile_expr(self, n: ast.AST) -> bool:
        if isinstance(n, ast.Name):
            return n.id in self.tiles
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            return any(self.is_tile_expr(v) for v in n.values)
        if isinstance(n, ast.IfExp):
            return self.is_tile_expr(n.body) or self.is_tile_expr(n.orelse)
        if isinstance(n, ast.BinOp):
            if isinstance(n.op, ast.Mult):
                return self.is_tile_expr(n.left) != self.is_tile_expr(n.right)
            if isinstance(n.op, ast.Add):
                return self.is_tile_expr(n.left) or self.is_tile_expr(n.right)
        return False

    def _split_mult(self, n: ast.BinOp):
        """-> (tile_expr, count_expr) for ``tile * n`` / ``n * tile``, else None."""
        if not isinstance(n.op, ast.Mult):
            return None
        lt, rt = self.is_tile_expr(n.left), self.is_tile_expr(n.right)
        if lt == rt:
            return None
        return (n.left, n.right) if lt else (n.right, n.left)

    @staticmethod
    def _is_float(n: ast.AST) -> bool:
        return isinstance(n, ast.Constant) and isinstance(n.value, float)

    # ---- expressions ----------------------------------------------------------------
    def visit_BinOp(self, node: ast.BinOp):
        parts = self._split_mult(node)
        if parts:
            tile, count = parts
            fn = "__maybe__" if self._is_float(count) else "__rep__"
            new = _call(fn, _lambda(self.visit(tile)), self.visit(count))
            return ast.copy_location(new, node)
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        if isinstance(node.op, ast.Or) and any(self.is_tile_expr(v) for v in node.values):
            new = _call("__pick__", *[_lambda(self.visit(v)) for v in node.values])
            return ast.copy_location(new, node)
        return self.generic_visit(node)

    def _cond(self, test: ast.expr) -> ast.expr:
        if isinstance(test, ast.BinOp):
            parts = self._split_mult(test)
            if parts and self._is_float(parts[1]):
                return ast.copy_location(_call("__roll__", parts[1]), test)
        return test

    def visit_If(self, node: ast.If):
        node.test = self._cond(node.test)
        return self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp):
        node.test = self._cond(node.test)
        return self.generic_visit(node)

    # ---- statements -----------------------------------------------------------------
    def visit_Expr(self, node: ast.Expr):
        if self.is_tile_expr(node.value):
            value = self.visit(node.value)
            self._emits[-1] = True
            new = ast.Assign(
                targets=[ast.Name("y", ast.Store())],
                value=_call("__emit__", value, ast.Name("x", ast.Load()), ast.Name("y", ast.Load())),
            )
            return ast.copy_location(new, node)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._emits.append(False)
        self.generic_visit(node)
        if self._emits.pop():
            a = node.args
            have = {p.arg for p in a.posonlyargs + a.args + a.kwonlyargs}
            for name in ("x", "y"):
                if name not in have:
                    a.args.append(ast.arg(arg=name))
                    a.defaults.append(ast.Constant(0))
        return node


def transform(tree: ast.AST, tiles: set[str]) -> ast.AST:
    tree = LevelTransformer(tiles).visit(tree)
    return ast.fix_missing_locations(tree)
