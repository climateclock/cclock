import cctime
from ctypes import byref, c_char, c_void_p
import frame
from sdl2 import *
import time

def flush_events():
    event = SDL_Event()
    while SDL_PollEvent(byref(event)):
        if event.key.keysym.scancode == SDL_SCANCODE_ESCAPE:
            raise SystemExit()
        if event.type == SDL_QUIT:
            raise SystemExit()


class SdlFrame(frame.Frame):
    def __init__(self, w, h, fps, title='Frame', scale=8):
        frame.Frame.__init__(self, w, h)
        self.timer = cctime.FrameTimer(fps)
        self.pixels = bytearray(b'\x00\x00\x00' * w * h)
        self.pixels_cptr = (c_char * len(self.pixels)).from_buffer(self.pixels)

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

    def unpack(self, cv):
        r, g, b = cv  # unpack bytearray
        return r, g, b  # return tuple

    def send(self):
        SDL_memcpy(c_void_p(self.canvas.contents.pixels),
            self.pixels_cptr, len(self.pixels))
        SDL_BlitScaled(self.canvas, None, self.surface, None)
        self.timer.wait()
        SDL_UpdateWindowSurface(self.window)
        flush_events()

    def get(self, x, y):
        offset = (x + y * self.w) * 3
        return self.pixels[offset:offset + 3]

    def set(self, x, y, cv):
        offset = (x + y * self.w) * 3
        cv = self.pack(*self.unpack(cv))
        self.pixels[offset:offset + 3] = cv

    def fill(self, x, y, w, h, cv):
        x, y, w, h = frame.clamp_rect(x, y, w, h, self.w, self.h)
        if w > 0 and h > 0:
            row = cv * w
            for y in range(y, y + h):
                start = (x + y * self.w) * 3
                self.pixels[start:start + w * 3] = row

    def paste(self, x, y, source, sx, sy, sw, sh):
        raise NotImplemented

    def new_text_frame(self, text, font_id, cv):
        raise NotImplemented
