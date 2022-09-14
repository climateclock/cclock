class Group:
    def __init__(self, x=0, y=0, scale=1):
        pass

    def append(self, item):
        pass


class Palette(list):
    def __init__(self, n=1):
        self[:] = [0] * n


class TileGrid:
    def __init__(self, *args, **kwargs):
        self.x = self.y = 0


class Bitmap(list):
    def __init__(self, w, h, depth):
        self.width = w
        self.height = h
        self.depth = depth
        self[:] = [0] * w * h

    # Simulates file.readinto(memoryview(bitmap)).
    def readbits(self, file):
        bits = []
        rowsize = (self.width + 31)//32 * 4
        for y in range(self.height):
            row = []
            for x in range(0, rowsize, 4):
                chunk = file.read(4)
                row += map(int,
                    bin(0x100 + chunk[3])[-8:] +
                    bin(0x100 + chunk[2])[-8:] +
                    bin(0x100 + chunk[1])[-8:] +
                    bin(0x100 + chunk[0])[-8:]
                )
            bits += row[:self.width]
        self[:] = bits

    # This is intended to be a direct Python translation of
    # displayio_bitmap_obj_fill and common_hal_displayio_bitmap_fill.
    def fill(self, pi=0, x1=0, y1=0, x2=None, y2=None):
        x1 = min(max(x1, 0), self.width)
        y1 = min(max(y1, 0), self.height)
        x2 = self.width if x2 is None else x2
        y2 = self.height if y2 is None else y2
        x2 = min(max(x2, x1), self.width)
        y2 = min(max(y2, y1), self.height)

        for x in range(x1, x2):
            for y in range(y1, y2):
                self[x + y*self.width] = pi

    # This is intended to be a direct Python translation of
    # common_hal_displayio_bitmap_freeblit.
    def freeblit(
        self, x, y,
        source, sx=0, sy=0, w=None, h=None,
        source_bg=None, dest_value=None):

        sl = sx
        st = sy

        # Fill in default values for w and h.
        w = source.width if w is None else w
        h = source.height if h is None else h

        # Clamp the bottom-right corner to the bottom-right of both bitmaps.
        sr = min(sl + w, source.width, sl + self.width - x)
        sb = min(st + h, source.height, st + self.height - y)

        # Clamp the top-left corner to the top-left of both bitmaps.
        min_x = min(sl, x)
        if min_x < 0:
            x += -min_x
            sl += -min_x
        min_y = min(st, y)
        if min_y < 0:
            y += -min_y
            st += -min_y

        # Proceed only if the resulting rectangle is non-empty.
        if x < self.width and y < self.height and sl < sr and st < sb:
            for sx in range(sl, sr):
                for sy in range(st, sb):
                    dx = x + sx - sl
                    dy = y + sy - st
                    value = source[sx + sy*source.width]
                    if source_bg is not None and value == source_bg:
                        continue
                    if dest_value is not None and value != 0:
                        value = dest_value
                    self[dx + dy*self.width] = value
