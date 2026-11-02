# Search Lab: Uninformed Search Techniques

Assignment 1. Three search problems, three algorithms and **one shared search engine**.
Problem 4 (Search Trees) is delivered as a PDF in [Search_Trees_PDF/](Search_Trees_PDF/).

**Live demo:** https://ai-first-assignment.onrender.com/#sudoku (the free server sleeps when unused; the first visit may take up to a minute)

## How to run

### Web app (FastAPI), the main way
```bash
pip install -r requirements.txt
python server.py               # open http://127.0.0.1:8000
```
Every algorithm runs **live** on the server. The page replays the search step by step on the board
(Sudoku, Latin Square, the Golfers schedule), together with a depth chart and optional sound.
The overview page has a **requirements matrix**: every requirement of the assignment links to the section that fulfils it.

| Endpoint | What it does |
|---|---|
| `GET /api/golfers?g=8&p=4&w=6&restarts=false` | DFS for SGP(g, p, w) |
| `GET /api/golfers/landscape?g=8&p=4&w=10` | Golfers landscape |
| `POST /api/sudoku` `{"level": "hard", "algo": "BFS"}` or `{"puzzle": "81 digits"}` | Sudoku solver |
| `GET /api/latin?n=5&algo=IDDFS` | Latin Square |
| `GET /api/race/{golfers,sudoku,latin}?algo=DFS` | algorithm race |

Automatic API documentation: `http://127.0.0.1:8000/docs`

### From the terminal
```bash
python main.py                 # interactive menu
python main.py golfers         # 32 players: "How many weeks?"
python main.py golfers 8 4 6   # Is g=8, p=4, w=6 possible?
python main.py sudoku          # Easy, Medium, Hard
python main.py sudoku hard     # one level (or 81 digits, 0 = empty)
python main.py latin 5         # Latin square with n = 5
python main.py race            # race: DFS vs BFS vs IDDFS
```

The algorithms only need Python 3.10 or newer. FastAPI is only needed for the web server.

## Project structure

| File | Contents |
|---|---|
| [engine.py](engine.py) | The engine: `Problem`, **DFS**, **BFS**, **IDDFS**, statistics |
| [golfers.py](golfers.py) | 1. Social Golfers (DFS + Backtracking) |
| [sudoku.py](sudoku.py) | 2. Sudoku (BFS + Backtracking), 3 levels + 1 bonus |
| [latin_square.py](latin_square.py) | 3. Latin Square (IDDFS + Backtracking) |
| [landscape.py](landscape.py) | Landscape computation (size + distribution of f) |
| [main.py](main.py) | Command-line program |
| [server.py](server.py) | FastAPI server (API + web page) |
| [static/](static/) | The live web app: `index.html`, `app.js` (logic), `style.css` + `visuals.css` + `polish.css` (design), `polish.js` (animations) |
| [Search_Trees_PDF/](Search_Trees_PDF/) | 4. Search Trees, drawn step by step (PDF) |

## Key idea: one engine for every problem

Every problem is described with the same parts:

| Part | Meaning |
|---|---|
| **Variables** | What we have to decide |
| **Domain** | The values a variable can take |
| **Constraints** | The rules that must not be broken |
| **Objective function** | `f(s)` = number of violations. **f(s) = 0 ⇔ s is a solution** |

The algorithms in `engine.py` **do not know** which problem they are solving. They only call:
`next_variable` (which variable comes next), `values` (which values are still allowed), `assign` / `unassign`.

**Backtracking** means: when a variable has no allowed value left, the branch is abandoned.
- In **DFS** and **IDDFS**: we undo the last decision (`unassign`) and try the next value.
- In **BFS**: a state with no way forward is dropped from the queue and never expanded. Values that break a constraint are never put in the queue.

Every solution found is **verified** with the objective function: the program prints `f(s) = 0`.

---

## 1. Social Golfers Problem (DFS + Backtracking)

### Model and representation
General case: `g` groups, `p` players per group, `w` weeks, `n = g·p`.

- **Variables:** `X(j, k, s)` = the player in week *j*, group *k*, seat *s*. In total `w·g·p` variables (for 8×4×10: 320).
- **Domain:** `{0, 1, …, n−1}`
- **Constraints:**
  - C1: in one week, every player plays exactly once.
  - C2: two players meet at most **once** over all weeks.
- **Symmetry breaking** (does not change the answer, only shortens the search):
  - S1: week 1 is fixed, **exactly as in the assignment's example**.
  - S2: inside a group, players are in increasing order (`{1,5,9,13}` = `{13,9,5,1}`).
  - S3: a group starts with the smallest player who has not played yet that week (the order of groups does not matter).
  - S4: weeks are ordered by player 0's second partner (the order of weeks does not matter).
- **Forward checking:** after every assignment we check whether every free player still has at least `p−1` partners they have not met. If not, the branch is cut **immediately**, without waiting to get stuck further down.
- **Representation in code:** sets are stored as **bitmasks** (an integer where bit *i* = player *i*). The check "have they met?" is a single operation.

**Note on the example:** in the assignment's table, "Week 1" sits in the "Group 1" column, so the groups are shifted one column and Group 8 is empty. The missing players are exactly 16, 17, 18, 19, so Group 8 = {16, 17, 18, 19}.

### Objective function
```
f(s) = Σ_{every pair (a,b)} max(0, meetings(a,b) − 1)  +  Σ_{every week} (repeated players)
f(s) = 0  ⇔  the schedule is valid
```

### The answer: how many weeks?
Each week a player meets `p − 1 = 3` new players. In total there are `n − 1 = 31` to meet. So:

```
w ≤ ⌊(n − 1) / (p − 1)⌋ = ⌊31 / 3⌋ = 10 weeks
```

| Method | Weeks found for 32 players |
|---|---|
| Theoretical bound | **10** |
| DFS + Backtracking (deterministic) | **6** (≈ 20 s, 2 million nodes) |
| DFS with random restarts | **7** (≈ 1 min) |

According to the literature (CSPLib, problem 10), a 10-week solution exists, but it was only found in 2004 with specialised constructive methods. Blind search slows down because very few free pairs are left in the last weeks.

**DFS with restarts:** plain DFS gets stuck early in a bad branch and never gets out. We stop it after 20,000 nodes and start again with a different value order. It is still DFS + Backtracking, with no heuristic.

**The bound is not always reachable:** for 12 players (4 groups × 3) the bound is ⌊11/2⌋ = 5. DFS explores the **whole** tree and **proves** that 5 weeks are impossible (`python main.py golfers 4 3 5`). The maximum is 4.

### Landscape (32 players, 10 weeks)
| Space | Size |
|---|---|
| No constraints: 32^320 | ≈ 10^482 |
| Each week a permutation (C1): (32!)^10 | ≈ 10^354 |
| Each week a partition into groups: P^10, where P = 32! / ((4!)^8 · 8!) | ≈ 10^198 |
| Week 1 fixed: P^9 | ≈ 10^178 |

Out of 2,000 random schedules, **none** has f = 0. Solutions are "a needle in a haystack".

---

## 2. Sudoku Solver (BFS + Backtracking)

### Model and representation
- **Variables:** `X(r, c)` for every **empty** cell.
- **Domain:** `{1, …, 9}`
- **Constraints:** AllDifferent in every row, column and 3×3 box (27 constraints). The given numbers never change.
- **State:** a list of 81 numbers, 0 = empty. The next variable is the first empty cell (fixed, uninformed order).
- **Link to Problem 3:** a solved Sudoku **is** a 9×9 Latin square with an extra constraint for the boxes.

### Objective function
```
f(s) = Σ_{27 units} (9 − number of distinct values in the unit)
f(s) = 0  ⇔  the Sudoku is solved
```

### The three levels
The level is **measured** by the work BFS needs. Every puzzle was checked to have **exactly one** solution.

| Level | Empty cells | BFS nodes | States in memory (max) | Time |
|---|---|---|---|---|
| Easy | 45 | 68 | 5 | 0.00 s |
| Medium | 51 | 4,631 | 738 | 0.01 s |
| Hard | 60 | 364,345 | 33,031 | ≈ 1 s |
| Extreme (bonus: Arto Inkala, 2012) | 61 | 2,068,780 | 356,812 | ≈ 6 s |

### Landscape
| Level | No constraints 9^empty | After removing values that clash with the givens | Solutions |
|---|---|---|---|
| Easy | 10^42.9 | 10^11.1 | 1 |
| Medium | 10^48.7 | 10^22.6 | 1 |
| Hard | 10^57.3 | 10^35.8 | 1 |

### Why BFS "with backtracking"?
Classic BFS does not go back, because it keeps every branch in the queue (FIFO) at the same time. Here backtracking happens in two places:
1. A value that breaks a constraint is **never put** in the queue (pruning).
2. A state whose next variable has **no** allowed value is dropped. It is a dead end and is counted as a backtrack.

The cost of BFS is **memory**: on the Extreme Sudoku it holds 356,812 partial Sudokus at once, while DFS holds only 61 (one per level).

---

## 3. Latin Square (IDDFS + Backtracking)

### Model and representation
- **Variables:** `X(r, c)` for every cell, n² variables.
- **Domain:** `{1, …, n}`
- **Constraints:** AllDifferent in every row and every column.
- **Symmetry breaking:** first row = 1 2 … n (as in the assignment's example), first column = 1 2 … n. Every Latin square can be brought into this form by relabelling the numbers and reordering the rows, so no solution is lost.

### Objective function
```
f(s) = Σ_{rows} (n − distinct values) + Σ_{columns} (n − distinct values)
f(s) = 0  ⇔  s is a Latin square
```

### IDDFS
DFS with a depth limit `L = 0, 1, 2, …`. Every iteration starts again from the root.
- Memory: like DFS, `O(depth)`.
- Guarantee: like BFS, it finds the shallowest solution.
- Cost: the upper levels are revisited in every iteration.

| n | IDDFS nodes | Iterations | Time |
|---|---|---|---|
| 4 | 151 | 10 | 0.00 s |
| 5 | 4,897 | 17 | 0.01 s |
| 6 | 1,194,051 | 26 | ≈ 2.6 s |

**Finding from the experiments:** for Latin squares **all** solutions sit at the deepest level (every cell filled). For every limit `L` before that, IDDFS explores the **whole** tree up to `L`, while the last iteration is just DFS. For n = 6, DFS needs 51 nodes and IDDFS 1.2 million. Without symmetry breaking, IDDFS cannot even solve n = 5 within 20 seconds. For n ≥ 7 the program explains this and shows the solution of the last iteration (DFS).

IDDFS shines when the solution is **shallow** and its depth is unknown, e.g. in the 8-Puzzle.

**Comparison without search:** `L[r][c] = ((c − r) mod n) + 1` gives **exactly** the output of the assignment's example.

**Note on the example:** in the assignment's Markdown the output starts with ` ```1 2 3 4 5 `, so the first row is read as the code block's language name and is not displayed. The full output for n = 5 has 5 rows, starting with `1 2 3 4 5`.

### Landscape (n = 5)
| Space | Size |
|---|---|
| No constraints: 5^25 | ≈ 10^17.5 |
| Every row a permutation: (5!)^5 | ≈ 10^10.4 |
| Latin squares (solutions): 161,280 | ≈ 10^5.2 |

The exact number of Latin squares by n (OEIS A002860): 1, 2, 12, 576, 161,280, 812,851,200, … For n ≤ 4 the program counts them itself (`latin_square.count_all(4)` = 576).

---

## 4. Search Trees

The three search trees are delivered as PDF files in [Search_Trees_PDF/](Search_Trees_PDF/):
`Search_Trees.pdf` (all three) and one file per problem. Each PDF shows the formulation,
the tree level by level, the full tree and the solution path. Every node is marked as
goal, invalid (breaks a constraint, not expanded) or repeated (seen before, not expanded).

### 8-Puzzle (BFS)
- **State:** a 3×3 board, 0 = the blank. **Actions:** move the blank UP, DOWN, LEFT, RIGHT.
- **Goal:** `123/456/78_`. From `123/_46/758` the solution takes 3 moves. The tree has 24 nodes.
- Fact: half of all 8-Puzzle states can never reach the goal (inversion parity).

### Missionaries and Cannibals (BFS)
- **State:** `(M, C, B)` = missionaries and cannibals on the left bank, B = where the boat is.
- **Actions:** the boat carries 1M, 2M, 1C, 2C or 1M+1C.
- **Constraint:** on no bank may cannibals outnumber missionaries (when there are missionaries).
- The full tree has 47 nodes. The solution takes **11 crossings**.

### Rotating Workforce Scheduling (DFS)
The assignment gives no data, so we defined a small instance ourselves:
- 3 workers, 7 days, shifts **D** (day), **N** (night), **-** (day off).
- Every day needs 1 D, 1 N and 1 day off.
- *Rotating:* the roster has 3 rows. Worker 1 starts on row 1 and moves to the next row every week, so the 21 days are read as one cyclic sequence.
- **Rules:** N is never followed by D · at most 4 work days in a row · at most 2 days off in a row.
- **State:** the days assigned so far. **Action:** assign the next day (6 ways).

---

## Algorithm race (`python main.py race`)

| Problem | DFS | BFS | IDDFS |
|---|---|---|---|
| Golfers 8×4, 5 weeks | ✔ 5,713 nodes, 0.06 s | ✖ memory: 600 thousand states | ✖ revisits |
| Sudoku Hard | ✔ 304,053 nodes | ✔ 364,345 nodes, 33 thousand in memory | ✖ > 2 million nodes |
| Latin Square n = 6 | ✔ 51 nodes | ✔ 172,914 nodes | ✔ 1,194,051 nodes |

**Conclusion:**
- **DFS** uses little memory and reaches the bottom fast, but it can get stuck in a bad branch.
- **BFS** finds the shallowest solution, but pays for it with a lot of memory.
- **IDDFS** has the memory of DFS and the guarantee of BFS, but repeats the upper levels. It is only worth it when the solution is shallow.

## The web app (`static/`)
- **Requirements matrix** on the overview page, linking every requirement to its section.
- **Model and representation** as interactive boards: hover a cell to see its variable, domain and constraints.
- **Objective function:** a live f(s) meter; conflicts light up in red.
- **Landscape:** a powers-of-ten ruler, the "haystack" of random states and the histogram of f(s).
- **Live algorithm:** a player that replays the search on the board, with a depth chart. DFS draws a sawtooth, BFS a staircase, IDDFS several sawtooths (one per iteration).
- **Golfers:** a ring graph of the players, the 32×32 meeting matrix and the schedule with your **class names**.
- **Race** between the three algorithms.
