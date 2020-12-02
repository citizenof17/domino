
import pygame as pg

from collections import namedtuple

from printables import *
from player import *
from utils import Turn, in_it
import logging
import random

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
ch.setFormatter(formatter)
LOG.addHandler(ch)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

MB_LEFT = 1
MB_RIGHT = 3
REAL_PLAYER_NUMBER = 0
II_NUMBER = 1

PLAYER_POSITIONS = [(0, SCREEN_HEIGHT - Tile.HEIGHT * 6), (SCREEN_WIDTH - Tile.WIDTH, 0)]
POSSIBLE_TILES = [
    (first, second)
    for first in range(0, 7)
    for second in range(first, 7)
]


class Game:
    def __init__(self):
        pg.init()
        clock = pg.time.Clock()
        clock.tick(30)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = True
        self.sprites = pg.sprite.Group()
        self.tiles = pg.sprite.Group()
        self.buttons = pg.sprite.Group()
        self.board = Board()
        self.players = None
        self.turn_number = -1
        # self.submit_button = Button()
        self.possible_tiles = POSSIBLE_TILES.copy()
        self.right_mouse_pressed = False
        self.mouse_position = (0, 0)

    def run(self):
        self.init_sprites()
        self.init_game_start()
        while self.running:
            self.handle_frame()
        pg.quit()

    def init_game_start(self):
        self.turn_number = REAL_PLAYER_NUMBER
        first_tile = self.find_first_tile()
        self.board.place_tile(first_tile, None, None,
                              SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def find_first_tile(self):
        return Tile()

    def init_sprites(self):
        self.sprites.add(self.board)

        self.init_players()
        self.init_buttons()

    def init_buttons(self):
        buttons_holder = ButtonHolder('sprites/button_holder.png',
                                      position=Point(SCREEN_WIDTH - 100,
                                                     SCREEN_HEIGHT - 100))
        self.sprites.add(buttons_holder)

        player = self.players[REAL_PLAYER_NUMBER]
        rotate_button = Button(player.hand.rotate_chosen_tile,
                               'sprites/rotate_button.png', position=Point(5, 0),
                               default_color='gainsboro')
        submit_button = Button(player.ready,
                               'sprites/submit_button.png', position=Point(5, 50),
                               default_color='darkgoldenrod3')
        self.buttons.add(rotate_button)
        self.buttons.add(submit_button)

        buttons_holder.add_sprite(rotate_button)
        buttons_holder.add_sprite(submit_button)

    def init_players(self):
        self.players = [get_player(), NeuralNetwork(height=100)]
        for i, player in enumerate(self.players):
            player.hand.set_position(*PLAYER_POSITIONS[i])
            self.sprites.add(player.hand)
            if i != REAL_PLAYER_NUMBER:
                player.hand.rotate()

            for _ in range(7):
                value = random.choice(self.possible_tiles)
                self.possible_tiles.remove(value)

                tile = Tile(value[0], value[1], covered=(i > 0))
                player.hand.add_tile(tile)

    def handle_frame(self):
        for event in pg.event.get():
            self.handle_event(event)

        self.handle_camera_movement()

        if not self.finished():
            self.make_turn()

        # self.player.move(pg.key.get_pressed())
        self.refresh()

    def finished(self):
        return False

    def refresh(self):
        self.update_sprites()
        pg.display.flip()

    def handle_camera_movement(self):
        pressed_mouse = pg.mouse.get_pressed()
        if pressed_mouse[MB_RIGHT - 1]:
            new_pos = pg.mouse.get_pos()
            self.board.rect.move_ip(new_pos[0] - self.mouse_position[0],
                                    new_pos[1] - self.mouse_position[1])
            LOG.error(f'{self.mouse_position} - {new_pos}')
            self.mouse_position = new_pos

    def handle_event(self, event):
        if event.type == pg.QUIT:
            self.running = False
        elif event.type == pg.KEYDOWN:
            self.handle_key(event)
        elif event.type == pg.MOUSEBUTTONDOWN:
            self.handle_mouse_down(event)

    def handle_key(self, key_event):
        pass
        # if key_event.key == pg.K_ESCAPE:
        #     self.running = False

    def handle_mouse_down(self, mouse_button):
        LOG.info(mouse_button)
        if mouse_button.button == MB_LEFT:
            if self.turn_number == REAL_PLAYER_NUMBER:
                self.chose_tile_for_real_player(mouse_button.pos)
                self.chose_region_for_tile(mouse_button.pos)
            self.handle_buttons(mouse_button.pos)
        if mouse_button.button == MB_RIGHT:
            LOG.info(f'PRESSED {MB_RIGHT}')
            self.mouse_position = pg.mouse.get_pos()

    def chose_tile_for_real_player(self, position):
        chosen_tile = None
        player = self.players[REAL_PLAYER_NUMBER]
        for tile in player.hand.tiles:
            if tile.in_it(position):
                chosen_tile = tile
                break
        if chosen_tile:
            player.hand.chose_tile(chosen_tile)

    def chose_region_for_tile(self, position):
        chosen_tile = None
        chosen_rect = None
        for tile in self.board.tiles:
            tile_shift = tile.get_shift()
            tile_shift = Point(tile_shift[0] - tile.rect.x,
                               tile_shift[1] - tile.rect.y)

            for possible_rect in tile.possible_placements:
                if in_it(possible_rect, position, tile_shift):
                    chosen_rect = possible_rect
                    break
            if chosen_rect:
                chosen_tile = tile
                break
        if chosen_tile:
            self.board.chose_area(chosen_tile, chosen_rect)

    def handle_buttons(self, pos):
        for button in self.buttons:
            if button.in_it(pos):
                button.press()

    def make_turn(self):
        player = self.players[self.turn_number]
        player_is_ready = player.is_ready()
        player.not_ready()

        if self.turn_number == REAL_PLAYER_NUMBER and not player_is_ready:
            return
        turn = player.turn(self.board)

        if not turn:
            return

        self.turn_number = (self.turn_number + 1) % len(self.players)
        # self.turn_number = REAL_PLAYER_NUMBER

        player.hand.remove_tile(turn.tile_from_hand)
        self.board.place_tile(turn.tile, turn.old_tile, turn.possible_rect,
                              turn.rect.x, turn.rect.y)
        self.board.clear_area()

    def update_sprites(self):
        for sprite in self.sprites:
            sprite.rec_blit()
            self.screen.blit(sprite.surf, sprite.rect)


if __name__ == '__main__':
    game = Game()
    game.run()
