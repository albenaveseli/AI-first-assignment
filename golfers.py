"""
1. SOCIAL GOLFERS PROBLEM - solved with DFS + Backtracking

MODEL (general case: g groups, p players per group, w weeks, n = g*p)
  Variables  : X(j, k, s) = the player in week j, group k, seat s
               j = 0..w-1, k = 0..g-1, s = 0..p-1          -> w*g*p variables
  Domain     : D = {0, 1, ..., n-1}
  Constraints:
     C1. In one week, every player plays exactly once.
     C2. Two players meet (are in the same group) at most ONCE over all weeks.
  Symmetry breaking (does not change the answer, only shortens the search):
     S1. Week 1 is fixed (taken from the assignment's example for 8x4).
     S2. Inside a group, players are in increasing order.
     S3. The first player of each group = the smallest player who has not played yet that week.
  Objective  : f(s) = sum over every pair (a,b) of max(0, meetings(a,b) - 1)
                    + sum over every week of (players repeated in that week)
               f(s) = 0  <=>  the schedule is valid

ANSWER to "How many weeks?" (upper bound):
  Each week a player meets p-1 new players. In total they can meet n-1.
  So w <= floor((n-1)/(p-1)).  For 32 players in groups of 4: (32-1)/(4-1) = 10.33 -> 10 weeks.
"""

import math
import random

from engine import Problem

# Week 1 as in the assignment's example (8 groups of 4 players)
EXAMPLE_WEEK1 = [
    [0, 1, 2, 3], [4, 5, 22, 23], [6, 7, 20, 21], [8, 25, 26, 27],
    [9, 10, 11, 24], [12, 13, 15, 30], [14, 28, 29, 31], [16, 17, 18, 19],
]


def upper_bound(g, p):
    n = g * p
    if p == 1:
        return math.inf   # players never meet
    if g == 1:
        return 1          # everyone in one group: only one week
    return (n - 1) // (p - 1)


def bits(mask):
    """Lists the players (indices of the 1-bits) in a bitmask, smallest first."""
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


class GolfState:
    """The schedule + helper structures that make constraint checks fast.

    Sets are stored as BITMASKS: an integer where bit i = player i.
    E.g. players {0, 2, 5} = 0b100101. Union = |, intersection = &, size = bit_count().
    """

    def __init__(self, n, total, weeks):
        self.schedule = [-1] * total   # the value of every variable (-1 = unassigned)
        self.filled = 0                # how many variables are assigned
        self.met = [0] * n             # met[a] = bitmask of the players a has met
        self.used = [0] * weeks        # used[j] = bitmask of the players playing in week j


class SocialGolfers(Problem):
    name = "Social Golfers"

    def __init__(self, g=8, p=4, w=10, week1=None, symmetry=True, forward_check=True, seed=None):
        self.g, self.p, self.w = g, p, w
        # seed != None -> values are tried in random order (for DFS with restarts)
        self.rng = random.Random(seed) if seed is not None else None
        self.n = g * p
        self.per_week = g * p
        self.total = w * self.per_week
        self.all = (1 << self.n) - 1
        self.symmetry = symmetry
        self.forward_check = forward_check
        if week1 is None and symmetry:
            if (g, p) == (8, 4):
                week1 = EXAMPLE_WEEK1
            else:
                week1 = [list(range(k * p, (k + 1) * p)) for k in range(g)]
        self.week1 = week1

    # --- helper: variable index -> (week, group, seat)
    def decode(self, var):
        j, rest = divmod(var, self.per_week)
        k, s = divmod(rest, self.p)
        return j, k, s

    def initial_state(self):
        st = GolfState(self.n, self.total, self.w)
        if self.week1 and self.w > 0:
            for k, group in enumerate(self.week1):
                for s, player in enumerate(sorted(group)):
                    self.assign(st, k * self.p + s, player)
        return st

    def copy(self, st):
        c = GolfState(self.n, 0, 0)
        c.schedule = list(st.schedule)
        c.filled = st.filled
        c.met = list(st.met)
        c.used = list(st.used)
        return c

    def next_variable(self, st):
        return st.filled if st.filled < self.total else None

    def group_members(self, st, var):
        """The players already sitting in this variable's group."""
        return st.schedule[var - (var % self.p):var]

    def values(self, st, var):
        j, k, s = self.decode(var)
        used = st.used[j]
        members = self.group_members(st, var)
        forbidden = used                          # C1: already played this week
        for m in members:
            forbidden |= st.met[m]                # C2: has already met a member of the group
        allowed = self.all & ~forbidden
        if self.symmetry:
            if s == 0:
                # S3: the group starts with the smallest free player -> a single candidate
                allowed &= -allowed
            else:
                start = members[-1] + 1           # S2: increasing order inside the group
                if k == 0 and s == 1 and j >= 2:
                    # S4: weeks are interchangeable -> order them by player 0's second partner
                    start = max(start, st.schedule[(j - 1) * self.per_week + 1] + 1)
                allowed &= ~((1 << start) - 1)
        result = []
        for x in bits(allowed):
            if self.forward_check and not self._still_feasible(st, var, j, x, members):
                continue
            result.append(x)
        if self.rng:
            self.rng.shuffle(result)
        return result

    def _still_feasible(self, st, var, j, x, members):
        """FORWARD CHECKING: after placing x, is this week still possible?
        Every player y who has not played yet this week must either:
          - be able to join the group being formed, or
          - have at least p-1 free partners they have not met (for a new group).
        If not, the branch is cut immediately (early backtracking)."""
        free = self.all & ~(st.used[j] | (1 << x))
        slots_left = self.p - len(members) - 1
        cand = 0
        if slots_left:
            forbidden = st.met[x]
            for m in members:
                forbidden |= st.met[m]
            cand = free & ~forbidden & ~((1 << (x + 1)) - 1)
            if cand.bit_count() < slots_left:
                return False
        for y in bits(free & ~cand):
            if (free & ~st.met[y]).bit_count() - 1 < self.p - 1:
                return False
        return True

    def assign(self, st, var, x):
        j = var // self.per_week
        for m in self.group_members(st, var):
            st.met[m] |= 1 << x
            st.met[x] |= 1 << m
        st.schedule[var] = x
        st.used[j] |= 1 << x
        st.filled += 1

    def unassign(self, st, var):
        j = var // self.per_week
        x = st.schedule[var]
        st.filled -= 1
        st.used[j] &= ~(1 << x)
        st.schedule[var] = -1
        for m in self.group_members(st, var):
            st.met[m] &= ~(1 << x)
            st.met[x] &= ~(1 << m)

    def depth_bound(self):
        return self.total - self.initial_state().filled

    def label(self, var, value):
        j, k, s = self.decode(var)
        return f"W{j + 1}G{k + 1}:{value}"

    # --- Objective function, works on a complete schedule (a list of w*g*p numbers)
    def objective(self, st):
        sched = st.schedule if isinstance(st, GolfState) else st
        meet = {}
        f = 0
        for j in range(self.w):
            week = sched[j * self.per_week:(j + 1) * self.per_week]
            f += len(week) - len(set(week))
            for k in range(self.g):
                grp = week[k * self.p:(k + 1) * self.p]
                for a in range(self.p):
                    for b in range(a + 1, self.p):
                        pair = (min(grp[a], grp[b]), max(grp[a], grp[b]))
                        meet[pair] = meet.get(pair, 0) + 1
        f += sum(c - 1 for c in meet.values() if c > 1)
        return f

    def random_state(self, rng):
        """A random schedule that respects C1 (every week is a permutation)."""
        sched = []
        for _ in range(self.w):
            perm = list(range(self.n))
            rng.shuffle(perm)
            sched.extend(perm)
        return sched

    def weeks_table(self, st):
        sched = st.schedule if isinstance(st, GolfState) else st
        return [[sched[j * self.per_week + k * self.p: j * self.per_week + (k + 1) * self.p]
                 for k in range(self.g)] for j in range(self.w)]


def to_text(problem, st):
    lines = []
    for j, week in enumerate(problem.weeks_table(st)):
        groups = "  ".join("{" + ",".join(f"{x:>2}" for x in grp) + "}" for grp in week)
        lines.append(f"Java {j + 1:>2}: {groups}")
    return "\n".join(lines)


def landscape_sizes(g, p, w):
    n = g * p
    log_fact = lambda k: math.lgamma(k + 1) / math.log(10)
    # the number of ways to split n players into g unordered groups of p
    one_week = log_fact(n) - g * log_fact(p) - log_fact(g)
    return [
        (f"Pa kufizime: n^(n*w) = {n}^{n * w}", n * w * math.log10(n)),
        ("Cdo jave nje permutacion (K1): (n!)^w", w * log_fact(n)),
        ("Cdo jave nje ndarje ne grupe: P^w", w * one_week),
        ("Me thyerje simetrie (java 1 fikse): P^(w-1)", (w - 1) * one_week),
    ]


def max_weeks(g, p, time_per_w=20, verbose=True):
    """Answers "How many weeks?": tries w = 1, 2, ... up to the upper bound."""
    from engine import dfs
    best = None
    ub = upper_bound(g, p)
    ub = 30 if ub == math.inf else ub
    for w in range(1, ub + 1):
        prob = SocialGolfers(g, p, w)
        stats = dfs(prob, time_limit=time_per_w)
        if verbose:
            print(f"  w = {w:>2}: {stats}")
        if stats.status == "zgjidhje":
            best = (w, prob, stats)
        else:
            break
    return best, ub


def dfs_with_restarts(g, p, w, node_limit=20000, time_limit=120, verbose=True):
    """DFS with RANDOM RESTARTS.

    Plain DFS can get stuck early in a bad branch and never get out of it.
    Here we stop DFS after `node_limit` nodes and start it again with a different
    (random) value order. It is still DFS + Backtracking, with no heuristic.
    """
    import time
    from engine import dfs
    t0 = time.perf_counter()
    total_nodes = 0
    seed = 0
    while time.perf_counter() - t0 < time_limit:
        prob = SocialGolfers(g, p, w, seed=seed)
        stats = dfs(prob, node_limit=node_limit)
        total_nodes += stats.nodes
        if stats.status == "zgjidhje":
            if verbose:
                print(f"  U gjet pas {seed + 1} rinisjesh, {total_nodes:,} nyje, "
                      f"{time.perf_counter() - t0:.1f}s")
            stats.nodes = total_nodes
            stats.seconds = time.perf_counter() - t0
            return prob, stats
        if stats.status == "pa zgjidhje":
            return prob, stats          # the whole tree was explored: no solution
        seed += 1
    if verbose:
        print(f"  Nuk u gjet brenda {time_limit}s ({seed} rinisje, {total_nodes:,} nyje)")
    return None, None
