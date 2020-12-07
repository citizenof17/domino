from enum import Enum
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])


class Orientation(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Direction(Enum):
    TO_RIGHT = 1
    TO_LEFT = 2
    TO_TOP = 3
    TO_BOTTOM = 4


class Turn:
    def __init__(self, tile, old_tile, rect, possible_rect, tile_from_hand=None):
        self.tile = tile
        self.old_tile = old_tile
        self.rect = rect
        self.possible_rect = possible_rect
        self.tile_from_hand = tile_from_hand or tile


def in_it(rect, position, shift=None):
    shift = shift or Point(0, 0)
    return rect.collidepoint(position[0] - shift.x, position[1] - shift.y)


def get_sprite_path(sprite_name):
    return f'sprites/{sprite_name}.png'
