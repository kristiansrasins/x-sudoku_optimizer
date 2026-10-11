"""Plot cost vs iterations for both move types on one instance -> results/convergence.png"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from xsudoku import Puzzle, simulated_annealing

ROOT = os.path.dirname(os.path.abspath(__file__))


def main(name="x16_medium", seed=0, max_iters=1_500_000):
    p = Puzzle.load(os.path.join(ROOT, "instances", name + ".txt"))
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for move, color in (("random", "#c0504d"), ("conflict", "#1f6fb2")):
        r = simulated_annealing(p, seed=seed, move=move, max_iters=max_iters,
                                time_limit=120, history_every=500)
        it = [h[0] for h in r["history"]]
        ax.plot(it, [h[1] for h in r["history"]], color=color, lw=0.8, alpha=0.6,
                label=f"{move}: pašreizējās izmaksas")
        ax.plot(it, [h[2] for h in r["history"]], color=color, lw=1.8,
                label=f"{move}: labākās izmaksas")
    ax.set_xlabel("iterācijas")
    ax.set_ylabel("izmaksas")
    ax.set_title(f"{name}, seed={seed}")
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(ROOT, "results", "convergence.png")
    fig.savefig(out, dpi=200)
    print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:2])
