from adafruit_bitmap_font import pcf
import displayio
import fs

dirs = ['.']
fonts = {}


def set_dirs(*new_dirs):
    dirs[:] = new_dirs


def get(font_id):
    if font_id not in fonts:
        for dir in dirs:
            path = dir + '/' + font_id + '.pcf'
            if fs.isfile(path):
                fonts[font_id] = pcf.PCF(fs.open(path), displayio.Bitmap)
                break
        else:
            raise ValueError(font_id + ' not found.')
    return fonts[font_id]
