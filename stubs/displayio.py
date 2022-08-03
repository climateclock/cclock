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
        source, x1=0, y1=0, x2=None, y2=None,
        skip_index=None, write_value=None):

        # Fill in default values for x2 and y2.
        x2 = source.width if x2 is None else x2
        y2 = source.height if y2 is None else y2

        # Clamp the bottom-right corner to the bottom-right of both bitmaps.
        x2 = min(x2, source.width, x1 + self.width - x)
        y2 = min(y2, source.height, y1 + self.height - y)

        # Clamp the top-left corner to the top-left of both bitmaps.
        min_x = min(x1, x)
        if min_x < 0:
            x += -min_x
            x1 += -min_x
        min_y = min(y1, y)
        if min_y < 0:
            y += -min_y
            y1 += -min_y

        # Proceed only if the resulting rectangle is non-empty.
        if (x < self.width and y < self.height and
            x1 < x2 and y1 < y2 and
            x1 < source.width and y1 < source.height):
            for sx in range(x1, x2):
                for sy in range(y1, y2):
                    dx = x + sx - x1
                    dy = y + sy - y1
                    value = source[sx + sy*source.width]
                    if skip_index is not None and value == skip_index:
                        continue
                    if write_value is not None and value != 0:
                        value = write_value
                    self[dx + dy*self.width] = value


class TileGrid:
    def __init__(self, *args, **kwargs):
        self.x = self. y = 0
