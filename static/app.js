"use strict";
/* =====================================================================
   SEARCH LAB - front end
   The page asks the server (FastAPI) and draws the results.
   A search trace is a list of nodes:
     [id, parent, label, depth, iteration, status, variable, value]
   ===================================================================== */

/* ---------------- helpers ---------------- */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
function h(tag, attrs = {}, html = "") {
  const e = document.createElement(tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (html) e.innerHTML = html;
  return e;
}
const fmt = n => n == null ? "–" : Number(n).toLocaleString("en-US");
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const WEEK = i => css(`--w${(((i % 10) + 10) % 10) + 1}`);
const NS = "http://www.w3.org/2000/svg";
const svgEl = (tag, attrs = {}) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const spin = text => `<p class="muted"><span class="spinner"></span> ${text}</p>`;
const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

async function api(url, body) {
  const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const r = await fetch(url, opt);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `Error ${r.status}`);
  return data;
}
function statusTag(s) {
  if (s === "solved") return `<span class="tag ok">✔ solved</span>`;
  if (s === "stopped") return `<span class="tag stop">⏱ stopped</span>`;
  return `<span class="tag no">✖ no solution</span>`;
}
function kpis(items) {
  return `<div class="kpis">${items.map(([v, l]) => `<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("")}</div>`;
}
function statKpis(st, extra = []) {
  return kpis([[statusTag(st.status), st.algorithm], [fmt(st.nodes), "nodes generated"], [fmt(st.backtracks), "backtracks"],
    [fmt(st.max_memory), st.algorithm === "BFS" ? "max queue size" : "max stack depth"],
    [st.seconds + " s", "time"], ...(st.algorithm === "IDDFS" ? [[st.iterations, "iterations"]] : []), ...extra]);
}
// mini grid as HTML (for small illustrations)
function miniCells(arr, cols, size = 14, color = v => v ? "var(--accent-soft)" : "var(--soft)", text = true) {
  return `<span style="display:inline-grid;grid-template-columns:repeat(${cols},${size}px);gap:2px">${arr.map(v =>
    `<span style="width:${size}px;height:${size}px;border-radius:3px;background:${color(v)};font:700 ${Math.round(size * .62)}px var(--mono);
      display:flex;align-items:center;justify-content:center;color:var(--ink)">${text && v ? v : ""}</span>`).join("")}</span>`;
}
function flow(el, steps) {
  el.innerHTML = steps.map((s, i) => (i ? `<div class="arrow">→</div>` : "") +
    `<div class="st ${s.goal ? "goal" : ""}"><div class="k">${s.k}</div><div class="vis">${s.vis}</div><div class="cap">${s.cap}</div></div>`).join("");
}

/* ---------------- theme ---------------- */
(function theme() {
  let t = null;
  try { t = localStorage.getItem("sl-theme"); } catch (e) {}
  if (t) document.documentElement.dataset.theme = t;
  $("#themeBtn").onclick = () => {
    const dark = document.documentElement.dataset.theme === "dark" ||
      (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("sl-theme", document.documentElement.dataset.theme); } catch (e) {}
  };
})();

/* ---------------- navigation ---------------- */
const PAGES = ["home", "golfers", "sudoku", "latin", "race"];
const ONSHOW = {}, SHOWN = {};
function go(page, anchor) {
  if (!PAGES.includes(page)) page = "home";
  $$(".page").forEach(p => p.classList.toggle("on", p.id === "page-" + page));
  $$("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.go === page));
  history.replaceState(null, "", "#" + page + (anchor ? "/" + anchor : ""));
  if (!SHOWN[page]) { SHOWN[page] = true; ONSHOW[page]?.(); }
  if (anchor) setTimeout(() => document.getElementById(anchor)?.scrollIntoView(), 40);
  else window.scrollTo(0, 0);
}
$$("[data-go]").forEach(b => b.onclick = () => go(b.dataset.go));
$$(".side").forEach(nav => {
  const page = nav.closest(".page").id.replace("page-", "");
  $$(".req[id]", nav.closest(".page")).forEach((sec, i) => {
    const a = h("a", { href: "#", class: "done" }, `<span class="n">${i + 1}</span>${$("h2", sec).textContent}`);
    a.onclick = e => { e.preventDefault(); go(page, sec.id); };
    nav.append(a);
  });
  nav.append(h("div", { class: "hint" }, "✔ = requirement fulfilled"));
});
fetch("/api/sudoku/levels").then(r => { if (r.ok) $("#apiDot").classList.add("ok"); }).catch(() => {});

/* =====================================================================
   OVERVIEW
   ===================================================================== */
(function matrix() {
  const cols = ["Model", "Representation", "Objective function", "Landscape", "Algorithm"];
  const rows = [["golfers", "1 · Social Golfers", "g", "DFS + Backtracking"],
    ["sudoku", "2 · Sudoku (Easy · Medium · Hard)", "s", "BFS + Backtracking"],
    ["latin", "3 · Latin Square", "l", "IDDFS + Backtracking"]];
  let html = `<tr><th>Problem</th>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
  rows.forEach(([pg, name, pre, algo]) => {
    html += `<tr><td><b>${name}</b></td>` + cols.map((c, i) =>
      `<td class="cell" data-pg="${pg}" data-a="${pre}-${i + 1}"><span class="check">✓</span>${i === 4 ? algo : c}</td>`).join("") + "</tr>";
  });
  $("#reqMatrix").innerHTML = html;
  $$("#reqMatrix .cell").forEach(c => c.onclick = () => go(c.dataset.pg, c.dataset.a));
})();

// hero animation: a tree searched with DFS, in a loop
(function heroArt() {
  const svg = $("#heroArt");
  (async function loop() {
    while (true) {
      svg.innerHTML = "";
      const nodes = [{ d: 0, kids: [], x: 230, y: 30 }], W = [0, 150, 52, 18];
      (function grow(n) {
        if (n.d >= 3) return;
        const k = n.d === 0 ? 3 : 2 + (Math.random() < .5 ? 1 : 0);
        for (let i = 0; i < k; i++) { const c = { d: n.d + 1, kids: [], parent: n }; nodes.push(c); n.kids.push(c); }
        n.kids.forEach((c, i) => { c.x = n.x + (i - (k - 1) / 2) * W[c.d]; c.y = 30 + c.d * 112; grow(c); });
      })(nodes[0]);
      const leaves = nodes.filter(n => !n.kids.length);
      const goal = leaves[Math.floor(leaves.length * (.55 + Math.random() * .4))];
      const gE = svgEl("g"), gN = svgEl("g"); svg.append(gE, gN);
      const dot = (n, color, r = 9) => gN.append(svgEl("circle", { cx: n.x, cy: n.y, r, fill: color, stroke: css("--bg"), "stroke-width": 3 }));
      dot(nodes[0], css("--ink"), 11);
      let found = false;
      async function dfs(n) {
        for (const c of n.kids) {
          if (found) return;
          gE.append(svgEl("line", { x1: n.x, y1: n.y, x2: c.x, y2: c.y, stroke: css("--line"), "stroke-width": 2 }));
          const isGoal = c === goal, dead = !c.kids.length && !isGoal;
          dot(c, isGoal ? css("--good") : dead ? css("--bad") : css("--accent"), isGoal ? 14 : 8);
          await sleep(160);
          if (isGoal) {
            found = true;
            for (let p = c; p.parent; p = p.parent) gE.append(svgEl("line", { x1: p.parent.x, y1: p.parent.y, x2: p.x, y2: p.y,
              stroke: css("--good"), "stroke-width": 6, "stroke-linecap": "round" }));
            return;
          }
          await dfs(c);
        }
      }
      await dfs(nodes[0]);
      await sleep(2600);
    }
  })();
})();

// engine diagram (colours are CSS variables so they follow the theme)
(function engineDiagram() {
  const s = $("#engineDiagram");
  const box = (x, y, w, hh, fill, stroke, r = 12) => s.append(svgEl("rect", { x, y, width: w, height: hh, rx: r, style: `fill:${fill};stroke:${stroke}`, "stroke-width": 1.5 }));
  const t = (x, y, str, size = 13, weight = 400, anchor = "middle", color) => {
    const e = svgEl("text", { x, y, "font-size": size, "font-weight": weight, "text-anchor": anchor }); e.setAttribute("style", `fill:${color || "var(--ink)"}`); e.textContent = str; s.append(e); };
  const arrow = (x1, y1, x2, y2) => s.append(svgEl("path", { d: `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`, style: "fill:none;stroke:var(--muted)", "stroke-width": 1.6, "marker-end": "url(#ah)" }));
  const defs = svgEl("defs"); const m = svgEl("marker", { id: "ah", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" });
  m.append(svgEl("path", { d: "M0,0 L10,5 L0,10 z", style: "fill:var(--muted)" })); defs.append(m); s.append(defs);
  // the problems
  const probs = [["Social Golfers", "DFS", 1], ["Sudoku", "BFS", 2], ["Latin Square", "IDDFS", 3]];
  probs.forEach(([name, al, i], k) => { const y = 38 + k * 80; box(10, y, 200, 54, "var(--paper)", "var(--line)");
    t(30, y + 33, String(i), 22, 700, "middle", "var(--accent)"); t(120, y + 25, name, 14, 700); t(120, y + 43, "uses " + al, 11, 400, "middle", "var(--muted)"); arrow(212, y + 27, 300, 150); });
  // the interface
  box(302, 40, 250, 220, "var(--accent-soft)", "var(--accent)");
  t(427, 70, "Problem interface", 15, 700);
  ["initial_state()", "next_variable(s)", "values(s, var)", "assign / unassign", "objective(s) → f"].forEach((m, i) => {
    box(322, 86 + i * 33, 210, 26, "var(--paper)", "var(--line)", 7); t(427, 104 + i * 33, m, 12.5, 600); });
  arrow(554, 150, 630, 150);
  // the engine
  box(632, 30, 160, 240, "var(--paper)", "var(--ink)");
  t(712, 60, "Engine", 16, 700);
  [["DFS", "--w1"], ["BFS", "--w2"], ["IDDFS", "--w3"]].forEach(([a, c], i) => { box(652, 78 + i * 60, 120, 46, `var(${c})`, `var(${c})`, 10); t(712, 107 + i * 60, a, 16, 800, "middle", "#fff"); });
  arrow(794, 150, 850, 150);
  box(852, 105, 100, 90, "var(--good-soft)", "var(--good)");
  t(902, 140, "solution", 13, 700); t(902, 162, "f(s) = 0 ✔", 13, 700, "middle", "var(--good)");
})();

// synthetic algorithm signatures
(function signatures() {
  const make = type => {
    const pts = []; let i = 0;
    if (type === "DFS") { let d = 0; for (let k = 0; k < 120; k++) { d = Math.random() < .62 || d < 2 ? Math.min(d + 1, 9) : Math.max(1, d - 1 - Math.floor(Math.random() * 3)); pts.push(d); } }
    if (type === "BFS") { for (let d = 1; d <= 6; d++) for (let k = 0; k < Math.round(2 * 1.75 ** d); k++) pts.push(d); }
    if (type === "IDDFS") { for (let L = 1; L <= 5; L++) { const rec = d => { pts.push(d); if (d < L) for (let c = 0; c < 2; c++) rec(d + 1); }; rec(0); } }
    return pts;
  };
  const info = { DFS: ["Dives deep, backs up on dead ends", ["memory O(d)", "may get stuck"], "--w1"],
    BFS: ["Finishes each level before the next", ["shallowest first", "memory O(bᵈ)"], "--w2"],
    IDDFS: ["Repeated DFS with growing limit L", ["memory O(d)", "repeats work"], "--w3"] };
  Object.entries(info).forEach(([a, [cap, tags, col]]) => {
    const pts = make(a), mx = Math.max(...pts);
    const poly = pts.map((d, i) => `${(i / (pts.length - 1) * 390 + 5).toFixed(1)},${(8 + d / mx * 100).toFixed(1)}`).join(" ");
    $("#signatures").append(h("div", { class: "sig" }, `<h3 style="color:var(${col})">${a}</h3>
      <svg viewBox="0 0 400 116" preserveAspectRatio="none"><polyline class="draw" points="${poly}" fill="none" stroke="var(${col})" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>
      <div class="cap" style="text-align:left">${cap} · ↓ depth, → time</div>
      <div class="tags">${tags.map((t, i) => `<span class="pill ${i ? "b" : "g"}">${t}</span>`).join("")}</div>`));
  });
})();

/* =====================================================================
   PLAYER: replays the search trace step by step
   ===================================================================== */
function createPlayer(container, trace, algorithm, render, finalRender) {
  const N = trace, n = N.length;
  if (!n) { container.append(h("p", { class: "muted" }, "No trace for this run.")); return; }
  const box = h("div", { class: "player" });
  box.innerHTML = `<div class="bar">
      <button class="btn primary" data-a="play">▶</button><button class="btn" data-a="back">⏮</button>
      <button class="btn" data-a="fwd">⏭</button><input type="range" min="0" max="${n}" value="0">
      <select class="btn" data-a="speed"><option value="250">slow</option><option value="60" selected>normal</option><option value="12">fast</option><option value="1">turbo</option></select>
      <button class="btn" data-a="end">⏩ end</button><button class="btn" data-a="snd" title="sound">🔇</button></div>
    <div class="now">Press ▶ to replay the search (${fmt(n)} steps).</div>`;
  const svg = svgEl("svg", { class: "finger", viewBox: "0 0 1000 170", preserveAspectRatio: "none" });
  box.append(svg, h("div", { class: "legend" }, `<span><i style="background:var(--accent)"></i>depth</span>
    <span><i style="background:var(--bad)"></i>dead end → backtrack</span><span><i style="background:var(--good)"></i>solution</span>
    ${algorithm === "IDDFS" ? "<span>dot colours = iterations (depth limit L)</span>" : ""}<span>→ time · ↓ deeper</span>`));
  container.append(box);
  const maxD = Math.max(...N.map(x => x[3]), 1);
  const X = i => 6 + i / Math.max(1, n - 1) * 988, Y = d => 8 + d / maxD * 154;
  const pts = N.map((x, i) => `${X(i).toFixed(1)},${Y(x[3]).toFixed(1)}`).join(" ");
  const clip = svgEl("clipPath", { id: "clip" + Math.random().toString(36).slice(2) });
  const clipRect = svgEl("rect", { x: 0, y: 0, width: 0, height: 170 }); clip.append(clipRect);
  const ghost = svgEl("polyline", { points: pts, fill: "none", stroke: css("--line"), "stroke-width": 1.2, "vector-effect": "non-scaling-stroke" });
  const live = svgEl("polyline", { points: pts, fill: "none", stroke: css("--accent"), "stroke-width": 1.5, "vector-effect": "non-scaling-stroke", "clip-path": `url(#${clip.id})` });
  const dots = svgEl("g", { "clip-path": `url(#${clip.id})` });
  N.forEach((x, i) => {
    if (x[5] === "ok" && algorithm !== "IDDFS") return;
    if (x[5] === "ok" && n > 1500 && i % 3) return;
    dots.append(svgEl("circle", { cx: X(i), cy: Y(x[3]), r: x[5] === "goal" ? 5 : 2.2,
      fill: x[5] === "goal" ? css("--good") : x[5] === "dead" ? css("--bad") : WEEK(x[4]) }));
  });
  const cursor = svgEl("line", { x1: 0, x2: 0, y1: 0, y2: 170, stroke: css("--ink"), "stroke-width": 1, "vector-effect": "non-scaling-stroke", opacity: .4 });
  svg.append(clip, ghost, live, dots, cursor);
  const range = $("input[type=range]", box), now = $(".now", box);
  const playBtn = $("[data-a=play]", box), sndBtn = $("[data-a=snd]", box), speed = $("[data-a=speed]", box);
  let k = 0, timer = null, sound = false, actx = null;
  // the values at step k = the path from node k up to the root
  function assignments(idx) {
    const m = new Map();
    for (let i = idx; i >= 0 && i < n; i = N[i][1]) if (!m.has(N[i][6])) m.set(N[i][6], N[i][7]);
    return m;
  }
  function show(step) {
    k = Math.max(0, Math.min(n, step)); range.value = k;
    const xx = k ? X(k - 1) + 1 : 0;
    clipRect.setAttribute("width", xx); cursor.setAttribute("x1", xx); cursor.setAttribute("x2", xx);
    if (k === 0) { render(-1, new Map(), null); now.textContent = "Initial state."; return; }
    const node = N[k - 1];
    render(k - 1, assignments(k - 1), node);
    now.textContent = `step ${fmt(k)}/${fmt(n)} · depth ${node[3]} · ${node[2]}` + (algorithm === "IDDFS" ? ` · iteration L = ${node[4]}` : "") +
      (node[5] === "goal" ? "  ✔ SOLUTION" : node[5] === "dead" ? "  ✖ dead end, backtrack" : "");
    if (k === n && finalRender) finalRender();
  }
  function beep(node) {
    if (!sound || !node) return;
    actx = actx || new (window.AudioContext || window.webkitAudioContext)();
    const o = actx.createOscillator(), g = actx.createGain();
    o.type = node[5] === "dead" ? "sawtooth" : "sine";
    o.frequency.value = node[5] === "dead" ? 110 : node[5] === "goal" ? 880 : 200 + node[3] * 14;
    g.gain.setValueAtTime(.06, actx.currentTime); g.gain.exponentialRampToValueAtTime(.0001, actx.currentTime + .1);
    o.connect(g).connect(actx.destination); o.start(); o.stop(actx.currentTime + .11);
  }
  function stop() { clearTimeout(timer); timer = null; playBtn.textContent = "▶"; }
  function tick() {
    if (k >= n) return stop();
    const ms = +speed.value, jump = ms <= 1 ? Math.max(1, Math.ceil(n / 400)) : 1;
    show(k + jump); beep(N[k - 1]);
    timer = setTimeout(tick, Math.max(ms, 4));
  }
  playBtn.onclick = () => { if (timer) return stop(); if (k >= n) show(0); playBtn.textContent = "⏸"; tick(); };
  $("[data-a=back]", box).onclick = () => { stop(); show(k - 1); };
  $("[data-a=fwd]", box).onclick = () => { stop(); show(k + 1); beep(N[k - 1]); };
  $("[data-a=end]", box).onclick = () => { stop(); show(n); };
  range.oninput = () => { stop(); show(+range.value); };
  sndBtn.onclick = () => { sound = !sound; sndBtn.textContent = sound ? "🔊" : "🔇"; };
  show(0);
}

/* =====================================================================
   COMPONENTS: f meter, landscape
   ===================================================================== */
function meter(el, f, max, label = "f(s)") {
  const r = 110, cx = 150, cy = 140, frac = Math.min(1, f / Math.max(1, max));
  const ang = Math.PI * (1 - frac), x = cx + r * Math.cos(ang), y = cy - r * Math.sin(ang);
  const col = f === 0 ? css("--good") : frac < .35 ? css("--warn") : css("--bad");
  el.innerHTML = `<svg viewBox="0 0 300 170">
    <path d="M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}" fill="none" stroke="${css("--line")}" stroke-width="18" stroke-linecap="round"/>
    <path d="M${cx - r},${cy} A${r},${r} 0 0 1 ${x.toFixed(1)},${y.toFixed(1)}" fill="none" stroke="${col}" stroke-width="18" stroke-linecap="round"/>
    <text x="${cx}" y="${cy - 18}" text-anchor="middle" font-family="Georgia,serif" font-size="54" font-weight="700" fill="${col}">${f}</text>
    <text x="${cx}" y="${cy + 22}" text-anchor="middle" font-size="13" fill="${css("--muted")}">${f === 0 ? "✔ " + label + " = 0, a solution" : label + " · violations"}</text>
    <text x="${cx - r}" y="${cy + 22}" text-anchor="middle" font-size="11" fill="${css("--muted")}">0</text>
    <text x="${cx + r}" y="${cy + 22}" text-anchor="middle" font-size="11" fill="${css("--muted")}">${max}</text></svg>`;
}

function renderLandscape(el, L, ratio) {
  const vals = L.sizes.filter(s => s.log10 != null);
  const maxL = Math.max(...vals.map(s => s.log10), 1) * 1.04;
  const step = maxL > 300 ? 100 : maxL > 120 ? 25 : maxL > 40 ? 10 : maxL > 15 ? 5 : 2;
  const cols = ["--bad", "--warn", "--accent", "--good"];
  let ticks = "";
  for (let v = 0; v <= maxL; v += step) ticks += `<div class="tick" style="left:${v / maxL * 100}%"></div><div class="tl" style="left:${v / maxL * 100}%">10<sup>${v}</sup></div>`;
  const marks = L.sizes.map((s, i) => s.log10 == null ? "" : `<div class="mk" data-l="${s.log10 / maxL * 100}" title="${s.label}">
    <div class="t" style="bottom:${44 + (i % 2) * 0}px;top:${i % 2 ? 0 : 18}px;color:var(${cols[i % 4]})">10^${s.log10.toFixed(1)}</div>
    <div class="ball" style="background:var(${cols[i % 4]})"></div></div>`).join("");
  const H = L.histogram, hm = Object.fromEntries(H.histogram), top = Math.max(...H.histogram.map(x => x[1]));
  let bars = "";
  for (let f = 0; f <= H.max; f++) bars += `<div class="${f === 0 ? "zero" : ""}" data-h="${(hm[f] || 0) / top * 100}" title="f = ${f}: ${hm[f] || 0} states" style="height:0"></div>`;
  el.innerHTML = `
    <h3>Size of the search space · powers of ten</h3>
    <div class="ruler"><div class="axis"></div>${ticks}${marks}</div>
    <div class="legend" style="justify-content:center">${L.sizes.map((s, i) => `<span><i style="background:var(${cols[i % 4]});border-radius:50%"></i>${s.label}</span>`).join("")}</div>
    <div class="land-grid">
      <div><h3>The haystack · ${fmt(H.samples)} random complete states</h3><canvas class="hay" width="900" height="300"></canvas>
        <div class="legend"><span><i style="background:var(--bad)"></i>many violations</span><span><i style="background:var(--warn)"></i>few</span><span><i style="background:var(--good)"></i>f = 0 (none found)</span></div></div>
      <div><h3>Distribution of f(s)</h3><div class="hist">${bars}</div>
        <div class="histx"><span>f = 0</span><span>mean ${H.mean}</span><span>${H.max}</span></div>
        <div class="big-ratio">${ratio}</div></div>
    </div>`;
  // the haystack: one dot per state, coloured by f
  const cv = $(".hay", el), ctx = cv.getContext("2d");
  const all = []; H.histogram.forEach(([f, c]) => { for (let i = 0; i < c; i++) all.push(f); });
  shuffle(all);
  const lo = H.min, hi = Math.max(H.max, lo + 1);
  all.forEach((f, i) => {
    const t = (f - lo) / (hi - lo);
    ctx.fillStyle = f === 0 ? css("--good") : t > .5 ? css("--bad") : css("--warn");
    ctx.globalAlpha = .35 + .5 * t;
    ctx.beginPath(); ctx.arc(8 + Math.random() * 884, 8 + Math.random() * 284, f === 0 ? 7 : 3, 0, 7); ctx.fill();
  });
  requestAnimationFrame(() => requestAnimationFrame(() => {
    $$(".mk", el).forEach(m => m.style.left = m.dataset.l + "%");
    $$(".hist div", el).forEach(d => d.style.height = d.dataset.h + "%");
  }));
}

/* =====================================================================
   RING GRAPH (Golfers): players on a circle, meetings as lines
   ===================================================================== */
function ring(svg, n, weeks, opts = {}) {
  svg.innerHTML = "";
  const R = 165, c = 200, P = i => [c + R * Math.cos(2 * Math.PI * i / n - Math.PI / 2), c + R * Math.sin(2 * Math.PI * i / n - Math.PI / 2)];
  const met = {};
  weeks.forEach(wk => wk.forEach(g => g.forEach(a => g.forEach(b => { if (a < b) { const k = a + "-" + b; met[k] = (met[k] || 0) + 1; } }))));
  const gE = svgEl("g"), gN = svgEl("g"); svg.append(gE, gN);
  const drawn = {};
  weeks.forEach((wk, j) => wk.forEach(g => g.forEach(a => g.forEach(b => {
    if (a >= b) return;
    const key = a + "-" + b, rep = met[key] > 1, [x1, y1] = P(a), [x2, y2] = P(b);
    if (rep && drawn[key]) return; drawn[key] = 1;
    const focus = opts.focus != null && (a === opts.focus || b === opts.focus);
    const col = rep ? css("--bad") : opts.weekColor ? opts.weekColor(j) : WEEK(j);
    gE.append(svgEl("path", { d: `M${x1},${y1} Q${c},${c} ${x2},${y2}`, fill: "none", stroke: col,
      "stroke-width": rep ? 3.2 : focus ? 2.4 : 1.2, opacity: opts.focus != null && !focus && !rep ? .12 : rep ? .95 : .7 }));
  }))));
  for (let i = 0; i < n; i++) {
    const [x, y] = P(i), [tx, ty] = [c + (R + 16) * Math.cos(2 * Math.PI * i / n - Math.PI / 2), c + (R + 16) * Math.sin(2 * Math.PI * i / n - Math.PI / 2)];
    const dot = svgEl("circle", { cx: x, cy: y, r: opts.focus === i ? 8 : 5.5, fill: opts.focus === i ? css("--accent") : css("--ink"), stroke: css("--paper"), "stroke-width": 2 });
    if (opts.onClick) { dot.style.cursor = "pointer"; dot.onclick = () => opts.onClick(i); }
    gN.append(dot);
    const t = svgEl("text", { x: tx, y: ty + 3, "text-anchor": "middle" }); t.textContent = opts.name ? opts.name(i) : i; gN.append(t);
  }
  return Object.values(met).reduce((s, v) => s + Math.max(0, v - 1), 0);
}

/* =====================================================================
   1. SOCIAL GOLFERS
   ===================================================================== */
const EX_WEEK1 = [[0, 1, 2, 3], [4, 5, 22, 23], [6, 7, 20, 21], [8, 25, 26, 27], [9, 10, 11, 24], [12, 13, 15, 30], [14, 28, 29, 31], [16, 17, 18, 19]];
flow($("#gFlow"), [
  { k: "Start", vis: miniCells(EX_WEEK1.flat().map((_, i) => Math.floor(i / 4) + 1).concat(Array(32).fill(0)), 16, 11, v => v ? WEEK(v - 1) : "var(--soft)", false), cap: "week 1 fixed · rest empty" },
  { k: "Action", vis: `<span style="font-size:34px">👤 → ▢</span>`, cap: "put a player in the next empty seat" },
  { k: "Goal", vis: `<span style="font:700 26px var(--serif)">320 / 320<br><span style="color:var(--good)">f = 0</span></span>`, cap: "all seats filled, no pair twice", goal: true }]);
ring($("#gRingModel"), 32, [EX_WEEK1]);
$("#gDomain").innerHTML = Array(32).fill("<span></span>").join("");
(function week1Table() {
  const el = $("#gWeek1");
  el.innerHTML = `<table class="sched"><tr><th></th>${EX_WEEK1.map((_, k) => `<th>Group ${k + 1}</th>`).join("")}</tr>
    <tr><th>Week 1</th>${EX_WEEK1.map((g, k) => `<td>${g.map((x, s) => `<span class="chip seat" data-k="${k}" data-s="${s}" style="background:color-mix(in srgb, ${WEEK(k)} 30%, var(--paper))">${x}</span>`).join("")}</td>`).join("")}</tr></table>
    <div class="cap" id="gSeatInfo" style="font-size:16px">👆 click a seat</div>`;
  $$(".seat", el).forEach(c => c.onclick = () => {
    $$(".seat", el).forEach(x => x.classList.remove("on")); c.classList.add("on");
    $("#gSeatInfo").innerHTML = `<span style="font-family:var(--serif);font-size:22px">X<sub>1,${+c.dataset.k + 1},${+c.dataset.s + 1}</sub> = <b style="color:var(--accent)">${c.textContent}</b></span>`;
  });
})();
// objective demo: week 1 + random weeks
(function golfObjective() {
  let weeks = [EX_WEEK1];
  const randWeek = () => { const p = shuffle([...Array(32).keys()]); return Array.from({ length: 8 }, (_, k) => p.slice(k * 4, k * 4 + 4)); };
  function draw() {
    const f = ring($("#gObjRing"), 32, weeks, { weekColor: j => j ? css("--w2") : css("--w1") });
    meter($("#gObjMeter"), f, 12 * Math.max(1, weeks.length - 1));
  }
  $("#gObjShuffle").onclick = () => { weeks = [EX_WEEK1, randWeek()]; draw(); };
  $("#gObjAdd").onclick = () => { weeks = [...weeks, randWeek()]; draw(); };
  $("#gObjReset").onclick = () => { weeks = [EX_WEEK1]; draw(); };
  weeks = [EX_WEEK1, randWeek()]; draw();
})();

let golfNames = "";
try { golfNames = localStorage.getItem("sl-names") || ""; } catch (e) {}

function golfersResult(out, d) {
  out.innerHTML = "";
  const ub = d.upper_bound;
  const verdict = d.stats.status === "solved"
    ? `<div class="note good"><b>YES.</b> ${d.n} golfers in ${d.g} groups of ${d.p} can play <b>${d.w} weeks</b>. Verified: <b>f(s) = ${d.objective}</b>.</div>`
    : d.stats.status === "no solution"
      ? `<div class="note" style="background:var(--bad-soft)"><b>NO.</b> DFS explored the <b>whole</b> tree. No schedule exists for ${d.w} weeks (a complete proof).${ub && d.w <= ub ? ` The theoretical bound was ${ub}, but it is not reachable.` : ""}</div>`
      : `<div class="note"><b>UNKNOWN.</b> DFS hit the time limit. ${ub && d.w > ub ? `Still, w = ${d.w} > ${ub} is <b>impossible</b> by the upper bound.` : "Try random restarts."}</div>`;
  out.append(h("div", {}, statKpis(d.stats, [[ub ?? "∞", "upper bound (weeks)"]]) + verdict));
  if (d.schedule) golfersSchedule(out, d.schedule, d);
  if (d.trace && d.trace.length) {
    out.append(h("h3", {}, "Replay: how DFS built the schedule"));
    const board = h("div", { class: "scroll" }); out.append(board);
    const per = d.g * d.p;
    createPlayer(out, d.trace, d.stats.algorithm, (i, asg, node) => {
      const sched = d.initial.slice();
      asg.forEach((v, k) => { if (k != null) sched[k] = v; });
      let html = `<table class="sched"><tr><th></th>${Array.from({ length: d.g }, (_, k) => `<th>G${k + 1}</th>`).join("")}</tr>`;
      for (let j = 0; j < d.w; j++) {
        html += `<tr><th style="color:${WEEK(j)}">W${j + 1}</th>`;
        for (let k = 0; k < d.g; k++) html += "<td>" + Array.from({ length: d.p }, (_, s) => {
          const idx = j * per + k * d.p + s, v = sched[idx], cur = node && node[6] === idx;
          return `<span class="chip ${v < 0 ? "empty" : ""} ${cur ? (node[5] === "dead" ? "mate" : "hl") : ""}">${v < 0 ? "·" : v}</span>`;
        }).join("") + "</td>";
        html += "</tr>";
      }
      board.innerHTML = html + "</table>";
    });
  }
}

function golfersSchedule(out, schedule, d) {
  const n = d.n, W = schedule.length;
  const wrap = h("div");
  wrap.innerHTML = `<div class="two" style="margin-top:14px">
      <div><svg class="ring gr" viewBox="0 0 400 400"></svg><input type="range" class="wk" min="1" max="${W}" value="${W}" style="width:100%">
        <div class="cap info"></div></div>
      <div><canvas width="420" height="420" style="width:100%;max-width:420px;border-radius:10px;display:block;margin:0 auto"></canvas>
        <div class="cap">Meeting matrix ${n}×${n}: cell (a, b) gets the colour of the week a and b met. No cell is ever coloured twice.</div></div></div>
    <div class="legend" style="justify-content:center">${schedule.map((_, j) => `<span><i style="background:${WEEK(j)}"></i>W${j + 1}</span>`).join("")}<span>👆 click a player in the ring</span></div>
    <h3>Schedule · type your class names (one per line) to replace the numbers</h3>`;
  const ta = h("textarea", { placeholder: "Alice\nBob\nCarol\n…" }); ta.value = golfNames;
  const tbl = h("div", { class: "scroll", style: "margin-top:10px" });
  wrap.append(ta, tbl); out.append(wrap);
  let focus = null;
  const name = i => { const L = ta.value.split("\n").map(s => s.trim()).filter(Boolean); return L[i] || i; };
  const slider = $(".wk", wrap), cv = $("canvas", wrap);
  function draw() {
    const upto = +slider.value, part = schedule.slice(0, upto);
    ring($(".gr", wrap), n, part, { focus, name, onClick: i => { focus = focus === i ? null : i; draw(); } });
    const ctx = cv.getContext("2d"), s = cv.width / n;
    ctx.fillStyle = css("--soft"); ctx.fillRect(0, 0, cv.width, cv.height);
    let pairs = 0;
    part.forEach((wk, j) => wk.forEach(g => g.forEach(a => g.forEach(b => {
      if (a === b) return; if (a < b) pairs++;
      ctx.fillStyle = WEEK(j); ctx.fillRect(b * s + .5, a * s + .5, Math.max(1, s - 1), Math.max(1, s - 1));
    }))));
    if (focus !== null) { ctx.strokeStyle = css("--ink"); ctx.lineWidth = 2; ctx.strokeRect(1, focus * s, cv.width - 2, s); }
    const total = n * (n - 1) / 2;
    $(".info", wrap).innerHTML = `<b>${upto}</b> weeks · <b>${pairs}</b> / ${total} pairs have met (${(pairs / total * 100).toFixed(0)}%)`;
    const mates = new Set();
    if (focus !== null) schedule.forEach(wk => wk.forEach(g => { if (g.includes(focus)) g.forEach(x => mates.add(x)); }));
    let html = `<table class="sched"><tr><th></th>${schedule[0].map((_, k) => `<th>Group ${k + 1}</th>`).join("")}</tr>`;
    schedule.forEach((wk, j) => {
      html += `<tr><th style="color:${WEEK(j)}">Week ${j + 1}</th>` + wk.map(g => "<td>" + g.map(x =>
        `<span class="chip ${x === focus ? "hl" : mates.has(x) ? "mate" : ""}" data-p="${x}">${name(x)}</span>`).join("") + "</td>").join("") + "</tr>";
    });
    tbl.innerHTML = html + "</table>";
    $$(".chip", tbl).forEach(c => c.onclick = () => { focus = +c.dataset.p === focus ? null : +c.dataset.p; draw(); });
  }
  ta.oninput = () => { golfNames = ta.value; try { localStorage.setItem("sl-names", ta.value); } catch (e) {} draw(); };
  slider.oninput = draw;
  draw();
}

async function golfersRun(p) {
  const out = $("#gOut");
  out.innerHTML = spin("DFS is searching on the server…");
  try { const d = await api(`/api/golfers?g=${p.g}&p=${p.p}&w=${p.w}&restarts=${p.r}&time_limit=${p.r ? 90 : 25}`); golfersResult(out, d); return d; }
  catch (e) { out.innerHTML = `<p class="err">${e.message}</p>`; }
}
const gParams = () => ({ g: +$("#gG").value, p: +$("#gP").value, w: +$("#gW").value, r: $("#gR").checked });
$("#gRun").onclick = () => { $("#gClimbBar").innerHTML = ""; golfersRun(gParams()); };
$("#gSmall").onclick = () => { $("#gG").value = 4; $("#gP").value = 3; $("#gW").value = 4; $("#gR").checked = false; $("#gRun").click(); };
$("#gClimb").onclick = async () => {
  const P = gParams(), bar = $("#gClimbBar"), btn = $("#gClimb");
  const n = P.g * P.p, ub = P.p > 1 ? (P.g === 1 ? 1 : Math.floor((n - 1) / (P.p - 1))) : 12;
  bar.innerHTML = Array.from({ length: ub }, (_, i) => `<div class="wk"><b>${i + 1}</b>week</div>`).join("") + `<div class="wk ub"><b>${ub + 1}</b>impossible</div>`;
  btn.disabled = true;
  let best = null;
  for (let w = 1; w <= ub; w++) {
    const cell = bar.children[w - 1]; cell.className = "wk run";
    $("#gW").value = w;
    const d = await golfersRun({ ...P, w });
    if (!d) break;
    cell.className = "wk " + (d.stats.status === "solved" ? "ok" : d.stats.status === "no solution" ? "no" : "stop");
    if (d.stats.status !== "solved") break;
    best = d;
  }
  if (best) { $("#gW").value = best.w; golfersResult($("#gOut"), best);
    $("#gOut").prepend(h("div", { class: "note good" }, `Maximum found: <b>${best.w} weeks</b> (upper bound ${ub}).`)); }
  btn.disabled = false;
};
async function golfersLand() {
  const el = $("#gLand"); el.innerHTML = spin("Computing…");
  try { renderLandscape(el, await api(`/api/golfers/landscape?g=${$("#glG").value}&p=${$("#glP").value}&w=${$("#glW").value}`),
    `0 <small>random schedules out of 1,500 reach f = 0</small>`); }
  catch (e) { el.innerHTML = `<p class="err">${e.message}</p>`; }
}
$("#glRun").onclick = golfersLand;
ONSHOW.golfers = golfersLand;

/* =====================================================================
   2. SUDOKU
   ===================================================================== */
let sLevels = {}, sCurrent = "easy", sCustom = null, sEditing = false, sEasySolution = null;
const LV = { easy: "Easy", medium: "Medium", hard: "Hard", extreme: "Extreme ★" };
const PEERS = Array.from({ length: 81 }, (_, i) => {
  const r = Math.floor(i / 9), c = i % 9, br = r - r % 3, bc = c - c % 3, s = new Set();
  for (let k = 0; k < 9; k++) { s.add(r * 9 + k); s.add(k * 9 + c); }
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) s.add((br + a) * 9 + bc + b);
  s.delete(i); return [...s];
});
const UNITS = [...Array.from({ length: 9 }, (_, r) => Array.from({ length: 9 }, (_, c) => r * 9 + c)),
  ...Array.from({ length: 9 }, (_, c) => Array.from({ length: 9 }, (_, r) => r * 9 + c)),
  ...[0, 3, 6].flatMap(br => [0, 3, 6].map(bc => [0, 1, 2].flatMap(a => [0, 1, 2].map(b => (br + a) * 9 + bc + b))))];

flow($("#sFlow"), [
  { k: "Start", vis: miniCells([5, 3, 0, 0, 7, 0, 6, 0, 0, 1, 9, 5, 0, 9, 8, 0, 0, 0, 0, 6, 0, 8, 0, 0, 0, 6, 0], 9, 13), cap: "the givens · 0 = empty" },
  { k: "Action", vis: `<span style="font-size:30px">▢ → <b style="color:var(--accent)">7</b></span>`, cap: "write a digit in the first empty cell" },
  { k: "Goal", vis: miniCells(Array.from({ length: 27 }, (_, i) => (i % 9 + Math.floor(i / 9) * 3) % 9 + 1), 9, 13, () => "var(--good-soft)"), cap: "no empty cell · f = 0", goal: true }]);

function sudokuBoard(el, puzzle, values, opts = {}) {
  const b = h("div", { class: "sudoku" + (opts.solved ? " solved" : "") });
  for (let i = 0; i < 81; i++) {
    const r = Math.floor(i / 9), c = i % 9, given = puzzle[i] > 0, v = given ? puzzle[i] : values[i];
    b.append(h("div", { class: "c" + (c === 2 || c === 5 ? " br" : "") + (r === 2 || r === 5 ? " bb" : "") + (given ? " given" : v ? " set" : "") +
      (opts.cur === i ? (opts.dead ? " dead" : " cur") : "") + (opts.conf?.has(i) ? " dead" : "") }, v ? v : ""));
  }
  el.innerHTML = ""; el.append(b);
}
function sudokuAnatomy() {
  const p = sLevels.easy, el = $("#sAnatomy");
  const g = h("div", { class: "anat s9", style: "grid-template-columns:repeat(9,1fr)" });
  p.forEach((v, i) => g.append(h("div", { class: v ? "given" : "empty", "data-i": i }, v || "·")));
  el.append(g);
  const show = i => {
    const r = Math.floor(i / 9), c = i % 9, br = r - r % 3, bc = c - c % 3;
    [...g.children].forEach((d, k) => {
      const kr = Math.floor(k / 9), kc = k % 9;
      d.className = (p[k] ? "given" : "empty") + (k === i ? " me" : kr === r ? " row" : kc === c ? " col" :
        (kr - kr % 3 === br && kc - kc % 3 === bc) ? " box" : "");
      if (k === i) d.style.color = "#fff"; else d.style.color = "";
    });
    const used = new Set(PEERS[i].map(k => p[k]));
    $("#sVar").innerHTML = `X<sub>${r + 1},${c + 1}</sub>`;
    $("#sDom").innerHTML = Array.from({ length: 9 }, (_, k) => `<span class="${used.has(k + 1) ? "x" : ""}">${k + 1}</span>`).join("");
  };
  [...g.children].forEach((d, i) => { d.onmouseenter = () => show(i); d.onclick = () => show(i); });
  show(p.indexOf(0));
}
function sudokuObjective() {
  const p = sLevels.easy;
  let grid;
  const fOf = gr => UNITS.reduce((f, u) => f + 9 - new Set(u.map(i => gr[i])).size, 0);
  function draw() {
    const bad = new Set();
    UNITS.forEach(u => { if (new Set(u.map(i => grid[i])).size < 9) u.forEach(i => bad.add(i)); });
    const g = h("div", { class: "anat s9", style: "grid-template-columns:repeat(9,1fr)" });
    grid.forEach((v, i) => g.append(h("div", { class: (p[i] ? "given" : "") + (bad.has(i) && !p[i] ? " bad" : "") }, v)));
    $("#sObjBoard").innerHTML = ""; $("#sObjBoard").append(g);
    meter($("#sObjMeter"), fOf(grid), 120);
  }
  $("#sObjRnd").onclick = () => { grid = p.map(v => v || 1 + Math.floor(Math.random() * 9)); draw(); };
  $("#sObjFix").onclick = () => {
    // fix one row that has repeats: its empty cells get the missing digits
    for (let r = 0; r < 9; r++) {
      const cells = UNITS[r];
      if (new Set(cells.map(i => grid[i])).size === 9) continue;
      const givens = new Set(cells.filter(i => p[i]).map(i => p[i]));
      const missing = shuffle([1, 2, 3, 4, 5, 6, 7, 8, 9].filter(d => !givens.has(d)));
      cells.filter(i => !p[i]).forEach((i, k) => grid[i] = missing[k]);
      break;
    }
    draw();
  };
  $("#sObjSol").onclick = async () => {
    if (!sEasySolution) sEasySolution = (await api("/api/sudoku", { level: "easy", algo: "DFS" })).solution;
    grid = sEasySolution.slice(); draw();
  };
  $("#sObjRnd").click();
}
function bfsQueueDemo() {
  const el = $("#sBfsExplain");
  el.innerHTML = `<div class="queue-wrap"><svg viewBox="0 0 300 160"></svg>
    <div><div class="queue"></div><div class="cap" style="text-align:left">FIFO queue: states leave from the left, children join on the right.
      <span style="color:var(--bad)">✖</span> = no legal value → dropped (backtracking).</div></div></div>`;
  const svg = $("svg", el), q = $(".queue", el);
  const lv = [[150], [70, 150, 230], [30, 70, 110, 150, 190, 230, 270]];
  const nodes = []; lv.forEach((xs, d) => xs.forEach(x => nodes.push({ x, y: 20 + d * 60, d })));
  nodes.forEach((n, i) => { if (n.d) { const p = n.d === 1 ? nodes[0] : nodes[1 + Math.floor((i - 4) / 2.34)];
    svg.append(svgEl("line", { x1: p.x, y1: p.y, x2: n.x, y2: n.y, stroke: css("--line"), "stroke-width": 2 })); } });
  const circles = nodes.map(n => { const c = svgEl("circle", { cx: n.x, cy: n.y, r: 11, fill: css("--soft"), stroke: css("--line"), "stroke-width": 2 }); svg.append(c); return c; });
  const dead = new Set([5, 9]);
  (async function loop() {
    while (document.body.contains(el)) {
      circles.forEach(c => c.setAttribute("fill", css("--soft")));
      q.innerHTML = "";
      for (let i = 0; i < nodes.length; i++) {
        circles[i].setAttribute("fill", dead.has(i) ? css("--bad") : WEEK(nodes[i].d + 1));
        const item = h("div", { class: "q", style: `background:${dead.has(i) ? css("--bad") : WEEK(nodes[i].d + 1)}` }, dead.has(i) ? "✖" : "L" + nodes[i].d);
        q.append(item);
        if (q.children.length > 6) q.firstChild.remove();
        await sleep(650);
      }
      await sleep(1500);
    }
  })();
}
function sudokuPreview() {
  const out = $("#sOut");
  out.innerHTML = `<div class="two"><div class="board-wrap" id="sPrev"></div><div id="sSide"></div></div>`;
  if (sEditing) return sudokuEditor($("#sPrev"));
  const p = sLevels[sCurrent];
  sudokuBoard($("#sPrev"), p, []);
  const empty = p.filter(v => !v).length;
  $("#sSide").innerHTML = kpis([[empty, "empty cells = variables"], [81 - empty, "givens"]]) +
    `<div class="formula" style="font-size:20px">search space 9<sup>${empty}</sup> ≈ 10<sup>${(empty * Math.log10(9)).toFixed(0)}</sup></div>` +
    (sCurrent === "extreme" ? `<div class="note">Arto Inkala's 2012 puzzle, called "the world's hardest". Watch BFS's queue size.</div>` : "");
}
function sudokuEditor(el) {
  const grid = sCustom || sLevels[sCurrent].slice();
  const b = h("div", { class: "sudoku" }), fbox = h("div", { class: "small", style: "margin-top:8px" }), inputs = [];
  function check() {
    const g = inputs.map(x => +x.value || 0), conf = new Set();
    g.forEach((v, i) => { if (v && PEERS[i].some(p => g[p] === v)) conf.add(i); });
    inputs.forEach((x, i) => x.parentElement.classList.toggle("dead", conf.has(i)));
    sCustom = g;
    fbox.innerHTML = `conflicts <b style="color:${conf.size ? "var(--bad)" : "var(--good)"}">${conf.size}</b> · givens ${g.filter(Boolean).length} · empty ${g.filter(v => !v).length}`;
  }
  for (let i = 0; i < 81; i++) {
    const r = Math.floor(i / 9), c = i % 9;
    const cell = h("div", { class: "c" + (c === 2 || c === 5 ? " br" : "") + (r === 2 || r === 5 ? " bb" : "") });
    const inp = h("input", { maxlength: 1, inputmode: "numeric" }); inp.value = grid[i] || "";
    inp.oninput = () => { inp.value = inp.value.replace(/[^1-9]/g, ""); check(); };
    inputs.push(inp); cell.append(inp); b.append(cell);
  }
  el.innerHTML = ""; el.append(b, fbox); check();
}
async function sudokuInit() {
  sLevels = await api("/api/sudoku/levels");
  const seg = $("#sLevels");
  Object.keys(sLevels).forEach(l => {
    const b = h("button", {}, LV[l] || l);
    b.onclick = () => { sCurrent = l; sEditing = false; sCustom = null; $$("#sLevels button").forEach(x => x.classList.toggle("on", x === b)); $("#sEdit").classList.remove("on"); sudokuPreview(); };
    seg.append(b);
  });
  seg.firstChild.classList.add("on");
  sudokuAnatomy(); sudokuObjective(); bfsQueueDemo(); sudokuPreview();
}
$("#sEdit").onclick = () => { sEditing = !sEditing; $("#sEdit").classList.toggle("on", sEditing); if (sEditing) sCustom = sLevels[sCurrent].slice(); sudokuPreview(); };
$("#sRun").onclick = async () => {
  const out = $("#sOut"), algo = $("#sAlgo").value;
  const body = sEditing ? { puzzle: sCustom.join(""), algo } : { level: sCurrent, algo };
  out.innerHTML = spin(`${algo} is searching…`); $("#sRun").disabled = true;
  try {
    const d = await api("/api/sudoku", body);
    out.innerHTML = statKpis(d.stats, [[d.empty, "variables"], [d.objective ?? "–", "f(s) of the result"]]);
    const two = h("div", { class: "two" }), left = h("div", { class: "board-wrap" }), right = h("div");
    two.append(left, right); out.append(two);
    right.innerHTML = `<div class="legend" style="margin-bottom:8px"><span><b>8</b> given</span><span><b style="color:var(--accent)">8</b> placed by ${algo}</span>
      <span><i style="background:var(--bad-soft);outline:1px solid var(--bad)"></i>dead end</span><span><b style="color:var(--good)">8</b> solved</span></div>
      ${d.stats.nodes > d.trace.length ? `<div class="cap" style="text-align:left">Replay shows the first ${fmt(d.trace.length)} of ${fmt(d.stats.nodes)} steps · ⏩ shows the final result.</div>` : ""}`;
    const showFinal = () => d.solution && sudokuBoard(left, d.puzzle, d.solution, { solved: true });
    createPlayer(right, d.trace, d.stats.algorithm, (i, asg, node) => {
      const vals = []; asg.forEach((v, k) => { if (k != null) vals[k] = v; });
      sudokuBoard(left, d.puzzle, vals, { cur: node ? node[6] : null, dead: node && node[5] === "dead", solved: node && node[5] === "goal" });
    }, showFinal);
    showFinal();
    const pr = d.landscape.sizes[1].log10;
    renderLandscape($("#sLand"), d.landscape, pr == null ? `0<small>a cell has no possible value, so no filling can work</small>`
      : `1 in 10<sup>${pr.toFixed(0)}</sup><small>exactly one solution among all fillings left after pruning</small>`);
  } catch (e) { out.innerHTML = `<p class="err">${e.message}</p>`; }
  $("#sRun").disabled = false;
};
ONSHOW.sudoku = async () => { await sudokuInit(); $("#sRun").click(); };

/* =====================================================================
   3. LATIN SQUARE
   ===================================================================== */
const LCOL = v => WEEK(v - 1);
const latinColor = v => v ? `color-mix(in srgb, ${LCOL(v)} 75%, var(--paper))` : "var(--soft)";
function latinBoard(el, n, arr, opts = {}) {
  const b = h("div", { class: "latin", style: `grid-template-columns:repeat(${n},auto)` });
  arr.forEach((v, i) => b.append(h("div", {
    class: "c" + (v ? "" : " empty") + (opts.fixed?.[i] ? " fixed" : "") + (opts.cur === i ? " cur" : "") +
      ((opts.cur === i && opts.dead) || opts.conf?.has(i) ? " dead" : ""), style: v ? `background:${LCOL(v)}` : "" }, v || "")));
  el.innerHTML = ""; el.append(b); return b;
}
const cyclic = n => Array.from({ length: n * n }, (_, i) => ((i % n - Math.floor(i / n)) % n + n) % n + 1);
flow($("#lFlow"), [
  { k: "Start", vis: miniCells([1, 2, 3, 4, 5, 2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 4, 0, 0, 0, 0, 5, 0, 0, 0, 0], 5, 15, latinColor), cap: "first row and column fixed" },
  { k: "Action", vis: `<span style="font-size:30px">▢ → <b style="color:var(--accent)">k</b></span>`, cap: "next empty cell gets a value 1…n" },
  { k: "Goal", vis: miniCells(cyclic(5), 5, 15, latinColor), cap: "n² cells filled · f = 0", goal: true }]);
(function symmetryPair() {
  const n = 5, base = cyclic(n), perm = [3, 5, 1, 4, 2], rows = [2, 4, 0, 3, 1];
  const scrambled = []; rows.forEach(r => base.slice(r * n, r * n + n).forEach(v => scrambled.push(perm[v - 1])));
  latinBoard($("#lSymA"), n, scrambled);
  // normalise: relabel so row 1 is 1..n, then sort the rows by the first column
  const map = {}; scrambled.slice(0, n).forEach((v, i) => map[v] = i + 1);
  const relabeled = scrambled.map(v => map[v]);
  const rs = Array.from({ length: n }, (_, r) => relabeled.slice(r * n, r * n + n)).sort((a, b) => a[0] - b[0]).flat();
  const b = latinBoard($("#lSymB"), n, rs, { fixed: rs.map((_, i) => i < n || i % n === 0) });
  $("#lSymA").append(h("div", { class: "cap" }, "any Latin square"));
  $("#lSymB").append(h("div", { class: "cap" }, "relabel + reorder rows → normalised"));
})();
(function latinAnatomy() {
  const n = 5, base = cyclic(n), arr = base.map((v, i) => i < 2 * n || i % n === 0 ? v : 0);
  const g = h("div", { class: "anat", style: `grid-template-columns:repeat(${n},1fr);width:min(100%,300px)` });
  arr.forEach(v => g.append(h("div", { class: v ? "fixed" : "empty" }, v || "·")));
  $("#lAnatomy").append(g);
  const show = i => {
    const r = Math.floor(i / n), c = i % n;
    [...g.children].forEach((d, k) => {
      d.className = (arr[k] ? "fixed" : "empty") + (k === i ? " me" : Math.floor(k / n) === r ? " row" : k % n === c ? " col" : "");
      d.style.color = k === i ? "#fff" : "";
    });
    const used = new Set([...arr.slice(r * n, r * n + n), ...arr.filter((_, k) => k % n === c)]);
    $("#lVar").innerHTML = `X<sub>${r},${c}</sub>`;
    $("#lDom").innerHTML = Array.from({ length: n }, (_, k) => `<span class="${used.has(k + 1) ? "x" : ""}">${k + 1}</span>`).join("");
  };
  [...g.children].forEach((d, i) => { d.onmouseenter = () => show(i); d.onclick = () => show(i); });
  show(2 * n + 1);
})();
(function latinPlayground() {
  let n = 4, g = [];
  const f = arr => { let s = 0; for (let i = 0; i < n; i++) { s += n - new Set(arr.slice(i * n, i * n + n)).size; s += n - new Set(arr.filter((_, k) => k % n === i)).size; } return s; };
  function draw() {
    const conf = new Set();
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) for (let k = j + 1; k < n; k++) {
      if (g[i * n + j] === g[i * n + k]) { conf.add(i * n + j); conf.add(i * n + k); }
      if (g[j * n + i] === g[k * n + i]) { conf.add(j * n + i); conf.add(k * n + i); }
    }
    const b = latinBoard($("#lPlay"), n, g, { conf });
    [...b.children].forEach((c, i) => { c.style.cursor = "pointer"; c.onclick = () => { g[i] = g[i] % n + 1; draw(); }; });
    meter($("#lPlayMeter"), f(g), 2 * n * (n - 1));
  }
  const rnd = () => { g = Array.from({ length: n * n }, () => 1 + Math.floor(Math.random() * n)); draw(); };
  $("#lPlayRnd").onclick = rnd;
  $("#lPlayCyc").onclick = () => { g = cyclic(n); draw(); };
  $("#lPlayN").onchange = () => { n = +$("#lPlayN").value; rnd(); };
  rnd();
})();
// IDDFS: 4 small trees, the limit L grows
(function iddfsDemo() {
  const el = $("#lIdExplain");
  el.innerHTML = `<div class="idd">${[0, 1, 2, 3].map(L => `<div class="it"><svg viewBox="0 0 200 90"></svg><b>L = ${L}</b>
    <div class="cap">${[1, 3, 7, 15][L]} nodes visited</div></div>`).join("")}</div>`;
  $$(".it svg", el).forEach((svg, L) => {
    const pos = []; for (let d = 0; d <= 3; d++) for (let i = 0; i < 2 ** d; i++) pos.push({ d, x: (i + .5) * 200 / 2 ** d, y: 10 + d * 25 });
    pos.forEach((p, i) => { if (i) { const par = pos[Math.floor((i - 1) / 2)];
      svg.append(svgEl("line", { x1: par.x, y1: par.y, x2: p.x, y2: p.y, stroke: p.d <= L ? WEEK(L + 2) : css("--line"), "stroke-width": p.d <= L ? 2 : 1 })); } });
    pos.forEach(p => svg.append(svgEl("circle", { cx: p.x, cy: p.y, r: 5, fill: p.d <= L ? WEEK(L + 2) : css("--soft"), stroke: css("--line") })));
  });
  el.append(h("div", { class: "cap" }, "Each iteration restarts from the root with a deeper limit. The top of the tree is revisited every time."));
})();
$("#lRun").onclick = async () => {
  const n = +$("#lN").value, algo = $("#lAlgo").value, sym = $("#lSym").checked, out = $("#lOut");
  out.innerHTML = spin(`${algo} is searching for n = ${n}…`); $("#lRun").disabled = true;
  try {
    const d = await api(`/api/latin?n=${n}&algo=${algo}&symmetry=${sym}`);
    out.innerHTML = statKpis(d.stats, [[d.objective ?? "–", "f(s) of the result"], [d.count ? fmt(d.count) : "?", `Latin squares of size ${n}`]]);
    const fixed = d.initial.map(v => v > 0), sol = d.solution || d.fallback?.solution;
    const two = h("div", { class: "two" }), left = h("div"), right = h("div");
    two.append(left, right); out.append(two);
    const board = h("div", { class: "board-wrap" }); left.append(board);
    if (sol) left.append(h("div", {}, `<pre class="box mono" style="margin:10px auto 0;width:max-content">Input: ${n}\nOutput:\n${
      Array.from({ length: n }, (_, r) => sol.slice(r * n, r * n + n).join(" ")).join("\n")}</pre>`));
    if (!d.solution && d.fallback) right.append(h("div", { class: "note" }, `<b>IDDFS hit the limit.</b> Every solution sits at the deepest level (${n * n} cells),
      so each shallower iteration explores the <i>whole</i> tree. The last iteration is plain DFS: it finds the answer in <b>${fmt(d.fallback.stats.nodes)}</b> nodes (left).`));
    createPlayer(right, d.trace, d.stats.algorithm, (i, asg, node) => {
      const arr = d.initial.slice(); asg.forEach((v, k) => { if (k != null) arr[k] = v; });
      latinBoard(board, n, arr, { fixed, cur: node ? node[6] : null, dead: node && node[5] === "dead" });
    }, () => sol && latinBoard(board, n, sol, { fixed }));
    if (sol) latinBoard(board, n, sol, { fixed });
    const cyc = h("div", { class: "two", style: "margin-top:16px;align-items:center" });
    cyc.innerHTML = `<div class="board-wrap" id="lCyc"></div><div><div class="formula" style="font-size:18px">L[r][c] = ((c − r) mod n) + 1</div>
      <div class="cap">No search at all: this formula gives exactly the assignment's example output.</div></div>`;
    out.append(cyc); latinBoard($("#lCyc", cyc), n, d.cyclic);
    const tot = d.landscape.sizes[0].log10, solL = d.landscape.sizes[2].log10;
    renderLandscape($("#lLand"), d.landscape, solL != null ? `1 in 10<sup>${(tot - solL).toFixed(1)}</sup><small>random fillings that are Latin squares (n = ${n})</small>` : "");
  } catch (e) { out.innerHTML = `<p class="err">${e.message}</p>`; }
  $("#lRun").disabled = false;
};
ONSHOW.latin = () => $("#lRun").click();

/* =====================================================================
   RACE
   ===================================================================== */
const RACE = { golfers: "Golfers 8×4 · 5 weeks", sudoku: "Sudoku Hard", latin: "Latin Square n = 6" };
let raceSel = "sudoku";
Object.entries(RACE).forEach(([k, v]) => {
  const b = h("button", {}, v); b.onclick = () => { raceSel = k; $$("#raceSel button").forEach(x => x.classList.toggle("on", x === b)); };
  if (k === raceSel) b.classList.add("on");
  $("#raceSel").append(b);
});
$("#raceRun").onclick = async () => {
  const lanes = $("#raceLanes"), algos = ["DFS", "BFS", "IDDFS"], res = {};
  $("#raceRun").disabled = true; $("#raceVerdict").innerHTML = "";
  lanes.innerHTML = algos.map(a => `<div class="lane" id="lane-${a}"><h3>${a}</h3><div class="body">${spin("waiting…")}</div></div>`).join("");
  const metrics = [["nodes", "nodes"], ["max_memory", "memory"], ["seconds", "time"]];
  function paint() {
    const done = Object.values(res), mx = {};
    metrics.forEach(([m]) => mx[m] = Math.max(...done.map(r => r[m]), 1e-9));
    algos.forEach(a => { const r = res[a]; if (!r) return;
      $(`#lane-${a} .body`).innerHTML = statusTag(r.status) + metrics.map(([m, l]) => {
        const scale = v => Math.log10(1 + v * (m === "seconds" ? 1000 : 1));
        const w = r[m] <= 0 ? 0 : Math.max(3, scale(r[m]) / scale(mx[m]) * 100);
        return `<div class="metric"><span class="muted">${l}</span><div class="track"><div class="fill ${a}" style="width:${w}%"></div></div>
          <span class="v">${m === "seconds" ? r[m].toFixed(3) + " s" : fmt(r[m])}</span></div>`; }).join(""); });
  }
  for (const a of algos) {
    $(`#lane-${a} .body`).innerHTML = spin("racing…");
    try { res[a] = await api(`/api/race/${raceSel}?algo=${a}`); } catch (e) { $(`#lane-${a} .body`).innerHTML = `<p class="err">${e.message}</p>`; }
    paint();
  }
  const ok = algos.filter(a => res[a]?.status === "solved");
  if (ok.length) {
    const fast = ok.reduce((x, y) => res[x].seconds <= res[y].seconds ? x : y);
    $(`#lane-${fast} h3`).insertAdjacentHTML("beforeend", ` <span class="winner">★ fastest</span>`);
    $("#raceVerdict").innerHTML = `🏆 <b>${fast}</b> wins. ` + (res.BFS && res.DFS ? `BFS held up to <b>${fmt(res.BFS.max_memory)}</b> states at once; DFS only <b>${fmt(res.DFS.max_memory)}</b>.` : "");
  }
  $("#raceRun").disabled = false;
};
(function tradeoff() {
  const lvl = (k, bad) => `<span class="lvl ${bad ? "bad" : ""}">${[1, 2, 3].map(i => `<i class="${i <= k ? "on" : ""}"></i>`).join("")}</span>`;
  const rows = [["DFS", "--w1", lvl(1), "✖", "✔*", lvl(1), "Golfers"], ["BFS", "--w2", lvl(3, 1), "✔", "✔", lvl(1), "Sudoku"], ["IDDFS", "--w3", lvl(1), "✔", "✔", lvl(3, 1), "Latin Square"]];
  $("#tradeoff").innerHTML = `<div class="scroll"><table class="trade"><tr><th>Algorithm</th><th>Memory</th><th>Shallowest first</th><th>Complete</th><th>Repeated work</th><th>Used for</th></tr>
    ${rows.map(([a, c, m, o, cpl, r, u]) => `<tr><td class="alg" style="color:var(${c})">${a}</td><td>${m}</td><td style="font-size:20px">${o}</td><td style="font-size:20px">${cpl}</td><td>${r}</td><td>${u}</td></tr>`).join("")}
  </table></div><div class="cap">* complete on finite trees (all our CSPs are finite)</div>`;
})();

/* ---------------- start ---------------- */
const [p0, a0] = location.hash.slice(1).split("/");
go(p0 || "home", a0);
