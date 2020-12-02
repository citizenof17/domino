from enum import Enum
from copy import deepcopy
import pygame as pg
import logging
from utils import Point, in_it, Orientation, Direction as Dir, Turn

from pygame import Rect

LOG = logging.getLogger('__main__')

TILE_FILE_PATTERN = 'sprites/{}_{}.png'
TILE_FILE_CHOSEN_PATTERN = 'sprites/{}_{}_chosen.png'


def find_possible_turn(hand, board):
    for tile in hand.tiles:
        rotated_tile = Tile(tile.first, tile.second)
        for _ in range(4):
            for board_tile in board.tiles:
                for possible_rect in board_tile.possible_placements:
                    area = Area(tile=board_tile, rect=possible_rect)
                    normalized_rect = board.is_valid_turn(rotated_tile, area)
                    if normalized_rect:
                        return Turn(rotated_tile, area.tile, normalized_rect,
                                    area.rect, tile)
            rotated_tile.rotate()
    return None


class Printable(pg.sprite.Sprite):
    default_sprite = None
    default_sprite_chosen = None
    default_color = 'black'
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, filename=None, parent=None, position=Point(0, 0),
                 default_color=None, width=None, height=None):
        super(Printable, self).__init__()
        self.rect = None
        self.surf = None
        self.chosen = False
        self._angle = 0
        self._image_set = None
        if default_color:
            self.default_color = default_color

        self.sprite_file = self.default_sprite
        self.sprite_file_chosen = self.default_sprite_chosen
        self.width = width or self.WIDTH
        self.height = height or self.HEIGHT
        self._set_surface(filename)
        self.parent = parent
        self.set_position(*position)
        self.sprites = pg.sprite.Group()

    def rotate(self):
        self._angle = (self._angle + 90) % 360
        self.surf = pg.transform.rotate(self.surf, 90)
        self.rect = self.surf.get_rect(left=self.rect.left, top=self.rect.top)

    def is_chosen(self):
        return self.chosen

    def add_sprite(self, sprite):
        sprite.parent = self
        self.sprites.add(sprite)

    def remove_sprite(self, tile):
        try:
            self.tiles.remove(tile)
        except ValueError:
            pass

    def rec_blit(self):
        self.fill_default()
        for sprite in self.sprites:
            sprite.rec_blit()
            self.surf.blit(sprite.surf, sprite.rect)

    def fill_default(self):
        if not self._image_set:
            self.surf.fill(pg.Color(self.default_color))

    def set_position(self, x, y):
        self.rect.move_ip(-self.rect.x + x, -self.rect.y + y)

    def _set_surface(self, filename=None):
        sprite_path = filename or self.sprite_file

        try:
            self.surf = pg.image.load(sprite_path).convert()
            self.surf = pg.transform.rotate(self.surf, self._angle)
        except Exception:
            self.surf = pg.Surface((self.width, self.height))
            self.fill_default()
        else:
            self._image_set = sprite_path

        old_rect = self.rect
        if old_rect:
            self.rect = self.surf.get_rect(left=old_rect.left, top=old_rect.top)
        else:
            self.rect = self.surf.get_rect()

    def chose(self):
        self._chose(True if not self.chosen else False)

    def unchose(self):
        self._chose(False)

    def _chose(self, chose=True):
        if not self.sprite_file_chosen:
            return

        if chose and not self.chosen:
            self.chosen = True
            self._set_surface(self.sprite_file_chosen)
        elif not chose and self.chosen:
            self.chosen = False
            self._set_surface(self.sprite_file)

    def get_shift(self):
        parent_shift = self.parent.get_shift() if self.parent else Point(0, 0)
        return Point(self.rect.x + parent_shift.x, self.rect.y + parent_shift.y)

    def in_it(self, position):
        absolut_shift = self.get_shift()
        absolut_shift = Point(absolut_shift[0] - self.rect.x,
                              absolut_shift[1] - self.rect.y)
        return in_it(self.rect, position, absolut_shift)


class MyRect(Rect):
    def __init__(self, dir, *args, **kwargs):
        super(MyRect, self).__init__(*args, **kwargs)
        self.dir = dir


class Tile(Printable):
    default_sprite = 'sprites/tile_base.png'
    default_sprite_chosen = 'sprites/tile_base_chosen.png'
    WIDTH = 100
    HEIGHT = 50
    SIZE = 50

    def __init__(self, first=0, second=0, covered=False, *args, **kwargs):
        super(Tile, self).__init__(*args, **kwargs)
        self.orientation = Orientation.HORIZONTAL
        self.possible_placements = None
        self.first = first
        self.second = second

        if not covered:
            self.sprite_file = TILE_FILE_PATTERN.format(first, second)
            self.sprite_file_chosen = TILE_FILE_CHOSEN_PATTERN.format(first, second)
        else:
            self.sprite_file = 'sprites/tile_back.png'
            self.sprite_file_chosen = self.sprite_file
        self._set_surface()
        self.double = first == second
        self._angle = 0

    def rotate(self):
        super(Tile, self).rotate()

        if self._angle in (90, 270):
            self.first, self.second = self.second, self.first

        if self.orientation == Orientation.HORIZONTAL:
            self.orientation = Orientation.VERTICAL
        else:
            self.orientation = Orientation.HORIZONTAL

    def _make_rect(self, x, y, dir):
        return MyRect(dir, x, y, self.WIDTH // 2, self.HEIGHT)

    def make_possible_placements(self):
        rect = self.rect
        if self.orientation == Orientation.HORIZONTAL:
            self.possible_placements = [
                self._make_rect(rect.right, rect.top, Dir.TO_RIGHT),
                self._make_rect(rect.left - self.SIZE, rect.top, Dir.TO_LEFT),
            ]
            if self.double:
                self.possible_placements.extend(
                    [self._make_rect(rect.left + self.SIZE / 2,
                                     rect.top - self.HEIGHT, Dir.TO_TOP),
                     self._make_rect(rect.left + self.SIZE / 2, rect.bottom,
                                     Dir.TO_BOTTOM)]
                )
        else:
            self.possible_placements = [
                self._make_rect(rect.left, rect.top - self.HEIGHT, Dir.TO_TOP),
                self._make_rect(rect.left, rect.bottom, Dir.TO_BOTTOM),
            ]
            if self.double:
                self.possible_placements.extend(
                    [self._make_rect(rect.right, rect.top + self.SIZE / 2,
                                     Dir.TO_RIGHT),
                     self._make_rect(rect.left - self.SIZE,
                                     rect.top + self.SIZE / 2, Dir.TO_LEFT)]
                )

    def remove_possible_placements_by_dir(self, discard_dir=None,
                                          discard_reversed_dir=None):
        reversed_dir = {
            Dir.TO_TOP: Dir.TO_BOTTOM,
            Dir.TO_BOTTOM: Dir.TO_TOP,
            Dir.TO_LEFT: Dir.TO_RIGHT,
            Dir.TO_RIGHT: Dir.TO_LEFT,
        }.get(discard_reversed_dir)

        self.possible_placements = list(filter(
            lambda x: x.dir not in [reversed_dir, discard_dir],
            self.possible_placements))

    def remove_possible_placement(self, possible_placement):
        if possible_placement in self.possible_placements:
            self.possible_placements.remove(possible_placement)


class Hand(Printable):
    default_sprite = 'sprites/hand.png'
    WIDTH = 700
    HEIGHT = 300

    def __init__(self, *args, **kwargs):
        super(Hand, self).__init__(*args, **kwargs)
        self.sprites = pg.sprite.Group()
        self.chosen_tile = None

    @property
    def tiles(self):
        return self.sprites

    def fill(self, tiles):
        for tile in tiles:
            self.add_tile(tile)

    def add_tile(self, tile):
        if self.tiles:
            max_tile = max(self.tiles, key=lambda x: (x.rect.y, x.rect.x))
            new_x, new_y = max_tile.rect.x + Tile.WIDTH, max_tile.rect.y
        else:
            new_x, new_y = 0, 0

        if new_x >= self.rect.width:
            new_x = 0
            new_y += Tile.SIZE * 2

        tile.set_position(new_x, new_y)
        self.add_sprite(tile)

    def remove_tile(self, tile):
        try:
            tile.unchose()
            if self.chosen_tile == tile:
                self.chosen_tile = None
            self.tiles.remove(tile)
        except ValueError:
            pass
        else:
            tiles = self.tiles.copy()
            self.tiles.empty()
            self.fill(tiles)

    def chose_tile(self, chosen_tile):
        if self.chosen_tile:
            self.chosen_tile.unchose()

        if chosen_tile == self.chosen_tile:
            self.chosen_tile = None
        else:
            chosen_tile.chose()
            self.chosen_tile = chosen_tile
        LOG.info("Chosen Tile: {}".format(chosen_tile))

    def rotate_chosen_tile(self):
        if self.chosen_tile:
            self.chosen_tile.rotate()


class Area(Printable):
    default_sprite = 'sprites/red_square.png'
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, tile=None, rect=None, *args, **kwargs):
        super(Area, self).__init__(*args, **kwargs)
        self.tile = tile
        self.rect = rect


class Board(Printable):
    default_sprite = 'sprites/board.png'
    default_color = 'beige'
    WIDTH = 1000
    HEIGHT = 1000

    def __init__(self):
        super(Board, self).__init__()
        self.chosen_area = None
        self.chosen_tile = None
        self.chosen_rect = None
        self.tiles = pg.sprite.Group()

    def chose_area(self, chosen_tile, chosen_rect):
        self.clear_area()
        self.chosen_area = Area(parent=self, tile=chosen_tile, rect=chosen_rect)
        self.add_sprite(self.chosen_area)
        LOG.info("Chosen Area: {}".format(self.chosen_area))

    def clear_area(self):
        if self.chosen_area:
            self.chosen_area.kill()
            self.chosen_area = None

    def place_tile(self, tile, next_to_tile, possible_rect, x, y):
        self.clear_area()

        if next_to_tile:
            next_to_tile.remove_possible_placements_by_dir(possible_rect.dir)

        self.add_sprite(tile)
        self.tiles.add(tile)
        tile.set_position(x, y)
        tile.make_possible_placements()
        if possible_rect:
            tile.remove_possible_placements_by_dir(
                discard_reversed_dir=possible_rect.dir)

    def is_valid_turn(self, tile_to_place, area=None):
        if not (self.chosen_area or area):
            return False

        area = area or self.chosen_area
        next_to_tile = area.tile
        rect = area.rect

        if tile_to_place.double:
            if (tile_to_place.orientation == Orientation.HORIZONTAL and
                    rect.dir in [Dir.TO_RIGHT, Dir.TO_LEFT]):
                return None
            if (tile_to_place.orientation == Orientation.VERTICAL and
                    rect.dir in [Dir.TO_TOP, Dir.TO_BOTTOM]):
                return None

        def get_rect_for_horizontal():
            if tile_to_place.orientation == Orientation.HORIZONTAL:
                if (rect.dir == Dir.TO_RIGHT and
                        next_to_tile.second == tile_to_place.first):
                    return Rect(rect.x, rect.y, Tile.SIZE * 2, Tile.SIZE)

                if (rect.dir == Dir.TO_LEFT and
                        next_to_tile.first == tile_to_place.second):
                    return Rect(rect.x - Tile.SIZE, rect.y, Tile.SIZE * 2, Tile.SIZE)
            else:
                if tile_to_place.double:
                    if ((rect.dir == Dir.TO_RIGHT and
                         next_to_tile.second == tile_to_place.first) or
                            (rect.dir == Dir.TO_LEFT and
                             next_to_tile.first == tile_to_place.second)):
                        return Rect(rect.x, rect.y - Tile.SIZE / 2,
                                    Tile.SIZE, Tile.SIZE * 2)
                    return None

                if not next_to_tile.double:
                    return None

                if (rect.dir == Dir.TO_TOP and
                        next_to_tile.second == tile_to_place.second):
                    return Rect(rect.x, rect.y - Tile.SIZE,
                                Tile.SIZE, Tile.HEIGHT * 2)

                if (rect.dir == Dir.TO_BOTTOM and
                        next_to_tile.first == tile_to_place.first):
                    return Rect(rect.x, rect.y, Tile.SIZE * 2, Tile.SIZE)
            return None

        def get_rect_for_vertical():
            if tile_to_place.orientation == Orientation.VERTICAL:
                if (rect.dir == Dir.TO_TOP and
                        next_to_tile.first == tile_to_place.second):
                    return Rect(rect.x, rect.y - Tile.SIZE, Tile.SIZE, Tile.SIZE * 2)

                if (rect.dir == Dir.TO_BOTTOM and
                        next_to_tile.second == tile_to_place.first):
                    return Rect(rect.x, rect.y, Tile.SIZE, Tile.SIZE * 2)
            else:
                if tile_to_place.double:
                    if ((rect.dir == Dir.TO_TOP and
                         next_to_tile.first == tile_to_place.second) or
                            (rect.dir == Dir.TO_BOTTOM and
                             next_to_tile.second == tile_to_place.first)):
                        return Rect(rect.x - Tile.SIZE / 2, rect.y,
                                    Tile.SIZE * 2, Tile.SIZE)
                    return None

                if not next_to_tile.double:
                    return None

                if (rect.dir == Dir.TO_RIGHT and
                        next_to_tile.first == tile_to_place.first):
                    return Rect(rect.x, rect.y, Tile.SIZE * 2, Tile.SIZE)
                if (rect.dir == Dir.TO_LEFT and
                        next_to_tile.first == tile_to_place.second):
                    return Rect(rect.x - Tile.SIZE, rect.y,
                                Tile.SIZE * 2, Tile.SIZE)
            return None

        if next_to_tile.orientation == Orientation.HORIZONTAL:
            normalized_rect = get_rect_for_horizontal()
        else:  # VERTICAL
            normalized_rect = get_rect_for_vertical()

        if normalized_rect:
            if self.intersects_anything(normalized_rect, except_for=[next_to_tile]):
                return False

            normalized_rect = MyRect(rect.dir, normalized_rect)
        return normalized_rect

    def intersects_anything(self, new_tile_rect, except_for=()):
        inflated_rect = Rect(new_tile_rect.x - 1, new_tile_rect.y - 1,
                             new_tile_rect.width + 2, new_tile_rect.height + 2)

        return inflated_rect.collidelist([
            tile.rect for tile in self.tiles if tile not in except_for]) != -1

    def possible_placement(self, *args):
        return False

    def chose_region(self, *args):
        pass


class ButtonHolder(Printable):
    default_color = 'cornflowerblue'
    HEIGHT = 100
    WIDTH = 150


class Button(Printable):
    def __init__(self, callback=None, *args, **kwargs):
        super(Button, self).__init__(*args, **kwargs)
        self.pressed = False
        self.callback = callback or (lambda: None)

    def press(self):
        self.callback()
        self.pressed = not self.pressed

    def relax(self):
        self.pressed = False
