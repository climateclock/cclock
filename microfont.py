from array import array
import displayio
import fs

large = None
small = None


def init(*dirs):
    global large
    global small
    large = get('kairon-16', dirs or [''])
    small = get('kairon-10', dirs or [''])


def get(font_id, dirs):
    for dir in dirs:
        path = dir + '/' + font_id + '.mcf'
        if fs.isfile(path):
            return Microfont(path)
    raise ValueError(font_id + ' not found.')


class Microfont:
    # All glyphs are concatenated horizontally into a single bitmap.
    # The set of available characters is represented as the union of
    # one or more codepoint ranges.  The file begins with a magic
    # number, the dimensions of the bitmap, and the number of ranges.
    # Then comes the bitmap data, followed by arrays that specify:
    #   - The starting and ending codepoints of each codepoint range
    #   - The x-offset into the bitmap of each glyph
    #   - The x-offset of each glyph within its bounding box
    #   - The advance width of each glyph

    def __init__(self, path):
        with fs.open(path, 'rb') as file:
            assert file.read(4) == b'\xc2\xb5f1'
            wh, wl, h, num_ranges = file.read(4)
            w = (wh << 8) + wl

            bitmap = displayio.Bitmap(w, h, 2)
            if hasattr(bitmap, 'readbits'):
                bitmap.readbits(file)
            else:
                file.readinto(memoryview(bitmap))

            starts = array('H', range(num_ranges))
            file.readinto(memoryview(starts))

            stops = array('H', range(num_ranges))
            file.readinto(memoryview(stops))

            num_chars = 0
            for i in range(num_ranges):
                num_chars += stops[i] - starts[i]

            sxs = array('H', range(num_chars + 1))
            file.readinto(memoryview(sxs))

            dxs = bytearray(num_chars)
            file.readinto(dxs)

            cws = bytearray(num_chars)
            file.readinto(cws)

            (self.w, self.h, self.bitmap, self.starts, self.stops, self.sxs,
                self.dxs, self.cws) = w, h, bitmap, starts, stops, sxs, dxs, cws


    def get_index(self, ch):
        c = ord(ch)
        r, nr = 0, len(self.starts)
        offset = 0
        while r < nr:
            start, stop = self.starts[r], self.stops[r]
            if c >= start and c < stop:
                return offset + c - start
            offset += stop - start
            r += 1
        return 0


    def measure(self, text):
        return sum(self.cws[self.get_index(ch)] for ch in text)


    def draw(self, text, bitmap, x=0, y=0, pi=1):
        for ch in text:
            i = self.get_index(ch)
            bitmap.freeblit(
                x + self.dxs[i], y,
                self.bitmap,
                self.sxs[i], 0, self.sxs[i + 1] - self.sxs[i], self.h,
                source_bg=0, dest_value=pi
            )
            x += self.cws[i]
        return x
