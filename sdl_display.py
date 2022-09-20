import cctime
from ctypes import byref, c_char, c_void_p
import display
from sdl2 import *

sdl_display = None


class FrameTimer:
    def __init__(self, fps):
        self.interval = int(1000/fps)
        self.next_frame = cctime.monotonic_millis() + self.interval

    def wait(self):
        """Waits until the next frame display time."""
        cctime.sleep_millis(self.next_frame - cctime.monotonic_millis())
        self.next_frame += self.interval


class SdlButton:
    def __init__(self, scancode):
        self.scancode = scancode

    @property
    def pressed(self):
        return self.scancode in sdl_display.pressed_scancodes


class SdlDial:
    def __init__(
        self, decr_scancode, incr_scancode, min_value, max_value, delta
    ):
        sdl_display.key_handlers.append(self)
        self.decr_scancode = decr_scancode
        self.incr_scancode = incr_scancode
        self.min_value = min_value
        self.max_value = max_value
        self.delta = delta
        self.value = min_value

    def key_down(self, scancode):
        if scancode == self.decr_scancode:
            self.value = max(self.min_value, self.value - self.delta)
        if scancode == self.incr_scancode:
            self.value = min(self.max_value, self.value + self.delta)

    def key_up(self, scancode):
        pass


def init(bitmap, fps):
    global sdl_display
    sdl_display = SdlDisplay(bitmap, fps, display.BIT_DEPTH)
    display.shader = [0]*bitmap.depth
    display.send = sdl_display.send


class SdlDisplay:
    def __init__(self, bitmap, fps, bit_depth, title='Frame', scale=8, pad=4):
        self.bitmap = bitmap
        self.timer = FrameTimer(fps)
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
        self.key_handlers = []
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

    def set_scale(self, scale):
        self.scale = scale
        SDL_SetWindowSize(self.window, self.pw * scale, self.ph * scale)

    def send(self):
        rgbs = [(0, 0, 0)] * self.bitmap.depth

        # Simulate the limited colour depth of the board.
        shift = 8 - self.bit_depth
        limit = 1 << self.bit_depth
        for pi in range(self.bitmap.depth):
            r = display.shader[pi] >> 16
            g = (display.shader[pi] >> 8) & 0xff
            b = display.shader[pi] & 0xff
            # Quantize and convert to colour values between 0.0 and 1.0.
            r = (r >> shift) / limit
            g = (g >> shift) / limit
            b = (b >> shift) / limit
            # Apply gamma correction (LED values are linear due to PWM).
            rgbs[pi] = int((r**0.6)*256), int((g**0.6)*256), int((b**0.6)*256)
        for y in range(self.bitmap.height):
            for x in range(self.bitmap.width):
                si = y * self.bitmap.width + x
                offset = ((x + self.pad) + (y + self.pad) * self.pw) * 3
                self.pixels[offset:offset + 3] = rgbs[self.bitmap[si]]
        SDL_memcpy(c_void_p(self.canvas.contents.pixels),
            self.pixels_cptr, len(self.pixels))
        surface = SDL_GetWindowSurface(self.window)
        SDL_BlitScaled(self.canvas, None, surface, None)
        self.timer.wait()
        SDL_UpdateWindowSurface(self.window)
        self.flush_events()
