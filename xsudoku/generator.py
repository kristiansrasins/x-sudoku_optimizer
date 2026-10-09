"""Test-instance generator (not part of the optimizer).

1. Build a random complete X-Sudoku grid with exact backtracking search
   (bitmasks + minimum-remaining-values heuristic).
2. Remove clues in random order. With `unique=True` a clue is removed only
   if the puzzle still has exactly one solution (checked by the same search).

Because every instance is built from a known complete grid, the optimal
cost of every instance is known: 0.
"""

import random

from .model import Puzzle


class _Search:
    def __init__(self, b, grid):
        self.b = b
        n = self.n = b * b
        self.grid = [row[:] for row in grid]
        self.row = [0] * n
        self.col = [0] * n
        self.box = [0] * n
        self.diag = [0, 0]
        self.empty = []
        for r in range(n):
            for c in range(n):
                v = self.grid[r][c]
                if v:
                    if not self._can(r, c, v):
                        raise ValueError("clues conflict")
                    self._set(r, c, v)
                else:
                    self.empty.append((r, c))

    def _bx(self, r, c):
        return (r // self.b) * self.b + c // self.b

    def _used(self, r, c):
        m = self.row[r] | self.col[c] | self.box[self._bx(r, c)]
        if r == c:
            m |= self.diag[0]
        if r + c == self.n - 1:
            m |= self.diag[1]
        return m

    def _can(self, r, c, v):
        return not (self._used(r, c) >> v) & 1

    def _set(self, r, c, v):
        bit = 1 << v
        self.grid[r][c] = v
        self.row[r] |= bit
        self.col[c] |= bit
        self.box[self._bx(r, c)] |= bit
        if r == c:
            self.diag[0] |= bit
        if r + c == self.n - 1:
            self.diag[1] |= bit

    def _unset(self, r, c, v):
        bit = ~(1 << v)
        self.grid[r][c] = 0
        self.row[r] &= bit
        self.col[c] &= bit
        self.box[self._bx(r, c)] &= bit
        if r == c:
            self.diag[0] &= bit
        if r + c == self.n - 1:
            self.diag[1] &= bit

    def solve(self, rng=None, limit=1, node_limit=None):
        """Return number of solutions found (up to `limit`); first one kept in self.solution."""
        self.found = 0
        self.solution = None
        self.nodes = 0
        self.node_limit = node_limit
        self.rng = rng
        full = ((1 << (self.n + 1)) - 1) & ~1
        self.full = full
        empty = set(self.empty)
        self._rec(empty, limit)
        return self.found

    def _rec(self, empty, limit):
        if not empty:
            self.found += 1
            if self.solution is None:
                self.solution = [row[:] for row in self.grid]
            return self.found >= limit
        self.nodes += 1
        if self.node_limit and self.nodes > self.node_limit:
            raise TimeoutError
        # MRV: cell with fewest candidates
        best, best_cands, best_k = None, 0, 99
        for (r, c) in empty:
            cands = self.full & ~self._used(r, c)
            k = bin(cands).count("1")
            if k < best_k:
                best, best_cands, best_k = (r, c), cands, k
                if k <= 1:
                    break
        if best_k == 0:
            return False
        r, c = best
        vals = [v for v in range(1, self.n + 1) if (best_cands >> v) & 1]
        if self.rng:
            self.rng.shuffle(vals)
        empty.discard(best)
        for v in vals:
            self._set(r, c, v)
            if self._rec(empty, limit):
                self._unset(r, c, v)
                empty.add(best)
                return True
            self._unset(r, c, v)
        empty.add(best)
        return False


def random_solution(b, rng, node_limit=200000):
    n = b * b
    while True:
        s = _Search(b, [[0] * n for _ in range(n)])
        try:
            if s.solve(rng=rng, limit=1, node_limit=node_limit):
                return s.solution
        except TimeoutError:
            continue  # unlucky branch, restart with new random order


def count_solutions(b, grid, limit=2, node_limit=None):
    return _Search(b, grid).solve(limit=limit, node_limit=node_limit)


def make_puzzle(b, clues, rng, unique=True, node_limit=20000):
    """Remove cells from a random full grid until `clues` remain.

    unique=True keeps the solution unique (cells whose removal breaks
    uniqueness, or whose check exceeds node_limit, are kept as clues),
    so the final number of clues can be larger than requested.
    """
    n = b * b
    solution = random_solution(b, rng)
    grid = [row[:] for row in solution]
    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    remaining = n * n
    for (r, c) in cells:
        if remaining <= clues:
            break
        v = grid[r][c]
        grid[r][c] = 0
        if unique:
            try:
                ok = count_solutions(b, grid, limit=2, node_limit=node_limit) == 1
            except TimeoutError:
                ok = False
            if not ok:
                grid[r][c] = v
                continue
        remaining -= 1
    return Puzzle(b, grid), solution
