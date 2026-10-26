"""
4. SEARCH TREES - 8-Puzzle, Missionaries & Cannibals, Rotating Workforce Scheduling

Nje SEARCH TREE (peme kerkimi) ndertohet keshtu:
  - rrenja = gjendja fillestare
  - femijet e nje nyje = gjendjet qe arrihen me nje veprim (successor function)
  - nje nyje shenohet:
        GOAL      -> gjendje perfundimtare (zgjidhje)
        INVALID   -> shkel nje kufizim (p.sh. kanibalet i hane misionaret) -> nuk zgjerohet
        REPEATED  -> gjendja eshte pare me pare -> nuk zgjerohet (perndryshe pema behet e pafundme)
        NORMAL    -> zgjerohet me tej
Pema ndertohet me BFS (nivel pas niveli) ose DFS.
"""

from collections import deque

GOAL, INVALID, REPEATED, NORMAL, CUTOFF = "goal", "invalid", "repeated", "normal", "cutoff"


class TreeNode:
    def __init__(self, nid, parent, action, state, depth):
        self.id = nid
        self.parent = parent
        self.action = action
        self.state = state
        self.depth = depth
        self.kind = NORMAL
        self.children = []
        self.on_solution = False


def build_tree(problem, strategy="bfs", max_depth=50, max_nodes=500, stop_at_goal=True):
    """Ndertuesi i perbashket i pemes. `problem` ka: start, successors(s), is_goal(s), show(s)."""
    root = TreeNode(0, None, "start", problem.start, 0)
    nodes = [root]
    seen = {problem.start}
    frontier = deque([root])
    goal_node = None

    if problem.is_goal(root.state):
        root.kind = GOAL
        goal_node = root

    while frontier and not (goal_node and stop_at_goal):
        node = frontier.popleft() if strategy == "bfs" else frontier.pop()
        if node.depth >= max_depth:
            node.kind = CUTOFF
            continue
        children = []
        for action, child_state, valid in problem.successors(node.state):
            if len(nodes) >= max_nodes:
                break
            child = TreeNode(len(nodes), node, action, child_state, node.depth + 1)
            nodes.append(child)
            node.children.append(child)
            if not valid:
                child.kind = INVALID
            elif child_state in seen:
                child.kind = REPEATED
            else:
                seen.add(child_state)
                if problem.is_goal(child_state):
                    child.kind = GOAL
                    goal_node = goal_node or child
                else:
                    children.append(child)
        if strategy == "dfs":
            children.reverse()            # qe femija i pare te zgjerohet i pari
        frontier.extend(children)

    # shenojme rrugen e zgjidhjes (nga goal deri te rrenja)
    n = goal_node
    while n:
        n.on_solution = True
        n = n.parent
    return root, nodes, goal_node


def solution_path(goal_node):
    path = []
    while goal_node:
        path.append(goal_node)
        goal_node = goal_node.parent
    return path[::-1]


ICONS = {GOAL: " [GOAL]", INVALID: " [X invalid]", REPEATED: " [perseritur]", CUTOFF: " [kufi]", NORMAL: ""}


def print_tree(problem, root, max_lines=400):
    lines = []

    def rec(node, prefix, last):
        if len(lines) >= max_lines:
            return
        star = "*" if node.on_solution else " "
        branch = "" if node.parent is None else ("`-- " if last else "|-- ")
        action = "" if node.parent is None else f"{node.action}: "
        lines.append(f"{star} {prefix}{branch}{action}{problem.show(node.state)}{ICONS[node.kind]}")
        ext = "" if node.parent is None else ("    " if last else "|   ")
        for i, ch in enumerate(node.children):
            rec(ch, prefix + ext, i == len(node.children) - 1)

    rec(root, "", True)
    print("\n".join(lines))
    if len(lines) >= max_lines:
        print("  ... (pema vazhdon)")


def tree_to_json(problem, nodes):
    return [{"id": n.id, "parent": n.parent.id if n.parent else None, "action": n.action,
             "state": problem.show(n.state), "grid": problem.grid(n.state) if hasattr(problem, "grid") else None,
             "kind": n.kind, "sol": n.on_solution, "depth": n.depth} for n in nodes]


# ===========================================================================
# 8-PUZZLE
#   Gjendja : tuple me 9 numra (0 = vendi bosh), rresht pas rreshti
#   Veprimet: levizja e vendit bosh LART / POSHTE / MAJTAS / DJATHTAS
#   Goal    : 1 2 3 / 4 5 6 / 7 8 _
# ===========================================================================
class EightPuzzle:
    name = "8-Puzzle"
    GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 0)
    MOVES = [("LART", -3), ("POSHTE", 3), ("MAJTAS", -1), ("DJATHTAS", 1)]

    def __init__(self, start=(1, 2, 3, 0, 4, 6, 7, 5, 8)):
        self.start = tuple(start)

    def is_goal(self, s):
        return s == self.GOAL_STATE

    def successors(self, s):
        z = s.index(0)
        r, c = divmod(z, 3)
        for name, d in self.MOVES:
            if (name == "LART" and r == 0) or (name == "POSHTE" and r == 2) or \
               (name == "MAJTAS" and c == 0) or (name == "DJATHTAS" and c == 2):
                continue                     # levizje jashte tabeles: nuk ekziston
            t = list(s)
            t[z], t[z + d] = t[z + d], t[z]
            yield name, tuple(t), True

    def show(self, s):
        return "/".join("".join(str(v) if v else "_" for v in s[i:i + 3]) for i in (0, 3, 6))

    def grid(self, s):
        return [list(s[i:i + 3]) for i in (0, 3, 6)]

    @staticmethod
    def is_solvable(s):
        """Gjysma e gjendjeve te 8-puzzle NUK arrijne dot goal-in (paritet i inversioneve)."""
        v = [x for x in s if x]
        inv = sum(1 for i in range(len(v)) for j in range(i + 1, len(v)) if v[i] > v[j])
        return inv % 2 == 0


# ===========================================================================
# MISSIONARIES AND CANNIBALS
#   Gjendja : (M, C, B) = misionare dhe kanibale ne bregun e MAJTE, B = 1 nese varka eshte majtas
#   Veprimet: varka merr (1M), (2M), (1C), (2C), (1M+1C) dhe kalon lumin
#   Kufizimi: ne asnje breg kanibalet s'mund te jene me shume se misionaret (nese ka misionare)
#   Goal    : (0, 0, 0) - te gjithe ne bregun e djathte
# ===========================================================================
class MissionariesCannibals:
    name = "Missionaries & Cannibals"
    LOADS = [(1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]

    def __init__(self, m=3, c=3, boat=2):
        self.M, self.C = m, c
        self.loads = [(a, b) for a, b in self.LOADS if 1 <= a + b <= boat]
        self.start = (m, c, 1)

    def is_goal(self, s):
        return s == (0, 0, 0)

    def is_safe(self, m, c):
        left_ok = m == 0 or m >= c
        right_ok = (self.M - m) == 0 or (self.M - m) >= (self.C - c)
        return left_ok and right_ok

    def successors(self, s):
        m, c, b = s
        sign = -1 if b == 1 else 1           # varka majtas -> njerezit ikin nga e majta
        for dm, dc in self.loads:
            nm, nc = m + sign * dm, c + sign * dc
            if not (0 <= nm <= self.M and 0 <= nc <= self.C):
                continue                     # s'ka aq njerez ne ate breg: veprimi s'ekziston
            action = f"{dm}M{dc}C {'->' if b == 1 else '<-'}"
            yield action, (nm, nc, 1 - b), self.is_safe(nm, nc)

    def show(self, s):
        m, c, b = s
        boat_l, boat_r = ("[B]", "   ") if b else ("   ", "[B]")
        return f"{m}M{c}C {boat_l}~~{boat_r} {self.M - m}M{self.C - c}C"


# ===========================================================================
# ROTATING WORKFORCE SCHEDULING (RWS)
#   Instance e vogel (e percaktuar nga ne, sepse detyra s'jep te dhena):
#     3 punetore, java 7-ditore, nderrime: D (dite), N (nate), - (pushim)
#     Kerkesa per cdo dite: 1 D, 1 N, 1 pushim  (pra cdo dite: nje permutacion i {D, N, -})
#   "Rotating": orari ka 3 rreshta (java 1, 2, 3). Punetori 1 nis me rreshtin 1,
#     punetori 2 me rreshtin 2, ... dhe cdo jave kalojne ne rreshtin tjeter (ciklikisht).
#     Pra 21 ditet lexohen si nje varg i vetem ciklik: rreshti1 + rreshti2 + rreshti3 + (perseri rreshti1)
#   Kufizimet (rregulla te punes):
#     R1. Pas nderrimit te NATES nuk lejohet nderrimi i DITES (duhet pushim).
#     R2. Jo me shume se 4 dite pune radhazi.
#     R3. Jo me shume se 2 dite pushim radhazi.
#   Gjendja : tuple me kolonat e caktuara deri tani; nje kolone = (nderrimi i rreshtit 1, 2, 3)
#   Veprimi : cakto diten e radhes (6 permutacione te mundshme)
#   Goal    : te 7 ditet te caktuara + kufizimet ciklike te plotesuara
# ===========================================================================
class RotatingWorkforce:
    name = "Rotating Workforce Scheduling"
    COLUMNS = [("D", "N", "-"), ("D", "-", "N"), ("N", "D", "-"),
               ("N", "-", "D"), ("-", "D", "N"), ("-", "N", "D")]
    DAYS = ["Hen", "Mar", "Mer", "Enj", "Pre", "Sht", "Die"]

    def __init__(self, workers=3, days=7, max_work=4, max_off=2):
        self.workers, self.days = workers, days
        self.max_work, self.max_off = max_work, max_off
        self.start = ()

    def sequence(self, s):
        """Vargu i plote (21 dite) i nje punetori: rreshti 1, pastaj 2, pastaj 3."""
        return [s[d][r] for r in range(self.workers) for d in range(len(s))]

    def valid(self, s, complete):
        rows = [[col[r] for col in s] for r in range(self.workers)]
        if complete:
            seq = [x for row in rows for x in row]
            seqs = [seq + seq[:self.max_work + 1]]    # ciklik: fundi lidhet me fillimin
        else:
            seqs = rows                              # vetem brenda cdo rreshti (javet ende s'jane mbyllur)
        for q in seqs:
            for a, b in zip(q, q[1:]):
                if a == "N" and b == "D":            # R1
                    return False
            work = off = 0
            for x in q:
                work = work + 1 if x != "-" else 0
                off = off + 1 if x == "-" else 0
                if work > self.max_work or off > self.max_off:   # R2, R3
                    return False
        return True

    def is_goal(self, s):
        return len(s) == self.days and self.valid(s, complete=True)

    def successors(self, s):
        if len(s) == self.days:
            return
        for col in self.COLUMNS:
            t = s + (col,)
            complete = len(t) == self.days
            yield f"{self.DAYS[len(s)]}={''.join(col)}", t, self.valid(t, complete)

    def show(self, s):
        if not s:
            return "(empty)"
        return " | ".join("".join(col[r] for col in s) for r in range(self.workers))

    def grid(self, s):
        return [[col[r] for col in s] for r in range(self.workers)]
