"""Cutscenes: a level is the stage, a timeline moves the actors, the camera and the lights.

In a .lvl (all times in seconds, all places in cells)::

    scene("intro", seconds=24, fps=12, view=(40, 22))
    actor("slime", {"idle": 🟢, "shy": 🟢shy}, 6, 14)       # a bare tile is the pose "idle"
    actor("gelly", 👧, 44, 14, flip=True)                    # flip: the picture looks left
    move("slime", 2, 6, 24, 14, hop=3)                       # walk (hopping 3 cells high) there between 2s and 6s
    pose("slime", 6.5, "shy")
    emote("gelly", 7, 💗, seconds=1.5)                       # a picture floats up above her head
    cam(0, 10, 10); cam(8, 26, 10, zoom=1.6)                 # the camera centre (and zoom) at those times
    fade(0, 1, 1, 0)                                         # from black to clear; fade(23, 24, 0, 1, "white") to white
    card(0.5, "SlimeJump", "A Love Story"); line(7, "Oh! Hello there...", who="Gelly")

Music video moves (all in the same file): ``scene("clip", seconds=48, bpm=120)`` and ``beat(8)`` (seconds of 8 beats) put everything on a grid; ``cut(t, x, y, zoom)`` is a
hard shot change; ``actor(..., size=(20, 14))`` draws an actor big (a close-up shot of its face, on a set somewhere else on the stage); ``show``/``hide``/``warp``/``face`` place and turn actors;
``dance("a", beat(16), beat(24), ["a", "b"], every=1, hop=0.6)`` changes pose and hops on the beat; ``punch(t, 0.08)`` and ``shake(t0, t1, 0.3)`` shove the camera.

Every function returns nothing and may be called in any order, except that the ``move``s (and ``warp``s and ``dance``s) of one actor must be added in time order.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field

EASES = ("linear", "in", "out", "inout", "cut")   # "cut": it stays where it was until the end time, then jumps


def ease(u: float, kind: str) -> float:
    u = min(1.0, max(0.0, u))
    if kind == "cut":
        return 1.0 if u >= 1.0 else 0.0
    if kind == "in":
        return u * u
    if kind == "out":
        return 1 - (1 - u) * (1 - u)
    if kind == "inout":
        return u * u * (3 - 2 * u)
    return u


def tri(v: float) -> float:
    """A triangle wave, -1..1, one period per unit (the shake; it is the same in Cutscene.cs)."""
    f = v - int(v)
    if f < 0:
        f += 1
    return f * 4 - 1 if f < 0.5 else 3 - f * 4


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


@dataclass
class Move:
    t0: float
    t1: float
    x0: float
    y0: float
    x1: float
    y1: float
    ease: str = "inout"
    hop: float = 0.0


@dataclass
class Actor:
    name: str
    poses: dict           # pose name -> Tile
    x: float
    y: float
    flip: bool = False
    moves: list = field(default_factory=list)
    pose_cues: list = field(default_factory=list)   # (t, pose name), by time
    emotes: list = field(default_factory=list)      # (t, tile, seconds)
    size: tuple | None = None                       # cells; None = the tile's own size (a bigger one is a close-up)
    vis: list = field(default_factory=list)         # (t, shown) cues, by time; it is shown until told otherwise
    faces: list = field(default_factory=list)       # (t, mirrored) cues

    def width_height(self, tile) -> tuple:
        return self.size or tile.size

    def visible(self, t: float) -> bool:
        shown = True
        for vt, v in self.vis:
            if t >= vt:
                shown = v
        return shown

    def flip_events(self) -> list:
        """[(t, mirrored)] by time: it looks where it walks (a cut does not turn it), and `face()` says so outright."""
        ev = [(m.t0, m.x1 < m.x0) for m in self.moves if m.ease != "cut" and abs(m.x1 - m.x0) > 0.01] + list(self.faces)
        return sorted(ev, key=lambda e: e[0])

    def position(self, t: float) -> tuple:
        x, y = self.x, self.y
        if len(self.moves) > 24:        # thousands of hops in a long dance: moves are ordered and never overlap, so bisect
            ks = getattr(self, "_move_keys", None)
            if ks is None or len(ks) != len(self.moves):
                ks = self._move_keys = [m.t0 for m in self.moves]
            i = bisect.bisect_right(ks, t) - 1
            if i < 0:
                return x, y
            m = self.moves[i]
            if m.ease == "cut" or t >= m.t1:
                return m.x1, m.y1
            u = ease((t - m.t0) / (m.t1 - m.t0), m.ease)
            return lerp(m.x0, m.x1, u), lerp(m.y0, m.y1, u) - m.hop * 4 * u * (1 - u)
        for m in self.moves:
            if m.ease == "cut":            # a jump: it is there from t0 on
                if t < m.t0:
                    break
                x, y = m.x1, m.y1
                continue
            if t >= m.t1:
                x, y = m.x1, m.y1
            elif t >= m.t0:
                u = ease((t - m.t0) / (m.t1 - m.t0), m.ease)
                return lerp(m.x0, m.x1, u), lerp(m.y0, m.y1, u) - m.hop * 4 * u * (1 - u)
        return x, y

    def facing_flip(self, t: float) -> bool:
        """True if the picture is mirrored at t: it looks where it last walked."""
        flip = self.flip
        for et, f in self.flip_events():
            if t >= et:
                flip = f
        return flip

    def pose(self, t: float) -> str:
        cur = "idle" if "idle" in self.poses else next(iter(self.poses))
        cues = self.pose_cues
        if not cues:
            return cur
        keys = getattr(self, "_pose_keys", None)
        if keys is None or len(keys) != len(cues):       # cues are kept sorted by time
            keys = self._pose_keys = [c[0] for c in cues]
        i = bisect.bisect_right(keys, t)
        return cues[i - 1][1] if i else cur


@dataclass
class Scene:
    name: str = "scene"
    seconds: float = 10.0
    fps: int = 12
    view: tuple = (40, 22)
    bpm: float = 120.0
    actors: dict = field(default_factory=dict)
    punches: list = field(default_factory=list)    # (t, amount, seconds): the camera zooms in a little and settles back
    shakes: list = field(default_factory=list)     # (t0, t1, amplitude in cells)
    cams: list = field(default_factory=list)       # (t, x, y, zoom, ease)
    fades: list = field(default_factory=list)      # (t0, t1, a0, a1, colour)
    captions: list = field(default_factory=list)   # {"kind", "t", "text", ...}
    fxs: list = field(default_factory=list)        # (t0, t1, name, amount): a post effect on the picture (see render/fx.py)
    rain: float = 0.0                              # rain over the picture in an HTML show (0 = none); layers named "rain..." are then not exported
    chaos: dict | None = None                      # the random director of an HTML show (see chaos() below)
    next: str | None = None                        # the scene an HTML show plays after this one (default: the next .lvl given)

    def fx_at(self, t: float) -> list:
        return [(n, a) for t0, t1, n, a in self.fxs if t0 <= t < t1]

    def stutter_at(self, t: float):
        """Seconds per held frame if a stutter is on at t (the picture freezes and steps), else None."""
        for t0, t1, n, a in self.fxs:
            if n == "stutter" and t0 <= t < t1:
                return max(0.05, 0.5 / max(1.0, a))
        return None

    def beat(self, n: float = 1.0) -> float:
        """Seconds of n beats."""
        return n * 60.0 / self.bpm

    def base_camera(self, t: float) -> tuple:
        if not self.cams:
            return self.view[0] / 2, self.view[1] / 2, 1.0
        if t <= self.cams[0][0]:
            return self.cams[0][1:4]
        for a, b in zip(self.cams, self.cams[1:]):
            if t < b[0]:
                u = ease((t - a[0]) / (b[0] - a[0]), b[4])
                return lerp(a[1], b[1], u), lerp(a[2], b[2], u), lerp(a[3], b[3], u)
        return self.cams[-1][1:4]

    def punch(self, t: float) -> float:
        """The zoom multiplier of the punches at t (1 = none)."""
        m = 1.0
        for p0, amt, dur in self.punches:
            if p0 <= t < p0 + dur:
                u = (t - p0) / dur
                m += amt * (1 - u) * (1 - u)
        return m

    def shake(self, t: float) -> tuple:
        sx = sy = 0.0
        for t0, t1, amp in self.shakes:
            if t0 <= t < t1:
                sx += amp * tri(t * 23.0)
                sy += amp * tri(t * 31.0 + 0.3)
        return sx, sy

    def camera(self, t: float) -> tuple:
        """(x, y, zoom) of the camera centre at t: the keys, then the punches and the shake."""
        x, y, z = self.base_camera(t)
        sx, sy = self.shake(t)
        return x + sx, y + sy, z * self.punch(t)

    def fade(self, t: float) -> tuple:
        """(alpha, colour) of the fade overlay at t."""
        fades = getattr(self, "_fades_sorted", None)
        if fades is None or len(fades) != len(self.fades):
            fades = self._fades_sorted = sorted(self.fades)
        i = bisect.bisect_right([f[0] for f in fades], t) if len(fades) < 64 else bisect.bisect_right(self._fade_keys(fades), t)
        if i == 0:
            return 0.0, "black"
        t0, t1, a0, a1, c = fades[i - 1]       # the latest one that has started
        return lerp(a0, a1, ease((t - t0) / max(t1 - t0, 1e-9), "linear")), c

    def _fade_keys(self, fades):
        keys = getattr(self, "_fade_keys_cache", None)
        if keys is None or len(keys) != len(fades):
            keys = self._fade_keys_cache = [f[0] for f in fades]
        return keys

    def to_dict(self) -> dict:
        return {
            "name": self.name, "seconds": self.seconds, "fps": self.fps, "view": list(self.view),
            "bpm": self.bpm, "punches": [list(p) for p in self.punches], "shakes": [list(k) for k in self.shakes],
            "actors": {n: {"size": list(a.size) if a.size else None, "vis": [list(v) for v in a.vis], "faces": [list(f) for f in a.faces], "poses": {k: v.name for k, v in a.poses.items()}, "x": a.x, "y": a.y, "flip": a.flip,
                           "moves": [[m.t0, m.t1, m.x0, m.y0, m.x1, m.y1, m.ease, m.hop] for m in a.moves],
                           "pose_cues": [list(c) for c in a.pose_cues],
                           "emotes": [[t, tile.name, s] for t, tile, s in a.emotes]} for n, a in self.actors.items()},
            **({"next": self.next} if self.next else {}), "fx": [list(x) for x in self.fxs], "cams": [list(c) for c in self.cams], "fades": [list(f) for f in self.fades], "captions": self.captions,
        }


def builtins(level) -> dict:
    """The scene functions of a .lvl; they build ``level.scene``."""

    def need() -> Scene:
        if getattr(level, "scene", None) is None:
            raise TypeError("start with scene(\"name\", seconds=...) before actor(), move(), cam() ...")
        return level.scene

    def actor_of(name) -> Actor:
        sc = need()
        if name not in sc.actors:
            raise NameError(f"no actor {name!r}: add it with actor({name!r}, tile, x, y) first")
        return sc.actors[name]

    def check_ease(e):
        if e not in EASES:
            raise ValueError(f"ease must be one of {', '.join(EASES)}, not {e!r}")

    def scene(name="scene", seconds=10, fps=12, view=(40, 22), bpm=120, next=None):
        level.scene = Scene(str(name), float(seconds), int(fps), tuple(view), float(bpm), next=str(next) if next else None)
        return level.scene

    def beat(n=1):
        """Seconds of n beats at the scene's bpm: ``move("a", beat(8), beat(12), ...)``."""
        return (level.scene.beat(n) if getattr(level, "scene", None) else n * 0.5)

    def actor(name, tiles, x, y, flip=False, size=None):
        sc = need()
        poses = dict(tiles) if isinstance(tiles, dict) else {"idle": tiles}
        if not poses:
            raise ValueError(f"actor {name!r} needs at least one tile")
        sc.actors[name] = Actor(str(name), poses, float(x), float(y), bool(flip), size=tuple(size) if size else None)

    def show(name, t=0):
        a = actor_of(name)
        a.vis.append((float(t), True))
        a.vis.sort(key=lambda v: v[0])

    def hide(name, t=0):
        a = actor_of(name)
        a.vis.append((float(t), False))
        a.vis.sort(key=lambda v: v[0])

    def face(name, t, left=True):
        """``face("a", 3, left=True)``: from t on the picture is mirrored (looks left) or not."""
        a = actor_of(name)
        a.faces.append((float(t), bool(left)))

    def warp(name, t, x, y):
        """Jump to a place at time t (a cut: into another set), without turning."""
        a = actor_of(name)
        if a.moves and t < a.moves[-1].t1:
            raise ValueError(f"warp({name!r}, {t}, ...): moves of one actor go in time order (the last ends at {a.moves[-1].t1})")
        x0, y0 = a.position(t)
        a.moves.append(Move(float(t), float(t), x0, y0, float(x), float(y), "cut", 0.0))

    def dance(name, t0, t1, poses, every=1, hop=0):
        """``dance("a", beat(16), beat(24), ["dance1", "dance2"], every=1, hop=0.6)``: change pose every `every` beats and hop in place."""
        sc = need()
        a = actor_of(name)
        poses = list(poses)
        for p in poses:
            if p not in a.poses:
                raise KeyError(f"actor {name!r} has no pose {p!r} (it has {', '.join(a.poses)})")
        dt = sc.beat(every)
        n = int((t1 - t0) / dt + 1e-9)
        if a.moves and t0 < a.moves[-1].t1:
            raise ValueError(f"dance({name!r}, {t0}, ...): moves of one actor go in time order (the last ends at {a.moves[-1].t1})")
        for k in range(n):
            t = t0 + k * dt
            a.pose_cues.append((t, poses[k % len(poses)]))
            if hop:
                x, y = a.position(t)
                a.moves.append(Move(t, t + dt, x, y, x, y, "linear", float(hop)))
        a.pose_cues.sort(key=lambda c: c[0])

    def punch(t, amount=0.08, seconds=0.25):
        """The camera zooms in by `amount` (0.08 = 8%) and settles back in `seconds`: do it on the beat."""
        need().punches.append((float(t), float(amount), float(seconds)))

    def shake(t0, t1, amp=0.25):
        need().shakes.append((float(t0), float(t1), float(amp)))

    def move(name, t0, t1, x, y, ease="inout", hop=0):
        check_ease(ease)
        a = actor_of(name)
        if t1 <= t0:
            raise ValueError(f"move({name!r}): it must end after it starts ({t0} -> {t1})")
        if a.moves and t0 < a.moves[-1].t1:
            raise ValueError(f"move({name!r}, {t0}, ...): moves of one actor go in time order and may not overlap (the last ends at {a.moves[-1].t1})")
        x0, y0 = a.position(t0)
        a.moves.append(Move(float(t0), float(t1), x0, y0, float(x), float(y), ease, float(hop)))

    def pose(name, t, which):
        a = actor_of(name)
        if which not in a.poses:
            raise KeyError(f"actor {name!r} has no pose {which!r} (it has {', '.join(a.poses)})")
        a.pose_cues.append((float(t), which))
        a.pose_cues.sort(key=lambda c: c[0])

    def emote(name, t, tile, seconds=1.5):
        actor_of(name).emotes.append((float(t), tile, float(seconds)))

    def cam(t, x, y, zoom=1.0, ease="inout"):
        check_ease(ease)
        sc = need()
        sc.cams.append((float(t), float(x), float(y), float(zoom), ease))
        sc.cams.sort(key=lambda c: c[0])

    def cut(t, x, y, zoom=1.0):
        """A hard cut: from t on the camera is there (a shot change)."""
        cam(t, x, y, zoom, "cut")

    def fade(t0, t1, a0, a1, color="black"):
        need().fades.append((float(t0), float(t1), float(a0), float(a1), color))

    def fx(t0, t1, name, amount=1.0):
        """``fx(10, 10.3, "rgb", 1.0)``: a post effect on the picture while it is on: grain scan rgb glitch vhs invert posterize solarize mirror kaleido blur pixel tint flicker vignette stutter zoom."""
        from .render.fx import NAMES
        if name not in NAMES:
            raise ValueError(f"fx({name!r}): the effects are {', '.join(NAMES)}")
        need().fxs.append((float(t0), float(t1), name, float(amount)))

    def rain(amount=1.0):
        """Rain in the HTML export, drawn by the page (cheap: scrolling streak tiles). The preview GIF does not show it: for the GIF, place rain pictures on a layer named "rain..."
        (a parallax=0, over=True layer), and the HTML export leaves those layers out when ``rain()`` is set."""
        need().rain = float(amount)

    def chaos(shots=None, floor=None, singer=None, pit=None, crowd=(), band=None, lights=None, rate=1.0, grain=0.4, smash_at=None, rigs=None, feedback=None, throw=0.0):
        """Set up the random director of the HTML export (open it with ``#chaos=SEED``: fast random cuts and tilts, flashes, strobes, colour washes, beams, fights in the
        pit, guitars and keyboards smashed). ``shots``: [(x, y, zoom)] wide views to cut to; ``singer=(x, y)``; ``band={"guitar": tile, "bass": tile, "keys": tile, "drums": tile}``
        (the animated tiles placed for them: those get smashed); ``pit=(x0, x1, y)``: where the crowd stands (feet at y); ``crowd=[tiles]``: the people thrown around;
        ``lights=[(x, y)]``: where the beams start; ``floor``: the stage's floor y; ``rate`` how dense the chaos is; ``grain`` the film grain over it.
        ``smash_at={"guitar": (x, y)}``: a band member smashes his instrument on that point (a speaker's face) instead of the floor; ``rigs=[(x, y, w, h)]``: the synths and
        drum machines, which the camera cuts to in close-ups of the hands; ``feedback=(tile, x, y, size)``: the animated feedback rings (a tile) that flare at that point (the speaker
        the guitarist leans on) now and then; ``throw``: volleys of mud per second thrown from the crowd at the crowd, the band and the stage (0 for none)."""
        need().chaos = {"shots": [tuple(s) for s in (shots or [])], "floor": floor, "singer": singer, "pit": pit, "crowd": list(crowd), "band": dict(band or {}),
                        "lights": [tuple(p) for p in (lights or [])], "rate": float(rate), "grain": float(grain),
                        "smash_at": {k: tuple(v) for k, v in (smash_at or {}).items()}, "rigs": [tuple(r) for r in (rigs or [])], "feedback": feedback and tuple(feedback), "throw": float(throw)}

    def line(t, text, who=None, seconds=3.0):
        need().captions.append({"kind": "say", "t": float(t), "text": str(text), "who": who, "seconds": float(seconds)})

    def card(t, text, sub=None, seconds=3.5):
        need().captions.append({"kind": "title", "t": float(t), "text": str(text), "sub": sub, "seconds": float(seconds)})

    return {"scene": scene, "beat": beat, "show": show, "hide": hide, "face": face, "warp": warp, "dance": dance, "punch": punch, "shake": shake,
            "actor": actor, "chaos": chaos, "rain": rain, "move": move, "pose": pose, "emote": emote, "cam": cam, "cut": cut, "fade": fade, "fx": fx, "line": line, "card": card}
