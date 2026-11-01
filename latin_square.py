"""
3. LATIN SQUARE - solved with IDDFS + Backtracking

MODEL
  Variables  : X(r,c) for every cell, r,c = 0..n-1      -> n*n variables
  Domain     : D = {1, 2, ..., n}
  Constraints: every row has different values (AllDifferent)
               every column has different values (AllDifferent)
  State      : a list of n*n cells; 0 = empty cell
  Objective  : f(s) = sum_rows (n - #distinct_values) + sum_columns (n - #distinct_values)
               f(s) = 0  <=>  s is a Latin square
"""

import math
import random

from engine import Problem

# The exact number of Latin squares (OEIS A002860), used for the landscape.
KNOWN_COUNTS = {
    1: 1, 2: 2, 3: 12, 4: 576, 5: 161280, 6: 812851200, 7: 61479419904000,
    8: 108776032459082956800, 9: 5524751496156892842531225600,
    10: 9982437658213039871725064756920320000,
    11: 776966836171770144107444346734230682311065600000,
}


class LatinSquare(Problem):
    name = "Latin Square"

    def __init__(self, n, symmetry=True, given=None):
        self.n = n
        self.symmetry = symmetry
        self.given = given  # optional: a grid with some cells given (0 = empty)

    def initial_state(self):
        if self.given:
            return list(self.given)
        n = self.n
        state = [0] * (n * n)
        if self.symmetry:
            # SYMMETRY BREAKING: first row = 1..n (as in the assignment's example),
            # first column = 1..n. Every Latin square can be brought into this form
            # by relabelling the numbers and reordering the rows, so nothing is lost.
            for c in range(n):
                state[c] = c + 1
            for r in range(n):
                state[r * n] = r + 1
        return state

    def copy(self, state):
        return list(state)

    def next_variable(self, state):
        # Fixed order: row by row (uninformed search)
        try:
            return state.index(0)
        except ValueError:
            return None

    def values(self, state, var):
        n = self.n
        r, c = divmod(var, n)
        used = set(state[r * n:(r + 1) * n]) | set(state[c::n])
        return [v for v in range(1, n + 1) if v not in used]

    def assign(self, state, var, value):
        state[var] = value

    def unassign(self, state, var):
        state[var] = 0

    def depth_bound(self):
        return self.initial_state().count(0)

    def label(self, var, value):
        r, c = divmod(var, self.n)
        return f"({r},{c})={value}"

    def objective(self, state):
        n = self.n
        f = 0
        for i in range(n):
            f += n - len(set(state[i * n:(i + 1) * n]))
            f += n - len(set(state[i::n]))
        return f

    def random_state(self, rng):
        return [rng.randint(1, self.n) for _ in range(self.n * self.n)]


def cyclic_construction(n):
    """No search at all: L[r][c] = ((c - r) mod n) + 1. Gives exactly the assignment's example."""
    return [((c - r) % n) + 1 for r in range(n) for c in range(n)]


def to_text(state, n):
    return "\n".join(" ".join(str(state[r * n + c]) for c in range(n)) for r in range(n))


def count_all(n):
    """Counts all Latin squares with an exhaustive DFS (small n only).
    No symmetry breaking, so that all of them are counted (not only the normalised forms)."""
    p = LatinSquare(n, symmetry=False)
    state = p.initial_state()
    count = 0

    def rec():
        nonlocal count
        var = p.next_variable(state)
        if var is None:
            count += 1
            return
        for v in p.values(state, var):
            p.assign(state, var, v)
            rec()
            p.unassign(state, var)

    rec()
    return count


def landscape_sizes(n):
    """The size of the search space, step by step."""
    return [
        ("Pa asnje kufizim: n^(n*n)", n * n * math.log10(n)),
        ("Cdo rresht permutacion: (n!)^n", n * math.log10(math.factorial(n))),
        ("Katrore latine te sakte (zgjidhje)", math.log10(KNOWN_COUNTS[n]) if n in KNOWN_COUNTS else None),
    ]
