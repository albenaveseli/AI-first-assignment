"""
2. SUDOKU - solved with BFS + Backtracking

MODEL
  Variables  : X(r,c) for every EMPTY cell, r,c = 0..8
  Domain     : D = {1, ..., 9}
  Constraints: AllDifferent in every row, column and 3x3 box (27 constraints);
               the given cells are never changed
  State      : a list of 81 numbers; 0 = empty cell
  Objective  : f(s) = sum over the 27 units of (9 - number_of_distinct_values_in_the_unit)
               f(s) = 0  <=>  the Sudoku is solved

Link to Latin Square: a solved Sudoku IS a 9x9 Latin square
with an extra constraint for the 3x3 boxes.
"""

import math

from engine import Problem

# Three levels + a bonus. The level is measured by the number of nodes BFS needs:
#   easy ~ 70 nodes | medium ~ 4.6 thousand | hard ~ 364 thousand ("Golden Nugget")
#   extreme: Arto Inkala's Sudoku (2012), "the world's hardest" - BFS holds ~356 thousand states in memory.
PUZZLES = {
    "easy": "000260701680070090190004500820100040004602900050003028009300074040050036703018000",
    "medium": "530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    "hard": "000000039000001005003050800008090006070002000100400000009080050020000600400700000",
    "extreme": "800000000003600000070090200050007000000045700000100030001000068008500010090000400",
}

# For every cell: the indices of its 20 "peers" (row, column, box)
PEERS = []
for _i in range(81):
    _r, _c = divmod(_i, 9)
    _br, _bc = 3 * (_r // 3), 3 * (_c // 3)
    _p = {_r * 9 + k for k in range(9)} | {k * 9 + _c for k in range(9)}
    _p |= {(_br + a) * 9 + _bc + b for a in range(3) for b in range(3)}
    _p.discard(_i)
    PEERS.append(tuple(_p))

# The 27 units: 9 rows, 9 columns, 9 boxes
UNITS = ([[r * 9 + c for c in range(9)] for r in range(9)] +
         [[r * 9 + c for r in range(9)] for c in range(9)] +
         [[(br + a) * 9 + bc + b for a in range(3) for b in range(3)]
          for br in (0, 3, 6) for bc in (0, 3, 6)])


def parse(text):
    digits = [int(ch) for ch in text.replace(".", "0") if ch.isdigit()]
    if len(digits) != 81:
        raise ValueError("A Sudoku must have exactly 81 cells")
    return digits


class Sudoku(Problem):
    name = "Sudoku"

    def __init__(self, puzzle):
        self.puzzle = parse(puzzle) if isinstance(puzzle, str) else list(puzzle)

    def initial_state(self):
        return list(self.puzzle)

    def copy(self, state):
        return list(state)

    def next_variable(self, state):
        # Fixed (uninformed) order: the first empty cell, row by row
        try:
            return state.index(0)
        except ValueError:
            return None

    def values(self, state, var):
        used = {state[p] for p in PEERS[var]}
        return [v for v in range(1, 10) if v not in used]

    def assign(self, state, var, value):
        state[var] = value

    def unassign(self, state, var):
        state[var] = 0

    def depth_bound(self):
        return self.puzzle.count(0)

    def label(self, var, value):
        r, c = divmod(var, 9)
        return f"r{r + 1}c{c + 1}={value}"

    def objective(self, state):
        return sum(9 - len(set(state[i] for i in unit)) for unit in UNITS)

    def random_state(self, rng):
        return [v if v else rng.randint(1, 9) for v in self.puzzle]

    def is_valid_start(self):
        """Checks that the given numbers do not clash with each other."""
        s = self.puzzle
        return all(s[i] == 0 or all(s[p] != s[i] for p in PEERS[i]) for i in range(81))

    def count_solutions(self, limit=2):
        """DFS that counts the solutions (stops at `limit`). 1 = a proper Sudoku."""
        state = self.initial_state()
        count = 0

        def rec():
            nonlocal count
            var = self.next_variable(state)
            if var is None:
                count += 1
                return count >= limit
            for v in self.values(state, var):
                state[var] = v
                if rec():
                    return True
                state[var] = 0
            return False

        rec()
        return count


def to_text(state):
    lines = []
    for r in range(9):
        if r in (3, 6):
            lines.append("------+-------+------")
        cells = [str(v) if v else "." for v in state[r * 9:(r + 1) * 9]]
        lines.append(" ".join(cells[0:3]) + " | " + " ".join(cells[3:6]) + " | " + " ".join(cells[6:9]))
    return "\n".join(lines)


def landscape_sizes(puzzle):
    s = parse(puzzle) if isinstance(puzzle, str) else puzzle
    empty = s.count(0)
    p = Sudoku(s)
    # how many values remain for each cell after the constraints with the givens
    counts = [len(p.values(s, i)) for i in range(81) if s[i] == 0]
    # a cell with no possible value means 0 fillings are left (log10 is undefined) -> None
    pruned = None if 0 in counts else sum(math.log10(c) for c in counts)
    return [
        (f"Pa kufizime: 9^{empty} (qeliza bosh)", empty * math.log10(9)),
        ("Pas heqjes se vlerave qe bien ndesh me te dhenat", pruned),
        ("Zgjidhje te sakta (Sudoku i mire ka 1)", 0.0),
    ]
