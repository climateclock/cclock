import frame
import subprocess
import time

class MpvFrame(frame.Frame):
    """A Frame implementation that uses the mpv video player for display."""

    def __init__(self, w, h, fps):
        frame.Frame.__init__(self, w, h, fps)
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
        self.next = 0

    def pack(self, r, g, b):
        """For MpvFrame, the pixel data type is a 3-element bytearray."""
        return bytearray([r, g, b])

    def unpack(self, cv):
        r, g, b = cv  # unpack bytearray
        return r, g, b  # return tuple

    def send(self):
        """Did you know that you can simply write PPM images to a pipe to
        mpv and it will display them in real time?  Amazing!"""
        now = time.time()
        if self.next > now:
            time.sleep(self.next - now)
        self.process.stdin.write(b"P6\n%d %d\n255\n" % (self.w, self.h))
        if len(self.pixels) != 18432:
            print(len(self.pixels))
        self.process.stdin.write(self.pixels)
        self.process.stdin.flush()
        self.next = now + self.interval

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
