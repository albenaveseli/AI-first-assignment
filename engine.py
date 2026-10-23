"""
Motori i perbashket i kerkimit (Search Engine).

Ideja kryesore: algoritmet DFS, BFS dhe IDDFS NUK e dine cili problem po zgjidhet.
Ata njohin vetem nderfaqen `Problem` me keto pjese:

    initial_state()          -> gjendja fillestare (disa variabla mund te jene te vendosura)
    next_variable(state)     -> variabla e radhes qe duhet vendosur (None = gjendja eshte e plote)
    values(state, var)       -> vlerat nga DOMAIN-i qe NUK e shkelin asnje kufizim (pruning)
    assign / unassign        -> vendos / heq nje vlere (perdoret nga DFS dhe IDDFS)
    copy(state)              -> kopje e gjendjes (perdoret nga BFS, qe mban shume gjendje njekohesisht)
    objective(state)         -> f(s) = numri i shkeljeve te kufizimeve; f = 0 do te thote zgjidhje

Backtracking = kur nje variabel nuk ka asnje vlere te vlefshme, degen e braktisim
dhe kthehemi mbrapa (DFS/IDDFS) ose thjesht nuk e zgjerojme me (BFS).
"""

import sys
import time
from collections import deque

sys.setrecursionlimit(20000)


class Problem:
    """Nderfaqja qe duhet ta implementoje cdo problem."""

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
        """Sa variabla jane per t'u vendosur (thellesia maksimale e pemes). Per IDDFS."""
        raise NotImplementedError

    def label(self, var, value):
        """Teksti i shkurter i nje hapi, p.sh. 'r2c3=5'. Perdoret ne vizualizim."""
        return f"{var}={value}"


class SearchStopped(Exception):
    """Ngritet kur kalohet kufiri i kohes ose i nyjeve."""


class Stats:
    """Statistikat e nje ekzekutimi. Keto i krahasojme ne 'garen e algoritmeve'."""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.nodes = 0           # sa nyje (gjendje) jane gjeneruar
        self.backtracks = 0      # sa here nje dege ka perfunduar pa rrugedalje
        self.max_memory = 0      # DFS/IDDFS: thellesia max e stack-ut; BFS: madhesia max e radhes
        self.iterations = 0      # vetem per IDDFS: sa kufij thellesie u provuan
        self.seconds = 0.0
        self.status = "pa filluar"  # "zgjidhje", "pa zgjidhje", "u nderpre"
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
    """Regjistron pemen e kerkimit (cdo nyje me prindin e saj) per vizualizim."""

    def __init__(self, limit=4000):
        self.limit = limit
        self.nodes = []  # [id, parent, label, depth, iteration, status, var, value]

    def add(self, parent, label, depth, iteration=0, var=None, value=None):
        if len(self.nodes) >= self.limit:
            return -1
        nid = len(self.nodes)
        self.nodes.append([nid, parent, label, depth, iteration, "ok", var, value])
        return nid

    def mark(self, nid, status):
        if 0 <= nid < len(self.nodes):
            self.nodes[nid][5] = status


class _Guard:
    """Kontrollon kufirin e kohes dhe te nyjeve."""

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
# 1) DEPTH FIRST SEARCH me Backtracking
# ---------------------------------------------------------------------------
def dfs(problem, time_limit=None, node_limit=None, tracer=None):
    """Shko sa me thelle ne nje dege; kur ngec, kthehu mbrapa (backtrack)."""
    stats = Stats("DFS")
    guard = _Guard(stats, time_limit, node_limit)
    state = problem.initial_state()

    def recurse(depth, parent_id):
        var = problem.next_variable(state)
        if var is None:                       # te gjitha variablat jane vendosur
            if tracer:
                tracer.mark(parent_id, "goal")
            return True
        stats.max_memory = max(stats.max_memory, depth + 1)
        for value in problem.values(state, var):
            stats.nodes += 1
            guard.check()
            nid = tracer.add(parent_id, problem.label(var, value), depth + 1, 0, var, value) if tracer else -1
            problem.assign(state, var, value)
            if recurse(depth + 1, nid):
                return True
            problem.unassign(state, var)      # BACKTRACK: zhbejme vendimin
        stats.backtracks += 1                 # asnje vlere nuk funksionoi
        if tracer:
            tracer.mark(parent_id, "dead")
        return False

    return _run(stats, guard, lambda: recurse(0, -1), problem, state, tracer)


# ---------------------------------------------------------------------------
# 2) BREADTH FIRST SEARCH me Backtracking (pruning)
# ---------------------------------------------------------------------------
def bfs(problem, time_limit=None, node_limit=None, tracer=None):
    """Eksploro nivel pas niveli me nje radhe (FIFO).

    BFS nuk "kthehet mbrapa" si DFS, sepse i mban te gjitha deget njekohesisht.
    Backtracking-u ketu do te thote: nje gjendje qe nuk ka asnje vlere te vlefshme
    per variablen e radhes eshte RRUGE E VDEKUR. E hedhim dhe nuk e zgjerojme me.
    Edhe vlerat qe shkelin kufizimet nuk futen kurre ne radhe.
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
                stats.backtracks += 1         # rruge e vdekur -> braktiset
                if tracer:
                    tracer.mark(nid, "dead")
            for value in children:
                stats.nodes += 1
                guard.check()
                child = problem.copy(state)
                problem.assign(child, var, value)
                cid = tracer.add(nid, problem.label(var, value), depth + 1, 0, var, value) if tracer else -1
                queue.append((child, cid, depth + 1))
        return False

    return _run(stats, guard, run, problem, None, tracer, result)


# ---------------------------------------------------------------------------
# 3) ITERATIVE DEEPENING DFS me Backtracking
# ---------------------------------------------------------------------------
def iddfs(problem, time_limit=None, node_limit=None, tracer=None):
    """DFS me kufi thellesie L = 0, 1, 2, ...  Cdo iteracion fillon nga e para.

    Perfitimi: memorie e vogel si DFS + garanci si BFS (gjen zgjidhjen me te cekte).
    Kostoja: nivelet e siperme rivizitohen ne cdo iteracion.
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
            return "cutoff"                   # u arrit kufiri, mund te kete me thelle
        stats.max_memory = max(stats.max_memory, depth + 1)
        any_cutoff = False
        for value in problem.values(state, var):
            stats.nodes += 1
            guard.check()
            nid = tracer.add(parent_id, problem.label(var, value), depth + 1, it, var, value) if tracer else -1
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
            if r == "failure":                # asgje nuk u pre nga kufiri -> nuk ka zgjidhje
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
    """Gara e algoritmeve: i njejti problem, tre algoritme, te njejtat kufij."""
    results = []
    for name, algo in ALGORITHMS.items():
        stats = algo(problem_factory(), time_limit=time_limit, node_limit=node_limit)
        results.append(stats)
    return results
