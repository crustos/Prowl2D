#!/usr/bin/env python3
"""Exports the demo level and plays it in headless Chromium on both engines (WebAssembly and WebGPU on SwiftShader).

    python3 tools/gpu_web_test.py [--engine wasm|webgpu] [--shot DIR]

Needs Node with Playwright and Chromium (PLAYWRIGHT_BROWSERS_PATH). WebGPU runs on SwiftShader (software Vulkan): slow, but it
is the real WebGPU API with the real WGSL. Canvas 2D screenshots are saved with --shot.
"""
import base64
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RUNNER = r"""
const { chromium } = require('playwright');
const [url, engine] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium', args: ['--headless=new','--no-sandbox','--enable-unsafe-webgpu','--enable-features=Vulkan,WebGPU','--use-angle=swiftshader','--use-webgpu-adapter=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 960, height: 600 } });
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url + '?manual=1&engine=' + engine);
  await p.waitForFunction(() => window.__ready, null, { timeout: 600000, polling: 500 });
  const out = await p.evaluate(async () => {
    const P = window.player, r = {}, W = P.level.width, H = P.level.height;
    r.engine = P.engine; r.crates = P.state.crates.size;
    r.crateTiles = P.level.cells.filter((c) => c && P.level.tiles[c].dynamic).length;
    await P.step(100);
    const ys = [...P.state.crates.keys()].map((id) => P.snap.poses.get(id).y);
    r.crateMinY = Math.min(...ys); r.crateMaxY = Math.max(...ys);
    r.finite = [...P.snap.poses.values()].every((q) => Number.isFinite(q.x) && Number.isFinite(q.y));
    const before = P.circles;
    await P.act('ball', [12, H - 2]); await P.act('ball', [15.5, H - 2]);
    r.balls = [...P.engineObject.bodies.values()].filter((k) => k === 'ball').length;
    await P.act('sand', [8, H - 2]); await P.act('sand', [8, H - 2]);
    r.sandAdded = P.circles - before - 2;
    await P.step(160);
    const balls = [...P.engineObject.bodies].filter(([, k]) => k === 'ball').map(([id]) => P.snap.poses.get(id));
    r.ballY = balls.map((q) => +q.y.toFixed(2));
    r.sand = P.snap.sand.length / 2;
    let low = 99, high = 0; for (let i = 1; i < P.snap.sand.length; i += 2) { low = Math.min(low, P.snap.sand[i]); high = Math.max(high, P.snap.sand[i]); }
    r.sandLow = low;
    const diggableBefore = P.state.cells.filter((c) => c && P.level.tiles[c].diggable).length;
    let gx = 0, gy = 0; outer: for (let ty = 0; ty < H; ty++) for (let tx = 0; tx < W; tx++) { const c = P.state.cells[(H - 1 - ty) * W + tx]; if (c && P.level.tiles[c].diggable) { gx = tx + 0.5; gy = ty + 0.5; break outer; } }
    await P.blast(gx, gy + 1, 3, 30);
    r.dug = diggableBefore - P.state.cells.filter((c) => c && P.level.tiles[c].diggable).length;
    r.cratesAfterBlast = P.state.crates.size;
    await P.step(40);
    r.png = await P.png();
    return r;
  });
  console.log(JSON.stringify({ out, errors }));
  await b.close();
})();
"""


def main(argv):
    engines = [argv[argv.index("--engine") + 1]] if "--engine" in argv else ["wasm", "webgpu"]
    shot = argv[argv.index("--shot") + 1] if "--shot" in argv else None
    work = tempfile.mkdtemp(prefix="gpuweb-")
    r = subprocess.run([sys.executable, os.path.join(HERE, "export_gpu_web.py"), "--demo", "--out", work], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=work, **k)

        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://localhost:%d/index.html" % srv.server_address[1]
    js = os.path.join(work, "run.js")
    open(js, "w").write(RUNNER)
    env = dict(os.environ)
    env["NODE_PATH"] = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + os.pathsep + env.get("NODE_PATH", "")
    bad = 0
    for eng in engines:
        p = subprocess.run(["node", js, url, eng], env=env, capture_output=True, text=True, timeout=1500)
        try:
            res = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:
            print("FAIL %s: no result\n%s%s" % (eng, p.stdout[-1500:], p.stderr[-1500:]))
            bad += 1
            continue
        o, errs = res["out"], res["errors"]

        def check(name, ok, extra=""):
            nonlocal bad
            print(("ok   " if ok else "FAIL ") + "[%s] %s %s" % (eng, name, extra))
            bad += not ok
        check("the requested engine ran", o["engine"] == eng, o["engine"])
        check("every movable tile became a crate", o["crates"] == o["crateTiles"] > 0, "%d crates" % o["crates"])
        check("crates fall and rest on the level", o["finite"] and 0.4 < o["crateMinY"] and o["crateMaxY"] < 12, "y %.2f..%.2f" % (o["crateMinY"], o["crateMaxY"]))
        check("balls rest on something", o["balls"] == 2 and all(0.3 < y < 11 for y in o["ballY"]), str(o["ballY"]))
        check("sand is poured and stays inside", o["sandAdded"] > 40 and o["sandLow"] > 0.5, "%d grains, lowest %.2f" % (o["sand"], o["sandLow"]))
        check("a blast digs the diggable tiles", o["dug"] > 0, "%d tiles" % o["dug"])
        check("no page errors", not errs, "; ".join(errs[:2]))
        png = base64.b64decode(o["png"].split(",")[1])
        check("the canvas drew something", len(png) > 3000, "%d bytes" % len(png))
        if shot:
            os.makedirs(shot, exist_ok=True)
            open(os.path.join(shot, "player-%s.png" % eng), "wb").write(png)
    print("%d FAILED" % bad if bad else "all checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
