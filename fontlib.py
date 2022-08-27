from adafruit_bitmap_font import pcf
import displayio
import fs


class FontLibrary:
    def __init__(self, dirs):
        self.dirs = dirs
        self.fonts = {}

    def get(self, font_id):
        if font_id not in self.fonts:
            for dir in self.dirs:
                path = dir + '/' + font_id + '.pcf'
                if fs.isfile(path):
                    self.fonts[font_id] = pcf.PCF(fs.open(path), displayio.Bitmap)
                    break
            else:
                raise ValueError(font_id + ' not found')
        return self.fonts[font_id]
