from enum import Enum
from collections import namedtuple
from copy import deepcopy

Point = namedtuple('Point', ['x', 'y'])
# Turn = namedtuple('Turn', ['tile', 'old_tile', 'rect', 'possible_rect'])


def in_it(rect, position, shift=None):
    shift = shift or Point(0, 0)
    return rect.collidepoint(position[0] - shift.x, position[1] - shift.y)


class Turn:
    def __init__(self, tile, old_tile, rect, possible_rect, tile_from_hand=None):
        self.tile = tile
        self.old_tile = old_tile
        self.rect = rect
        self.possible_rect = possible_rect
        self.tile_from_hand = tile_from_hand or tile


class Orientation(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Direction(Enum):
    TO_RIGHT = 1
    TO_LEFT = 2
    TO_TOP = 3
    TO_BOTTOM = 4
