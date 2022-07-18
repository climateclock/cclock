import utils

utils.mem('fontlib1')
from adafruit_bitmap_font import pcf
utils.mem('fontlib2')
import displayio
utils.mem('fontlib3')


class FontLibrary:
    def __init__(self, fs, dirs):
        self.fs = fs
        self.dirs = dirs
        self.fonts = {}

    def get(self, font_id):
        if font_id not in self.fonts:
            for dir in self.dirs:
                path = dir + '/' + font_id + '.pcf'
                if self.fs.isfile(path):
                    f = self.fs.open(path)
                    self.fonts[font_id] = pcf.PCF(f, displayio.Bitmap)
                    break
            else:
                raise ValueError(font_id + ' not found')
        return self.fonts[font_id]
