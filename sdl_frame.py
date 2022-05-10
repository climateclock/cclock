import cctime
from ctypes import byref, c_char, c_void_p
import displayio
import frame
from sdl2 import *
import time
from adafruit_bitmap_font import pcf
from adafruit_display_text import bitmap_label

FONTS = {}

def load_font(font_id):
    if font_id not in FONTS:
        FONTS[font_id] = pcf.PCF(open(font_id + '.pcf', 'rb'), displayio.Bitmap)
    return FONTS[font_id]


def flush_events():
    event = SDL_Event()
    while SDL_PollEvent(byref(event)):
        if event.key.keysym.scancode == SDL_SCANCODE_ESCAPE:
            raise SystemExit()
        if event.type == SDL_QUIT:
            raise SystemExit()


class SdlFrame(frame.Frame):
    def __init__(self, w, h, fps, title='Frame', scale=8):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.timer = cctime.FrameTimer(fps)
        self.pixels = bytearray(b'\x00\x00\x00' * w * h)
        self.pixels_cptr = (c_char * len(self.pixels)).from_buffer(self.pixels)

        SDL_Init(SDL_INIT_VIDEO)
        self.window = SDL_CreateWindow(
            bytes(title, 'utf-8'),
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            w * scale, h * scale,
            SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        )
        self.surface = SDL_GetWindowSurface(self.window)
        self.canvas = SDL_CreateRGBSurface(
            0, w, h, 24, 0x0000ff, 0x00ff00, 0xff0000, 0)
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

    def paste(self, x, y, source, sx=None, sy=None, w=None, h=None):
        x, y, sx, sy, w, h = frame.intersect(self, x, y, source, sx, sy, w, h)
        i = (x + y * self.w) * 3
        si = (sx + sy * source.w) * 3
        for dy in range(0, h):
            self.pixels[i:i + w * 3] = source.pixels[si:si + w * 3]
            i += self.w * 3
            si += source.w * 3

    def new_label(self, text, font_id, cv):
        return LabelFrame(text, font_id, cv)


class LabelFrame(frame.Frame):
    def __init__(self, text, font_id, cv):
        font = load_font(font_id)
        label = bitmap_label.Label(font, text=text)
        black = bytearray([0, 0, 0])
        palette = [black, cv]
        self.w = label.bitmap.width
        self.h = label.bitmap.height
        self.pixels = b''.join(palette[p] for p in label.bitmap)
