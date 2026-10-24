"""
2. SUDOKU - zgjidhet me BFS + Backtracking

MODELIMI
  Variablat : X(r,c) per cdo qelize BOSH, r,c = 0..8
  Domain    : D = {1, ..., 9}
  Kufizimet : AllDifferent ne cdo rresht, kolone dhe kuti 3x3 (27 kufizime);
              qelizat e dhena nuk ndryshohen
  Gjendja   : lista me 81 numra; 0 = qelize bosh
  Objective : f(s) = shuma mbi 27 njesite (9 - numri_i_vlerave_te_ndryshme_ne_njesi)
              f(s) = 0  <=>  Sudoku eshte zgjidhur

Lidhja me Latin Square: nje Sudoku i zgjidhur ESHTE katror latin 9x9,
me nje kufizim shtese per kutite 3x3.
"""

import math

from engine import Problem

# Tri nivele + nje bonus. Niveli eshte matur me numrin e nyjeve qe i duhen BFS-it:
#   easy ~ 70 nyje | medium ~ 4.6 mije | hard ~ 364 mije ("Golden Nugget")
#   extreme: Sudoku i Arto Inkala (2012), "me i veshtiri ne bote" - BFS mban ~356 mije gjendje ne memorie.
PUZZLES = {
    "easy": "000260701680070090190004500820100040004602900050003028009300074040050036703018000",
    "medium": "530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    "hard": "000000039000001005003050800008090006070002000100400000009080050020000600400700000",
    "extreme": "800000000003600000070090200050007000000045700000100030001000068008500010090000400",
}

# Per secilen qelize: indekset e 20 "fqinjeve" (rreshti, kolona, kutia)
PEERS = []
for _i in range(81):
    _r, _c = divmod(_i, 9)
    _br, _bc = 3 * (_r // 3), 3 * (_c // 3)
    _p = {_r * 9 + k for k in range(9)} | {k * 9 + _c for k in range(9)}
    _p |= {(_br + a) * 9 + _bc + b for a in range(3) for b in range(3)}
    _p.discard(_i)
    PEERS.append(tuple(_p))

# 27 njesite: 9 rreshta, 9 kolona, 9 kuti
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
        # Renditje fikse (e painformuar): qeliza e pare bosh, rresht pas rreshti
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
        """Kontrollon qe numrat e dhene nuk bien ndesh mes vete."""
        s = self.puzzle
        return all(s[i] == 0 or all(s[p] != s[i] for p in PEERS[i]) for i in range(81))

    def count_solutions(self, limit=2):
        """DFS qe numeron zgjidhjet (ndalet te `limit`). 1 = Sudoku i mirefillte."""
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
    # sa vlera mbeten per cdo qelize pas kufizimeve me numrat e dhene
    pruned = sum(math.log10(len(p.values(s, i))) for i in range(81) if s[i] == 0)
    return [
        (f"Pa kufizime: 9^{empty} (qeliza bosh)", empty * math.log10(9)),
        ("Pas heqjes se vlerave qe bien ndesh me te dhenat", pruned),
        ("Zgjidhje te sakta (Sudoku i mire ka 1)", 0.0),
    ]
