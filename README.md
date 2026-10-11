# X-Sudoku with Simulated Annealing

Small practical work for the course *Praktiskā kombinatoriālā optimizācija* (LU).

Solves X-Sudoku (Sudoku where both main diagonals must also contain every digit)
with Simulated Annealing implemented from scratch in Python (standard library only;
matplotlib is used only for the plot).

## Structure

- `xsudoku/model.py` – domain (grid, fixed clues, box-wise initial fill) and cost function
  (duplicate digits in rows, columns and both diagonals, updated incrementally)
- `xsudoku/sa.py` – simulated annealing (geometric cooling, reheating, two move types:
  `random` and `conflict`)
- `xsudoku/generator.py` – backtracking generator for test instances with a unique solution
- `instances/` – 11 test instances from 4x4 to 25x25 (`*.solution.txt` = known optimum)
- `results/` – benchmark results (`results.csv`, `summary.md`, `convergence.png`)
- `report/` – report (LaTeX source and PDF)

## Running

```
python generate_instances.py     # regenerate instances (already in the repo)
python run_tests.py              # benchmark: every instance x 2 moves x 5 seeds
python plot_convergence.py       # cost vs iterations plot
```

Solving a single instance:

```python
from xsudoku import Puzzle, simulated_annealing, format_grid
p = Puzzle.load("instances/x9_medium.txt")
r = simulated_annealing(p, seed=0)
print(r["best_cost"], r["time"])
print(format_grid(r["best_grid"]))
```

Instance file format: first line `b` (box size, grid is `b*b x b*b`), then the grid row by row,
`0` = empty cell.
