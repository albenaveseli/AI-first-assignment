"""
Runs every problem and saves the results in web/data.js,
so that the static page web/index.html can show them (no server, opens directly in a browser).

    python export_web.py
"""

import json
import os

import golfers
import landscape
import latin_square
import search_trees
import sudoku
from engine import Tracer, bfs, dfs, iddfs

RACE_TIME = 8
RACE_NODES = 2_000_000


def race(make):
    out = []
    for algo in (dfs, bfs, iddfs):
        s = algo(make(), time_limit=RACE_TIME, node_limit=RACE_NODES)
        print("   ", s)
        out.append(s.as_dict())
    return out


def trace(algo, problem, limit=400):
    t = Tracer(limit)
    s = algo(problem, tracer=t, time_limit=10)
    return {"algorithm": s.algorithm, "nodes": t.nodes, "stats": s.as_dict()}


def sizes(rows):
    return [{"label": a, "log10": None if b is None else round(b, 2)} for a, b in rows]


def export_golfers():
    print("Social Golfers ...")
    g, p = 8, 4
    best, ub = golfers.max_weeks(g, p, time_per_w=25, verbose=True)
    wb, prob, stats = best
    plain_weeks = wb
    method = "DFS"
    print("   DFS me rinisje per", wb + 1, "java ...")
    rp, rs = golfers.dfs_with_restarts(g, p, wb + 1, time_limit=180)
    if rs and rs.status == "zgjidhje":
        wb, prob, stats, method = wb + 1, rp, rs, "DFS me rinisje te rastesishme"
    small = golfers.SocialGolfers(4, 3, 4)
    return {
        "g": g, "p": p, "upper_bound": ub, "weeks_found": wb, "plain_weeks": plain_weeks, "method": method,
        "schedule": prob.weeks_table(stats.solution),
        "objective": prob.objective(stats.solution),
        "stats": stats.as_dict(),
        "landscape": sizes(golfers.landscape_sizes(g, p, 10)),
        "histogram": landscape.sample_objective(golfers.SocialGolfers(g, p, 10), 2000),
        "race": race(lambda: golfers.SocialGolfers(8, 4, 5)),
        "trace": trace(dfs, small),
        "trace_title": "4 grupe x 3 lojtare, 4 java (12 lojtare)",
    }


def export_sudoku():
    print("Sudoku ...")
    levels = {}
    for lvl, pz in sudoku.PUZZLES.items():
        prob = sudoku.Sudoku(pz)
        s = bfs(prob, time_limit=60)
        print("   ", lvl, s)
        levels[lvl] = {
            "puzzle": prob.puzzle, "solution": s.solution, "stats": s.as_dict(),
            "empty": prob.puzzle.count(0),
            "landscape": sizes(sudoku.landscape_sizes(prob.puzzle)),
            "objective": prob.objective(s.solution) if s.solution else None,
        }
    return {
        "levels": levels,
        "histogram": landscape.sample_objective(sudoku.Sudoku(sudoku.PUZZLES["medium"]), 2000),
        "race": race(lambda: sudoku.Sudoku(sudoku.PUZZLES["hard"])),
        "trace": trace(bfs, sudoku.Sudoku(sudoku.PUZZLES["easy"])),
        "trace_title": "Sudoku easy me BFS",
    }


def export_latin():
    print("Latin Square ...")
    squares = {}
    for n in range(2, 7):
        prob = latin_square.LatinSquare(n)
        s = iddfs(prob, time_limit=30)
        print("   ", n, s)
        squares[n] = {"solution": s.solution, "stats": s.as_dict(),
                      "cyclic": latin_square.cyclic_construction(n),
                      "landscape": sizes(latin_square.landscape_sizes(n))}
    return {
        "squares": squares,
        "counts": {k: str(v) for k, v in latin_square.KNOWN_COUNTS.items()},
        "histogram": landscape.sample_objective(latin_square.LatinSquare(5, symmetry=False), 2000),
        "race": race(lambda: latin_square.LatinSquare(6)),
        "trace": trace(iddfs, latin_square.LatinSquare(4)),
        "trace_title": "Latin Square n=4 me IDDFS (cdo ngjyre = nje iteracion)",
    }


def export_trees():
    print("Search Trees ...")
    out = []
    for prob, strategy in [(search_trees.EightPuzzle(), "bfs"),
                           (search_trees.MissionariesCannibals(), "bfs"),
                           (search_trees.RotatingWorkforce(), "dfs")]:
        root, nodes, goal = search_trees.build_tree(prob, strategy=strategy, max_nodes=500)
        out.append({"name": prob.name, "strategy": strategy.upper(),
                    "nodes": search_trees.tree_to_json(prob, nodes),
                    "solution_length": goal.depth if goal else None})
    return out


def main():
    data = {
        "golfers": export_golfers(),
        "sudoku": export_sudoku(),
        "latin": export_latin(),
        "trees": export_trees(),
    }
    os.makedirs("web", exist_ok=True)
    with open(os.path.join("web", "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    print("\nU ruajt: web/data.js  ->  hap web/index.html ne browser")


if __name__ == "__main__":
    main()
