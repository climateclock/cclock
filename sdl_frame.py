import cctime
from ctypes import byref, c_char, c_void_p
from displayio import Bitmap
import draw_text
import frame
from sdl2 import *
import time


class SdlButton:
    def __init__(self, frame, scancode):
        self.frame = frame
        self.scancode = scancode

    @property
    def pressed(self):
        return self.scancode in self.frame.pressed_scancodes


class SdlDial:
    def __init__(
        self, frame, decr_scancode, incr_scancode, min_value, max_value, delta
    ):
        frame.key_handlers.append(self)
        self.decr_scancode = decr_scancode
        self.incr_scancode = incr_scancode
        self.min_value = min_value
        self.max_value = max_value
        self.delta = delta
        self.value = (min_value + max_value)/2
        if isinstance(min_value + max_value, int):
            self.value = int(self.value)

    def key_down(self, scancode):
        if scancode == self.decr_scancode:
            self.value = max(self.min_value, self.value - self.delta)
        if scancode == self.incr_scancode:
            self.value = min(self.max_value, self.value + self.delta)

    def key_up(self, scancode):
        pass


class SdlFrame(frame.Frame):
    def __init__(self, w, h, fps, title='Frame', scale=8, pad=4, fontlib=None):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.timer = cctime.FrameTimer(fps)
        self.scale = scale
        self.pad = pad
        self.fontlib = fontlib

        self.pw = w + pad*2  # width with padding
        self.ph = h + pad*2  # height with padding
        self.pixels = bytearray(b'\x60\x60\x60' * self.pw * self.ph)
        self.pixels_cptr = (c_char * len(self.pixels)).from_buffer(self.pixels)
        self.key_handlers = []
        self.clear()

        SDL_Init(SDL_INIT_VIDEO)
        self.window = SDL_CreateWindow(
            bytes(title, 'utf-8'),
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            (w + pad*2) * scale, (h + pad*2) * scale,
            SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        )
        self.canvas = SDL_CreateRGBSurface(
            0, self.pw, self.ph, 24, 0x0000ff, 0x00ff00, 0xff0000, 0)
        self.pressed_scancodes = set()
        self.flush_events()

    def set_brightness(self, brightness):
        print('brightness =', brightness)
        # TODO: Actually change the brightness of the displayed pixels

    def pack(self, r, g, b):
        r = int(((float(r & 0xf0)/255.0) ** 0.3) * 255.99)
        g = int(((float(g & 0xf0)/255.0) ** 0.3) * 255.99)
        b = int(((float(b & 0xf0)/255.0) ** 0.3) * 255.99)
        return bytes([r, g, b])

    def set_scale(self, scale):
        self.scale = scale
        SDL_SetWindowSize(self.window, self.pw * scale, self.ph * scale)

    def send(self):
        SDL_memcpy(c_void_p(self.canvas.contents.pixels),
            self.pixels_cptr, len(self.pixels))
        surface = SDL_GetWindowSurface(self.window)
        SDL_BlitScaled(self.canvas, None, surface, None)
        self.timer.wait()
        SDL_UpdateWindowSurface(self.window)
        self.flush_events()

    def flush_events(self):
        event = SDL_Event()
        while SDL_PollEvent(byref(event)):
            scancode = event.key.keysym.scancode
            if event.type == SDL_KEYDOWN:
                self.pressed_scancodes.add(scancode)
                for key_handler in self.key_handlers:
                    key_handler.key_down(scancode)
                if scancode == SDL_SCANCODE_MINUS:
                    if self.scale > 1:
                        self.set_scale(self.scale - 1)
                elif scancode == SDL_SCANCODE_EQUALS:
                    self.set_scale(self.scale + 1)
            if event.type == SDL_KEYUP:
                self.pressed_scancodes -= {scancode}
                for key_handler in self.key_handlers:
                    key_handler.key_up(scancode)
            if scancode == SDL_SCANCODE_ESCAPE:
                raise SystemExit()
            if event.type == SDL_QUIT:
                raise SystemExit()

    def get_offset(self, x, y):
        return ((x + self.pad) + (y + self.pad) * self.pw) * 3

    def get(self, x, y):
        offset = self.get_offset(x, y)
        return self.pixels[offset:offset + 3]

    def set(self, x, y, cv):
        offset = self.get_offset(x, y)
        self.pixels[offset:offset + 3] = cv

    def fill(self, x, y, w, h, cv):
        x, y, w, h = frame.clamp_rect(x, y, w, h, self.w, self.h)
        if w > 0 and h > 0:
            row = cv * w
            for y in range(y, y + h):
                start = self.get_offset(x, y)
                self.pixels[start:start + w * 3] = row

    def paste(self, x, y, source, sx=0, sy=0, w=None, h=None, bg=None, cv=None):
        if source.w == 0 or source.h == 0:
            return
        x, y, sx, sy, w, h = frame.intersect(self, x, y, source, sx, sy, w, h)
        for dy in range(h):
            i = self.get_offset(x, y + dy)
            si = (sx + (sy + dy) * source.w) * 3
            if bg is None and cv is None:
                self.pixels[i:i + w * 3] = source.pixels[si:si + w * 3]
            else:
                for dx in range(w):
                    value = source.pixels[si:si + 3]
                    if value == bg:
                        continue
                    if cv is not None and value != b'\x00\x00\x00':
                        value = cv
                    self.pixels[i:i + 3] = value
                    i += 3
                    si += 3

    def measure(self, text, font):
        font = self.fontlib.get(font_id)
        return draw_text.measure(text, font)

    def print(self, x, y, text, font_id, cv=1):
        font = self.fontlib.get(font_id)
        label = LabelFrame(text, font)
        self.paste(x, y, label, cv=cv)

    def new_label(self, text, font_id):
        font = self.fontlib.get(font_id)
        return LabelFrame(text, font)


class LabelFrame(frame.Frame):
    def __init__(self, text, font):
        self.w = draw_text.measure(text, font)
        self.h = font.get_bounding_box()[1]
        bitmap = Bitmap(self.w, self.h, 2)
        draw_text.draw(text, font, bitmap)
        palette = b'\x00\x00\x00', b'\xff\xff\xff'
        self.pixels = b''.join(palette[p] for p in bitmap)
