"use strict";
/* =====================================================================
   POLISH - visual effects (does not change any algorithm)
   ===================================================================== */
(function () {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const cssv = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  /* 1. reading progress bar */
  const bar = document.getElementById("progress");
  const onScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = (max > 0 ? scrollY / max * 100 : 0) + "%";
  };
  addEventListener("scroll", onScroll, { passive: true });

  /* 2. hero background: drifting nodes that connect when close */
  (function heroBackground() {
    const cv = document.getElementById("heroBg");
    if (!cv || reduce) return;
    const ctx = cv.getContext("2d");
    let W, H, pts;
    function size() {
      const r = cv.getBoundingClientRect();
      W = cv.width = Math.max(300, r.width * devicePixelRatio); H = cv.height = Math.max(200, r.height * devicePixelRatio);
      pts = Array.from({ length: 46 }, () => ({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .35, vy: (Math.random() - .5) * .35 }));
    }
    size(); addEventListener("resize", size);
    (function frame() {
      if (cv.offsetParent !== null) {
        ctx.clearRect(0, 0, W, H);
        const acc = cssv("--accent"), lim = 150 * devicePixelRatio;
        pts.forEach(p => { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1; });
        for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
          const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
          if (d < lim) { ctx.globalAlpha = (1 - d / lim) * .35; ctx.strokeStyle = acc; ctx.lineWidth = devicePixelRatio;
            ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke(); }
        }
        ctx.globalAlpha = .6; ctx.fillStyle = acc;
        pts.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 2.2 * devicePixelRatio, 0, 7); ctx.fill(); });
      }
      requestAnimationFrame(frame);
    })();
  })();

  /* 3. sections fade in while scrolling */
  if (!reduce && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .06 });
    document.querySelectorAll(".req, .ptitle, .hero > div").forEach(el => { el.classList.add("reveal"); io.observe(el); });
  }

  /* 4. numbers "count up" to their value */
  function countUp(el) {
    const txt = el.textContent.trim();
    if (!/^[\d,]+$/.test(txt) || el.dataset.counted) return;
    const target = +txt.replace(/,/g, "");
    if (target < 10 || reduce) return;
    el.dataset.counted = 1;
    const t0 = performance.now(), dur = 900;
    (function step() {
      const k = Math.max(0, Math.min(1, (performance.now() - t0) / dur)), e = 1 - Math.pow(1 - k, 3);
      el.textContent = k >= 1 ? txt : Math.round(target * e).toLocaleString("en-US");
      if (k < 1) requestAnimationFrame(step);
    })();
  }

  /* 5. trees: zoom and drag */
  function treeTools(wrap) {
    const svg = wrap.querySelector("svg");
    if (!svg || wrap.dataset.tools) return;
    wrap.dataset.tools = 1;
    const baseW = +svg.getAttribute("width"), baseH = +svg.getAttribute("height");
    let z = 1;
    const apply = () => { svg.setAttribute("width", baseW * z); svg.setAttribute("height", baseH * z); };
    const tools = document.createElement("div");
    tools.className = "tree-tools";
    tools.innerHTML = `<button class="btn" data-z="out">−</button><button class="btn" data-z="fit">⤢ fit</button><button class="btn" data-z="in">+</button>`;
    tools.onclick = e => {
      const a = e.target.dataset.z; if (!a) return;
      z = a === "in" ? Math.min(3, z * 1.25) : a === "out" ? Math.max(.2, z / 1.25) : Math.min(1, (wrap.clientWidth - 10) / baseW);
      apply();
    };
    wrap.parentNode.insertBefore(tools, wrap);
    let sx, sy, sl, st, down = false;
    wrap.addEventListener("mousedown", e => { down = true; sx = e.clientX; sy = e.clientY; sl = wrap.scrollLeft; st = wrap.scrollTop; wrap.classList.add("drag"); });
    addEventListener("mouseup", () => { down = false; wrap.classList.remove("drag"); });
    wrap.addEventListener("mousemove", e => { if (!down) return; wrap.scrollLeft = sl - (e.clientX - sx); wrap.scrollTop = st - (e.clientY - sy); });
    wrap.addEventListener("wheel", e => { if (!e.ctrlKey) return; e.preventDefault(); z = Math.max(.2, Math.min(3, z * (e.deltaY < 0 ? 1.1 : .9))); apply(); }, { passive: false });
  }

  /* 6. golfers: "Play weeks" lights the weeks up one by one */
  function weekPlayer(slider) {
    if (slider.dataset.player) return;
    slider.dataset.player = 1;
    const box = document.createElement("div");
    box.className = "ring-tools";
    box.innerHTML = `<button class="btn primary">▶ Play weeks</button>`;
    slider.after(box);
    box.firstChild.onclick = async () => {
      const max = +slider.max;
      for (let w = 1; w <= max; w++) {
        slider.value = w; slider.dispatchEvent(new Event("input"));
        await new Promise(r => setTimeout(r, 650));
      }
    };
  }

  /* watch every new piece of content added to the page */
  const scan = root => {
    if (!(root instanceof Element)) return;
    root.querySelectorAll(".kpi b, .hero-stats b").forEach(countUp);
    if (root.matches?.(".kpi b")) countUp(root);
    root.querySelectorAll(".tree-svg-wrap").forEach(treeTools);
    if (root.closest?.(".tree-svg-wrap")) treeTools(root.closest(".tree-svg-wrap"));
    root.querySelectorAll("input.wk").forEach(weekPlayer);
  };
  new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(scan))).observe(document.body, { childList: true, subtree: true });
  scan(document.body);
})();
