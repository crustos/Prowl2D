// curves.js -- the smooth surfaces of an exported level: the quadratic Bezier curves in level.json's "curves".
//
//   { "kind": "solid" | "wall",
//     "segments": [[x0, y0, x1, y1, x2, y2], ...],     quadratic Beziers p0 -> control p1 -> p2 in tile units (y up), end to end
//     "closed": false,                                  solid only: true when the segments close up on their own; otherwise a straight
//                                                       line from the last point back to the first closes the fill (it is not a collider)
//     "friction": 0.4, "bounciness": 0,                 Unity's numbers
//     "fill": "#4d8f3a", "edge": "#2f6b2a", "thickness": 0.1 }
//
// "solid" is a hill, a bank, a cave floor: balls and crates are pushed out of it; the inside is the side the closed outline encloses.
// "wall" is a thin ramp or bowl, solid on both faces, drawn as a ribbon of `thickness`.
//
// Drawn once into a layer (and again after a resize): by Windfoil (closed-form antialiasing on the GPU) where WebGPU exists, with
// Canvas 2D otherwise; both fill the same outlines.
import { Windfoil } from "./windfoil.js";

const line = (x0, y0, x1, y1) => [x0, y0, (x0 + x1) / 2, (y0 + y1) / 2, x1, y1];

/** +1 when the closed outline of a solid runs counter-clockwise (its inside is on the left of the direction), else -1. */
export function solidSide(curve) {
  const pts = [];
  for (const q of curve.segments) for (const t of [0, 0.25, 0.5, 0.75]) {
    const u = 1 - t;
    pts.push([u * u * q[0] + 2 * u * t * q[2] + t * t * q[4], u * u * q[1] + 2 * u * t * q[3] + t * t * q[5]]);
  }
  let area = 0;
  for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; area += a[0] * b[1] - b[0] * a[1]; }
  return area >= 0 ? 1 : -1;
}

/** The contour a fill draws: the chain, closed by a straight line when it does not close itself. */
function closedChain(segments, closed) {
  const out = segments.map((q) => q.slice());
  const a = segments[0], b = segments[segments.length - 1];
  if (!closed && (Math.abs(a[0] - b[4]) > 1e-6 || Math.abs(a[1] - b[5]) > 1e-6)) out.push(line(b[4], b[5], a[0], a[1]));
  return out;
}

/** A ribbon `w` wide around a chain of quadratics (control points offset by the miter: exact for lines, close for gentle curves). */
export function ribbon(segments, w) {
  const h = w / 2, side = (sgn) => segments.map((q) => {
    let n0x = -(q[3] - q[1]), n0y = q[2] - q[0], n2x = -(q[5] - q[3]), n2y = q[4] - q[2];
    let l0 = Math.hypot(n0x, n0y) || 1, l2 = Math.hypot(n2x, n2y) || 1;
    n0x /= l0; n0y /= l0; n2x /= l2; n2y /= l2;
    const mx = n0x + n2x, my = n0y + n2y, k = 1 + n0x * n2x + n0y * n2y;
    return [q[0] + sgn * h * n0x, q[1] + sgn * h * n0y, q[2] + sgn * h * mx / Math.max(k, 0.2), q[3] + sgn * h * my / Math.max(k, 0.2), q[4] + sgn * h * n2x, q[5] + sgn * h * n2y];
  });
  const fwd = side(1), back = side(-1).map((q) => [q[4], q[5], q[2], q[3], q[0], q[1]]).reverse();
  const out = [];
  const chain = (list) => list.forEach((q) => {
    const p = out[out.length - 1];
    if (p && (Math.abs(p[4] - q[0]) > 1e-6 || Math.abs(p[5] - q[1]) > 1e-6)) out.push(line(p[4], p[5], q[0], q[1]));
    out.push(q);
  });
  chain(fwd); chain(back);
  const a = out[0], b = out[out.length - 1];
  if (Math.abs(a[0] - b[4]) > 1e-6 || Math.abs(a[1] - b[5]) > 1e-6) out.push(line(b[4], b[5], a[0], a[1]));
  return out;
}

function parseColor(c, alpha = 1) {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?$/i.exec(c || "");
  if (!m) return [0.6, 0.6, 0.6, alpha];
  return [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255, (m[4] ? parseInt(m[4], 16) / 255 : 1) * alpha];
}

/** What to paint, back to front: [{ contour, color: [r, g, b, a] }]. */
export function paintList(curves) {
  const list = [];
  for (const c of curves || []) {
    if (!c.segments?.length) continue;
    const th = c.thickness ?? 0.1;
    if (c.kind === "wall") list.push({ contour: ribbon(c.segments, th), color: parseColor(c.fill || "#8e9bb0") });
    else {
      list.push({ contour: closedChain(c.segments, c.closed), color: parseColor(c.fill || "#4d8f3a") });
      if (c.edge !== null) list.push({ contour: ribbon(c.segments, th), color: parseColor(c.edge || "#2f6b2a") });
    }
  }
  return list;
}

let sharedDevice = null;
async function gpuDevice() {
  if (sharedDevice !== null) return sharedDevice || null;
  sharedDevice = false;
  try {
    const adapter = navigator.gpu && await navigator.gpu.requestAdapter();
    if (adapter) sharedDevice = await adapter.requestDevice();
  } catch { sharedDevice = false; }
  return sharedDevice || null;
}

/** Paints the curves into a canvas-sized layer. view = { s: pixels per tile, ox, oy: where the level's lower left... }, see player.js.
 *  mode "auto" (Windfoil when WebGPU works), "windfoil" or "canvas". Returns { canvas, mode } or null when there is nothing to draw. */
export async function bakeLayer(curves, { width, height, scale, camera, mode = "auto" }) {
  const list = paintList(curves);
  if (!list.length) return null;
  const layer = document.createElement("canvas");
  layer.width = width; layer.height = height;
  const device = mode === "canvas" ? null : await gpuDevice();
  if (device) {
    try {
      const target = device.createTexture({ size: [width, height], format: "rgba8unorm", usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_SRC });
      const stride = Math.ceil(width * 4 / 256) * 256;
      const readback = device.createBuffer({ size: stride * height, usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ });
      const enc = device.createCommandEncoder();
      const pass = enc.beginRenderPass({ colorAttachments: [{ view: target.createView(), clearValue: [0, 0, 0, 0], loadOp: "clear", storeOp: "store" }] });
      const fills = list.map((p) => Windfoil.create(device, "rgba8unorm").setPath([p.contour], { pad: 2 / scale }));
      fills.forEach((f, i) => f.draw(pass, { camera, scale, res: [width, height], color: list[i].color }));
      pass.end();
      enc.copyTextureToBuffer({ texture: target }, { buffer: readback, bytesPerRow: stride }, [width, height]);
      device.queue.submit([enc.finish()]);
      await readback.mapAsync(GPUMapMode.READ);
      const src = new Uint8Array(readback.getMappedRange().slice(0));
      readback.unmap(); readback.destroy(); target.destroy();
      const img = new ImageData(width, height), d = img.data;
      for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {      // premultiplied -> straight alpha
        const s = y * stride + 4 * x, o = 4 * (y * width + x), a = src[s + 3];
        d[o + 3] = a;
        if (a) { d[o] = Math.min(255, Math.round(src[s] * 255 / a)); d[o + 1] = Math.min(255, Math.round(src[s + 1] * 255 / a)); d[o + 2] = Math.min(255, Math.round(src[s + 2] * 255 / a)); }
      }
      layer.getContext("2d").putImageData(img, 0, 0);
      return { canvas: layer, mode: "windfoil" };
    } catch (e) { console.warn("Windfoil failed, using Canvas 2D:", e); }
  }
  const ctx = layer.getContext("2d");
  const sx = (x) => width / 2 + (x - camera[0]) * scale, sy = (y) => height / 2 - (y - camera[1]) * scale;
  for (const p of list) {
    ctx.beginPath();
    p.contour.forEach((q, i) => {
      if (i === 0 || Math.abs(q[0] - p.contour[i - 1][4]) > 1e-6 || Math.abs(q[1] - p.contour[i - 1][5]) > 1e-6) ctx.moveTo(sx(q[0]), sy(q[1]));
      ctx.quadraticCurveTo(sx(q[2]), sy(q[3]), sx(q[4]), sy(q[5]));
    });
    ctx.closePath();
    const [r, g, b, a] = p.color;
    ctx.fillStyle = `rgba(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)},${a})`;
    ctx.fill("nonzero");
  }
  return { canvas: layer, mode: "canvas" };
}
