class Group:
    def __init__(self, x=0, y=0, scale=1):
        self._scale = scale

    def __iter__(self):
        return iter([])

    def append(self, item):
        pass

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, new_scale):
        self._scale = new_scale


class Palette(list):
    def __init__(self, n=1):
        self[:] = [0] * n

    def make_opaque(self, i):
        pass

    def make_transparent(self, i):
        pass

class Bitmap(list):
    def __init__(self, w, h, depth):
        self.width = w
        self.height = h
        self.depth = depth
        self[:] = [0] * w * h

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


class TileGrid:
    def __init__(self, *args, **kwargs):
        self.x = self. y = 0
