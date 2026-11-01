"""
Generates PDFs of the search trees, step by step.

    python make_trees_pdf.py

The output is saved in the folder  Search_Trees_PDF/ :
    Search_Trees.pdf                     -> all three trees in one file
    1_8-Puzzle.pdf, 2_Missionaries_Cannibals.pdf, 3_Rotating_Workforce.pdf

The trees come directly from search_trees.py (the same algorithm as the program).
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle

import search_trees as st

OUT = "Search_Trees_PDF"
PAGE = (11.69, 8.27)          # A4 horizontal (inch)
COL = {"goal": ("#dff3e6", "#1d8a50"), "invalid": ("#fae4e1", "#c7362b"),
       "repeated": ("#efece3", "#8a877d"), "normal": ("#ffffff", "#2f55c9"), "cutoff": ("#f9eedb", "#b07116")}
NEW = "#fff4c2"               # colour of the nodes added in the current step
KIND_SQ = {"goal": "GOAL", "invalid": "e pavlefshme", "repeated": "e përsëritur", "normal": "zgjerohet", "cutoff": "kufi"}


# ---------------------------------------------------------------------------
# Tree layout: leaves get x in order, a parent sits in the middle of its children
# ---------------------------------------------------------------------------
def layout(root):
    pos, leaf = {}, [0]

    def rec(n):
        if not n.children:
            pos[n.id] = (leaf[0], n.depth)
            leaf[0] += 1
        else:
            for c in n.children:
                rec(c)
            xs = [pos[c.id][0] for c in n.children]
            pos[n.id] = ((xs[0] + xs[-1]) / 2, n.depth)

    rec(root)
    return pos, leaf[0]


# ---------------------------------------------------------------------------
# Drawing the state inside a node, for each problem
# ---------------------------------------------------------------------------
def draw_puzzle(ax, s, x, y, w, h):
    cx, cy = w / 3.3, h / 3.3                      # size of one cell (x and y)
    for i, v in enumerate(s):
        r, k = divmod(i, 3)
        if v:
            px, py = x + (k - 1) * cx, y + (r - 1) * cy   # the y axis is inverted: r = 0 at the top
            ax.add_patch(Rectangle((px - cx * .44, py - cy * .44), cx * .88, cy * .88,
                                   facecolor="#e5ebfa", edgecolor="none", zorder=4))
            ax.text(px, py, str(v), ha="center", va="center",
                    fontsize=9 * SCALE[0], fontweight="bold", zorder=5, family="monospace")


def draw_mc(ax, s, x, y, w, h, prob):
    m, c, b = s
    ax.text(x, y - h * .17, f"({m},{c},{'L' if b else 'R'})", ha="center", va="center", fontsize=8.5 * SCALE[0],
            fontweight="bold", zorder=5, family="monospace")
    ax.text(x, y + h * .22, f"{m}M{c}C|{prob.M - m}M{prob.C - c}C", ha="center", va="center", fontsize=6.5 * SCALE[0],
            zorder=5, family="monospace", color="#555")


def draw_rws(ax, s, x, y, w, h):
    if not s:
        ax.text(x, y, "∅", ha="center", va="center", fontsize=12 * SCALE[0], zorder=5)
        return
    rows = ["".join(col[r] for col in s) for r in range(3)]
    for r, row in enumerate(rows):
        ax.text(x, y + (r - 1) * h * .28, row.replace("-", "·"), ha="center", va="center",
                fontsize=8 * SCALE[0], zorder=5, family="monospace")


SCALE = [1.0]   # set for each tree according to its width


def fs(size, k):
    """Font size based on the node size (in plot units)."""
    return max(3.5, min(11, size * k))


# ---------------------------------------------------------------------------
# One page with the tree up to depth `upto`
# ---------------------------------------------------------------------------
def tree_page(pdf, prob, nodes, root, title, subtitle, upto=None, final=False, drawer=None):
    pos, leaves = layout(root)
    maxd = max(n.depth for n in nodes)
    SCALE[0] = max(0.45, min(1.0, 16 / max(leaves, 1)))
    fig = plt.figure(figsize=PAGE)
    ax = fig.add_axes([0.03, 0.08, 0.94, 0.8])
    ax.set_xlim(-0.8, leaves - 0.2)
    ax.set_ylim(maxd + 0.7, -0.7)
    ax.axis("off")
    fig.text(0.03, 0.95, title, fontsize=17, fontweight="bold", family="serif")
    fig.text(0.03, 0.915, subtitle, fontsize=10, color="#555")

    # node size in plot units
    w = min(0.86, max(0.5, 0.86))
    h = min(0.62, 0.62)
    show = [n for n in nodes if upto is None or n.depth <= upto]
    ids = {n.id for n in show}

    for n in show:
        if n.parent is not None and n.parent.id in ids:
            x1, y1 = pos[n.parent.id]
            x2, y2 = pos[n.id]
            on = final and n.on_solution
            ax.plot([x1, x2], [y1 + h / 2, y2 - h / 2], color="#1d8a50" if on else "#b9b5a8",
                    lw=2.6 if on else .8, zorder=1)
            if leaves <= 20 or (final and n.on_solution):
                ax.text((x1 + x2) / 2, (y1 + y2) / 2, n.action, fontsize=7 * max(SCALE[0], .75), color="#2f55c9",
                        ha="center", va="center", zorder=3,
                        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=.85))

    for n in show:
        x, y = pos[n.id]
        fill, edge = COL[n.kind]
        is_new = upto is not None and n.depth == upto and not final
        if is_new:
            fill = NEW
        if final and n.on_solution:
            edge = "#1d8a50"
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    facecolor=fill, edgecolor=edge, lw=2.2 if (final and n.on_solution) else 1.1,
                                    linestyle="--" if n.kind == "repeated" else "-", zorder=2))
        drawer(ax, n.state, x, y, w, h)
        if n.kind == "invalid":
            ax.plot([x - w / 2 + .05, x + w / 2 - .05], [y - h / 2 + .05, y + h / 2 - .05], color="#c7362b", lw=1.3, zorder=6)
        # node number = creation order
        ax.text(x - w / 2, y - h / 2 - .02, str(n.id), fontsize=6.5 * max(SCALE[0], .7), color="#777", ha="left", va="bottom", zorder=6)

    legend(fig)
    pdf.savefig(fig)
    plt.close(fig)


def legend(fig):
    items = [("normal", "zgjerohet"), ("goal", "GOAL (qëllimi)"), ("invalid", "e pavlefshme ✕"), ("repeated", "e përsëritur (- - -)")]
    x = 0.03
    for kind, text in items:
        fill, edge = COL[kind]
        fig.patches.append(FancyBboxPatch((x, 0.025), 0.018, 0.022, boxstyle="round,pad=0.002", transform=fig.transFigure,
                                          facecolor=fill, edgecolor=edge, linestyle="--" if kind == "repeated" else "-"))
        fig.text(x + 0.023, 0.036, text, fontsize=8.5, va="center")
        x += 0.15
    fig.patches.append(FancyBboxPatch((x, 0.025), 0.018, 0.022, boxstyle="round,pad=0.002", transform=fig.transFigure,
                                      facecolor=NEW, edgecolor="#999"))
    fig.text(x + 0.023, 0.036, "nyje e re në këtë hap", fontsize=8.5, va="center")
    fig.text(0.97, 0.036, "numri te nyja = rendi i krijimit", fontsize=8.5, va="center", ha="right", color="#777")


# ---------------------------------------------------------------------------
# The formulation page and the solution path page
# ---------------------------------------------------------------------------
def text_page(pdf, title, lines):
    fig = plt.figure(figsize=PAGE)
    fig.text(0.06, 0.9, title, fontsize=24, fontweight="bold", family="serif")
    y = 0.8
    for head, body in lines:
        fig.text(0.06, y, head, fontsize=12.5, fontweight="bold", color="#2f55c9")
        for ln in body.split("\n"):
            y -= 0.045
            fig.text(0.08, y, ln, fontsize=12)
        y -= 0.06
    pdf.savefig(fig)
    plt.close(fig)


def path_page(pdf, prob, goal, title, drawer):
    path = st.solution_path(goal)
    SCALE[0] = 1.6
    fig = plt.figure(figsize=PAGE)
    fig.text(0.03, 0.93, title, fontsize=17, fontweight="bold", family="serif")
    fig.text(0.03, 0.895, f"Rruga nga gjendja fillestare deri te qëllimi: {len(path) - 1} hapa", fontsize=10.5, color="#555")
    per_row = 6
    rows = (len(path) + per_row - 1) // per_row
    ax = fig.add_axes([0.03, 0.06, 0.94, 0.8])
    ax.set_xlim(-0.6, per_row - 0.4)
    ax.set_ylim(rows * 1.6 - 0.4, -0.9)
    ax.axis("off")
    w, h = 0.86, 0.8
    for i, n in enumerate(path):
        r, c = divmod(i, per_row)
        x, y = c, r * 1.6
        fill, edge = COL["goal"] if i == len(path) - 1 else ("#ffffff", "#2f55c9")
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    facecolor=fill, edgecolor=edge, lw=1.4))
        drawer(ax, n.state, x, y, w, h)
        ax.text(x, y - h / 2 - .12, f"Hapi {i}" if i else "Fillimi", ha="center", fontsize=9.5, fontweight="bold")
        if i:
            ax.text(x, y + h / 2 + .16, n.action, ha="center", fontsize=9, color="#2f55c9", family="monospace")
        if c < per_row - 1 and i < len(path) - 1:
            ax.annotate("", xy=(x + .62, y), xytext=(x + .43, y), arrowprops=dict(arrowstyle="->", color="#888"))
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
PROBLEMS = [
    ("1_8-Puzzle", st.EightPuzzle(), "bfs", lambda p: (lambda ax, s, x, y, w, h: draw_puzzle(ax, s, x, y, w, h)), [
        ("Gjendja", "Tabela 3×3 me numrat 1–8 dhe një vend bosh (_)."),
        ("Gjendja fillestare", "1 2 3 / _ 4 6 / 7 5 8"),
        ("Veprimet", "Vendi bosh lëviz: LART, POSHTË, MAJTAS, DJATHTAS (lëvizjet jashtë tabelës nuk ekzistojnë)."),
        ("Qëllimi (Goal)", "1 2 3 / 4 5 6 / 7 8 _"),
        ("Ndërtimi i pemës", "BFS: nivel pas niveli. Gjendjet e para më parë shënohen 'e përsëritur' dhe nuk zgjerohen."),
    ]),
    ("2_Missionaries_Cannibals", st.MissionariesCannibals(), "bfs", lambda p: (lambda ax, s, x, y, w, h: draw_mc(ax, s, x, y, w, h, p)), [
        ("Gjendja", "(M, C, B): misionarë dhe kanibalë në bregun e majtë, B = ku është varka.\nNë nyje: 'majtas | djathtas', ◄B = varka majtas, B► = varka djathtas."),
        ("Gjendja fillestare", "(3, 3, majtas): të gjithë në bregun e majtë."),
        ("Veprimet", "Varka merr 1M, 2M, 1C, 2C ose 1M+1C dhe kalon lumin (→ ose ←)."),
        ("Kufizimi", "Në asnjë breg kanibalët nuk janë më shumë se misionarët (kur ka misionarë)."),
        ("Qëllimi (Goal)", "(0, 0, djathtas): të gjithë në bregun e djathtë."),
    ]),
    ("3_Rotating_Workforce", st.RotatingWorkforce(), "dfs", lambda p: (lambda ax, s, x, y, w, h: draw_rws(ax, s, x, y, w, h)), [
        ("Rasti (i përcaktuar nga ne)", "3 punëtorë, 7 ditë. Ndërrimet: D (ditë), N (natë), · (pushim).\nÇdo ditë: 1 D, 1 N dhe 1 pushim."),
        ("Rotating", "Orari ka 3 rreshta (java 1, 2, 3). Çdo javë punëtori kalon në rreshtin tjetër,\nprandaj 21 ditët formojnë një cikël."),
        ("Rregullat", "Pas N nuk vjen D · max 4 ditë pune radhazi · max 2 pushime radhazi."),
        ("Gjendja · Veprimi", "Ditët e caktuara deri tani (3 rreshta në nyje) · cakto ditën e radhës (6 mënyra)."),
        ("Ndërtimi i pemës", "DFS: ndalet te orari i parë i vlefshëm."),
    ]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    all_pdf = PdfPages(os.path.join(OUT, "Search_Trees.pdf"))
    for fname, prob, strategy, mk, info in PROBLEMS:
        root, nodes, goal = st.build_tree(prob, strategy=strategy, max_nodes=500)
        drawer = mk(prob)
        maxd = max(n.depth for n in nodes)
        one = PdfPages(os.path.join(OUT, fname + ".pdf"))
        for pdf in (one, all_pdf):
            text_page(pdf, f"Search Tree: {prob.name}", info + [
                ("Rezultati", f"{len(nodes)} nyje · zgjidhja në thellësinë {goal.depth if goal else '–'} · "
                              f"faqet në vijim e ndërtojnë pemën nivel pas niveli ({maxd + 1} hapa).")])
            for d in range(maxd + 1):
                cnt = sum(1 for n in nodes if n.depth == d)
                tree_page(pdf, prob, nodes, root, f"{prob.name}: hapi {d + 1} nga {maxd + 1}",
                          f"Niveli {d} ({cnt} nyje të reja, me të verdhë). Pema me {strategy.upper()}.",
                          upto=d, drawer=drawer)
            tree_page(pdf, prob, nodes, root, f"{prob.name}: pema e plotë",
                      "Rruga e zgjidhjes është e theksuar me të gjelbër.", final=True, drawer=drawer)
            if goal:
                path_page(pdf, prob, goal, f"{prob.name}: zgjidhja hap pas hapi", drawer)
        one.close()
        print(f"  {fname}.pdf  ({len(nodes)} nyje, {maxd + 1} nivele)")
    all_pdf.close()
    print(f"\nU ruajt ne folderin: {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
