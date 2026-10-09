"""Simulated Annealing, implemented from scratch following the lecture pseudocode:

    function SIMULATED_ANNEALING(phi, f, V, t, L)
        best, i := INITIALIZE(phi, f)
        k := 0
        repeat
            for n := 0 to L[k] do
                j := GENERATE(V(i))
                if f(j) - f(best) < 0 then best := j
                if f(j) - f(i) < 0 or random(1) < exp((f(i) - f(j)) / t[k]) then i := j
            k := k + 1
        until t[k] ~ 0
        return best

Schedules used here:
    t[k] = t0 * alpha^k            (geometric cooling)
    L[k] = L = l_factor * (#free cells)   (constant chain length per temperature)

Addition (reheating): if t[k] reaches t_min without finding cost 0, the
temperature is reset to t0 and annealing continues from the current solution.
This repeats until cost 0 (optimum) is found or the time/iteration budget runs out.
"""

import math
import random
import statistics
import time

from .model import State


def initial_temperature(state, rng, samples=200):
    """t0 = standard deviation of cost deltas of random moves from the start solution."""
    deltas = []
    for _ in range(samples):
        a, b = state.random_move(rng)
        deltas.append(state.swap(a, b))
        state.swap(a, b)  # undo
    sd = statistics.pstdev(deltas)
    return sd if sd > 0 else 1.0


def simulated_annealing(puzzle, seed=None, alpha=0.99, l_factor=1.0, t_min=0.01,
                        time_limit=60.0, max_iters=None, t0=None, history_every=0):
    rng = random.Random(seed)
    start = time.perf_counter()

    state = State(puzzle, rng)                      # INITIALIZE
    initial_cost = state.cost
    if not state.box_free:                          # nothing to move
        return _result(state, state.snapshot(), state.cost, initial_cost, 0, 0, 0, start, [])

    t0 = t0 if t0 is not None else initial_temperature(state, rng)
    L = max(10, int(l_factor * state.free_count))

    best_cost, best_grid = state.cost, state.snapshot()
    t = t0
    iters = 0
    reheats = 0
    temp_levels = 0
    history = []
    exp = math.exp
    rnd = rng.random

    while best_cost > 0:
        for _ in range(L):                          # for n := 0 to L[k]
            a, b = state.random_move(rng)           # j := GENERATE(V(i))
            delta = state.swap(a, b)                # f(j) - f(i)
            iters += 1
            if delta <= 0 or rnd() < exp(-delta / t):
                if state.cost < best_cost:          # f(j) - f(best) < 0
                    best_cost = state.cost
                    best_grid = state.snapshot()
                    if best_cost == 0:
                        break
            else:
                state.swap(a, b)                    # reject: undo the move
            if history_every and iters % history_every == 0:
                history.append((iters, state.cost, best_cost, t))
        if best_cost == 0:
            break
        temp_levels += 1
        t *= alpha                                  # k := k + 1
        if t < t_min:                               # t[k] ~ 0  -> reheat
            t = t0
            reheats += 1
        if time.perf_counter() - start > time_limit:
            break
        if max_iters is not None and iters >= max_iters:
            break

    return _result(state, best_grid, best_cost, initial_cost, iters, reheats,
                   temp_levels, start, history, t0=t0, L=L)


def _result(state, best_grid, best_cost, initial_cost, iters, reheats, temp_levels,
            start, history, t0=None, L=None):
    return {
        "best_cost": best_cost,
        "best_grid": best_grid,
        "initial_cost": initial_cost,
        "iterations": iters,
        "reheats": reheats,
        "temp_levels": temp_levels,
        "time": time.perf_counter() - start,
        "t0": t0,
        "L": L,
        "history": history,
    }
