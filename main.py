from enum import Enum

import pygame as pg
import logging

from pygame.locals import RLEACCEL

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
ch.setFormatter(formatter)
LOG.addHandler(ch)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

MB_LEFT = 1

MOVING = True


class Orientation(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Printable(pg.sprite.Sprite):
    default_sprite = None
    default_sprite_chosen = None
    WIDTH = 50
    HEIGHT = 50
    # COLOR_KEY = (0, 0, 0)
    # CHOSEN_COLOR_KEY = (255, 0, 0)

    def __init__(self, filename=None):
        super(Printable, self).__init__()
        self.rect = None
        self.surf = None
        self.chosen = False

        self.set_surface(filename)

    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_surface(self, filename):
        sprite_path = filename or self.default_sprite
        LOG.info(sprite_path)
        if sprite_path:
            self.surf = pg.image.load(sprite_path).convert()
        else:
            self.surf = pg.Surface((self.WIDTH, self.HEIGHT))

        old_rect = self.rect
        self.rect = self.surf.get_rect()
        if old_rect:
            self.set_position(old_rect.x, old_rect.y)

    def chose(self):
        if not self.default_sprite_chosen:
            return
        if not self.chosen:
            self.chosen = True
            self.set_surface(self.default_sprite_chosen)
        else:
            self.chosen = False
            self.set_surface(self.default_sprite)

    def in_it(self, position):
        return self.rect.collidepoint(*position)


class Tile(Printable):
    default_sprite = 'sprites/tile_base.png'
    default_sprite_chosen = 'sprites/tile_base_chosen.png'
    WIDTH = 100
    HEIGHT = 50

    def __init__(self, *args, **kwargs):
        super(Tile, self).__init__(*args, **kwargs)
        self.orientation = Orientation.HORIZONTAL

    def rotate(self):
        if self.orientation == Orientation.HORIZONTAL:
            self.surf = pg.transform.rotate(self.surf, -90)
            self.orientation = Orientation.VERTICAL
        else:
            self.orientation = Orientation.HORIZONTAL
            self.surf = pg.transform.rotate(self.surf, 90)


class MovingPlayer(Printable):
    def __init__(self):
        super(MovingPlayer, self).__init__()
        self.surf.fill(pg.Color('darkcyan'))

    def move(self, pressed_keys):
        dirs = {
            pg.K_w: (0, -5),
            pg.K_s: (0, 5),
            pg.K_a: (-5, 0),
            pg.K_d: (5, 0)
        }

        for key, direction in dirs.items():
            if pressed_keys[key]:
                LOG.info('PRESSED %s', key)
                self.rect.move_ip(*direction)

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT


def get_player():
    if MOVING:
        return MovingPlayer()


class Board(Printable):
    pass


class Game:
    def __init__(self):
        pg.init()
        clock = pg.time.Clock()
        clock.tick(30)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = True
        self.sprites = pg.sprite.Group()
        self.tiles = pg.sprite.Group()
        self.player = get_player()

    def run(self):
        self.fill_sprites()
        while self.running:
            self.handle_frame()
        pg.quit()

    def fill_sprites(self):
        self.sprites.add(self.player)
        for i in range(5):
            tile = Tile()
            tile.set_position(Tile.WIDTH * i, 0)
            self.sprites.add(tile)
            self.tiles.add(tile)

    def handle_frame(self):
        for event in pg.event.get():
            self.handle_event(event)
        self.player.move(pg.key.get_pressed())
        self.update_sprites()
        pg.display.flip()

    def handle_event(self, event):
        if event.type == pg.QUIT:
            self.running = False
        elif event.type == pg.KEYDOWN:
            self.handle_key(event)
        elif event.type == pg.MOUSEBUTTONDOWN:
            self.handle_mouse(event)

    def handle_key(self, key_event):
        if key_event.key == pg.K_ESCAPE:
            self.running = False

    def handle_mouse(self, mouse_button):
        LOG.info(mouse_button)
        if mouse_button.button == MB_LEFT:
            for tile in self.tiles:
                if tile.in_it(mouse_button.pos):
                    tile.chose()
        print(mouse_button)

    def update_sprites(self):
        self.screen.fill(pg.Color('beige'))
        for sprite in self.sprites:
            self.screen.blit(sprite.surf, sprite.rect)


if __name__ == '__main__':
    game = Game()
    game.run()
