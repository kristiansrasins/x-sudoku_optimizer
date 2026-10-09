"""Generate the fixed benchmark set into instances/ (deterministic seeds).

Every instance is created from a known complete X-Sudoku grid, so the
optimal cost is 0 for all of them; the solution is saved next to the puzzle.
"""

import os
import random

from xsudoku.generator import make_puzzle
from xsudoku.model import Puzzle

# (name, b, target clues)
INSTANCES = [
    ("x4_easy", 2, 8),
    ("x4_hard", 2, 4),
    ("x9_easy", 3, 36),
    ("x9_medium", 3, 28),
    ("x9_hard", 3, 20),
    ("x16_easy", 4, 160),
    ("x16_medium", 4, 128),
    ("x16_hard", 4, 100),
    ("x25_easy", 5, 420),
    ("x25_medium", 5, 360),
    ("x25_hard", 5, 300),
]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instances")


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, (name, b, clues) in enumerate(INSTANCES):
        rng = random.Random(1000 + i)
        puzzle, solution = make_puzzle(b, clues, rng, unique=True)
        puzzle.save(os.path.join(OUT, name + ".txt"))
        Puzzle(b, solution).save(os.path.join(OUT, name + ".solution.txt"))
        n = b * b
        print(f"{name:12s} {n:2d}x{n:<2d} clues={puzzle.clues:4d} "
              f"({100 * puzzle.clues / n / n:.0f}%) free={n * n - puzzle.clues}")


if __name__ == "__main__":
    main()
