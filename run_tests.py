"""Benchmark: run SA on every instance in instances/ and record time and quality.

Quality is compared with the known optimum (cost 0 = valid X-Sudoku).
As a reference, the exact backtracking search from the generator is timed too.

Usage:  python run_tests.py [--seeds 5] [--workers 8] [--moves conflict,random]
Output: results/results.csv (one row per run), results/summary.md
"""

import argparse
import csv
import glob
import os
import statistics
import time
from multiprocessing import Pool

from xsudoku import Puzzle, simulated_annealing, is_valid_solution
from xsudoku.generator import count_solutions

ROOT = os.path.dirname(os.path.abspath(__file__))
TIME_LIMIT = {4: 5, 9: 20, 16: 60, 25: 120}  # seconds per run, by grid size


def instance_paths():
    paths = glob.glob(os.path.join(ROOT, "instances", "*.txt"))
    paths = [p for p in paths if not p.endswith(".solution.txt")]
    return sorted(paths, key=lambda p: (Puzzle.load(p).n, -Puzzle.load(p).clues))


def run_sa(job):
    path, move, seed = job
    p = Puzzle.load(path)
    r = simulated_annealing(p, seed=seed, move=move, time_limit=TIME_LIMIT[p.n])
    return {
        "instance": os.path.basename(path)[:-4],
        "n": p.n,
        "clues": p.clues,
        "move": move,
        "seed": seed,
        "initial_cost": r["initial_cost"],
        "best_cost": r["best_cost"],
        "solved": int(r["best_cost"] == 0 and is_valid_solution(p, r["best_grid"])),
        "time_s": round(r["time"], 3),
        "iterations": r["iterations"],
        "reheats": r["reheats"],
        "t0": round(r["t0"], 3),
        "L": r["L"],
    }


def run_exact(path):
    p = Puzzle.load(path)
    start = time.perf_counter()
    try:
        count_solutions(p.b, p.grid, limit=1, node_limit=2_000_000)
        t = round(time.perf_counter() - start, 3)
    except TimeoutError:
        t = None
    return os.path.basename(path)[:-4], t


def summarize(rows, exact):
    lines = ["| instance | n | clues | move | solved | best cost (min/avg/max) "
             "| avg time s (solved runs) | avg iterations | exact search s |",
             "|---|---|---|---|---|---|---|---|---|"]
    keys = []
    for r in rows:
        k = (r["instance"], r["move"])
        if k not in keys:
            keys.append(k)
    for inst, move in keys:
        rs = [r for r in rows if r["instance"] == inst and r["move"] == move]
        costs = [r["best_cost"] for r in rs]
        solved = [r for r in rs if r["solved"]]
        t = f"{statistics.mean(r['time_s'] for r in solved):.2f}" if solved else "-"
        lines.append(
            f"| {inst} | {rs[0]['n']} | {rs[0]['clues']} | {move} | {len(solved)}/{len(rs)} "
            f"| {min(costs)} / {statistics.mean(costs):.1f} / {max(costs)} | {t} "
            f"| {statistics.mean(r['iterations'] for r in rs):,.0f} "
            f"| {exact.get(inst) if exact.get(inst) is not None else '>limit'} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--moves", default="conflict,random")
    args = ap.parse_args()

    paths = instance_paths()
    jobs = [(p, m, s) for p in paths for m in args.moves.split(",") for s in range(args.seeds)]
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)

    with Pool(args.workers) as pool:
        exact = dict(pool.map(run_exact, paths))
        rows = []
        for row in pool.imap(run_sa, jobs):
            rows.append(row)
            print(f"{row['instance']:12s} {row['move']:8s} seed={row['seed']} "
                  f"cost={row['best_cost']:3d} time={row['time_s']:7.2f}s "
                  f"iters={row['iterations']}", flush=True)

    with open(os.path.join(ROOT, "results", "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ROOT, "results", "summary.md"), "w") as f:
        f.write(summarize(rows, exact))
    print(summarize(rows, exact))


if __name__ == "__main__":
    main()
