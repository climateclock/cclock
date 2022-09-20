import cctime
from ctypes import byref, c_char, c_void_p
import display
from sdl2 import *
import sim_inputs


def install():
    display.init = init


def init(bitmap):
    sim_display = SimDisplay(bitmap, 20, display.BIT_DEPTH)
    display.shader = [0]*bitmap.depth
    display.send = sim_display.send


class SimDisplay:
    def __init__(self, bitmap, fps, bit_depth, title='Frame', scale=8, pad=4):
        self.bitmap = bitmap
        self.fps = fps
        self.bit_depth = bit_depth
        self.scale = scale
        self.pad = pad

        self.pw = bitmap.width + pad*2  # width with padding
        self.ph = bitmap.height + pad*2  # height with padding
        self.pixels = bytearray(b'\x60\x60\x60' * self.pw * self.ph)
        self.pixels_cptr = (c_char * len(self.pixels)).from_buffer(self.pixels)

        SDL_Init(SDL_INIT_VIDEO)
        self.window = SDL_CreateWindow(
            bytes(title, 'utf-8'),
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            (self.bitmap.width + pad*2) * scale,
            (self.bitmap.height + pad*2) * scale,
            SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        )
        self.canvas = SDL_CreateRGBSurface(
            0, self.pw, self.ph, 24, 0x0000ff, 0x00ff00, 0xff0000, 0)
        self.pressed_scancodes = set()
        self.flush_events()

    def flush_events(self):
        event = SDL_Event()
        while SDL_PollEvent(byref(event)):
            sim_inputs.handle_event(event)
            scancode = event.key.keysym.scancode
            if event.type == SDL_KEYDOWN:
                if scancode == SDL_SCANCODE_MINUS:
                    if self.scale > 1:
                        self.set_scale(self.scale - 1)
                if scancode == SDL_SCANCODE_EQUALS:
                    self.set_scale(self.scale + 1)
            if scancode == SDL_SCANCODE_ESCAPE:
                raise SystemExit()
            if event.type == SDL_QUIT:
                raise SystemExit()

    def set_scale(self, scale):
        self.scale = scale
        SDL_SetWindowSize(self.window, self.pw * scale, self.ph * scale)

    def send(self):
        rgbs = [(0, 0, 0)] * len(display.shader)

        # Simulate the limited colour depth of the board.
        shift = 8 - self.bit_depth
        limit = 1 << self.bit_depth
        for pi in range(len(display.shader)):
            r = display.shader[pi] >> 16
            g = (display.shader[pi] >> 8) & 0xff
            b = display.shader[pi] & 0xff
            # Quantize and convert to colour values between 0.0 and 1.0.
            r = (r >> shift) / limit
            g = (g >> shift) / limit
            b = (b >> shift) / limit
            # Apply gamma correction (LED values are linear due to PWM).
            rgbs[pi] = int((r**0.5)*256), int((g**0.5)*256), int((b**0.5)*256)
        for y in range(self.bitmap.height):
            for x in range(self.bitmap.width):
                si = y * self.bitmap.width + x
                offset = ((x + self.pad) + (y + self.pad) * self.pw) * 3
                self.pixels[offset:offset + 3] = rgbs[self.bitmap[si]]
        SDL_memcpy(c_void_p(self.canvas.contents.pixels),
            self.pixels_cptr, len(self.pixels))
        surface = SDL_GetWindowSurface(self.window)
        SDL_BlitScaled(self.canvas, None, surface, None)
        cctime.sleep_millis(1000//self.fps)
        SDL_UpdateWindowSurface(self.window)
        self.flush_events()
