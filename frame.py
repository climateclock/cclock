"""Defines the Frame interface for drawing to a display."""

from abc import ABC, abstractmethod

class Frame(ABC):  # Frame is an abstract interface
    def __init__(self, w, h, fps):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.interval = 1/fps

    @abstractmethod
    def pack(self, r, g, b):
        """Packs three colour cmponents (each 0-255) into a colour value."""

    @abstractmethod
    def unpack(self, rgb):
        """Unpacks a colour value into its R, G, B components (each 0-255)."""

    @abstractmethod
    def send(self):
        """Causes the contents of the frame to appear on the display device
        one frame interval after the preceding frame appeared.  The
        implementation of this method is responsible for blocking as
        necessary to ensure that frames do not queue up indefinitely."""

    @abstractmethod
    def get(self, x, y):
        """Gets the colour of the single pixel at (x, y).  If the given
        coordinates are out of range, returns black."""

    @abstractmethod
    def set(self, x, y, rgb):
        """Sets the colour of the single pixel at (x, y) to rgb.  If the
        given coordinates are out of range, no exception is raised."""

    @abstractmethod
    def fill(self, x, y, w, h, rgb):
        """Sets the colour of all pixels in the rectangle from (x, y) to
        (x + w - 1), (y + h - 1), inclusive, to rgb.  Both w and h must be
        positive.  No exception is raised when any part of the rectangle is
        out of range; pixels in range are filled and the rest are ignored."""

    @abstractmethod
    def paste(self, x, y, source, sx, sy, sw, sh):
        """Copies a rectangle of pixels from a source frame into this frame,
        placing the top-left corner of the rectangle at (x, y).  No exception
        is raised when some pixels are out of range; pixels in range are
        pasted over and the rest are ignored."""

    @abstractmethod
    def print(self, font, text, horiz=-1, vert=-1):
        """Prints text into the frame using the given font.  Alignment within
        this frame is given by horiz (-1 for left, 0 for center, +1 for right)
        and vert (-1 for top, 0 for baseline, +1 for bottom).  No exception is
        raised when any part of the text is out of range; pixels in range are
        painted over and the rest are ignored."""
