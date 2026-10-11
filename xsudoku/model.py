"""X-Sudoku domain and cost function.

X-Sudoku: an n x n grid (n = b*b) where every row, column, b x b box and
both main diagonals must contain each digit 1..n exactly once.

Domain (solution representation)
--------------------------------
A full grid. Given cells (clues) are fixed; every free cell is a planning
variable whose value is a digit 1..n. The initial solution fills each box
with the digits missing from that box, so the box constraint holds from the
start and is kept by the move (swap inside one box).

Cost (evaluation)
-----------------
cost = sum over units u in {rows, columns, diagonal, anti-diagonal} of
       (n - number of distinct digits in u)
     = sum over units u, digits v of max(0, count[u][v] - 1)

cost == 0  <=>  the grid is a valid X-Sudoku solution (global optimum).
"""

import random


class Puzzle:
    """Immutable problem instance."""

    def __init__(self, b, grid):
        self.b = b
        self.n = b * b
        self.grid = [list(row) for row in grid]  # 0 = empty
        if len(self.grid) != self.n or any(len(r) != self.n for r in self.grid):
            raise ValueError("grid must be n x n")

    @property
    def clues(self):
        return sum(1 for row in self.grid for v in row if v)

    @classmethod
    def load(cls, path):
        """File format: first line b, then n lines of n integers (0 = empty)."""
        with open(path) as f:
            tokens = f.read().split()
        b = int(tokens[0])
        n = b * b
        vals = [int(t) for t in tokens[1:1 + n * n]]
        return cls(b, [vals[r * n:(r + 1) * n] for r in range(n)])

    def save(self, path):
        width = len(str(self.n))
        with open(path, "w") as f:
            f.write(f"{self.b}\n")
            for row in self.grid:
                f.write(" ".join(str(v).rjust(width) for v in row) + "\n")


def is_valid_solution(puzzle, grid):
    """Independent full check: clues kept and all 3n+2 units are permutations."""
    n, b = puzzle.n, puzzle.b
    full = set(range(1, n + 1))
    for r in range(n):
        for c in range(n):
            if puzzle.grid[r][c] and puzzle.grid[r][c] != grid[r][c]:
                return False
    units = [[grid[r][c] for c in range(n)] for r in range(n)]
    units += [[grid[r][c] for r in range(n)] for c in range(n)]
    units += [[grid[br + i][bc + j] for i in range(b) for j in range(b)]
              for br in range(0, n, b) for bc in range(0, n, b)]
    units.append([grid[i][i] for i in range(n)])
    units.append([grid[i][n - 1 - i] for i in range(n)])
    return all(set(u) == full for u in units)


class State:
    """Mutable current solution with incremental cost bookkeeping."""

    def __init__(self, puzzle, rng):
        self.p = puzzle
        n, b = puzzle.n, puzzle.b
        self.n = n
        self.grid = [row[:] for row in puzzle.grid]

        # Free cells grouped by box (only boxes with >= 2 free cells can move).
        self.box_free = []
        self.box_of_cell = {}
        for br in range(0, n, b):
            for bc in range(0, n, b):
                cells = [(r, c) for r in range(br, br + b) for c in range(bc, bc + b)
                         if puzzle.grid[r][c] == 0]
                present = {puzzle.grid[r][c] for r in range(br, br + b)
                           for c in range(bc, bc + b)}
                missing = [v for v in range(1, n + 1) if v not in present]
                rng.shuffle(missing)
                for (r, c), v in zip(cells, missing):
                    self.grid[r][c] = v
                if len(cells) >= 2:
                    self.box_free.append(cells)
                    for cell in cells:
                        self.box_of_cell[cell] = cells
        self.movable = [cell for cells in self.box_free for cell in cells]
        self.free_count = sum(1 for row in puzzle.grid for v in row if v == 0)

        # Units checked by the cost: rows 0..n-1, cols n..2n-1, diag 2n, anti 2n+1.
        self.cell_units = [[None] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                u = [r, n + c]
                if r == c:
                    u.append(2 * n)
                if r + c == n - 1:
                    u.append(2 * n + 1)
                self.cell_units[r][c] = u

        self.stride = n + 1
        self.counts = [0] * ((2 * n + 2) * self.stride)
        for r in range(n):
            for c in range(n):
                for u in self.cell_units[r][c]:
                    self.counts[u * self.stride + self.grid[r][c]] += 1
        self.cost = self.full_cost()

    def full_cost(self):
        """Cost from scratch (used for initialization and verification)."""
        return sum(max(0, k - 1) for k in self.counts)

    def _remove(self, r, c, v):
        d = 0
        for u in self.cell_units[r][c]:
            i = u * self.stride + v
            if self.counts[i] > 1:
                d -= 1
            self.counts[i] -= 1
        return d

    def _add(self, r, c, v):
        d = 0
        for u in self.cell_units[r][c]:
            i = u * self.stride + v
            if self.counts[i] > 0:
                d += 1
            self.counts[i] += 1
        return d

    def swap(self, a, b):
        """Swap values of cells a and b (same box). Returns cost delta. O(1)."""
        (r1, c1), (r2, c2) = a, b
        v1, v2 = self.grid[r1][c1], self.grid[r2][c2]
        d = self._remove(r1, c1, v1) + self._remove(r2, c2, v2)
        d += self._add(r1, c1, v2) + self._add(r2, c2, v1)
        self.grid[r1][c1], self.grid[r2][c2] = v2, v1
        self.cost += d
        return d

    def random_move(self, rng):
        """Neighbourhood: pick a box with >= 2 free cells, pick two free cells in it."""
        cells = rng.choice(self.box_free)
        return rng.sample(cells, 2)

    def in_conflict(self, r, c):
        v = self.grid[r][c]
        return any(self.counts[u * self.stride + v] > 1 for u in self.cell_units[r][c])

    def conflict_move(self, rng, tries=20):
        """Conflict-directed neighbourhood: the first cell is a movable cell that
        currently violates a row/column/diagonal constraint (sampled, up to
        `tries` attempts), the second is another free cell of the same box."""
        free = self.movable
        for _ in range(tries):
            a = rng.choice(free)
            if self.in_conflict(*a):
                break
        cells = self.box_of_cell[a]
        b = a
        while b == a:
            b = rng.choice(cells)
        return a, b

    def snapshot(self):
        return [row[:] for row in self.grid]


def format_grid(grid):
    width = len(str(len(grid)))
    return "\n".join(" ".join(str(v).rjust(width) if v else "." * width for v in row)
                     for row in grid)
