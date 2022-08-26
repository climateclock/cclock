import cctime
import frame
import subprocess
import time


class FrameTimer:
    def __init__(self, fps):
        self.next = 0
        self.interval = int(1000/fps)

    def wait(self):
        """Waits until the next frame display time."""
        next = self.next + self.interval
        cctime.wait_until_millis(self.next)
        self.next = next


class MpvFrame(frame.Frame):
    """A Frame implementation that uses the mpv video player for display."""

    def __init__(self, w, h, fps):
        """Creates a Frame with a given width and height.  Coordinates of the
        top-left and bottom-right pixels are (0, 0) and (w - 1, h - 1)."""
        self.w = w
        self.h = h
        self.timer = FrameTimer(fps)
        self.pixels = bytearray(b'\x00\x00\x00' * w * h)
        self.process = subprocess.Popen([
            'mpv',

            # Show each pixel as an 8x8 block, with no smoothing.
            f'--geometry={w*8}x{h*8}',
            '--scale=oversample',

            # All these options are here to make mpv display frames in
            # real time as it receives them, with the absolute minimum
            # processing, buffering, or synchronization.
            '--audio-buffer=0',
            '--cache-pause=no',
            '--vd-lavc-threads=1',
            '--demuxer-lavf-o-add=fflags=+nobuffer',
            '--demuxer-lavf-analyzeduration=0.1',
            '--video-sync=audio',
            '--interpolation=no',
            '--video-latency-hacks=yes',
            '--untimed',

            # Read video data from stdin!
            '-'
        ], stdin=subprocess.PIPE)

    def pack(self, r, g, b):
        """For MpvFrame, the pixel data type is a 3-element bytearray."""
        return bytearray([r, g, b])

    def send(self):
        """Did you know that you can simply write PPM images to a pipe to
        mpv and it will display them in real time?  Amazing!"""
        self.timer.wait()
        self.process.stdin.write(b"P6\n%d %d\n255\n" % (self.w, self.h))
        if len(self.pixels) != 18432:
            print(len(self.pixels))
        self.process.stdin.write(self.pixels)
        self.process.stdin.flush()

    def get(self, x, y):
        offset = (x + y * self.w) * 3
        return self.pixels[offset:offset + 3]

    def set(self, x, y, cv):
        offset = (x + y * self.w) * 3
        self.pixels[offset:offset + 3] = cv

    def fill(self, x, y, w, h, cv):
        x, y, w, h = frame.clamp_rect(x, y, w, h, self.w, self.h)
        if w > 0 and h > 0:
            row = cv * w
            for y in range(y, y + h):
                start = (x + y * self.w) * 3
                self.pixels[start:start + w * 3] = row

    def paste(self, x, y, source, sx, sy, sw, sh):
        raise NotImplemented

    def print(self, font, text, horiz=-1, vert=-1):
        raise NotImplemented
