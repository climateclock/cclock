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

class TileGrid:
    def __init__(self, *args, **kwargs):
        self.x = self. y = 0
