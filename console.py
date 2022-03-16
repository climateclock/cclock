import code
import displayio
import fontio

from adafruit_bitmap_font import pcf
from adafruit_display_text import bitmap_label
from frame import *

def run(frame):
    code.interact(local=dict(globals(), frame=frame))
