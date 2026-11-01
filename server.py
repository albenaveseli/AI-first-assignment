"""
SEARCH LAB - web server (FastAPI)

    pip install -r requirements.txt
    python server.py              ->  open http://127.0.0.1:8000

Every request runs the algorithm LIVE and returns: the solution, the statistics,
the search trace (for the animation) and the landscape.
"""

import math
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import golfers
import landscape
import latin_square
import search_trees
import sudoku
from engine import ALGORITHMS, Tracer

app = FastAPI(title="Search Lab", description="Uninformed search techniques")
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

TRACE_LIMIT = 2500      # how many trace nodes are sent for the animation
MAX_TIME = 30           # time limit for one request (seconds)


def run(problem, algo, time_limit, node_limit=None, trace=True):
    if algo not in ALGORITHMS:
        raise HTTPException(400, f"Algorithm must be one of: {', '.join(ALGORITHMS)}")
    tracer = Tracer(TRACE_LIMIT) if trace else None
    stats = ALGORITHMS[algo](problem, time_limit=min(time_limit, MAX_TIME),
                             node_limit=node_limit, tracer=tracer)
    return stats, (tracer.nodes if tracer else [])


STATUS_EN = {"zgjidhje": "solved", "pa zgjidhje": "no solution", "u nderpre": "stopped", "pa filluar": "not started"}


def stats_en(stats):
    d = stats.as_dict()
    d["status"] = STATUS_EN.get(d["status"], d["status"])
    return d


def sizes(rows, labels):
    """Landscape sizes with English labels (in the same order as in the module)."""
    return [{"label": lab, "log10": None if b is None else round(b, 2)} for lab, (_, b) in zip(labels, rows)]


GOLF_LABELS = ["No constraints: n^(n·w)", "Each week a permutation: (n!)^w",
               "Each week a partition into groups: P^w", "Week 1 fixed (symmetry breaking): P^(w−1)"]
SUDOKU_LABELS = ["No constraints: 9^(empty cells)", "After removing values that clash with the givens",
                 "Solutions (a proper Sudoku has exactly 1)"]
LATIN_LABELS = ["No constraints: n^(n²)", "Every row a permutation: (n!)^n", "Latin squares (solutions)"]
ACTIONS_EN = {"LART": "UP", "POSHTE": "DOWN", "MAJTAS": "LEFT", "DJATHTAS": "RIGHT",
              "Hen": "Mon", "Mar": "Tue", "Mer": "Wed", "Enj": "Thu", "Pre": "Fri", "Sht": "Sat", "Die": "Sun"}


def action_en(a):
    for k, v in ACTIONS_EN.items():
        a = a.replace(k, v)
    return a


def hist(problem, samples=1500):
    r = landscape.sample_objective(problem, samples)
    r["histogram"] = [list(x) for x in r["histogram"]]
    return r


# ---------------------------------------------------------------------------
# 1. SOCIAL GOLFERS
# ---------------------------------------------------------------------------
@app.get("/api/golfers")
def api_golfers(g: int = Query(8, ge=1, le=12), p: int = Query(4, ge=1, le=8),
                w: int = Query(5, ge=1, le=20), algo: str = "DFS",
                restarts: bool = False, time_limit: float = 20):
    ub = golfers.upper_bound(g, p)
    trace = []
    if restarts and algo == "DFS":
        prob, stats = golfers.dfs_with_restarts(g, p, w, time_limit=min(time_limit, 120), verbose=False)
        if stats is None:
            return {"status": "stopped", "g": g, "p": p, "w": w, "n": g * p, "upper_bound": ub if ub != math.inf else None,
                    "stats": {"algorithm": "DFS", "status": "stopped", "nodes": 0, "backtracks": 0,
                              "max_memory": 0, "iterations": 0, "seconds": time_limit}}
    else:
        prob = golfers.SocialGolfers(g, p, w)
        stats, trace = run(prob, algo, time_limit, node_limit=3_000_000, trace=(g * p <= 16))
    sol = stats.solution
    return {
        "g": g, "p": p, "w": w, "n": g * p,
        "initial": prob.initial_state().schedule,
        "upper_bound": ub if ub != math.inf else None,
        "stats": stats_en(stats),
        "schedule": prob.weeks_table(sol) if sol else None,
        "objective": prob.objective(sol) if sol else None,
        "trace": trace,
    }


@app.get("/api/golfers/landscape")
def api_golfers_landscape(g: int = Query(8, ge=1, le=12), p: int = Query(4, ge=1, le=8),
                          w: int = Query(10, ge=1, le=20)):
    return {"sizes": sizes(golfers.landscape_sizes(g, p, w), GOLF_LABELS),
            "histogram": hist(golfers.SocialGolfers(g, p, w))}


# ---------------------------------------------------------------------------
# 2. SUDOKU
# ---------------------------------------------------------------------------
class SudokuRequest(BaseModel):
    puzzle: str | None = None
    level: str | None = "easy"
    algo: str = "BFS"
    time_limit: float = 30


@app.get("/api/sudoku/levels")
def api_sudoku_levels():
    return {k: sudoku.parse(v) for k, v in sudoku.PUZZLES.items()}


@app.post("/api/sudoku")
def api_sudoku(req: SudokuRequest):
    text = req.puzzle or sudoku.PUZZLES.get(req.level or "easy")
    if not text:
        raise HTTPException(400, "Unknown level")
    try:
        prob = sudoku.Sudoku(text)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not prob.is_valid_start():
        raise HTTPException(400, "The givens already conflict with each other")
    stats, trace = run(prob, req.algo, req.time_limit, node_limit=4_000_000)
    sol = stats.solution
    return {
        "puzzle": prob.puzzle, "empty": prob.puzzle.count(0),
        "stats": stats_en(stats), "solution": sol,
        "objective": prob.objective(sol) if sol else None,
        "objective_start": prob.objective([v if v else 0 for v in prob.puzzle]),
        "landscape": {"sizes": sizes(sudoku.landscape_sizes(prob.puzzle), SUDOKU_LABELS), "histogram": hist(prob)},
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# 3. LATIN SQUARE
# ---------------------------------------------------------------------------
@app.get("/api/latin")
def api_latin(n: int = Query(5, ge=1, le=12), algo: str = "IDDFS", symmetry: bool = True,
              time_limit: float = 15):
    prob = latin_square.LatinSquare(n, symmetry=symmetry)
    stats, trace = run(prob, algo, time_limit, node_limit=5_000_000)
    sol = stats.solution
    fallback = None
    if not sol and algo == "IDDFS":
        # the last IDDFS iteration = a full DFS
        fb, _ = run(latin_square.LatinSquare(n, symmetry=symmetry), "DFS", 10, trace=False)
        fallback = {"stats": stats_en(fb), "solution": fb.solution}
    return {
        "n": n, "initial": prob.initial_state(), "stats": stats_en(stats), "solution": sol,
        "objective": prob.objective(sol) if sol else None,
        "cyclic": latin_square.cyclic_construction(n),
        "fallback": fallback,
        "count": str(latin_square.KNOWN_COUNTS.get(n, "")),
        "landscape": {"sizes": sizes(latin_square.landscape_sizes(n), LATIN_LABELS),
                      "histogram": hist(latin_square.LatinSquare(n, symmetry=False))},
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# 4. SEARCH TREES
# ---------------------------------------------------------------------------
def tree_response(prob, strategy, max_nodes=600):
    root, nodes, goal = search_trees.build_tree(prob, strategy=strategy, max_nodes=max_nodes)
    kinds = {}
    for nd in nodes:
        kinds[nd.kind] = kinds.get(nd.kind, 0) + 1
    path = search_trees.solution_path(goal) if goal else []
    tree = search_trees.tree_to_json(prob, nodes)
    for nd in tree:
        nd["action"] = action_en(nd["action"])
    return {"name": prob.name, "strategy": strategy.upper(), "nodes": tree,
            "kinds": kinds, "solution_length": goal.depth if goal else None,
            "path": [{"action": action_en(nd.action), "state": prob.show(nd.state),
                      "grid": prob.grid(nd.state) if hasattr(prob, "grid") else None} for nd in path]}


@app.get("/api/trees/puzzle")
def api_tree_puzzle(start: str = "123046758", strategy: str = "bfs"):
    digits = [int(c) for c in start if c.isdigit()]
    if sorted(digits) != list(range(9)):
        raise HTTPException(400, "The state must contain each of 0..8 exactly once")
    if not search_trees.EightPuzzle.is_solvable(digits):
        raise HTTPException(400, "This state can NOT reach the goal (odd inversion parity)")
    return tree_response(search_trees.EightPuzzle(digits), strategy, max_nodes=800)


@app.get("/api/trees/mc")
def api_tree_mc(m: int = Query(3, ge=1, le=6), c: int = Query(3, ge=1, le=6),
                boat: int = Query(2, ge=1, le=4), strategy: str = "bfs"):
    prob = search_trees.MissionariesCannibals(m, c, boat)
    if not prob.is_safe(m, c):
        raise HTTPException(400, "The start state already breaks the rule: cannibals outnumber missionaries on the left bank")
    return tree_response(prob, strategy)


@app.get("/api/trees/rws")
def api_tree_rws(max_work: int = Query(4, ge=2, le=7), max_off: int = Query(2, ge=1, le=4),
                 strategy: str = "dfs"):
    return tree_response(search_trees.RotatingWorkforce(max_work=max_work, max_off=max_off), strategy)


# ---------------------------------------------------------------------------
# RACE
# ---------------------------------------------------------------------------
RACES = {
    "golfers": lambda: golfers.SocialGolfers(8, 4, 5),
    "sudoku": lambda: sudoku.Sudoku(sudoku.PUZZLES["hard"]),
    "latin": lambda: latin_square.LatinSquare(6),
}


@app.get("/api/race/{name}")
def api_race(name: str, algo: str = "DFS"):
    if name not in RACES:
        raise HTTPException(404, "Unknown problem")
    stats, _ = run(RACES[name](), algo, 8, node_limit=2_000_000, trace=False)
    return stats_en(stats)


# ---------------------------------------------------------------------------
@app.middleware("http")
async def no_stale_cache(request, call_next):
    """Tell the browser to always check for the newest page files (no stale app.js after an update)."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("\n  Search Lab -> http://127.0.0.1:8000\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
