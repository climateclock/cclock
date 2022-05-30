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

class Frame:
    def __init__(self):
        raise NotImplementedError('Frame is an abstract interface')

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

    def clear(self, x=0, y=0, w=None, h=None):
        """Clears all pixels to black."""
        if w is None:
            w = self.w
        if h is None:
            h = self.h
        self.fill(x, y, w, h, self.pack(0, 0, 0))

    def fill(self, x, y, w, h, cv):
        """Sets the colour of all pixels in the rectangle from (x, y) to
        (x + w - 1), (y + h - 1), inclusive, to cv.  Both w and h must be
        positive.  No exception is raised when any part of the rectangle is
        out of range; pixels in range are filled and the rest are ignored."""
        raise NotImplementedError

    def paste(self, x, y, source, sx=None, sy=None, w=None, h=None):
        """Copies a rectangle of pixels from a source frame into this frame,
        placing the top-left corner of the rectangle at (x, y).  No exception
        is raised when some pixels are out of range; all pixels that would
        land in this frame are pasted over and the rest are ignored."""
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
