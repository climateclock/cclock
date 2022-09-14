import cctime
from ctypes import byref, c_char, c_void_p
import displayio
import microfont
from sdl2 import *


class FrameTimer:
    def __init__(self, fps):
        self.interval = int(1000/fps)
        self.next_frame = cctime.monotonic_millis() + self.interval

    def wait(self):
        """Waits until the next frame display time."""
        cctime.sleep_millis(self.next_frame - cctime.monotonic_millis())
        self.next_frame += self.interval


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


class SdlFrame:
    def __init__(self, w, h, fps, title='Frame', scale=8, pad=4):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.timer = FrameTimer(fps)
        self.scale = scale
        self.pad = pad

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
        print('Setting brightness to', brightness)
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

    def clear(self, x=0, y=0, w=None, h=None):
        if w is None:
            w = self.w
        if h is None:
            h = self.h
        self.fill(x, y, w, h, self.pack(0, 0, 0))

    def fill(self, x, y, w, h, cv):
        x, y, w, h = clamp_rect(x, y, w, h, self.w, self.h)
        if w > 0 and h > 0:
            row = cv * w
            for y in range(y, y + h):
                start = self.get_offset(x, y)
                self.pixels[start:start + w * 3] = row

    def paste(self, x, y, source, sx=0, sy=0, w=None, h=None, bg=None, cv=None):
        if source.w == 0 or source.h == 0:
            return
        x, y, sx, sy, w, h = intersect(self, x, y, source, sx, sy, w, h)
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

    def measure(self, text, font_id):
        return microfont.get(font_id).measure(text)

    def print(self, x, y, text, font_id, cv=1):
        label = LabelFrame(microfont.get(font_id), text)
        self.paste(x, y, label, cv=cv)
        return x + label.w

    def new_label(self, text, font_id):
        return LabelFrame(microfont.get(font_id), text)


class LabelFrame:
    def __init__(self, font, text):
        self.w, self.h = font.measure(text), font.h
        bitmap = displayio.Bitmap(self.w, self.h, 2)
        font.draw(text, bitmap)
        palette = b'\x00\x00\x00', b'\xff\xff\xff'
        self.pixels = b''.join(palette[p] for p in bitmap)


def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def clamp_rect(x, y, w, h, fw, fh):
    xl = clamp(x, 0, fw)
    xr = clamp(x + w, xl, fw)
    yt = clamp(y, 0, fh)
    yb = clamp(y + h, yt, fh)
    return xl, yt, xr - xl, yb - yt

def intersect(frame, x, y, source, sx, sy, w, h):
    # Fill in defaults for the source rectangle.
    sl = 0 if sx is None else sx
    st = 0 if sy is None else sy
    w = source.w if w is None else w
    h = source.h if h is None else h

    # Clamp the bottom-right corner to the bottom-right of both frames.
    sr = min(sl + w, source.w, sl + frame.w - x)
    sb = min(st + h, source.h, st + frame.h - y)

    # Clamp the top-left corner to the top-left of both frames.
    dx = max(-sl, -x)
    if dx > 0:
        x += dx
        sl += dx
    dy = max(-st, -y)
    if dy > 0:
        y += dy
        st += dy

    # Return the resulting rectangle if it is non-empty.
    if x < frame.w and y < frame.h:
        if sl < sr <= source.w and st < sb <= source.h:
            return x, y, sl, st, sr - sl, sb - st
    return 0, 0, 0, 0, 0, 0
