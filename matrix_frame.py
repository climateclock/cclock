from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import bitmap_label
import bitmaptools
import board
import cctime
import displayio
import frame
import framebufferio
import rgbmatrix
from ulab import numpy as np

FONTS = {}

def load_font(font_id):
    if font_id not in FONTS:
        FONTS[font_id] = bitmap_font.load_font(font_id + '.pcf')
    return FONTS[font_id]


def new_display_frame(w, h, depth):
    displayio.release_displays()
    return MatrixFrame(w, h, depth, rgbmatrix.RGBMatrix(
        width=192, height=32, bit_depth=4,
        rgb_pins=[
            board.MTX_R1, board.MTX_G1, board.MTX_B1,
            board.MTX_R2, board.MTX_G2, board.MTX_B2
        ],
        addr_pins=[
            board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD
        ],
        clock_pin=board.MTX_CLK,
        latch_pin=board.MTX_LAT,
        output_enable_pin=board.MTX_OE
    ))


class MatrixFrame(frame.Frame):
    def __init__(self, w, h, depth, matrix=None):
        frame.Frame.__init__(self, w, h)
        self.bitmap = displayio.Bitmap(w, h, depth)
        self.depth = depth
        self.display = None
        if matrix:
            self.display = framebufferio.FramebufferDisplay(matrix)
            self.shader = displayio.Palette(2)
            self.shader[0] = 0
            self.shader[1] = 0xeb1c23
            self.layer = displayio.TileGrid(self.bitmap, pixel_shader=self.shader)
            self.group = displayio.Group()
            self.group.append(self.layer)
            self.display.show(self.group)

    def pack(self, r, g, b):
        # TODO handle real colour values; update the palette shader
        return ((r << 16) | (g << 8) | b) % self.depth

    def unpack(self, cv):
        return (cv >> 16) & 0xff, (cv >> 8) & 0xff, cv & 0xff

    def send(self):
        # FramebufferDisplay has auto_refresh set, so no need to do anything.
        pass

    def get(self, x, y):
        return self.bitmap[x, y]

    def set(self, x, y, cv):
        self.bitmap[x, y] = cv

    def fill(self, x, y, w, h, cv):
        x, y, w, h = frame.clamp_rect(x, y, w, h, self.w, self.h)
        bitmaptools.fill_region(self.bitmap, x, y, x + w, y + h, cv)

    def paste(self, x, y, source, sx=None, sy=None, sw=None, sh=None, cv=None):
        x1 = sx or 0
        y1 = sy or 0
        x2 = x1 + (sw or source.w)
        y2 = y1 + (sh or source.h)
        self.bitmap.blit(x, y, source.bitmap, x1=x1, y1=y1, x2=x2, y2=y2)

    def new_label(self, text, font_id, cv):
        return LabelFrame(text, font_id, cv)


class LabelFrame(frame.Frame):
    def __init__(self, text, font_id, cv):
        font = load_font(font_id)
        label = bitmap_label.Label(font, text=text, color=cv, save_text=False)
        self.bitmap = label.bitmap
        frame.Frame.__init__(self, self.bitmap.width, self.bitmap.height)