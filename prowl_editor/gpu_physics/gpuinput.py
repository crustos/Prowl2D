"""What the CPU feeds the GPU each frame: keyboard, mouse, time.

GPU scripts cannot call Input2D; the host packs the same state into one small
buffer and every script kernel that asks for it (a parameter named `input_u32`
and/or `input_f32`, both views of the same memory) reads it from there:

    words 0..511   key state, one u32 per key code, 1 while held. Codes are
                   Input2D's: arrows 263 262 264 265, Space 32, Escape 256,
                   letters and digits are their capital letter / digit codes.
    word  512      mouse buttons, a bitmask (bit 0 left, 1 middle, 2 right)
    word  513      mouse x   (f32, world units)
    word  514      mouse y   (f32, world units)
    word  515      frame number (u32)
    word  516      dt, seconds (f32)
    word  517      time since play started, seconds (f32)
    word  518      number of live bodies (u32)
    word  519      reserved

`pressed` / `released` edges are not stored: a kernel that wants one compares
with state it keeps in its own buffer. `INPUT_U32` / `INPUT_F32` are the names
a kernel declares; the layout constants below are mirrored in
gpu/prowl_input.md for script authors.
"""
import struct

KEYS = 512
BUTTONS, MOUSE_X, MOUSE_Y, FRAME, DT, TIME, COUNT = 512, 513, 514, 515, 516, 517, 518
WORDS = 520
INPUT_U32 = "input_u32"
INPUT_F32 = "input_f32"

# Input2D key codes (Native/Engine2D/Input2D.cs)
KEY_LEFT, KEY_RIGHT, KEY_DOWN, KEY_UP = 263, 262, 264, 265
KEY_SPACE, KEY_ESCAPE = 32, 256


class GpuInput:
    def __init__(self):
        self.keys = [0] * KEYS
        self.buttons = 0
        self.mouse = (0.0, 0.0)
        self.frame = 0
        self.dt = 0.0
        self.time = 0.0
        self.count = 0

    # the same calls the engine's p2d_set_key / p2d_set_mouse get
    def set_key(self, key, down):
        if 0 <= key < KEYS:
            self.keys[key] = 1 if down else 0

    def set_mouse(self, x, y, buttons):
        self.mouse = (float(x), float(y))
        self.buttons = int(buttons) & 7

    def clear(self):
        self.keys = [0] * KEYS
        self.buttons = 0

    def tick(self, dt, count):
        self.frame += 1
        self.dt = float(dt)
        self.time += float(dt)
        self.count = int(count)

    def key(self, key):
        return 0 <= key < KEYS and self.keys[key] != 0

    def pack(self):
        """The buffer contents, WORDS * 4 bytes."""
        head = struct.pack("<%dI" % KEYS, *self.keys)
        tail = struct.pack("<IffIffII", self.buttons, self.mouse[0], self.mouse[1],
                           self.frame & 0xFFFFFFFF, self.dt, self.time, self.count, 0)
        return head + tail
