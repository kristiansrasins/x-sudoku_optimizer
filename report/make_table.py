"""results/results.csv -> report/table.tex (LaTeX rows for the report)."""

import csv
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "results.csv"))))
keys = []
for r in rows:
    k = r["instance"]
    if k not in keys:
        keys.append(k)


def cell(rs):
    solved = [r for r in rs if r["solved"] == "1"]
    costs = [int(r["best_cost"]) for r in rs]
    t = f"{statistics.mean(float(r['time_s']) for r in solved):.2f}" if solved else "--"
    cost = "0" if max(costs) == 0 else f"{min(costs)}/{statistics.mean(costs):.1f}/{max(costs)}"
    return f"{len(solved)}/{len(rs)} & {t} & {cost}"


out = []
for inst in keys:
    rs = [r for r in rows if r["instance"] == inst]
    n, clues = int(rs[0]["n"]), int(rs[0]["clues"])
    name = inst.replace("_", r"\_")
    out.append(f"{name} & {n}$\\times${n} & {clues} ({100 * clues / n / n:.0f}\\%) & "
               + cell([r for r in rs if r["move"] == "random"]) + " & "
               + cell([r for r in rs if r["move"] == "conflict"]) + r" \\")

with open(os.path.join(ROOT, "report", "table.tex"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
