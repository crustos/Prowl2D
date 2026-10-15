// player.js -- plays an exported Prowl2D level (tools/export_gpu_web.py) on the gpu-physics-engine, in the browser.
//
// Two engines behind one small interface: WebAssembly (the whole C runtime on the CPU) and WebGPU (the circle pipeline
// on the GPU, thousands of grains). `?engine=wasm|webgpu` picks one; the default is WebGPU where the browser has it.
// `?manual=1` stops the clock: window.player.step(n) advances n frames (what the tests use). `?level=URL` for another level.
//
// Controls: click drops a ball, B a crate, hold F and drag (or the sand tool) for sand, T hangs a rope, right click blasts
// (diggable tiles go, crates shatter into shards), R restarts.
// level.json's "curves" (see curves.js) are smooth Bezier surfaces: colliders on both engines, drawn by Windfoil (`?curves=canvas` for Canvas 2D).
import { loadGpuPhys } from "./gpuphys.js";
import { solidSide, bakeLayer } from "./curves.js";

const FIXED = 1 / 60, BALL_R = 0.35, SAND_R = 0.08, GRAVITY = [0, -18], SHARD_TTL = 2.5;
const q = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const canvas = $("screen"), ctx = canvas.getContext("2d"), msg = $("msg"), stats = $("stats");

// ------------------------------------------------------------------------------------------ engines
/** Hands level.json's curves to an engine's world: a solid's segments get the side its outline encloses, a wall is solid on both faces. */
function addCurves(world, curves) {
  let n = 0;
  for (const c of curves || []) {
    const side = c.kind === "wall" ? 0 : solidSide(c);
    for (const q of c.segments) if (world.addCurve(q[0], q[1], q[2], q[3], q[4], q[5], c.friction ?? 0.4, c.bounciness ?? 0, side) >= 0) n++;
  }
  return n;
}
class WasmEngine {
  static async create(level) {
    const gp = await loadGpuPhys(new URL("gpuphys.wasm", import.meta.url));
    return new WasmEngine(gp, level);
  }
  constructor(gp, level) {
    this.name = "wasm";
    this.world = gp.createWorld({ capacity: 24000, maxJoints: 48000, width: level.width, height: level.height, gravity: GRAVITY });
    this.sand = [];                 // circle indices of the grains
    this.bodies = new Map();        // id -> kind
  }
  setSolid(cells, w, h) { this.world.setTiles(w, h, cells); }
  addCurves(curves) { return addCurves(this.world, curves); }
  addBall(x, y, vx = 0, vy = 0) { const id = this.world.addBall(x, y, BALL_R, vx, vy); if (id >= 0) this.bodies.set(id, "ball"); return id; }
  addCrate(x, y, w, h, angle = 0, vx = 0, vy = 0) { const id = this.world.addBox(x, y, w, h, angle, vx, vy); if (id >= 0) this.bodies.set(id, "box"); return id; }
  addRope(ax, ay, bx, by) { const id = this.world.addRope(ax, ay, bx, by, 14, 0.09, true, false); if (id >= 0) this.bodies.set(id, "rope"); return id; }
  addSand(x, y, count) {
    let made = 0;
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2, d = 0.7 * Math.sqrt(Math.random());
      const c = this.world.addSand(x + Math.cos(a) * d, y + Math.sin(a) * d, SAND_R);
      if (c >= 0) { this.sand.push(c); made++; }
    }
    return made;
  }
  retire(id) { this.world.setBodyActive(id, false); this.bodies.delete(id); }
  async blast(x, y, r, f) { return this.world.blast(x, y, r, f); }
  step(dt) { this.world.step(dt); }
  get circles() { return this.world.circleCount; }
  async snapshot() {
    const poses = new Map(), ropes = new Map();
    for (const [id, kind] of this.bodies) {
      const p = this.world.bodyPose(id);
      poses.set(id, p);
      if (kind === "rope") {
        const pts = [], n = this.world.bodyCircles(id);
        for (let k = 0; k < n; k++) { const c = this.world.circle(this.world.bodyCircle(id, k)); pts.push([c.x, c.y]); }
        ropes.set(id, pts);
      }
    }
    const sand = new Float32Array(2 * this.sand.length);
    this.sand.forEach((c, i) => { const g = this.world.circle(c); sand[2 * i] = g.x; sand[2 * i + 1] = g.y; });
    return { poses, ropes, sand };
  }
}

class WebGpuEngine {
  static async create(level) {
    if (!navigator.gpu) throw new Error("no WebGPU in this browser");
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) throw new Error("no WebGPU adapter");
    const { GpuWorld } = await import("./gpuphys_webgpu.js");
    const device = await adapter.requestDevice({ requiredLimits: GpuWorld.limits(adapter) });
    device.lost.then((i) => { msg.textContent = "WebGPU device lost: " + i.message; });
    const world = await GpuWorld.create(device, { kernels: "spirv", capacity: 30000, world: [level.width, level.height], gravity: GRAVITY, maxRadius: 0.5 });
    return new WebGpuEngine(world, adapter);
  }
  constructor(world, adapter) { this.name = "webgpu"; this.world = world; this.adapter = adapter; this.bodies = new Map(); this.shapes = new Map(); }
  setSolid(cells, w, h) { this.world.setTileGrid(w, h, cells); }
  addCurves(curves) { return addCurves(this.world, curves); }
  addBall(x, y, vx = 0, vy = 0) { try { const id = this.world.addBall(x, y, BALL_R, vx, vy); this.bodies.set(id, "ball"); return id; } catch { return -1; } }
  addCrate(x, y, w, h, angle = 0, vx = 0, vy = 0) { try { const id = this.world.addBox(x, y, w, h, angle, vx, vy); this.bodies.set(id, "box"); return id; } catch { return -1; } }
  addRope(ax, ay, bx, by) { try { const id = this.world.addRope(ax, ay, bx, by, 14, 0.09, true, false); this.bodies.set(id, "rope"); return id; } catch { return -1; } }
  addSand(x, y, count) { return this.world.brushSand(x, y, 0.7, count, SAND_R); }
  retire(id) { if (this.world.bodies.has(id)) this.world.removeBody(id); this.bodies.delete(id); }
  async blast(x, y, r, f) { return this.world.blast(x, y, r, f); }
  step(dt) { this.world.step(dt); }
  get circles() { return this.world.n; }
  async snapshot() {
    const w = this.world, pos = await w.readPositions(), poses = new Map(), ropes = new Map();
    for (const [id, kind] of this.bodies) {
      const b = w.bodies.get(id);
      if (!b) continue;
      const cs = b.circles;
      let x = 0, y = 0;
      for (const c of cs) { x += pos[2 * c]; y += pos[2 * c + 1]; }
      let angle = 0;
      if (kind === "box") angle = Math.atan2(pos[2 * cs[1] + 1] - pos[2 * cs[0] + 1], pos[2 * cs[1]] - pos[2 * cs[0]]);
      poses.set(id, { x: x / cs.length, y: y / cs.length, angle });
      if (kind === "rope") ropes.set(id, cs.map((c) => [pos[2 * c], pos[2 * c + 1]]));
    }
    const sand = [];
    for (let i = 0; i < w.n; i++) if (w.tagMirror[i] === 1) sand.push(pos[2 * i], pos[2 * i + 1]);
    return { poses, ropes, sand: Float32Array.from(sand) };
  }
}

// ------------------------------------------------------------------------------------------- the game
const level = await (await fetch(q.get("level") || "level.json")).json();
const W = level.width, H = level.height;
$("title").textContent = level.name || "Prowl2D";
document.title = (level.name || "Prowl2D") + " - GPU physics";

const images = {};                                           // emoji -> [HTMLImageElement frames]
await Promise.all(Object.entries(level.tiles).map(async ([emoji, t]) => {
  if (!t.sprite) return;
  images[emoji] = await Promise.all(t.sprite.map((url) => new Promise((ok) => { const im = new Image(); im.onload = () => ok(im); im.src = url; })));
}));

let engine, state, layer = null;
async function makeEngine() {
  const want = q.get("engine") || "auto";
  const errors = [];
  for (const kind of want === "wasm" ? ["wasm"] : want === "webgpu" ? ["webgpu"] : ["webgpu", "wasm"]) {
    try { return kind === "wasm" ? await WasmEngine.create(level) : await WebGpuEngine.create(level); }
    catch (e) { errors.push(`${kind}: ${e.message}`); }
  }
  throw new Error(errors.join("; "));
}

function tileAt(tx, ty) { return level.cells[(H - 1 - ty) * W + tx]; }      // ty counts up from the bottom
function solidGrid() {
  const g = new Uint32Array(W * H);
  for (let ty = 0; ty < H; ty++) for (let tx = 0; tx < W; tx++) {
    const t = level.tiles[state.cells[(H - 1 - ty) * W + tx]];
    if (t && t.solid && !t.dynamic) g[ty * W + tx] = 1;
  }
  return g;
}

async function start() {
  state = { cells: [...level.cells], crates: new Map(), balls: [], shards: [], time: 0, acc: 0, snap: null, steps: 0 };
  engine = await makeEngine();
  engine.setSolid(solidGrid(), W, H);
  state.curves = engine.addCurves(level.curves);
  await rebake();
  for (let ty = 0; ty < H; ty++) for (let tx = 0; tx < W; tx++) {
    const emoji = state.cells[(H - 1 - ty) * W + tx], t = level.tiles[emoji];
    if (t && t.dynamic) {                                       // a movable tile becomes a crate
      const id = engine.addCrate(tx + 0.5, ty + 0.5, 1, 1);
      if (id >= 0) { state.crates.set(id, { emoji }); state.cells[(H - 1 - ty) * W + tx] = ""; }
    }
  }
  state.snap = await engine.snapshot();
  msg.textContent = "";
}

function shatter(id, crate) {
  const p = state.snap?.poses.get(id);
  if (!p) return;
  engine.retire(id); state.crates.delete(id);
  for (let i = 0; i < 7; i++) {
    const s = 0.22 + Math.random() * 0.18, ox = (Math.random() - 0.5) * 0.6, oy = (Math.random() - 0.5) * 0.6;
    const sid = engine.addCrate(p.x + ox, p.y + oy, s, s, Math.random() * 3.14, ox * 8 + (Math.random() - 0.5) * 2, oy * 8 + 1 + Math.random() * 3);
    if (sid >= 0) state.shards.push({ id: sid, ttl: SHARD_TTL, size: s, emoji: crate.emoji });
  }
}

async function blast(x, y, radius = 3.5, force = 40) {
  let dug = false;
  for (let ty = Math.floor(y - radius); ty <= Math.ceil(y + radius); ty++) for (let tx = Math.floor(x - radius); tx <= Math.ceil(x + radius); tx++) {
    if (tx < 0 || ty < 0 || tx >= W || ty >= H) continue;
    const i = (H - 1 - ty) * W + tx, t = level.tiles[state.cells[i]];
    if (t && t.diggable && Math.hypot(tx + 0.5 - x, ty + 0.5 - y) < radius * 0.8) { state.cells[i] = ""; dug = true; }
  }
  if (dug) engine.setSolid(solidGrid(), W, H);
  for (const [id, crate] of [...state.crates]) {
    const p = state.snap?.poses.get(id);
    if (p && Math.hypot(p.x - x, p.y - y) < radius * 0.45) shatter(id, crate);
  }
  await engine.blast(x, y, radius, force);
}

function stepOnce() {
  engine.step(FIXED);
  state.time += FIXED; state.steps++;
  for (const s of [...state.shards]) if ((s.ttl -= FIXED) <= 0) { engine.retire(s.id); state.shards.splice(state.shards.indexOf(s), 1); }
}

// ---------------------------------------------------------------------------------------------- draw
const view = { s: 1, ox: 0, oy: 0 };
function fit() {
  const r = canvas.getBoundingClientRect(), d = devicePixelRatio || 1;
  canvas.width = Math.max(2, Math.round(r.width * d)); canvas.height = Math.max(2, Math.round(r.height * d));
  view.s = Math.min(canvas.width / W, canvas.height / H);
  view.ox = (canvas.width - W * view.s) / 2; view.oy = (canvas.height - H * view.s) / 2;
}
/** Paints the curves for the current canvas size (at the start and after a resize). */
async function rebake(mode = q.get("curves") || "auto") {
  layer = null;
  if (!level.curves?.length) return null;
  layer = await bakeLayer(level.curves, { width: canvas.width, height: canvas.height, scale: view.s, camera: [W / 2, H / 2], mode });
  return layer;
}
const toScreen = (x, y) => [view.ox + x * view.s, view.oy + (H - y) * view.s];
function toWorld(ev) {
  const r = canvas.getBoundingClientRect(), px = (ev.clientX - r.left) * canvas.width / r.width, py = (ev.clientY - r.top) * canvas.height / r.height;
  return [(px - view.ox) / view.s, H - (py - view.oy) / view.s];
}
function frameOf(emoji) {
  const f = images[emoji], t = level.tiles[emoji];
  return f ? f[Math.floor(state.time * (t.fps || 8)) % f.length] : null;
}
function draw() {
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#0b0e13"; ctx.fillRect(0, 0, canvas.width, canvas.height);
  const g = ctx.createLinearGradient(0, view.oy, 0, view.oy + H * view.s);
  g.addColorStop(0, "#1d2a44"); g.addColorStop(1, "#3a4a63");
  ctx.fillStyle = g; ctx.fillRect(view.ox, view.oy, W * view.s, H * view.s);
  for (let ty = 0; ty < H; ty++) for (let tx = 0; tx < W; tx++) {
    const emoji = state.cells[(H - 1 - ty) * W + tx];
    if (!emoji) continue;
    const [sx, sy] = toScreen(tx, ty + 1), im = frameOf(emoji);
    if (im) ctx.drawImage(im, sx, sy, view.s + 0.5, view.s + 0.5);
    else { ctx.fillStyle = "#6b7a90"; ctx.fillRect(sx, sy, view.s, view.s); }
  }
  if (layer?.canvas) ctx.drawImage(layer.canvas, 0, 0);
  const snap = state.snap;
  if (!snap) return;
  for (const [id, crate] of state.crates) drawBox(snap.poses.get(id), 1, 1, crate.emoji);
  for (const s of state.shards) drawBox(snap.poses.get(s.id), s.size, s.size, s.emoji);
  for (const pts of snap.ropes.values()) {
    ctx.strokeStyle = "#a07a45"; ctx.lineWidth = Math.max(2, 0.18 * view.s); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.beginPath();
    pts.forEach(([x, y], i) => { const [sx, sy] = toScreen(x, y); i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); });
    ctx.stroke();
  }
  ctx.fillStyle = "#dcbd6b";
  for (let i = 0; i < snap.sand.length; i += 2) {
    const [sx, sy] = toScreen(snap.sand[i], snap.sand[i + 1]);
    ctx.fillRect(sx - SAND_R * view.s, sy - SAND_R * view.s, 2 * SAND_R * view.s, 2 * SAND_R * view.s);
  }
  for (const [id, kind] of engine.bodies) {
    const p = snap.poses.get(id);
    if (kind !== "ball" || !p) continue;
    const [sx, sy] = toScreen(p.x, p.y), r = BALL_R * view.s;
    const rg = ctx.createRadialGradient(sx - r * 0.35, sy - r * 0.35, r * 0.1, sx, sy, r);
    rg.addColorStop(0, "#9cc8ff"); rg.addColorStop(1, "#3d74d6");
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(sx, sy, r, 0, 7); ctx.fill();
  }
  stats.textContent = `${engine.name}${engine.adapter ? " · " + (engine.adapter.info?.description || engine.adapter.info?.vendor || "gpu") : ""} · ${engine.circles} circles · ${fps.toFixed(0)} fps`;
}
function drawBox(p, w, h, emoji) {
  if (!p) return;
  const [sx, sy] = toScreen(p.x, p.y), im = frameOf(emoji);
  ctx.save(); ctx.translate(sx, sy); ctx.rotate(-p.angle);
  if (im) ctx.drawImage(im, -w * view.s / 2, -h * view.s / 2, w * view.s, h * view.s);
  else { ctx.fillStyle = "#9a6b3a"; ctx.fillRect(-w * view.s / 2, -h * view.s / 2, w * view.s, h * view.s); }
  ctx.restore();
}

// -------------------------------------------------------------------------------------------- input
let tool = "ball", pointer = null, held = new Set(), fps = 0;
function setTool(t) { tool = t; document.querySelectorAll("[data-tool]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.tool === t)); }
document.querySelectorAll("[data-tool]").forEach((b) => (b.onclick = () => setTool(b.dataset.tool)));
$("reset").onclick = () => restart();
addEventListener("keydown", (e) => {
  held.add(e.key.toLowerCase());
  if (e.key === "r" || e.key === "R") restart();
  if (e.key === "b" || e.key === "B") act("crate", pointer ?? [W / 2, H - 2]);
  if (e.key === "t" || e.key === "T") act("rope", pointer ?? [W / 2, H - 2]);
});
addEventListener("keyup", (e) => held.delete(e.key.toLowerCase()));
canvas.addEventListener("contextmenu", (e) => e.preventDefault());
canvas.addEventListener("pointerdown", (e) => {
  pointer = toWorld(e); canvas.setPointerCapture(e.pointerId); state.down = true;
  act(e.button === 2 ? "blast" : tool, pointer);
});
canvas.addEventListener("pointermove", (e) => { pointer = toWorld(e); });
canvas.addEventListener("pointerup", () => { state.down = false; });
async function act(what, [x, y]) {
  if (what === "ball") { const id = engine.addBall(x, y, (Math.random() - 0.5) * 3, 0); if (id < 0) msg.textContent = "the world is full"; }
  else if (what === "crate") { const id = engine.addCrate(x, y, 1, 1, Math.random() * 3); if (id >= 0) state.crates.set(id, { emoji: Object.keys(level.tiles).find((e) => level.tiles[e].dynamic) ?? "" }); }
  else if (what === "rope") engine.addRope(x, y, x + 6, y);
  else if (what === "sand") engine.addSand(x, y, 24);
  else if (what === "blast") await blast(x, y);
}

// -------------------------------------------------------------------------------------------- loop
async function restart() { await start(); }
fit();
let resizing = 0;
addEventListener("resize", () => { fit(); clearTimeout(resizing); resizing = setTimeout(() => rebake().then(draw), 150); });
await start();

let last = performance.now(), counted = 0, since = last, busy = false;
async function frame(now) {
  if (busy) return requestAnimationFrame(frame);
  busy = true;
  try {
    state.acc += Math.min((now - last) / 1000, 0.1); last = now;
    if (state.down && (tool === "sand" || held.has("f")) && pointer) engine.addSand(pointer[0], pointer[1], 6);
    let n = 0;
    while (state.acc >= FIXED && n < 4) { stepOnce(); state.acc -= FIXED; n++; }
    state.snap = await engine.snapshot();
    draw();
    counted++;
    if (now - since > 500) { fps = counted * 1000 / (now - since); counted = 0; since = now; }
  } catch (e) { msg.textContent = e.message; console.error(e); }
  busy = false;
  requestAnimationFrame(frame);
}
if (!q.has("manual")) requestAnimationFrame(frame);

// the tests' handle
window.player = {
  get engine() { return engine.name; }, level, get state() { return state; },
  async step(n = 1) { for (let i = 0; i < n; i++) stepOnce(); state.snap = await engine.snapshot(); draw(); return state.steps; },
  act, blast, restart, rebake, get layer() { return layer; }, get snap() { return state.snap; }, get circles() { return engine.circles; },
  get engineObject() { return engine; },
  async png() { return canvas.toDataURL("image/png"); },
};
window.__ready = true;
