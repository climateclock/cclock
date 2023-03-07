import board
import displayio
import framebufferio
import prefs
import rgbmatrix

# NOTE: Setting BIT_DEPTH to 5 gives the best colour rendering and brightness
# control (higher than 5 doesn't help because the hardware colour depth appears
# to be 5 red, 6 green, 5 blue).  If memory is tight, though, we sometimes need
# to set BIT_DEPTH lower to avoid MemoryErrors.
BIT_DEPTH = 5

brightness = 1.0
colours = [(0, 0, 0)]
shader = [0]
fb_display = None


# Sets up the matrix display to show the contents of a given bitmap.
def init(bitmap):
    global shader
    global fb_display

    prefs.init()
    rgb_pin_names = prefs.get('rgb_pins').split()
    addr_pin_names = prefs.get('addr_pins').split()

    displayio.release_displays()
    matrix = rgbmatrix.RGBMatrix(
        width=bitmap.width, height=bitmap.height, bit_depth=BIT_DEPTH,
        rgb_pins=[getattr(board, name) for name in rgb_pin_names],
        addr_pins=[getattr(board, name) for name in addr_pin_names],
        clock_pin=board.MTX_CLK,
        latch_pin=board.MTX_LAT,
        output_enable_pin=board.MTX_OE
    )
    shader = displayio.Palette(bitmap.depth)
    tilegrid = displayio.TileGrid(bitmap, pixel_shader=shader)
    group = displayio.Group()
    group.append(tilegrid)
    fb_display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)
    fb_display.show(group)


# Updates the display to match the contents of the bitmap.
def send():
    fb_display.refresh(minimum_frames_per_second=0)
    # Display bug: refresh() doesn't cause a refresh unless we also set
    # auto_refresh = False (even though auto_refresh is already False!).
    fb_display.auto_refresh = False


def srgb_to_linear(v):
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055)**2.4


def get_shader_rgb(r, g, b, brightness):
    min_value = 0x100 >> BIT_DEPTH
    mid = (r + g + b)/3
    # When scaling down, don't scale down any nonzero values to zero,
    # and avoid scaling down saturated colours to pure grey.
    min_r = 2*min_value if r > mid else min_value if r else 0
    min_g = 2*min_value if g > mid else min_value if g else 0
    min_b = 2*min_value if b > mid else min_value if b else 0
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    if prefs.get('colorspace') == 'SRGB':
        r = srgb_to_linear(r)
        g = srgb_to_linear(g)
        b = srgb_to_linear(b)
    factor = brightness * 255.99
    return (
        max(min_r, int(factor * r)),
        max(min_g, int(factor * g)),
        max(min_b, int(factor * b))
    )


# Sets the brightness to a level from 0.0 to 1.0.
def set_brightness(new_brightness):
    global brightness
    brightness = new_brightness
    for pi in range(len(colours)):
        r, g, b = colours[pi]
        sr, sg, sb = get_shader_rgb(r, g, b, brightness)
        shader[pi] = ((sr << 16) | (sg << 8) | sb)


# Allocates or retrieves the palette index for the given RGB colour.
def get_pi(r, g, b):
    for pi, rgb in enumerate(colours):
        if rgb == (r, g, b):
            return pi
    if len(colours) < len(shader):
        pi = len(colours)
        colours.append((r, g, b))
        sr, sg, sb = get_shader_rgb(r, g, b, brightness)
        shader[pi] = ((sr << 16) | (sg << 8) | sb)
        return pi
    return 1  # no more palette slots available; just return 1


# Gets the RGB values for the given palette index.
def get_rgb(pi):
    if pi < len(colours):
        return colours[pi]
    return colours[1]  # pi is out of range; just return colour 1
