(() => {
"use strict";
const SHOW = JSON.parse(document.getElementById("show").textContent);
const $ = (id) => document.getElementById(id);
const stage = $("stage"), svg = $("view"), backG = $("back"), farG = $("far"), camG = $("cam"), nearG = $("near"), bubblesEl = $("bubbles"), cardsEl = $("cards"),
      fadeEl = $("fade"), fxEl = $("fxlayer"), barEl = $("bar"), playBtn = $("play"), scenesEl = $("scenes"), clockEl = $("clock"), muteBtn = $("mute"), soundBtn = $("sound"), soundIn = $("soundin"), startEl = $("start");
const SVGNS = "http://www.w3.org/2000/svg";
const ANIM_PERIOD = 2.4, SWAY_AMP = 0.10;

// ---------------------------------------------------------------------------------------------------------------- timeline math (scene.py)
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, u) => a + (b - a) * u;
const EASE = { linear: (u) => u, in: (u) => u * u, out: (u) => 1 - (1 - u) * (1 - u), inout: (u) => u * u * (3 - 2 * u), cut: (u) => (u >= 1 ? 1 : 0) };
const ease = (u, k) => EASE[k](clamp(u, 0, 1));
function tri(v) { let f = v - Math.trunc(v); if (f < 0) f += 1; return f < 0.5 ? f * 4 - 1 : 3 - f * 4; }
function lastBefore(list, t, key) {                         // index of the last item whose key(item) <= t (list sorted by key), or -1
  let lo = 0, hi = list.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (key(list[mid]) <= t) lo = mid + 1; else hi = mid; }
  return lo - 1;
}
function baseCamera(sc, t) {
  const c = sc.cams;
  if (!c.length) return [sc.view[0] / 2, sc.view[1] / 2, 1];
  if (t <= c[0][0]) return [c[0][1], c[0][2], c[0][3]];
  for (let i = 0; i + 1 < c.length; i++) {
    const a = c[i], b = c[i + 1];
    if (t < b[0]) { const u = ease((t - a[0]) / (b[0] - a[0]), b[4]); return [lerp(a[1], b[1], u), lerp(a[2], b[2], u), lerp(a[3], b[3], u)]; }
  }
  const l = c[c.length - 1];
  return [l[1], l[2], l[3]];
}
function camera(sc, t) {
  let [x, y, z] = baseCamera(sc, t);
  let sx = 0, sy = 0, m = 1;
  for (const [t0, t1, amp] of sc.shakes) if (t >= t0 && t < t1) { sx += amp * tri(t * 23); sy += amp * tri(t * 31 + 0.3); }
  for (const [p0, amt, dur] of sc.punches) if (t >= p0 && t < p0 + dur) { const u = (t - p0) / dur; m += amt * (1 - u) * (1 - u); }
  return [x + sx, y + sy, z * m];
}
function fadeAt(sc, t) {
  const i = lastBefore(sc.fades, t, (f) => f[0]);
  if (i < 0) return [0, "black"];
  const [t0, t1, a0, a1, c] = sc.fades[i];
  return [lerp(a0, a1, ease((t - t0) / Math.max(t1 - t0, 1e-9), "linear")), c];
}
function stutterAt(sc, t) {
  for (const [t0, t1, n, a] of sc.fx) if (n === "stutter" && t >= t0 && t < t1) return Math.max(0.05, 0.5 / Math.max(1, a));
  return null;
}
function position(a, t) {
  const i = lastBefore(a.moves, t, (m) => m[0]);
  if (i < 0) return [a.x, a.y];
  const [t0, t1, x0, y0, x1, y1, e, hop] = a.moves[i];
  if (e === "cut" || t >= t1) return [x1, y1];
  const u = ease((t - t0) / (t1 - t0), e);
  return [lerp(x0, x1, u), lerp(y0, y1, u) - hop * 4 * u * (1 - u)];
}
function poseAt(a, t) { const i = lastBefore(a.cues, t, (c) => c[0]); return i < 0 ? a.idle : a.cues[i][1]; }
function visibleAt(a, t) { const i = lastBefore(a.vis, t, (v) => v[0]); return i < 0 ? true : a.vis[i][1]; }
function flipAt(a, t) { const i = lastBefore(a.flips, t, (f) => f[0]); return i < 0 ? a.flip : a.flips[i][1]; }
const fadeCurve = (age, secs, edge = 0.35) => (age < 0 || age > secs ? 0 : Math.max(0, Math.min(1, age / edge, (secs - age) / edge)));

// ---------------------------------------------------------------------------------------------------------------- a loaded scene
let S = null;               // the current scene state
let W = 640, H = 360;       // the stage in pixels

function el(tag, cls, parent) { const e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; }

function loadScene(i) {
  const sc = SHOW.scenes[i];
  window.SHOW_TILES = SHOW.tiles;
  Chaos.prepare(sc, i);
  const root = document.importNode($("scene" + i).content.firstElementChild, true);
  const q = (cls) => root.querySelector(":scope > g." + cls);
  for (const old of svg.querySelectorAll("defs.scenedefs")) old.remove();
  const defs = root.querySelector(":scope > defs");
  defs.setAttribute("class", "scenedefs");
  svg.insertBefore(defs, svg.firstChild);
  backG.replaceChildren(...q("back").children);
  farG.replaceChildren(...q("far").children);
  camG.replaceChildren(...q("world").children);
  nearG.replaceChildren(...q("nearl").children);
  svg.setAttribute("viewBox", `0 0 ${sc.view[0]} ${sc.view[1]}`);
  Chaos.mount(camG, stage);
  const lays = [...farG.querySelectorAll(":scope > .lay"), ...nearG.querySelectorAll(":scope > .lay")].map((g) => ({ g, px: +g.dataset.px, py: +g.dataset.py }));
  const dyn = sc.dyn.map((d) => ({ d, g: $(d.id), u: $(d.id + "u"), frame: -1 }));
  const actors = sc.actors.map((a) => {
    const g = $(a.id);
    const poses = {};
    for (const p of g.querySelectorAll(":scope > .pose")) poses[p.dataset.pose] = { g: p, u: $(a.poses[p.dataset.pose].use), frame: -1 };
    const emotes = a.emotes.map((e) => ({ e, g: $(e.id + "g"), u: $(e.id), frame: -1 }));
    return { a, g, poses, emotes, shown: null, bubbleTarget: null };
  });
  bubblesEl.replaceChildren(); cardsEl.replaceChildren();
  const caps = sc.captions.map((c) => {
    const wl = c.who ? String(c.who).toLowerCase() : "";
    const who = c.who ? (actors.find((a) => a.a.name.toLowerCase() === wl) || actors.find((a) => wl.split(/\s+/).includes(a.a.name.toLowerCase()))) : null;
    if (c.kind === "title") {
      const d = el("div", "card", cardsEl);
      el("h1", "", d).textContent = c.text;
      if (c.sub) el("p", "", d).textContent = c.sub;
      return { c, d };
    }
    const d = el("div", "bubble" + (who ? "" : " bar"), bubblesEl);
    if (c.who) el("div", "who", d).textContent = c.who;
    const txt = el("div", "txt", d);
    const on = el("span", "on", txt), off = el("span", "off", txt);
    const chars = Array.from(c.text);
    off.textContent = c.text;
    return { c, d, on, off, chars, who, shownN: -1, bw: 0, bh: 0 };
  });
  S = { i, sc, lays, dyn, actors, caps, vw: sc.view[0], vh: sc.view[1], fx: { tint: 0 } };
  fitStage();
}

// ---------------------------------------------------------------------------------------------------------------- rain: scrolling streak tiles
const rainEl = $("rain");
const rainState = { far: null, near: null };
function rainTile(px, n, len, w, color, seed) {
  let a = seed, rnd = () => { a = (a * 1664525 + 1013904223) >>> 0; return a / 4294967296; };
  let l = "";
  for (let i = 0; i < n; i++) { const x = rnd() * px, y = rnd() * px, dx = -len * 0.12; for (const k of [-px, 0]) l += `<line x1="${x}" y1="${y + k}" x2="${x + dx}" y2="${y + k + len}" /><line x1="${x + px}" y1="${y + k}" x2="${x + dx + px}" y2="${y + k + len}" />`; }
  const svgt = `<svg xmlns='http://www.w3.org/2000/svg' width='${px}' height='${px}'><g stroke='${color}' stroke-width='${w}' stroke-linecap='round'>${l}</g></svg>`;
  return `url("data:image/svg+xml;utf8,${encodeURIComponent(svgt)}")`;
}
function setupRain() {
  const amt = S ? S.sc.rain : 0;
  rainEl.style.display = amt ? "block" : "none";
  if (!amt) return;
  const px = Math.max(200, Math.round(H * 0.8));
  for (const [k, n, len, w, col, sp] of [["far", 26, H * 0.04, Math.max(1, H * 0.0022), "rgba(150,170,185,.55)", 1.1], ["near", 14, H * 0.09, Math.max(1.4, H * 0.0036), "rgba(190,205,220,.7)", 1.9]]) {
    const d = rainEl.querySelector("." + k);
    d.style.cssText = `position:absolute;left:${-px}px;top:${-px}px;width:${W + 2 * px}px;height:${H + 2 * px}px;background-image:${rainTile(px, Math.round(n * amt), len, w, col, k === "far" ? 7 : 11)};background-size:${px}px ${px}px;opacity:${Math.min(1, 0.5 + amt * 0.5)}`;
    rainState[k] = { d, px, sp: sp * H };
  }
}
function moveRain(t) {
  if (!S || !S.sc.rain) return;
  for (const k of ["far", "near"]) { const r = rainState[k]; if (!r) continue; const y = (t * r.sp) % r.px; r.d.style.transform = `translate3d(${(-y * 0.12).toFixed(1)}px,${y.toFixed(1)}px,0)`; }
}
function fitStage() {
  if (!S) return;
  const aspect = S.vw / S.vh;
  const bw = innerWidth, bh = innerHeight;
  W = Math.min(bw, bh * aspect); H = W / aspect;
  stage.style.width = W + "px"; stage.style.height = H + "px";
  stage.style.setProperty("--u", H / 22 + "px");
  for (const c of S.caps) if (c.d) { c.bw = c.bh = 0; }
  setupRain();
}

// ---------------------------------------------------------------------------------------------------------------- drawing one moment
function setAttr(node, name, v) { const k = "__" + name; if (node && node[k] !== v) { node.setAttribute(name, v); node[k] = v; } }
function setHref(node, id) { if (node) node.setAttribute("href", "#" + id); }
const n3 = (v) => Math.round(v * 1000) / 1000;

function render(tReal) {
  const sc = S.sc;
  let t = tReal;
  const hold = stutterAt(sc, t);
  if (hold) t = Math.floor(t / hold) * hold;
  const [cols, rows] = sc.world;
  let [cx, cy, zoom] = camera(sc, t);
  zoom = Math.max(0.2, zoom);
  const wc = S.vw / zoom, wr = S.vh / zoom;
  cx = wc < cols ? clamp(cx, wc / 2, cols - wc / 2) : cols / 2;
  cy = wr < rows ? clamp(cy, wr / 2, rows - wr / 2) : rows / 2;
  const left = cx - wc / 2, top = cy - wr / 2;
  const wt = `scale(${n3(zoom)}) translate(${n3(-left)} ${n3(-top)})`;
  camG.setAttribute("transform", wt); backG.setAttribute("transform", wt);
  for (const L of S.lays) L.g.setAttribute("transform", `scale(${n3(zoom)}) translate(${n3(-left * L.px)} ${n3(-top * L.py)})`);

  // animated tiles: kmj frames, bob, sway, swim
  for (const D of S.dyn) {
    const d = D.d;
    let dx = 0, dy = 0, flip = d.flip, skew = 0;
    const u = (((t / ANIM_PERIOD + d.phase) % 1) + 1) % 1;
    if (d.bob) dy = Math.sin(2 * Math.PI * u) * 0.22;
    if (d.sway) { const amp = d.sway === true ? SWAY_AMP : d.sway; skew = -Math.atan(amp * Math.sin(2 * Math.PI * u - 0.9 * d.h / 2)) * 180 / Math.PI; }
    if (d.swim) { const [n, , period] = d.swim; const w = (((t / period + d.phase) % 1) + 1) % 1; dx = (1 - Math.abs(2 * w - 1)) * n; flip = flip !== (w > 0.5); }
    let tr = `translate(${n3(d.x + dx)} ${n3(d.y + dy)})`;
    if (skew) tr += ` translate(0 ${d.h}) skewX(${n3(skew)}) translate(0 ${-d.h})`;
    if (flip) tr += ` translate(${d.w} 0) scale(-1 1)`;
    setAttr(D.g, "transform", tr);
    if (d.frames) { const k = Math.floor(t * d.fps) % d.frames.length; if (k !== D.frame) { D.frame = k; setHref(D.u, d.frames[k]); } }
  }

  // the cast
  for (const A of S.actors) {
    const a = A.a;
    if (!visibleAt(a, t)) { if (A.shown !== "") { A.g.style.display = "none"; A.shown = ""; } for (const E of A.emotes) E.g.style.display = "none"; continue; }
    const name = poseAt(a, t), p = a.poses[name];
    if (A.shown !== name) { for (const k in A.poses) A.poses[k].g.style.display = k === name ? "" : "none"; A.g.style.display = ""; A.shown = name; }
    const [ax, ay] = position(a, t);
    const flip = flipAt(a, t);
    setAttr(A.g, "transform", flip ? `translate(${n3(ax + p.w)} ${n3(ay)}) scale(-1 1)` : `translate(${n3(ax)} ${n3(ay)})`);
    const P = A.poses[name];
    if (p.frames) { const k = Math.floor(t * p.fps) % p.frames.length; if (k !== P.frame) { P.frame = k; setHref(P.u, p.frames[k]); } }
    A.pos = [ax, ay, p.w, p.h];
    for (const E of A.emotes) {
      const age = t - E.e.t;
      if (age < 0 || age > E.e.sec) { E.g.style.display = "none"; continue; }
      const k = age / E.e.sec;
      const pop = 0.6 + 0.4 * Math.min(1, k * 5);
      const x = ax + (p.w - E.e.w * pop) / 2, y = ay - E.e.h * 0.9 - k * 0.8 * Math.max(1, p.w / 4);
      E.g.style.display = "";
      E.g.setAttribute("transform", `translate(${n3(x)} ${n3(y)}) scale(${n3(pop)})`);
      E.g.setAttribute("opacity", n3(Math.min(1, k * 6, (1 - k) * 3)));
      if (E.e.frames) { const f = Math.floor(age * E.e.fps) % E.e.frames.length; if (f !== E.frame) { E.frame = f; setHref(E.u, E.e.frames[f]); } }
    }
  }

  // the dialog: speech bubbles above the speaker, title cards, a bar for a voice nobody has
  const kpx = (W / S.vw) * zoom;
  for (const C of S.caps) {
    const c = C.c, age = t - c.t, a = fadeCurve(age, c.seconds);
    if (a <= 0) { if (C.d.style.display !== "none") C.d.style.display = "none"; continue; }
    C.d.style.display = "block";
    C.d.style.opacity = a;
    if (c.kind === "title") continue;
    const cps = Math.max(28, C.chars.length / (c.seconds * 0.45));
    const n = Math.min(C.chars.length, Math.floor(Math.max(0, age) * cps));
    if (n !== C.shownN) { C.shownN = n; C.on.textContent = C.chars.slice(0, n).join(""); C.off.textContent = C.chars.slice(n).join(""); }
    if (!C.bw) { C.bw = C.d.offsetWidth; C.bh = C.d.offsetHeight; }
    const m = H * 0.02;
    if (!C.who || !C.who.pos) {                                     // a caption bar at the bottom
      C.d.style.transform = `translate(${n3((W - C.bw) / 2)}px, ${n3(H - C.bh - H * 0.055)}px)`;
      continue;
    }
    const [ax, ay, aw, ah] = C.who.pos;
    const sx = (ax + aw / 2 - left) * kpx, sTop = (ay - top) * kpx, sBot = (ay + ah - top) * kpx;
    const gap = H * 0.035;
    const x = clamp(sx, C.bw / 2 + m, W - C.bw / 2 - m);
    let y = sTop - gap - C.bh, below = false;
    if (y < m) { y = sBot + gap; below = true; }
    y = clamp(y, m, H - C.bh - m);
    C.d.classList.toggle("below", below);
    C.d.style.setProperty("--tail", n3(clamp(sx - (x - C.bw / 2), H * 0.05, C.bw - H * 0.05)) + "px");
    C.d.style.transform = `translate(${n3(x - C.bw / 2)}px, ${n3(y)}px)`;
  }

  moveRain(tReal);
  if (Chaos.on) Chaos.draw(S, t, null);
  // fade and effects
  const [fa, fc] = fadeAt(sc, t);
  fadeEl.style.background = fc;
  fadeEl.style.opacity = Math.min(1, fa);
  effects(sc, tReal, t);
}

// ---------------------------------------------------------------------------------------------------------------- effects
const GRAIN = "url(\"data:image/svg+xml;utf8," + encodeURIComponent("<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .6 0 0 0 0 .6 0 0 0 0 .6 2.2 0 0 0 -1.05'/></filter><rect width='200' height='200' filter='url(#n)'/></svg>") + "\")";
const fxDivs = {};
function fxDiv(name) { return fxDivs[name] || (fxDivs[name] = el("div", name, fxEl)); }
const hash = (i, k) => { let x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
let mirrorSvg = null;
function effects(sc, t, held) {
  const i = Math.floor(t * sc.fps);
  const on = sc.fx.filter(([t0, t1, n]) => t >= t0 && t < t1 && n !== "stutter");
  const filters = [];
  let tf = "";
  const show = {};
  let mirror = false;
  const px = W / 640;
  on.forEach(([, , name, amt], n) => {
    const r = hash(i, n);
    if (name === "invert") filters.push(`invert(${amt >= 0.5 ? 1 : 2 * amt})`);
    else if (name === "blur") filters.push(`blur(${n3(W * 0.004 * amt)}px)`);
    else if (name === "solarize") { if (amt >= 0.5) filters.push("invert(.5) contrast(1.9)"); }
    else if (name === "flicker") filters.push(`brightness(${n3(1 + 0.157 * amt * (i % 2 ? 1 : -0.6))})`);
    else if (name === "rgb") { const d = W * 0.012 * amt * (1 + r); tf += ` translate(${n3(d * (r > 0.5 ? 1 : -1))}px,0)`; filters.push(`hue-rotate(${n3((r - 0.5) * 120 * amt)}deg) saturate(${n3(1.6 + amt * 0.6)}) contrast(1.15)`); }     // (a cheap stand in for a colour split: the real one is slow)
    else if (name === "glitch") {
      const d = W * 0.02 * amt * (r - 0.5) * 2; tf += ` translate(${n3(d)}px,${n3(H * 0.01 * (hash(i, n + 5) - 0.5) * amt)}px)`;
      filters.push(`saturate(${n3(1.5 + amt * 0.5)}) contrast(1.2)`);
      if (amt > 0.6 && r > 0.6) filters.push("hue-rotate(180deg)");
    } else if (name === "vhs") {
      tf += ` translate(${n3(Math.sin(i * 0.9) * 3 * amt * px)}px,0)`; show.scan = amt; show.bar = amt;
      filters.push(`saturate(1.4) hue-rotate(${n3(Math.sin(i) * 25)}deg)`);
    } else if (name === "zoom") tf += ` scale(${n3(1 + 0.35 * amt)})`;
    else if (name === "mirror") mirror = true;
    else if (name === "tilt") tf += ` rotate(${n3(amt)}deg) scale(${n3(1 + Math.abs(amt) * 0.022)})`;
    else if (name === "flipx") tf += " scaleX(-1)";
    else if (["grain", "scan", "tint", "vignette"].includes(name)) show[name] = amt;
  });
  svg.style.filter = filters.join(" ");
  svg.style.transform = tf;
  svg.style.transformOrigin = "50% 50%";
  const set = (name, amt, css) => { const d = fxDiv(name); d.style.display = amt ? "block" : "none"; if (amt) Object.assign(d.style, css(amt)); };
  set("tint", show.tint, (a) => ({ background: Math.floor(i / 3) % 2 ? "#ff3cac" : "#3cdcff", opacity: 0.4 * a }));
  set("vignette", show.vignette, (a) => ({ background: `radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,${0.55 * a}) 110%)` }));
  set("grain", show.grain, (a) => ({ backgroundImage: GRAIN, backgroundPosition: `${Math.floor(hash(i, 1) * 200)}px ${Math.floor(hash(i, 2) * 200)}px`, opacity: Math.min(1, 0.5 * a + 0.2) }));
  set("scan", show.scan, (a) => ({ backgroundImage: "repeating-linear-gradient(transparent 0, transparent 2px, rgba(0,0,0,.45) 2px, rgba(0,0,0,.45) 4px)", opacity: Math.min(1, a) }));
  set("bar", show.bar, (a) => ({ inset: "auto 0 auto 0", top: ((i * 13) % 100) + "%", height: "5%", background: `rgba(255,255,255,${0.2 * a})` }));
  if (mirror !== !!mirrorSvg) {
    if (mirror) { mirrorSvg = document.createElementNS(SVGNS, "svg"); mirrorSvg.id = "mirror"; stage.insertBefore(mirrorSvg, fxEl); }
    else { mirrorSvg.remove(); mirrorSvg = null; }
  }
  if (mirrorSvg) {
    mirrorSvg.setAttribute("viewBox", `0 0 ${S.vw} ${S.vh}`);
    mirrorSvg.style.display = "block";
    mirrorSvg.innerHTML = `<use href="#scenebox" transform="matrix(-1 0 0 1 ${S.vw} 0)"/>`;
    mirrorSvg.style.filter = svg.style.filter;
  }
}

// ---------------------------------------------------------------------------------------------------------------- clock, scenes, audio
let cur = -1, t = 0, playing = false, last = performance.now(), trans = null, ended = false, muted = false, gesture = false;
let userAudio = null;
const audioOf = (i) => { if (userAudio) return userAudio; const k = SHOW.audio[SHOW.scenes[i].name]; return k === undefined ? null : $("audio" + k); };
const fmt = (s) => { s = Math.max(0, Math.floor(s)); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
const TRANS = 0.4;

function buildBar() {
  scenesEl.replaceChildren();
  muteBtn.hidden = !Object.keys(SHOW.audio).length;
  SHOW.scenes.forEach((s, i) => { const b = el("button", "", scenesEl); b.textContent = `${i + 1} ${s.name}`; b.title = s.name; b.onclick = () => jump(i); });
}
function loadSound(file) {
  if (!file) return;
  if (userAudio) { userAudio.pause(); URL.revokeObjectURL(userAudio.src); }
  for (const k of Object.values(SHOW.audio)) $("audio" + k).pause();
  const a = userAudio = new Audio(URL.createObjectURL(file));
  a.preload = "auto"; a.muted = muted;
  a.onloadedmetadata = () => { SHOW.scenes.forEach((s) => (s.seconds = a.duration)); a.currentTime = 0; t = 0; ended = false; };
  a.onended = () => { if (userAudio === a) onEnd(); };
  muteBtn.hidden = false; soundBtn.title = "sound: " + file.name;
  setPlaying(true);
}
function markBar() { [...scenesEl.children].forEach((b, i) => b.classList.toggle("on", i === cur)); playBtn.textContent = playing ? "⏸" : (ended ? "↻" : "▶"); }

function enter(i, at = 0) {
  for (const k of Object.values(SHOW.audio)) { const a = $("audio" + k); a.pause(); }
  cur = i; loadScene(i); t = at; ended = false;
  const a = audioOf(i);
  if (a) { try { a.currentTime = at; } catch (e) {} a.muted = muted; if (playing) a.play().catch(needGesture); }
  markBar();
  render(t);
}
function jump(i, now = performance.now()) {
  if (cur < 0) { enter(i); return; }
  if (trans) return;
  trans = { to: i, t0: now, phase: "out" };
  if (!playing) { playing = true; }
  markBar();
}
function next(d) { const n = SHOW.scenes.length; jump((cur + d + n) % n); }
function needGesture() { startEl.hidden = false; playing = false; markBar(); }
function setPlaying(p) {
  playing = p;
  const a = audioOf(cur);
  if (a) { if (p) { if (ended) { a.currentTime = 0; } a.play().catch(needGesture); } else a.pause(); }
  if (p && ended) { ended = false; t = 0; }
  markBar();
}
function onEnd() {
  const sc = SHOW.scenes[cur];
  if (Chaos.on && Chaos.loop) { Chaos.bump(); enter(cur); return; }
  let nx = sc.next ? SHOW.scenes.findIndex((s) => s.name === sc.next) : cur + 1 < SHOW.scenes.length ? cur + 1 : SHOW.loop ? 0 : -1;
  if (nx < 0) { playing = false; ended = true; const a = audioOf(cur); if (a) a.pause(); markBar(); return; }
  jump(nx);
}

const cutEl = el("div", "", stage); cutEl.id = "cut";
function tick(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (S) {
    const sc = S.sc;
    if (trans) {
      const k = (now - trans.t0) / 1000 / TRANS;
      if (trans.phase === "out") {
        cutEl.style.opacity = clamp(k, 0, 1);
        const a = audioOf(cur); if (a) a.volume = clamp(1 - k, 0, 1);
        if (k >= 1) { const to = trans.to; const a2 = audioOf(cur); if (a2) a2.volume = 1; enter(to); trans = { to, t0: now, phase: "in" }; }
      } else {
        cutEl.style.opacity = clamp(1 - k, 0, 1);
        if (k >= 1) trans = null;
      }
    }
    if (playing && !(trans && trans.phase === "out")) {
      const a = audioOf(cur);
      if (a && !a.paused && a.currentTime > 0) t = a.currentTime; else t += dt;
      if (t >= sc.seconds && !trans && !(userAudio && !userAudio.ended && sc.seconds < userAudio.duration)) { t = sc.seconds - 1e-6; onEnd(); }
    }
    render(clamp(t, 0, sc.seconds));
    clockEl.textContent = `${fmt(t)} / ${fmt(sc.seconds)}`;
  }
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------------------------------------------------------- UI
let uiTimer = 0;
function showUi() { document.body.classList.add("ui"); clearTimeout(uiTimer); uiTimer = setTimeout(() => document.body.classList.remove("ui"), 2500); }
addEventListener("mousemove", showUi); addEventListener("touchstart", showUi);
addEventListener("resize", fitStage);
playBtn.onclick = () => setPlaying(!playing);
$("full").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());
muteBtn.onclick = () => { muted = !muted; muteBtn.textContent = muted ? "🔇" : "🔊"; for (const k of Object.values(SHOW.audio)) $("audio" + k).muted = muted; };
soundBtn.onclick = () => soundIn.click();
soundIn.onchange = () => loadSound(soundIn.files[0]);
addEventListener("dragover", (e) => e.preventDefault());
addEventListener("drop", (e) => { e.preventDefault(); const f = [...e.dataTransfer.files].find((x) => x.type.startsWith("audio") || /\.(mp3|wav|ogg|m4a|flac)$/i.test(x.name)); loadSound(f); });
startEl.querySelector("button").onclick = () => { startEl.hidden = true; gesture = true; setPlaying(true); };
addEventListener("keydown", (e) => {
  if (e.key === " " || e.key === "k") { e.preventDefault(); setPlaying(!playing); }
  else if (e.key === "ArrowRight" || e.key === "n") next(1);
  else if (e.key === "ArrowLeft" || e.key === "p") next(-1);
  else if (/^[1-9]$/.test(e.key) && +e.key <= SHOW.scenes.length) jump(+e.key - 1);
  else if (e.key === "r" && Chaos.on) { Chaos.bump(); trans = null; cutEl.style.opacity = 0; enter(cur); }
  else if (e.key === "f") $("full").click();
  else if (e.key === "m") muteBtn.click();
  showUi();
});

// ---------------------------------------------------------------------------------------------------------------- start
const params = new URLSearchParams(location.hash.slice(1));
if (params.has("clean")) document.body.classList.add("clean");
if (params.has("grid")) {                           // several takes at once: each tile is this page with its own seed
  const [gc, gr] = params.get("grid").split("x").map((v) => parseInt(v, 10) || 1);
  const seed0 = parseInt(params.get("chaos"), 10) || 1;
  document.body.innerHTML = `<div style="position:fixed;inset:0;display:grid;grid-template-columns:repeat(${gc},1fr);grid-template-rows:repeat(${gr},1fr);gap:2px;background:#000"></div>`;
  const box = document.body.firstChild;
  for (let k = 0; k < gc * gr; k++) {
    const f = document.createElement("iframe");
    f.style.cssText = "width:100%;height:100%;border:0;background:#000";
    f.src = location.href.split("#")[0] + "#chaos=" + (seed0 + k) + "&clean&loop" + (params.has("len") ? "&len=" + params.get("len") : "") + (params.has("rate") ? "&rate=" + params.get("rate") : "") + (params.has("scene") ? "&scene=" + params.get("scene") : "");
    box.appendChild(f);
  }
  return;
}
buildBar();
const first = Math.max(0, SHOW.scenes.findIndex((s) => s.name === params.get("scene")));
const paused = params.has("paused");
playing = !paused;
enter(first, +params.get("t") || 0);
if (!paused && audioOf(first)) { const a = audioOf(first); a.play().catch(needGesture); }
markBar();
window.show = { scenes: SHOW.scenes.map((s) => s.name), seek(name, at = 0) { const i = SHOW.scenes.findIndex((s) => s.name === name); trans = null; cutEl.style.opacity = 0; enter(i < 0 ? 0 : i, at); },
                pause: () => setPlaying(false), play: () => setPlaying(true), at: () => ({ scene: SHOW.scenes[cur].name, t }), render: (x) => { t = x; render(x); } };
showUi();
last = performance.now();
requestAnimationFrame(tick);
window.__ready = true;
})();
