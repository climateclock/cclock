"""Defines the Frame interface for drawing to a display.

Each implementation of Frame is free to use its own internal formats and depths
for pixel data and colour values.  Clients should treat each colour value (cv)
as an opaque object; call pack() to convert an (r, g, b) triple into a colour
value and unpack() to extract the (r, g, b) components from a colour value.

Implementing send() is optional.  A Frame that cannot send() is useful as a
buffer that can efficiently paste() from and to Frames of the same subtype.
The Frame returned by new_label() need not implement any methods; it only
needs to have self.w and self.h attributes and be accepted by self.paste().
"""

class Frame:  # Frame is an abstract interface
    def __init__(self, w, h):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h

    def pack(self, r, g, b):
        """Packs R, G, B components (each 0 to 255) into a colour value."""
        raise NotImplementedError

    def unpack(self, cv):
        """Unpacks a colour value into R, G, B components (each 0 to 255)."""
        raise NotImplementedError

    def send(self):
        """Causes the contents of the frame to appear on the display device
        one frame interval after the preceding frame appeared.  The
        implementation of this method is responsible for blocking as
        necessary to ensure that frames do not queue up indefinitely."""
        raise NotImplementedError

    def get(self, x, y):
        """Gets the colour of the single pixel at (x, y).  If the given
        coordinates are out of range, returns black."""
        raise NotImplementedError

    def set(self, x, y, cv):
        """Sets the colour of the single pixel at (x, y) to cv.  If the
        given coordinates are out of range, no exception is raised."""
        raise NotImplementedError

    def fill(self, x, y, w, h, cv):
        """Sets the colour of all pixels in the rectangle from (x, y) to
        (x + w - 1), (y + h - 1), inclusive, to cv.  Both w and h must be
        positive.  No exception is raised when any part of the rectangle is
        out of range; pixels in range are filled and the rest are ignored."""
        raise NotImplementedError

    def paste(self, x, y, source, sx=None, sy=None, sw=None, sh=None):
        """Copies a rectangle of pixels from a source frame into this frame,
        placing the top-left corner of the rectangle at (x, y).  No exception
        is raised when some pixels are out of range; pixels in range are
        pasted over and the rest are ignored."""
        raise NotImplementedError

    def new_label(self, text, font_id, cv):
        """Returns a new Frame, acceptable as a source argument to the paste()
        method, containing the given text rendered with the specified font and
        colour value.  The resulting frame is sized to the total width of the
        text and the height of a character cell in the specified font."""
        raise NotImplementedError


def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def clamp_rect(x, y, w, h, fw, fh):
    xl = clamp(x, 0, fw)
    xr = clamp(x + w, xl, fw)
    yt = clamp(y, 0, fh)
    yb = clamp(y + h, yt, fh)
    return xl, yt, xr - xl, yb - yt
