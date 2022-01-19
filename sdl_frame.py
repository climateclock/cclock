from ctypes import byref, c_char, c_void_p
from frame import Frame
from sdl2 import *
import time

def flush_events():
    event = SDL_Event()
    while SDL_PollEvent(byref(event)):
        if event.type == SDL_QUIT:
            raise SystemExit()


class SdlFrame(Frame):
    def __init__(self, w, h, fps, title='Frame', scale=8):
        Frame.__init__(self, w, h, fps)
        self.pixels = bytearray(b'\x00\x00\x00' * w * h)
        self.pixels_cptr = (c_char * len(self.pixels)).from_buffer(self.pixels)
        self.next = 0

        SDL_Init(SDL_INIT_VIDEO)
        self.window = SDL_CreateWindow(
            title.encode('utf-8'),
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            w * scale, h * scale,
            SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        )
        self.surface = SDL_GetWindowSurface(self.window)
        self.canvas = SDL_CreateRGBSurface(
            0, w, h, 24, 0xff0000, 0x00ff00, 0x0000ff, 0)
        flush_events()

    def pack(self, r, g, b):
        return bytearray([r, g, b])
        return bytearray([r & 0xc0, g & 0xc0, b & 0xc0])

    def unpack(self, rgb):
        r, g, b = rgb  # unpack bytearray
        return r, g, b  # return tuple

    def send(self):
        SDL_memcpy(c_void_p(self.canvas.contents.pixels),
            self.pixels_cptr, len(self.pixels))
        SDL_BlitScaled(self.canvas, None, self.surface, None)
        SDL_UpdateWindowSurface(self.window)

        now = time.time()
        if self.next > now:
            time.sleep(self.next - now)
        self.next = now + self.interval
        flush_events()

    def get(self, x, y):
        offset = (x + y * self.w) * 3
        return self.pixels[offset:offset + 3]

    def set(self, x, y, rgb):
        offset = (x + y * self.w) * 3
        rgb = self.pack(*self.unpack(rgb))
        self.pixels[offset:offset + 3] = rgb

    def fill(self, x, y, w, h, rgb):
        x, y, w, h = clamp_rect(x, y, w, h, self.w, self.h)
        if w > 0 and h > 0:
            row = rgb * w
            for y in range(y, y + h):
                start = (x + y * self.w) * 3
                self.pixels[start:start + w * 3] = row

    def paste(self, x, y, source, sx, sy, sw, sh):
        raise NotImplemented

    def print(self, font, text, horiz=-1, vert=-1):
        raise NotImplemented

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def clamp_rect(x, y, w, h, fw, fh):
    xl = clamp(x, 0, fw)
    xr = clamp(x + w, xl, fw)
    yt = clamp(y, 0, fh)
    yb = clamp(y + h, yt, fh)
    return xl, yt, xr - xl, yb - yt
