#!/usr/bin/env python3
"""make_bodies.py: writes bodies.txt, the four animated ASCII art bodies of SlimeJumpFaces (the sprite ASCII format of prowl.py --import-ascii, so the file opens in the
editor and each frame can be painted over by hand).

    python3 tools/slime_faces/make_bodies.py            # -> tools/slime_faces/bodies.txt

Each body has 4 frames. A 32x32 square of `@` (magenta #ff00ff) is where the head goes (emoji_faces.py puts it there, in every frame, so the body can move it: the
spring squashes, the jetpack bobs); the body is drawn around it and never under it. A 1 pixel outline is put round everything that is not the square.

    body_spring   a coil spring on a foot plate: squashes and stretches            for the zany face   (kind 2)
    body_jet      a jetpack: two pods and a flickering flame                       for the grump       (kind 3)
    body_spider   eight legs, walking in two sets                                  for the screamer    (kind 4)
    body_golem    a steam golem: swinging fists, a gauge, a stepping gait, steam   for the boss        (kind 5)
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = 32            # the head's square, in pixels (2 world units at 16 pixels to a unit)
FRAMES = 4


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [["."] * w for _ in range(h)]

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for d in range(thick):
                self.put(x + (d if abs(y1 - y0) > abs(x1 - x0) else 0), y + (d if abs(y1 - y0) <= abs(x1 - x0) else 0), c)

    def disc(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def outline(self, c="K"):
        """1 pixel of `c` round every pixel that is drawn (not empty)."""
        edge = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] != ".":
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and self.px[ny][nx] not in (".", c):
                        edge.append((x, y))
                        break
        for x, y in edge:
            self.px[y][x] = c

    def head(self, x, y):
        self.rect(x, y, x + HEAD - 1, y + HEAD - 1, "@")

    def rows(self):
        return ["".join(r) for r in self.px]


def finish(cv, hx, hy):
    cv.outline()
    cv.head(hx, hy)               # the square goes last: nothing of the body is under the head
    return cv.rows()


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# body_spring: 40 x 56

SPRING = {"@": "#ff00ff", "K": "#241c33", "S": "#aab4c4", "H": "#e6edf7", "P": "#6a5aa0", "Q": "#9486cc", "D": "#3b3463"}


def body_spring(f):
    L = (22, 15, 8, 15)[f]                       # how long the spring is: stretched, halfway, squashed, halfway
    cv = Canvas(40, 64)
    hy = 28 - L
    top = hy + HEAD
    cv.rect(18, top, 21, 59, "D")                # the post the coils turn about: it shows between the coils when the spring is long
    for k in range(5):
        y0 = top + k * (L - 3) / 4.0             # the first coil is under the chin, the last one on the foot plate
        for x in range(11, 29):
            y = y0 + (x - 11) * 2 / 17.0         # a coil leans: it is a turn of a helix seen from the side
            cv.put(x, y, "H")
            cv.put(x, y + 1, "S")
            cv.put(x, y + 2, "D")
    cv.rect(8, 60, 31, 63, "P")                  # the foot plate
    cv.rect(8, 60, 31, 60, "Q")
    cv.put(11, 62, "D"); cv.put(28, 62, "D")
    return finish(cv, 4, hy)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# body_jet: 44 x 56

JET = {"@": "#ff00ff", "K": "#241c33", "M": "#9aa3b8", "N": "#586078", "R": "#e8452c", "O": "#ff9a2e", "Y": "#ffe45e"}


def flame(cv, cx, y0, length, wmax):
    for i in range(length):
        t = i / float(length)
        for c, w in (("R", wmax * (1 - t) ** 0.7), ("O", 0.62 * wmax * (1 - t) ** 0.8 if t < 0.8 else 0), ("Y", 0.3 * wmax * (1 - t) if t < 0.6 else 0)):
            w = int(round(w))
            if w < 1:
                continue
            for x in range(w):
                cv.put(cx - (w - 1) / 2.0 + x, y0 + i, c)


def body_jet(f):
    cv = Canvas(44, 56)
    hy = (4, 5, 4, 3)[f]
    for x0 in (1, 38):                            # the two pods
        cv.rect(x0, hy + 14, x0 + 4, hy + 27, "M")
        cv.rect(x0 + (3 if x0 == 1 else 0), hy + 14, x0 + (4 if x0 == 1 else 1), hy + 27, "N")
        cv.rect(x0 + 1, hy + 28, x0 + 3, hy + 29, "N")
        flame(cv, x0 + 2, hy + 30, (3, 5, 2, 4)[f], 3)
    cv.rect(18, hy + 32, 25, hy + 32, "M")        # the nozzle under the chin
    cv.rect(19, hy + 33, 24, hy + 33, "M")
    cv.rect(19, hy + 34, 24, hy + 34, "N")
    flame(cv, 21.5 + (0, 1, -1, 0)[f], hy + 35, (12, 16, 9, 14)[f], 8)
    return finish(cv, 6, hy)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# body_spider: 72 x 50

SPIDER = {"@": "#ff00ff", "K": "#241c33", "B": "#6b4a94", "C": "#a183cc", "L": "#8f6dbb", "E": "#ff5a5a"}


def body_spider(f):
    cv = Canvas(72, 50)
    hy = (2, 3, 2, 3)[f]
    cx = 36
    for side in (-1, 1):
        for k in range(4):
            group = (k + (0 if side < 0 else 1)) % 2         # the legs walk in two sets, opposite corners together
            lift = ((3, 1, 0, 1) if group == 0 else (0, 1, 3, 1))[f]
            hip = (cx + side * (4 + k * 3), hy + 38)
            knee = (cx + side * (19 + k * 4.5), hy + 30 - lift)
            foot = (cx + side * (24 + k * 3.5), 47 - lift)
            cv.line(hip[0], hip[1], knee[0], knee[1], "L", 2)
            cv.line(knee[0], knee[1], foot[0], foot[1], "L", 2)
    cv.disc(cx, hy + 37, 17, 8, "B")                          # the shell
    cv.rect(cx - 13, hy + 36, cx + 13, hy + 36, "C")
    for ex in (cx - 9, cx + 7):                                # two red eyes that look down at the floor
        cv.rect(ex, hy + 41, ex + 2, hy + 42, "E")
    return finish(cv, 20, hy)


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# body_golem: 88 x 94

GOLEM = {"@": "#ff00ff", "K": "#1f1a26", "I": "#5b6475", "L": "#8b95aa", "D": "#3a4152", "B": "#c9922e", "Y": "#f0c15a", "R": "#c4452c", "W": "#e8eef6"}


def body_golem(f):
    cv = Canvas(88, 94)
    hy = (2, 3, 4, 3)[f]
    hx = 28
    swing = (1, 0, -1, 0)[f]                                  # the left fist up, level, down; the right one the other way round
    steam = f * 3
    for puff in range(2):                                     # steam out of the shoulders, rising
        for side, px in ((-1, 18), (1, 69)):
            y = hy + 30 - (steam + puff * 6) % 12
            r = 1 + (steam + puff * 6) % 12 // 5
            cv.disc(px + side * puff, y, r, r, "W")
    cv.rect(36, hy + 30, 51, hy + 36, "D")                    # the neck
    cv.rect(22, hy + 34, 65, hy + 62, "I")                    # the chest
    cv.rect(22, hy + 34, 65, hy + 35, "L")
    cv.rect(22, hy + 60, 65, hy + 62, "D")
    cv.rect(30, hy + 42, 57, hy + 56, "D")                    # a panel with a gauge in it
    cv.rect(31, hy + 43, 56, hy + 55, "I")
    for rx, ry in ((32, hy + 44), (55, hy + 44), (32, hy + 54), (55, hy + 54)):
        cv.put(rx, ry, "Y")
    cv.disc(43.5, hy + 49, 7, 7, "B")
    cv.disc(43.5, hy + 49, 5.2, 5.2, "W")
    a = math.radians((-70, -25, 25, -25)[f] - 90)
    cv.line(43.5, hy + 49, 43.5 + 4.5 * math.cos(a), hy + 49 + 4.5 * math.sin(a), "R")
    for side, sx in ((-1, 17), (1, 70)):                      # shoulders, and the arms hanging from them with a fist at the end
        cv.disc(sx, hy + 42, 9, 9, "L")
        cv.disc(sx, hy + 42, 3, 3, "B")
        raised = swing if side < 0 else -swing
        fx, fy = 9 if side < 0 else 78, hy + 66 - 7 * raised
        for d in range(5):
            cv.line(sx - 2 + d, hy + 48, fx - 2 + d, fy - 5, "I")
        cv.line(sx - 2, hy + 48, fx - 2, fy - 5, "L")
        cv.rect(fx - 5, fy - 5, fx + 5, fy + 5, "I")          # the fist
        cv.rect(fx - 5, fy - 5, fx + 5, fy - 4, "L")
        cv.rect(fx - 5, fy + 3, fx + 5, fy + 5, "D")
        cv.rect(fx - 4, fy - 1, fx + 4, fy - 1, "B")
    for lx, lift in ((28, (0, 2, 0, 0)[f]), (47, (0, 0, 0, 2)[f])):    # the legs: one steps, then the other
        cv.rect(lx, hy + 62, lx + 12, hy + 80 - lift, "I")
        cv.rect(lx + 9, hy + 62, lx + 12, hy + 80 - lift, "D")
        cv.rect(lx - 2, hy + 81 - lift, lx + 14, hy + 86 - lift, "D")
        cv.rect(lx - 2, hy + 81 - lift, lx + 14, hy + 82 - lift, "B")
    return finish(cv, hx, hy)


BODIES = (("body_spring", SPRING, body_spring), ("body_jet", JET, body_jet), ("body_spider", SPIDER, body_spider), ("body_golem", GOLEM, body_golem))


def text():
    out = []
    for name, palette, make in BODIES:
        frames = [make(f) for f in range(FRAMES)]
        used = {c for fr in frames for row in fr for c in row} - {"."}
        out += ["# sprite: " + name, "# fps: 8", "# palette: " + " ".join("%s=%s" % (k, v) for k, v in palette.items() if k in used)]
        for fr in frames:
            out += fr + [""]
    return "\n".join(out)


if __name__ == "__main__":
    path = os.path.join(HERE, "bodies.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text())
    print("wrote", path)
