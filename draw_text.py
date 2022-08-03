def measure(text, font):
    width = 0
    for ch in text:
        glyph = font.get_glyph(ord(ch))
        if glyph:
            width += glyph.shift_x
    return width

def draw(text, font, bitmap, x=0, y=0, cv=1):
    width, height, x_offset, y_offset = font.get_bounding_box()
    baseline = height + y_offset
    for ch in text:
        glyph = font.get_glyph(ord(ch))
        if glyph:
            bitmap.freeblit(
                x + glyph.dx,
                y + baseline - glyph.height - glyph.dy,
                glyph.bitmap,
                write_value=cv
            )
        x += glyph.shift_x
