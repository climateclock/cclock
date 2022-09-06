import board
import cctime
import displayio
import frame
import framebufferio
import microfont
import rgbmatrix
import utils

# NOTE: Setting BIT_DEPTH to 5 gives the best colour rendering and brightness
# control (higher than 5 doesn't help because the hardware colour depth appears
# to be 5 red, 6 green, 5 blue).  If memory is tight, though, we sometimes need
# to set BIT_DEPTH lower to avoid MemoryErrors.
BIT_DEPTH = 4
MIN_RGB_VALUE = 0x100 >> BIT_DEPTH


def new_display_frame(w, h, depth, rgb_pins, addr_pins):
    displayio.release_displays()
    matrix = rgbmatrix.RGBMatrix(
        width=192, height=32, bit_depth=BIT_DEPTH,
        rgb_pins=[getattr(board, name) for name in rgb_pins.split()],
        addr_pins=[getattr(board, name) for name in addr_pins.split()],
        clock_pin=board.MTX_CLK,
        latch_pin=board.MTX_LAT,
        output_enable_pin=board.MTX_OE
    )
    return MatrixFrame(w, h, depth, matrix)


def apply_brightness(brightness, r, g, b):
    # When scaling down, don't scale down any nonzero values to zero.
    min_r = MIN_RGB_VALUE if r else 0
    min_g = MIN_RGB_VALUE if g else 0
    min_b = MIN_RGB_VALUE if b else 0
    return (
        max(min_r, int(brightness * r)),
        max(min_g, int(brightness * g)),
        max(min_b, int(brightness * b))
    )


class MatrixFrame(frame.Frame):
    def __init__(self, w, h, depth, matrix=None):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.depth = depth
        self.bitmap = displayio.Bitmap(w, h, depth)
        self.display = None
        if matrix:
            self.display = framebufferio.FramebufferDisplay(
                matrix, auto_refresh=False)

            self.shader = displayio.Palette(depth)
            self.colours = [(0, 0, 0)] * self.depth
            self.brightness = 1.0
            self.next_cv = 1

            self.layer = displayio.TileGrid(self.bitmap, pixel_shader=self.shader)
            self.group = displayio.Group()
            self.group.append(self.layer)
            self.display.show(self.group)
            self.error_label = None

    def set_brightness(self, brightness):
        self.brightness = brightness
        for cv in range(self.next_cv):
            sr, sg, sb = apply_brightness(self.brightness, *self.colours[cv])
            self.shader[cv] = ((sr << 16) | (sg << 8) | sb)

    def pack(self, r, g, b):
        for cv in range(0, self.next_cv):
            if self.colours[cv] == (r, g, b):
                return cv
        if self.next_cv < self.depth:
            self.colours[self.next_cv] = (r, g, b)
            sr, sg, sb = apply_brightness(self.brightness, r, g, b)
            self.shader[self.next_cv] = ((sr << 16) | (sg << 8) | sb)
            self.next_cv += 1
        return self.next_cv - 1

    def unpack(self, cv):
        return self.colours[cv]

    def send(self):
        self.display.refresh(minimum_frames_per_second=0)
        # Display bug: refresh() doesn't cause a refresh unless we also set
        # auto_refresh = False (even though auto_refresh is already False!).
        self.display.auto_refresh = False

    def get(self, x, y):
        return self.bitmap[x, y]

    def set(self, x, y, cv):
        self.bitmap[x, y] = cv

    def fill(self, x, y, w, h, cv):
        self.bitmap.fill(cv, x, y, x + w, y + h)

    def paste(self, x, y, source, sx=0, sy=0, w=None, h=None, bg=None, cv=None):
        self.bitmap.freeblit(x, y, source.bitmap, sx, sy, w, h, bg, cv)

    def measure(self, text, font_id):
        return microfont.get(font_id).measure(text)

    def print(self, x, y, text, font_id, cv=1):
        return microfont.get(font_id).draw(text, self.bitmap, x, y, cv)

    def new_label(self, text, font_id):
        return LabelFrame(microfont.get(font_id), text)


class LabelFrame(frame.Frame):
    def __init__(self, font, text):
        self.w, self.h = font.measure(text), font.h
        self.bitmap = displayio.Bitmap(self.w, self.h, 2)
        font.draw(text, self.bitmap)
