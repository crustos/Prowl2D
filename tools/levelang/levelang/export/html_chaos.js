// The chaos director: with  #chaos=SEED  the scene is replaced by a random, repeatable take of it: fast cuts, tilts, flashes, strobes, colour washes,
// beams, fights in the pit, guitars and keyboards smashed. Everything is made from the seed, so the same seed is the same take.
//   A page with a director plays take after take by itself (seed 1, 2, 3 ...; the r key skips to the next); #nochaos plays the plain scene instead.
//   #chaos=7 (start at seed 7)  &len=60 (seconds)  &noloop (stop after one take)  &clean (no controls, no cursor, no label)  &rate=1.5 (denser)
//   #grid=3x2&chaos=100  shows 6 takes (seeds 100..105) side by side, to record them all at once.
(() => {
"use strict";
const P = new URLSearchParams(location.hash.slice(1));
const HAS = document.getElementById("show").textContent.includes('"chaos":{');     // the page has a director set up
const ON = !P.has("grid") && !P.has("nochaos") && (P.has("chaos") || HAS);
let seed = ON ? (parseInt(P.get("chaos"), 10) || 1) : 0;
const LEN = Math.max(5, parseFloat(P.get("len")) || 60), LOOP = !P.has("noloop"), RATE = parseFloat(P.get("rate")) || 1;
const TAU = Math.PI * 2;
const mul = (a) => () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const lerp = (a, b, u) => a + (b - a) * u, clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const f1 = (v) => Math.round(v * 100) / 100;
const WASH = ["#ff1744", "#2979ff", "#ffd600", "#ff3cac", "#00e5ff", "#76ff03", "#b388ff", "#ffffff"];
const BEAM = ["#ff2040", "#3070ff", "#ffe030", "#ff40b0", "#30f0ff", "#90ff40", "#c090ff", "#ffffff"];
const DARK = "#1a0f08";

let C = null;                       // the current take: { sc, cfg, ev, beams, washes, strobes, ... }

// ------------------------------------------------------------------------------------------------------------------------ building a take
function prepare(sc, idx) {
  if (!sc.__o) sc.__o = { cams: sc.cams, punches: sc.punches, shakes: sc.shakes, fades: sc.fades, fx: sc.fx, seconds: sc.seconds };
  if (!ON) { C = null; return; }
  const o = sc.__o;
  sc.cams = o.cams.slice(); sc.punches = o.punches.slice(); sc.shakes = o.shakes.slice(); sc.fades = o.fades.slice(); sc.fx = o.fx.slice(); sc.captions = sc.captions;
  const cfg = sc.chaos || {};
  const R = mul(seed * 1009 + idx * 7919 + 17);
  const rr = (a, b) => a + (b - a) * R(), pick = (a) => a[Math.floor(R() * a.length)], chance = (p) => R() < p;
  const rate = RATE * (cfg.rate || 1), T = LEN;
  const W = sc.world[0], H = sc.world[1];
  const pit = cfg.pit, crowd = cfg.crowd && cfg.crowd.length ? cfg.crowd : null;
  const members = [], bandDyn = {};
  for (const [role, tile] of Object.entries(cfg.band || {})) {
    bandDyn[role] = sc.dyn.filter((d) => d.tile === tile);
    for (const d of bandDyn[role]) members.push([d.x + d.w / 2, d.y + d.h / 2]);
  }
  const rigs = cfg.rigs || [], fbk = cfg.feedback;
  const ev = [];
  const person = () => (crowd ? pick(crowd) : null);
  // ---- events with something to look at: fights, jumpers, surfers, smashes
  if (pit && crowd) {
    for (let t = rr(0.2, 1); t < T; t += rr(0.7, 2.4) / rate) {
      const k = R();
      const x = rr(pit[0] + 2, pit[1] - 2);
      if (k < 0.45) ev.push({ k: "fight", t, d: rr(0.9, 1.9), x, y: pit[2], a: person(), b: person(), dir: chance(0.5) ? 1 : -1, s: R() * 1e6, f: [x, pit[2] - 3, rr(1.2, 2.2)] });
      else if (k < 0.75) ev.push({ k: "jump", t, d: rr(1.2, 3.2), x, y: pit[2], n: 3 + Math.floor(R() * 4), s: R() * 1e6, tiles: [person(), person(), person(), person(), person(), person()], f: [x, pit[2] - 4, rr(1, 1.8)] });
      else ev.push({ k: "surf", t, d: rr(1, 1.8), x, x1: x + rr(-14, 14), y: pit[2] - rr(4.5, 7), a: person(), s: R() * 1e6, f: [x, pit[2] - 5, rr(1, 1.7)] });
    }
  }
  for (const [role, ds] of Object.entries(bandDyn)) {
    for (const d of ds) {
      for (let t = rr(1, 6); t < T; t += rr(4.5, 10) / rate)
        ev.push({ k: "smash", role, t, d: role === "keys" ? 1.7 : role === "drums" ? 1.3 : 1.5, dyn: d, a: person(), s: R() * 1e6, f: [d.x + d.w / 2, d.y + d.h / 2, rr(1.5, 2.4)] });
    }
  }
  ev.sort((a, b) => a.t - b.t);
  // ---- mud: volleys thrown from the crowd at the crowd, at the band and at the stage (not events the camera waits for: they are everywhere)
  const vol = [];
  const throwRate = (cfg.throw || 0) * rate;
  if (pit && throwRate > 0) {
    const targetsBand = members.length ? members : [];
    for (let t = rr(0, 0.6); t < T; t += rr(0.5, 1.6) / throwRate) {
      const sx = rr(pit[0] + 1, pit[1] - 1), sy = pit[2] - rr(1.8, 3.4), n = 3 + Math.floor(R() * 4);
      const kind = R() < 0.4 && targetsBand.length ? "band" : R() < 0.7 ? "crowd" : "stage";
      const balls = [];
      for (let i = 0; i < n; i++) {
        let tx, ty;
        if (kind === "band") { const m = pick(targetsBand); tx = m[0] + rr(-1.2, 1.2); ty = m[1] + rr(-1.5, 1.5); }
        else if (kind === "stage" && cfg.floor != null) { tx = rr(2, Math.max(6, pit[0] - 3)); ty = cfg.floor - rr(0, 1); }
        else { tx = sx + rr(-14, 14); ty = pit[2] - rr(1.5, 3.4); }
        const T1 = rr(0.45, 0.85) * (1 + Math.abs(tx - sx) / 60);
        balls.push({ x0: sx + rr(-1.2, 1.2), y0: sy + rr(-0.5, 0.5), tx, ty, T1, d: i * rr(0.05, 0.14), r: rr(0.25, 0.5), s: R() * 1e6 });
      }
      vol.push({ t, balls, kind });
    }
  }
  const fb = [];
  if (fbk) for (let u = rr(0.2, 1.5); u < T; u += rr(1.2, 3.5) / rate) { fb.push({ t: u, d: rr(0.4, 1.8) }); u += 0; }
  // ---- camera: cuts, drifts, punches, shakes, tilts
  const wide = cfg.shots || [], rooms = cfg.rooms || [];
  const shot = () => {
    let k = R();
    if (rooms.length) {
      if (k < 0.14) {                    // a room of its own (a big face, a wall of screens): fill the frame exactly, zoomed in a little at times
        const r = pick(rooms), z = Math.max(sc.view[0] / r[2], sc.view[1] / r[3]) * (R() < 0.5 ? 1 : rr(1, 1.5));
        return [r[0] + r[2] / 2 + rr(-1, 1) * Math.max(0, (r[2] - sc.view[0] / z) / 2), r[1] + r[3] / 2 + rr(-1, 1) * Math.max(0, (r[3] - sc.view[1] / z) / 2), z];
      }
      k = (k - 0.14) / 0.86;                           // the other shots keep their odds
    }
    if (rigs.length && k < 0.24) {                     // close on the hands: the knobs, sliders and pads of a rig
      const r = pick(rigs), zoom = (sc.view[0] / (r[2] * rr(0.55, 1.1)));
      return [r[0] + r[2] * rr(0.25, 0.75), r[1] + r[3] * rr(0.4, 0.75), zoom];
    }
    if (fbk && k < 0.3) return [fbk[1] + rr(-1.5, 1.5), fbk[2] + rr(-1, 2), rr(1.6, 3.2)];      // the guitarist and his speaker
    if (k < 0.4 && wide.length) { const s = pick(wide); return [s[0] + rr(-3, 3), s[1] + rr(-2, 2), s[2] * rr(0.85, 1.2)]; }
    if (k < 0.5 && cfg.singer) return [cfg.singer[0] + rr(-1.5, 1.5), cfg.singer[1] + rr(-1.5, 1.5), rr(1.3, 2.8)];
    if (k < 0.66 && members.length) { const m = pick(members); return [m[0] + rr(-1, 1), m[1] + rr(-1, 1), rr(1.4, 2.8)]; }
    if (k < 0.88 && pit) return [rr(pit[0], pit[1]), pit[2] - 3 + rr(-1, 1), rr(0.9, 2.2)];
    return [rr(0, W), rr(0, H), rr(0.5, 1.4)];
  };
  let t = 0, ei = 0;
  while (t < T) {
    let dur = R() < 0.5 ? rr(0.07, 0.2) : R() < 0.7 ? rr(0.2, 0.55) : rr(0.55, 1.4);
    dur /= rate;
    while (ei < ev.length && ev[ei].t < t - 0.05) ei++;
    let s = shot(), ee = ei < ev.length && ev[ei].t < t + Math.max(dur, 0.3) && chance(0.7) ? ev[ei] : null;
    if (ee) { s = ee.f; dur = Math.max(dur, Math.min(0.9, ee.d * 0.6)); ei++; }
    sc.cams.push([t, s[0], s[1], s[2], "cut"]);
    if (chance(0.35)) sc.cams.push([t + dur - 0.001, s[0] + rr(-3, 3), s[1] + rr(-1.5, 1.5), s[2] * rr(0.85, 1.3), "linear"]);
    if (chance(0.5)) sc.punches.push([t, rr(0.05, 0.3), rr(0.1, 0.3)]);
    if (chance(0.25)) sc.shakes.push([t, t + rr(0.1, 0.45), rr(0.15, 0.7)]);
    if (chance(0.25)) sc.fx.push([t, t + dur, "tilt", rr(4, 16) * (chance(0.5) ? -1 : 1)]);
    if (chance(0.12)) sc.fx.push([t, t + dur, "flipx", 1]);
    t += dur;
  }
  sc.cams.sort((a, b) => a[0] - b[0]);
  // ---- effects, flashes
  sc.fx.push([0, T, "grain", cfg.grain || 0.4], [0, T, "vignette", 1]);
  const FX = ["glitch", "glitch", "rgb", "rgb", "flicker", "flicker", "invert", "vhs", "zoom", "blur", "tint", "solarize", "stutter", "mirror"];
  for (let u = rr(0, 0.3); u < T; u += rr(0.1, 0.5) / rate) {
    const n = pick(FX);
    sc.fx.push([u, u + (n === "invert" ? rr(0.03, 0.1) : rr(0.04, 0.35)), n, n === "stutter" ? rr(6, 12) : rr(0.6, 1.6)]);
  }
  for (let u = rr(0, 0.5); u < T; u += rr(0.3, 1.5) / rate) {
    const k = R();
    if (k < 0.5) sc.fades.push([u, u + rr(0.05, 0.14), rr(0.5, 0.9), 0, "white"]);
    else if (k < 0.65) sc.fades.push([u, u + rr(0.08, 0.25), 1, 0, "black"]);
    else if (k < 0.9) sc.fades.push([u, u + rr(0.06, 0.18), rr(0.35, 0.7), 0, pick(["#ff2040", "#2a60ff", "#ffd400", "#ff3cac"])]);
    else { sc.fades.push([u, u + 0.05, 1, 0, "#dfe8ff"]); sc.fades.push([u + 0.09, u + 0.3, 0.9, 0, "#dfe8ff"]); }
  }
  // ---- lights: beams that sweep and blink, colour washes, strobes
  const beams = [], src = cfg.lights && cfg.lights.length ? cfg.lights : [[W / 2, 2]];
  for (const [sx, sy] of src) {
    for (let u = rr(0, 1); u < T; u += rr(0.3, 1.8)) {
      const on = rr(0.2, 1.6) / rate;
      beams.push({ t0: u, t1: u + on, sx, sy, c: Math.floor(R() * BEAM.length), base: rr(-35, 35), amp: rr(5, 30), fr: rr(1, 6), ph: R() * TAU, sp: rr(4, 10), len: (cfg.floor == null ? H : cfg.floor) - sy + 8 });
      u += on;
    }
  }
  const washes = [], strobes = [];
  for (let u = rr(0, 0.5); u < T; u += rr(0.1, 0.9) / rate) washes.push([u, u + rr(0.08, 0.5), pick(WASH), rr(0.1, 0.38)]);
  for (let u = rr(1, 3); u < T; u += rr(2, 6) / rate) strobes.push([u, u + rr(0.3, 1.2), rr(8, 18)]);
  // ---- the impacts: shake, punch, flash where things break
  for (const e of ev) {
    if (e.k === "smash") {
      const hit = e.t + e.d * (e.role === "drums" ? 0.3 : 0.42);
      sc.shakes.push([hit, hit + 0.35, rr(0.4, 0.9)]); sc.punches.push([hit, 0.2, 0.25]); sc.fades.push([hit, hit + 0.1, 0.8, 0, "white"]);
      sc.fx.push([hit, hit + 0.15, "rgb", 1.4]);
      e.hit = hit;
      if (cfg.smash_at && cfg.smash_at[e.role] && cfg.feedback) fb.push({ t: hit - 0.1, d: 1.4 });
    } else if (e.k === "fight") { sc.shakes.push([e.t + 0.15, e.t + 0.15 + e.d * 0.6, 0.25]); }
  }
  sc.shakes.sort((a, b) => a[0] - b[0]);
  if (P.has("calm")) { sc.fx = o.fx.slice(); sc.fades = o.fades.slice(); washes.length = 0; strobes.length = 0; }       // debugging: just the props
  if (P.has("lock")) { const [lx, ly, lz] = P.get("lock").split(",").map(Number); sc.cams = [[0, lx, ly, lz, "cut"]]; sc.punches = []; sc.shakes = []; }
  sc.seconds = T;
  for (const f of fb) sc.shakes.push([f.t, f.t + f.d, 0.12]);
  sc.shakes.sort((a, b) => a[0] - b[0]);
  C = { sc, cfg, ev, vol, fb, beams, washes, strobes, hidden: new Set() };
}

// ------------------------------------------------------------------------------------------------------------------------ drawing the props
const tilesOf = () => window.SHOW_TILES;
function frameId(tile, t, off = 0) {
  const info = tilesOf()[String(tile)];
  if (!info || !info.frames || !info.frames.length) return null;
  const k = info.frames.length > 1 ? Math.floor((t + off) * (info.fps || 8)) % info.frames.length : 0;
  return info.frames[k];
}
function human(tile, x, y, w, h, t, o = {}) {      // a crowd person with the box top left (x, y), turned, rolled (rot degrees about the middle)
  const id = frameId(tile, t, o.off || 0);
  if (!id) return "";
  const cx = x + w / 2, cy = y + h / 2;
  let tr = `translate(${f1(cx)} ${f1(cy)})`;
  if (o.rot) tr += ` rotate(${f1(o.rot)})`;
  if (o.flip) tr += " scale(-1 1)";
  return `<use href="#${id}" x="${f1(-w / 2)}" y="${f1(-h / 2)}" width="${f1(w)}" height="${f1(h)}" transform="${tr}"/>`;
}
const star = (x, y, r, rot, fill) => {
  let p = "";
  for (let i = 0; i < 10; i++) { const a = rot + i * Math.PI / 5, rad = i % 2 ? r * 0.45 : r; p += `${f1(x + Math.cos(a) * rad)},${f1(y + Math.sin(a) * rad)} `; }
  return `<polygon points="${p}" fill="${fill}" stroke="${DARK}" stroke-width="0.07"/>`;
};
function cloud(x, y, r, t, seedv) {                  // a cartoon brawl: a rolling dust cloud with fists, feet and stars
  const R = mul(Math.floor(t * 12) + Math.floor(seedv));
  let o = "";
  for (let i = 0; i < 9; i++) { const a = i * 0.7 + t * 6, rad = r * (0.45 + 0.25 * Math.sin(i * 2 + t * 14)); o += `<circle cx="${f1(x + Math.cos(a) * rad)}" cy="${f1(y + Math.sin(a) * rad * 0.8)}" r="${f1(r * 0.5)}" fill="${i % 2 ? "#d9d4c6" : "#bdb7a6"}" stroke="#7a7466" stroke-width="0.08"/>`; }
  for (let i = 0; i < 5; i++) {                      // limbs poking out
    const a = R() * TAU, l = r * (0.9 + R() * 0.5), hx = x + Math.cos(a) * l, hy = y + Math.sin(a) * l * 0.8;
    o += `<line x1="${f1(x + Math.cos(a) * r * 0.4)}" y1="${f1(y + Math.sin(a) * r * 0.3)}" x2="${f1(hx)}" y2="${f1(hy)}" stroke="${DARK}" stroke-width="0.55" stroke-linecap="round"/><line x1="${f1(x + Math.cos(a) * r * 0.4)}" y1="${f1(y + Math.sin(a) * r * 0.3)}" x2="${f1(hx)}" y2="${f1(hy)}" stroke="#5b4126" stroke-width="0.34" stroke-linecap="round"/><circle cx="${f1(hx)}" cy="${f1(hy)}" r="0.34" fill="#6b4a26" stroke="${DARK}" stroke-width="0.1"/>`;
  }
  for (let i = 0; i < 3; i++) o += star(x + (R() - 0.5) * r * 2.2, y + (R() - 0.7) * r * 1.8, 0.45 + R() * 0.4, R() * 3, ["#ffe030", "#ff6a30", "#ffffff"][i]);
  return o;
}
function splat(x, y, u, n, seedv) {                  // mud thrown up and falling
  const R = mul(Math.floor(seedv));
  let o = "";
  for (let i = 0; i < n; i++) {
    const vx = (R() - 0.5) * 18, vy = -8 - R() * 16, g = 44;
    o += `<circle cx="${f1(x + vx * u)}" cy="${f1(y + vy * u + 0.5 * g * u * u)}" r="${f1(0.18 + R() * 0.3)}" fill="${R() < 0.7 ? "#4a3018" : "#7d5c36"}"/>`;
  }
  return o;
}
function guitar(x, y, L, ang, col, flip) {            // an electric guitar held by the neck's base at (x, y), length L, pointing along `ang` degrees
  const s = flip ? -1 : 1;
  return `<g transform="translate(${f1(x)} ${f1(y)}) scale(${s} 1) rotate(${f1(ang)}) scale(${f1(L)})"><ellipse cx="-0.16" cy="0.02" rx="0.24" ry="0.17" fill="${col}" stroke="${DARK}" stroke-width="0.03"/><ellipse cx="-0.08" cy="-0.1" rx="0.12" ry="0.08" fill="${col}" stroke="${DARK}" stroke-width="0.03"/><rect x="0.05" y="-0.035" width="0.9" height="0.07" fill="#3a2410" stroke="${DARK}" stroke-width="0.025"/><rect x="0.95" y="-0.06" width="0.16" height="0.12" rx="0.02" fill="${DARK}"/><circle cx="-0.18" cy="0.04" r="0.03" fill="#d8d8d8"/><line x1="-0.1" y1="0" x2="0.95" y2="0" stroke="#e8e8e8" stroke-width="0.012"/></g>`;
}
function piece(kind, x, y, rot, L, col) {
  if (kind === "gA") return `<g transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)}) scale(${f1(L)})"><path d="M-0.4 0.02 C-0.4 -0.15 -0.2 -0.2 -0.05 -0.12 L0.0 -0.02 L-0.06 0.05 L-0.02 0.17 C-0.2 0.2 -0.4 0.17 -0.4 0.02 Z" fill="${col}" stroke="${DARK}" stroke-width="0.03"/><line x1="-0.1" y1="0" x2="0.1" y2="-0.05" stroke="#e8e8e8" stroke-width="0.015"/></g>`;
  if (kind === "gB") return `<g transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)}) scale(${f1(L)})"><path d="M-0.05 -0.12 L0.05 -0.035 L0.95 -0.035 L0.95 0.035 L0.05 0.035 L-0.02 0.17 L-0.08 0.05 L-0.04 -0.04 Z" fill="${col}" stroke="${DARK}" stroke-width="0.03"/><rect x="0.95" y="-0.06" width="0.16" height="0.12" rx="0.02" fill="${DARK}"/></g>`;
  if (kind === "splinter") return `<polygon points="0,-0.25 0.5,0 0,0.25" transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)}) scale(${f1(L)})" fill="#a97b45" stroke="${DARK}" stroke-width="0.12"/>`;
  if (kind === "key") return `<rect x="${f1(-L * 0.2)}" y="${f1(-L * 0.6)}" width="${f1(L * 0.4)}" height="${f1(L * 1.2)}" transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)})" fill="${col}" stroke="${DARK}" stroke-width="0.05"/>`;
  if (kind === "board") return `<g transform="translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)}) scale(${f1(L)})"><rect x="-0.5" y="-0.12" width="1" height="0.24" rx="0.03" fill="#2b2b33" stroke="${DARK}" stroke-width="0.03"/><rect x="-0.46" y="-0.02" width="0.4" height="0.12" fill="#f2f0e6"/></g>`;
  if (kind === "cymbal") return `<ellipse cx="${f1(x)}" cy="${f1(y)}" rx="${f1(L)}" ry="${f1(L * 0.22)}" transform="rotate(${f1(rot)} ${f1(x)} ${f1(y)})" fill="#e0b040" stroke="${DARK}" stroke-width="0.08"/>`;
  return "";
}
const ARC = (x0, y0, vx, vy, u, g = 44) => [x0 + vx * u, y0 + vy * u + 0.5 * g * u * u];

function draw(S, t, cam) {
  if (!C || C.sc !== S.sc) return;
  const w = S.sc.world, o = [], over = [];
  const pit = C.cfg.pit;
  const hidden = new Set();
  // beams (world space, screen blended)
  let bm = "";
  for (const b of C.beams) {
    if (t < b.t0 || t >= b.t1) continue;
    const a = (b.base + b.amp * Math.sin(b.fr * (t - b.t0) + b.ph)) * Math.PI / 180, sp = b.sp * Math.PI / 180;
    const ax = b.sx + Math.sin(a - sp) * b.len, ay = b.sy + Math.cos(a - sp) * b.len, bx = b.sx + Math.sin(a + sp) * b.len, by = b.sy + Math.cos(a + sp) * b.len;
    bm += `<polygon points="${f1(b.sx - 0.3)},${f1(b.sy)} ${f1(b.sx + 0.3)},${f1(b.sy)} ${f1(bx)},${f1(by)} ${f1(ax)},${f1(ay)}" fill="url(#cbeam${b.c})"/>`;
  }
  for (const e of C.ev) {
    const u = (t - e.t) / e.d;
    if (u < 0 || u > 1.6) continue;
    if (e.k === "fight") {
      const D = e.d;
      if (u <= 0.15) {                                  // two run at each other
        const k = u / 0.15;
        o.push(human(e.a, e.x - 6 * e.dir * (1 - k) - 1.2, e.y - 3.4, 2.4, 3.4, t, { flip: e.dir < 0 }) + human(e.b, e.x + 6 * e.dir * (1 - k) - 1.2, e.y - 3.4, 2.4, 3.4, t, { flip: e.dir > 0 }));
      } else if (u <= 0.72) {
        o.push(cloud(e.x + Math.sin(t * 9) * 0.6 + (u - 0.15) * 4 * e.dir, e.y - 1.9, 2.1 + 0.4 * Math.sin(t * 20), t, e.s));
      } else if (u <= 1.6) {                            // the loser flies out, mud flies
        const v = (u - 0.72) * D;
        const [px, py] = ARC(e.x + 1.5 * e.dir, e.y - 3, e.dir * (12 + (e.s % 9)), -26, v);
        o.push(human(e.b, px - 1.2, py - 1.7, 2.4, 3.4, t, { rot: v * 520 * e.dir, flip: e.dir < 0 }));
        o.push(splat(e.x, e.y - 1, v, 14, e.s));
      }
    } else if (e.k === "jump") {
      if (u > 1) continue;
      for (let i = 0; i < e.n; i++) {
        const R = mul(Math.floor(e.s) + i * 31), ph = R() * TAU, fr = 3.5 + R() * 3, hh = 3 + R() * 5;
        const jy = -Math.abs(Math.sin(fr * (t - e.t) + ph)) * hh;
        o.push(human(e.tiles[i], e.x + (i - e.n / 2) * 2.1 - 1.2, e.y - 3.4 + jy, 2.4, 3.4, t, { off: i * 0.13, rot: Math.sin(fr * t + ph) * 12, flip: i % 2 }));
      }
    } else if (e.k === "surf") {
      if (u > 1) continue;
      const x = lerp(e.x, e.x1, u), y = e.y + Math.sin(u * TAU * 2) * 0.4;
      o.push(human(e.a, x - 1.5, y - 2, 3.0, 4.2, t, { rot: 78 + Math.sin(u * 14) * 10, flip: e.x1 < e.x }));
    } else if (e.k === "smash") {
      const d = e.dyn, bx = d.x + d.w / 2, by = d.y + d.h / 2, s = d.flip ? -1 : 1;
      const R = mul(Math.floor(e.s));
      if (u < 1.6) hidden.add(d.id);
      const hu = e.role === "drums" ? 0.3 : 0.42;
      // the player himself (a mud person) in place of the drawn one while it happens
      const lean = u < hu ? -8 * Math.min(1, u / hu) : 0;
      if (u <= 1.2) over.push(human(e.a, d.x, d.y, d.w, d.h, t, { flip: d.flip, rot: lean, off: e.s % 1 }));
      if (e.role === "guitar" || e.role === "bass") {
        const L = d.h * 0.5, col = e.role === "guitar" ? "#c0302a" : "#2a6fc0";
        const hx = bx + s * d.w * 0.15, hy = by - d.h * 0.1;
        const at = C.cfg.smash_at && C.cfg.smash_at[e.role];
        if (u < hu) {                                     // raised, then swung down
          const k = u / hu, ang = k < 0.7 ? lerp(10, -110, k / 0.7) : lerp(-110, 55, (k - 0.7) / 0.3);
          over.push(guitar(hx, hy - (k < 0.7 ? k * 2 : 1.4), L, ang, col, d.flip));
        } else if (u <= 1.6) {
          const v = (u - hu) * e.d, ix = at ? at[0] : hx + s * L * 0.8, iy = at ? at[1] : d.y + d.h * 0.95;
          if (v < 0.14) over.push(`<circle cx="${f1(ix)}" cy="${f1(iy)}" r="${f1(0.8 + v * 22)}" fill="#fffbe0" stroke="#ffd030" stroke-width="0.25"/>`);
          for (let i = 0; i < 12; i++) { const a = R() * TAU, r1 = 0.4 + v * 18 * (0.5 + R()); if (v < 0.4) over.push(`<line x1="${f1(ix + Math.cos(a) * 0.5)}" y1="${f1(iy + Math.sin(a) * 0.5)}" x2="${f1(ix + Math.cos(a) * r1)}" y2="${f1(iy + Math.sin(a) * r1)}" stroke="#ffe030" stroke-width="0.14" stroke-linecap="round"/>`); }
          const vxA = -s * (6 + R() * 8), vxB = s * (7 + R() * 9);
          const [ax, ay] = ARC(ix, iy, vxA, -14 - R() * 6, v), [bx2, by2] = ARC(ix, iy, vxB, -16 - R() * 8, v);
          over.push(piece("gA", ax, ay, v * 600 * -s, L, col), piece("gB", bx2, by2, v * 380 * s, L, col));
          for (let i = 0; i < 9; i++) { const [sx, sy] = ARC(ix, iy, (R() - 0.5) * 24, -8 - R() * 14, v); over.push(piece("splinter", sx, sy, v * 900 * (R() - 0.5), 0.3 + R() * 0.4)); }
        }
      } else if (e.role === "keys") {
        const hx = bx, hy = by - d.h * 0.12, L = d.w * 1.1;
        if (u < hu) {
          const k = u / hu, ang = k < 0.7 ? lerp(0, -70, k / 0.7) : lerp(-70, 10, (k - 0.7) / 0.3);
          over.push(piece("board", hx, hy - (k < 0.7 ? k * 2.6 : 1.8), ang, L));
        } else if (u <= 1.6) {
          const v = (u - hu) * e.d, ix = hx, iy = d.y + d.h * 0.8;
          if (v < 0.12) over.push(`<circle cx="${f1(ix)}" cy="${f1(iy)}" r="${f1(0.8 + v * 22)}" fill="#e8f0ff" stroke="#60a0ff" stroke-width="0.25"/>`);
          for (let i = 0; i < 12; i++) { const a = R() * TAU, r1 = 0.4 + v * 16 * (0.5 + R()); if (v < 0.4) over.push(`<line x1="${f1(ix)}" y1="${f1(iy)}" x2="${f1(ix + Math.cos(a) * r1)}" y2="${f1(iy + Math.sin(a) * r1)}" stroke="#90c8ff" stroke-width="0.14" stroke-linecap="round"/>`); }
          for (const sgn of [-1, 1]) { const [px, py] = ARC(ix, iy, sgn * (5 + R() * 5), -12 - R() * 5, v); over.push(piece("board", px, py, v * 300 * sgn, L * 0.5)); }
          for (let i = 0; i < 16; i++) { const [px, py] = ARC(ix, iy, (R() - 0.5) * 30, -6 - R() * 20, v); over.push(piece("key", px, py, v * 700 * (R() - 0.5), 0.5 + R() * 0.2, R() < 0.65 ? "#f2f0e6" : "#1a1a22")); }
        }
      } else {                                            // drums: cymbals and sticks fly, the kit shudders
        const ix = bx, iy = by - d.h * 0.15;
        if (u > hu) {
          const v = (u - hu) * e.d;
          if (v < 0.2) over.push(`<circle cx="${f1(ix)}" cy="${f1(iy)}" r="${f1(1 + v * 30)}" fill="none" stroke="#ffffff" stroke-width="${f1(0.3 * (1 - v * 4))}"/>`);
          for (let i = 0; i < 3; i++) { const [px, py] = ARC(ix, iy, (R() - 0.5) * 24, -14 - R() * 10, v); over.push(piece("cymbal", px, py, v * 500 * (R() - 0.5), 1.4 + R() * 0.8)); }
          for (let i = 0; i < 5; i++) { const [px, py] = ARC(ix, iy, (R() - 0.5) * 28, -10 - R() * 14, v); over.push(`<line x1="${f1(px)}" y1="${f1(py)}" x2="${f1(px + Math.cos(v * 20 * (i + 1)) * 2.4)}" y2="${f1(py + Math.sin(v * 20 * (i + 1)) * 2.4)}" stroke="#c9a46a" stroke-width="0.22" stroke-linecap="round"/>`); }
        }
      }
    }
  }
  // flying mud
  for (const V of C.vol) {
    if (t < V.t || t > V.t + 2.4) continue;
    for (const b of V.balls) {
      const v = t - V.t - b.d;
      if (v < 0) continue;
      if (v < b.T1) {
        const g = 44, vx = (b.tx - b.x0) / b.T1, vy = (b.ty - b.y0) / b.T1 - 0.5 * g * b.T1;
        const [px, py] = ARC(b.x0, b.y0, vx, vy, v);
        o.push(`<ellipse cx="${f1(px)}" cy="${f1(py)}" rx="${f1(b.r * 1.15)}" ry="${f1(b.r)}" fill="#4a3018" stroke="${DARK}" stroke-width="0.07" transform="rotate(${f1(v * 700)} ${f1(px)} ${f1(py)})"/><circle cx="${f1(px - b.r * 0.3)}" cy="${f1(py - b.r * 0.3)}" r="${f1(b.r * 0.25)}" fill="#8a6a3e"/>`);
        const [qx, qy] = ARC(b.x0, b.y0, vx, vy, Math.max(0, v - 0.03));
        o.push(`<line x1="${f1(qx)}" y1="${f1(qy)}" x2="${f1(px)}" y2="${f1(py)}" stroke="#4a3018" stroke-width="${f1(b.r * 0.8)}" stroke-linecap="round" opacity="0.35"/>`);
      } else {                                              // splat: drops fly off the target, a stain stays a moment
        const w2 = v - b.T1;
        if (w2 < 0.5) o.push(splat(b.tx, b.ty, w2, 7, b.s));
        if (w2 < 1.4) o.push(`<ellipse cx="${f1(b.tx)}" cy="${f1(b.ty)}" rx="${f1(b.r * 2.2)}" ry="${f1(b.r * 1.6)}" fill="#4a3018" stroke="${DARK}" stroke-width="0.06" opacity="${f1(Math.max(0, 1 - w2 / 1.4))}"/>`);
      }
    }
  }
  // feedback rings at the speaker
  if (C.cfg.feedback) {
    const [ft, fx, fy, fs] = C.cfg.feedback;
    for (const f of C.fb) {
      if (t < f.t || t > f.t + f.d) continue;
      const id = frameId(ft, t - f.t);
      if (id) over.push(`<g style="mix-blend-mode:screen"><use href="#${id}" x="${f1(fx - fs / 2)}" y="${f1(fy - fs / 2)}" width="${f1(fs)}" height="${f1(fs)}"/></g>`);
      break;
    }
  }
  // the drawn players are hidden while their replacements smash
  for (const D of S.dyn) {
    const hide = hidden.has(D.d.id), was = C.hidden.has(D.d.id);
    if (hide && !was) { D.g.style.display = "none"; C.hidden.add(D.d.id); }
    else if (!hide && was) { D.g.style.display = ""; C.hidden.delete(D.d.id); }
  }
  C.g.innerHTML = `<g style="mix-blend-mode:screen">${bm}</g>${o.join("")}${over.join("")}`;
  // the screen-space lights: colour washes and strobes
  let wash = "";
  for (const [t0, t1, c, a] of C.washes) if (t >= t0 && t < t1) wash += `<div style="position:absolute;inset:0;background:${c};opacity:${a}"></div>`;
  for (const [t0, t1, hz] of C.strobes) if (t >= t0 && t < t1 && Math.floor((t - t0) * hz * 2) % 2 === 0) wash += `<div style="position:absolute;inset:0;background:#fff;opacity:.85"></div>`;
  if (wash !== C.lastWash) { C.lights.innerHTML = wash; C.lastWash = wash; }
  if (C.label) C.label.textContent = `seed ${seed}  ${t.toFixed(1)}s`;
}

function mount(camG, stage) {                       // called after the scene's groups are in the page
  if (!C) return;
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.id = "chaosw";
  g.innerHTML = "";
  camG.appendChild(g);
  C.g = g;
  C.lights = document.getElementById("chaoslights");
  C.lights.innerHTML = ""; C.lastWash = "";
  let defs = document.getElementById("chaosdefs");
  if (!defs) {
    defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.id = "chaosdefs";
    defs.innerHTML = BEAM.map((c, i) => `<linearGradient id="cbeam${i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c}" stop-opacity=".65"/><stop offset="1" stop-color="${c}" stop-opacity=".05"/></linearGradient>`).join("");
    document.getElementById("view").insertBefore(defs, document.getElementById("view").firstChild);
  }
  if (!P.has("clean")) {
    if (!C.label) { C.label = document.createElement("div"); C.label.style.cssText = "position:fixed;left:8px;top:6px;font:12px monospace;color:#fff;opacity:.6;z-index:15;text-shadow:0 0 3px #000"; document.body.appendChild(C.label); }
  }
}
function bump() { seed++; }
window.Chaos = { events: () => (C ? C.ev.map((e) => ({ k: e.k, role: e.role, t: e.t, d: e.d, f: e.f })) : []), on: ON, loop: LOOP, prepare, mount, draw, bump, seed: () => seed };
})();
