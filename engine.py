"""
Shared search engine.

Key idea: the DFS, BFS and IDDFS algorithms do NOT know which problem they are solving.
They only know the `Problem` interface, which has these parts:

    initial_state()          -> the start state (some variables may already be assigned)
    next_variable(state)     -> the next variable to assign (None = the state is complete)
    values(state, var)       -> the DOMAIN values that break NO constraint (pruning)
    assign / unassign        -> set / remove a value (used by DFS and IDDFS)
    copy(state)              -> a copy of the state (used by BFS, which keeps many states at once)
    objective(state)         -> f(s) = number of constraint violations; f = 0 means a solution

Backtracking = when a variable has no valid value left, we abandon that branch
and go back (DFS/IDDFS) or simply stop expanding it (BFS).
"""

import sys
import time
from collections import deque

sys.setrecursionlimit(20000)


class Problem:
    """The interface every problem must implement."""

    name = "Problem"

    def initial_state(self):
        raise NotImplementedError

    def copy(self, state):
        raise NotImplementedError

    def next_variable(self, state):
        raise NotImplementedError

    def values(self, state, var):
        raise NotImplementedError

    def assign(self, state, var, value):
        raise NotImplementedError

    def unassign(self, state, var):
        raise NotImplementedError

    def objective(self, state):
        raise NotImplementedError

    def depth_bound(self):
        """How many variables still have to be assigned (maximum tree depth). Used by IDDFS."""
        raise NotImplementedError

    def label(self, var, value):
        """Short text for one step, e.g. 'r2c3=5'. Used in the visualisation."""
        return f"{var}={value}"


class SearchStopped(Exception):
    """Raised when the time limit or the node limit is exceeded."""


class Stats:
    """Statistics of one run. These are what we compare in the 'algorithm race'."""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.nodes = 0           # how many nodes (states) were generated
        self.backtracks = 0      # how many times a branch ended with no way forward
        self.max_memory = 0      # DFS/IDDFS: max stack depth; BFS: max queue size
        self.iterations = 0      # IDDFS only: how many depth limits were tried
        self.seconds = 0.0
        self.status = "pa filluar"  # "zgjidhje" (solved), "pa zgjidhje" (no solution), "u nderpre" (stopped)
        self.solution = None

    def as_dict(self):
        return {
            "algorithm": self.algorithm,
            "nodes": self.nodes,
            "backtracks": self.backtracks,
            "max_memory": self.max_memory,
            "iterations": self.iterations,
            "seconds": round(self.seconds, 4),
            "status": self.status,
        }

    def __str__(self):
        s = (f"{self.algorithm:6} | statusi: {self.status:12} | nyje: {self.nodes:>10,} | "
             f"backtracks: {self.backtracks:>9,} | memoria max: {self.max_memory:>9,} | "
             f"koha: {self.seconds:8.3f}s")
        if self.algorithm == "IDDFS":
            s += f" | iteracione: {self.iterations}"
        return s


class Tracer:
    """Records the search tree (every node with its parent) for the visualisation."""

    def __init__(self, limit=4000):
        self.limit = limit
        self.nodes = []  # [id, parent, label, depth, iteration, status, var, value]

    def add(self, parent, label, depth, iteration=0, var=None, value=None):
        if len(self.nodes) >= self.limit:
            return -1
        nid = len(self.nodes)
        self.nodes.append([nid, parent, label, depth, iteration, "ok", var, value])
        return nid

    @property
    def full(self):
        return len(self.nodes) >= self.limit

    def mark(self, nid, status):
        if 0 <= nid < len(self.nodes):
            self.nodes[nid][5] = status


class _Guard:
    """Enforces the time limit and the node limit."""

    def __init__(self, stats, time_limit, node_limit):
        self.stats = stats
        self.t0 = time.perf_counter()
        self.time_limit = time_limit
        self.node_limit = node_limit

    def check(self):
        if self.node_limit and self.stats.nodes >= self.node_limit:
            raise SearchStopped()
        if self.time_limit and (self.stats.nodes & 255) == 0:
            if time.perf_counter() - self.t0 > self.time_limit:
                raise SearchStopped()


# ---------------------------------------------------------------------------
# 1) DEPTH-FIRST SEARCH with Backtracking
# ---------------------------------------------------------------------------
def dfs(problem, time_limit=None, node_limit=None, tracer=None):
    """Go as deep as possible along one branch; when stuck, go back (backtrack)."""
    stats = Stats("DFS")
    guard = _Guard(stats, time_limit, node_limit)
    state = problem.initial_state()

    def recurse(depth, parent_id):
        var = problem.next_variable(state)
        if var is None:                       # every variable has been assigned
            if tracer:
                tracer.mark(parent_id, "goal")
            return True
        stats.max_memory = max(stats.max_memory, depth + 1)
        for value in problem.values(state, var):
            stats.nodes += 1
            guard.check()
            nid = tracer.add(parent_id, problem.label(var, value), depth + 1, 0, var, value) if tracer and not tracer.full else -1
            problem.assign(state, var, value)
            if recurse(depth + 1, nid):
                return True
            problem.unassign(state, var)      # BACKTRACK: undo the decision
        stats.backtracks += 1                 # no value worked
        if tracer:
            tracer.mark(parent_id, "dead")
        return False

    return _run(stats, guard, lambda: recurse(0, -1), problem, state, tracer)


# ---------------------------------------------------------------------------
# 2) BREADTH-FIRST SEARCH with Backtracking (pruning)
# ---------------------------------------------------------------------------
def bfs(problem, time_limit=None, node_limit=None, tracer=None):
    """Explore level by level with a FIFO queue.

    BFS does not "go back" like DFS, because it keeps every branch at the same time.
    Here backtracking means: a state that has no valid value for its next variable
    is a DEAD END. We drop it and never expand it again.
    Values that break a constraint are never put in the queue either.
    """
    stats = Stats("BFS")
    guard = _Guard(stats, time_limit, node_limit)
    result = {"state": None}

    def run():
        queue = deque([(problem.initial_state(), -1, 0)])
        while queue:
            stats.max_memory = max(stats.max_memory, len(queue))
            state, nid, depth = queue.popleft()
            var = problem.next_variable(state)
            if var is None:
                result["state"] = state
                if tracer:
                    tracer.mark(nid, "goal")
                return True
            children = list(problem.values(state, var))
            if not children:
                stats.backtracks += 1         # dead end -> abandoned
                if tracer:
                    tracer.mark(nid, "dead")
            for value in children:
                stats.nodes += 1
                guard.check()
                child = problem.copy(state)
                problem.assign(child, var, value)
                cid = tracer.add(nid, problem.label(var, value), depth + 1, 0, var, value) if tracer and not tracer.full else -1
                queue.append((child, cid, depth + 1))
        return False

    return _run(stats, guard, run, problem, None, tracer, result)


# ---------------------------------------------------------------------------
# 3) ITERATIVE DEEPENING DFS with Backtracking
# ---------------------------------------------------------------------------
def iddfs(problem, time_limit=None, node_limit=None, tracer=None):
    """DFS with a depth limit L = 0, 1, 2, ...  Every iteration starts over from the root.

    Benefit: small memory like DFS + the guarantee of BFS (finds the shallowest solution).
    Cost: the upper levels are revisited in every iteration.
    """
    stats = Stats("IDDFS")
    guard = _Guard(stats, time_limit, node_limit)
    holder = {"state": None}

    def depth_limited(state, depth, limit, parent_id, it):
        var = problem.next_variable(state)
        if var is None:
            if tracer:
                tracer.mark(parent_id, "goal")
            return "found"
        if depth == limit:
            return "cutoff"                   # limit reached, there may be more below
        stats.max_memory = max(stats.max_memory, depth + 1)
        any_cutoff = False
        for value in problem.values(state, var):
            stats.nodes += 1
            guard.check()
            nid = tracer.add(parent_id, problem.label(var, value), depth + 1, it, var, value) if tracer and not tracer.full else -1
            problem.assign(state, var, value)
            r = depth_limited(state, depth + 1, limit, nid, it)
            if r == "found":
                return "found"
            if r == "cutoff":
                any_cutoff = True
            problem.unassign(state, var)      # BACKTRACK
        if not any_cutoff:
            stats.backtracks += 1
            if tracer:
                tracer.mark(parent_id, "dead")
        return "cutoff" if any_cutoff else "failure"

    def run():
        for limit in range(0, problem.depth_bound() + 1):
            stats.iterations += 1
            state = problem.initial_state()
            r = depth_limited(state, 0, limit, -1, limit)
            if r == "found":
                holder["state"] = state
                return True
            if r == "failure":                # nothing was cut off by the limit -> no solution
                return False
        return False

    return _run(stats, guard, run, problem, None, tracer, holder)


def _run(stats, guard, fn, problem, state, tracer, holder=None):
    try:
        found = fn()
        stats.status = "zgjidhje" if found else "pa zgjidhje"
        if found:
            stats.solution = holder["state"] if holder else state
    except SearchStopped:
        stats.status = "u nderpre"
    stats.seconds = time.perf_counter() - guard.t0
    return stats


ALGORITHMS = {"DFS": dfs, "BFS": bfs, "IDDFS": iddfs}


def race(problem_factory, time_limit=10, node_limit=2_000_000):
    """Algorithm race: the same problem, three algorithms, the same limits."""
    results = []
    for name, algo in ALGORITHMS.items():
        stats = algo(problem_factory(), time_limit=time_limit, node_limit=node_limit)
        results.append(stats)
    return results
