from attrs import define

@define
class Glyph:
    bitmap: object
    tile_index: int
    width: int
    height: int
    dx: int
    dy: int
    shift_x: int
    shift_y: int

class BuiltinFont:
    pass
