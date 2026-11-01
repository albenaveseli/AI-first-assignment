"""
SEARCH LAB - Assignment 1: Uninformed Search Techniques (command-line program)

Usage:
    python main.py                      -> interactive menu
    python main.py golfers [g p w]      -> Social Golfers with DFS (default 8 4, asks "how many weeks?")
    python main.py sudoku [easy|medium|hard|extreme|<81 digits>]
    python main.py latin [n]
    python main.py race                 -> race DFS vs BFS vs IDDFS on all three problems
"""

import sys

import golfers
import landscape
import latin_square
import sudoku
from engine import bfs, dfs, iddfs

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def title(text):
    print("\n" + "=" * 78)
    print("  " + text)
    print("=" * 78)


def section(text):
    print(f"\n--- {text} " + "-" * max(0, 72 - len(text)))


# ---------------------------------------------------------------------------
def run_golfers(g=8, p=4, w=None, time_limit=60):
    title(f"1. SOCIAL GOLFERS  (g={g} grupe x p={p} lojtare = {g * p} lojtare)  -  DFS + Backtracking")
    print(golfers.__doc__)
    ub = golfers.upper_bound(g, p)

    section("Pergjigjja teorike: sa java?")
    print(f"  Nje lojtar takon {p - 1} te rinj ne jave dhe gjithsej ka {g * p - 1} per te takuar.")
    print(f"  => w <= floor({g * p - 1}/{p - 1}) = {ub} java (kufiri i siperm)")

    section("Landscape")
    landscape.print_sizes(golfers.landscape_sizes(g, p, w or min(ub, 10)))
    landscape.print_histogram(landscape.sample_objective(golfers.SocialGolfers(g, p, w or min(ub, 10)), 2000))

    if w:
        section(f"A eshte e mundur per w = {w}?  (DFS, kufi kohe {time_limit}s)")
        prob = golfers.SocialGolfers(g, p, w)
        stats = dfs(prob, time_limit=time_limit)
        print(" ", stats)
        if stats.status == "zgjidhje":
            print("  PO. Orari:")
            print(golfers.to_text(prob, stats.solution))
            print(f"  Verifikim: f(s) = {prob.objective(stats.solution)}")
        elif stats.status == "pa zgjidhje":
            print(f"  JO. DFS e eksploroi te gjithe pemen: nuk ekziston orar per {w} java.")
        else:
            print("  E PANJOHUR: DFS nuk perfundoi brenda kohes (hapesira eshte shume e madhe).")
        return

    section(f"Sa java gjen DFS? (provon w = 1, 2, ...; {time_limit}s per secilen)")
    best, _ = golfers.max_weeks(g, p, time_per_w=time_limit)
    if best:
        wb, prob, stats = best
        print(f"\n  DFS gjeti orar te vlefshem per {wb} java (f = {prob.objective(stats.solution)}):")
        print(golfers.to_text(prob, stats.solution))
        if wb < ub:
            print(f"\n  Kufiri teorik eshte {ub}. Kerkimi i verber ngadalesohet shume ne javet e fundit,")
            print("  sepse ciftet e lira mbeten pak dhe DFS kthehet mbrapa shume here.")
            section(f"DFS me rinisje te rastesishme: provojme w = {wb + 1} ({4 * time_limit}s)")
            prob, stats = golfers.dfs_with_restarts(g, p, wb + 1, time_limit=4 * time_limit)
            if stats and stats.status == "zgjidhje":
                print(golfers.to_text(prob, stats.solution))
                print(f"  Verifikim: f(s) = {prob.objective(stats.solution)}")


# ---------------------------------------------------------------------------
def run_sudoku(level="medium", time_limit=60):
    puzzle = sudoku.PUZZLES.get(level, level)
    name = level if level in sudoku.PUZZLES else "i dhene nga perdoruesi"
    title(f"2. SUDOKU ({name})  -  BFS + Backtracking")
    print(sudoku.__doc__)
    try:
        prob = sudoku.Sudoku(puzzle)
    except ValueError:
        print("  Sudoku duhet te kete saktesisht 81 shifra (0 = qelize bosh).")
        return
    if not prob.is_valid_start():
        print("  Sudoku i dhene ka konflikte qe ne fillim: nuk ka zgjidhje.")
        return
    print(sudoku.to_text(prob.puzzle))

    section("Landscape")
    landscape.print_sizes(sudoku.landscape_sizes(prob.puzzle))
    landscape.print_histogram(landscape.sample_objective(prob, 2000))

    section(f"BFS (kufi kohe {time_limit}s)")
    stats = bfs(prob, time_limit=time_limit)
    print(" ", stats)
    if stats.solution:
        print(sudoku.to_text(stats.solution))
        print(f"  Verifikim: f(s) = {prob.objective(stats.solution)}")


# ---------------------------------------------------------------------------
def run_latin(n=5, time_limit=20):
    title(f"3. LATIN SQUARE  n = {n}  -  IDDFS + Backtracking")
    print(latin_square.__doc__)

    section("Landscape")
    landscape.print_sizes(latin_square.landscape_sizes(n))
    landscape.print_histogram(landscape.sample_objective(latin_square.LatinSquare(n, symmetry=False), 2000))

    section(f"IDDFS (kufi kohe {time_limit}s)")
    prob = latin_square.LatinSquare(n)
    stats = iddfs(prob, time_limit=time_limit)
    print(" ", stats)
    if stats.solution:
        print(latin_square.to_text(stats.solution, n))
        print(f"  Verifikim: f(s) = {prob.objective(stats.solution)}")
    else:
        print("  IDDFS nuk perfundoi. Arsyeja: te gjitha zgjidhjet jane ne thellesine e fundit,")
        print("  prandaj cdo iteracion para saj eksploron TE GJITHA gjendjet e pjesshme.")
        print("  Iteracioni i fundit i IDDFS eshte thjesht DFS. Ja zgjidhja me DFS:")
        s2 = dfs(latin_square.LatinSquare(n), time_limit=time_limit)
        print(" ", s2)
        if s2.solution:
            print(latin_square.to_text(s2.solution, n))

    section("Krahasim: ndertimi ciklik pa kerkim, L[r][c] = ((c - r) mod n) + 1")
    print(latin_square.to_text(latin_square.cyclic_construction(n), n))


# ---------------------------------------------------------------------------
def run_race(time_limit=10):
    title("GARA E ALGORITMEVE: i njejti problem, tre algoritme")
    cases = [
        ("Social Golfers 8x4, 5 java", lambda: golfers.SocialGolfers(8, 4, 5)),
        ("Sudoku hard", lambda: sudoku.Sudoku(sudoku.PUZZLES["hard"])),
        ("Latin Square n=6", lambda: latin_square.LatinSquare(6)),
    ]
    for name, make in cases:
        section(name)
        for algo in (dfs, bfs, iddfs):
            print(" ", algo(make(), time_limit=time_limit, node_limit=3_000_000))
    print("\n  Memoria max: DFS/IDDFS = thellesia e stack-ut, BFS = madhesia e radhes.")


# ---------------------------------------------------------------------------
def menu():
    while True:
        print("""
  SEARCH LAB - Teknikat e Painformuara te Kerkimit
  1) Social Golfers (DFS)
  2) Sudoku (BFS)
  3) Latin Square (IDDFS)
  4) Gara e algoritmeve
  0) Dil""")
        ch = input("  Zgjedhja: ").strip()
        if ch == "1":
            g = int(input("  g (numri i grupeve) [8]: ") or 8)
            p = int(input("  p (lojtare per grup) [4]: ") or 4)
            w = input("  w (java; bosh = gjej maksimumin): ").strip()
            run_golfers(g, p, int(w) if w else None, time_limit=30)
        elif ch == "2":
            lvl = input("  Niveli (easy/medium/hard/extreme) ose 81 shifra: ").strip() or "easy"
            run_sudoku(lvl)
        elif ch == "3":
            run_latin(int(input("  n [5]: ") or 5))
        elif ch == "4":
            run_race()
        elif ch == "0":
            break


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        menu()
    elif args[0] == "golfers":
        nums = [int(a) for a in args[1:]]
        run_golfers(*(nums[:2] or [8, 4]), w=nums[2] if len(nums) > 2 else None, time_limit=30)
    elif args[0] == "sudoku":
        if len(args) > 1:
            run_sudoku(args[1])
        else:
            for lvl in ("easy", "medium", "hard"):
                run_sudoku(lvl)
    elif args[0] == "latin":
        run_latin(int(args[1]) if len(args) > 1 else 5)
    elif args[0] == "race":
        run_race()
    else:
        print(__doc__)
