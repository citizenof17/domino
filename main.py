
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


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000

INF = 1e4

MB_LEFT = 1
MB_RIGHT = 3
REAL_PLAYER_NUMBER = 0
II_NUMBER = 1

PLAYER_POSITIONS = [(0, SCREEN_HEIGHT - Tile.HEIGHT * 6),
                    (SCREEN_WIDTH - Tile.WIDTH, 0)]
POSSIBLE_TILES = [
    (first, second)
    for first in range(0, 7)
    for second in range(first, 7)
]
TILES_IN_HAND = 7


class Game:
    def __init__(self):
        pg.init()
        pg.font.init()
        clock = pg.time.Clock()
        clock.tick(30)

        self.font = pg.font.SysFont('freesansbold.ttf', 32)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = True
        self.sprites = pg.sprite.Group()
        self.texts = []
        self.buttons = pg.sprite.Group()
        self.board = None
        self.players = None
        self.turn_number = 0
        self.possible_tiles = POSSIBLE_TILES.copy()
        self.right_mouse_pressed = False
        self.mouse_position = (0, 0)
        self.restart = False
        self.user_needs_tile = False
        self._finished = False
        self._set_board()

    def run(self):
        self.init_sprites()
        self.init_game_start()
        while self.running:
            self.handle_frame()
        pg.quit()
        return self.restart

    def _set_board(self):
        x_shift = -(Board.WIDTH - SCREEN_WIDTH) / 2
        y_shift = -(Board.HEIGHT - SCREEN_HEIGHT) / 2
        self.board = Board(position=Point(x_shift, y_shift))

    def init_game_start(self):
        player_idx, first_tile = self.find_first_tile()
        self.players[player_idx].hand.remove_tile(first_tile)
        if player_idx != REAL_PLAYER_NUMBER:
            first_tile = Tile(first_tile.first, first_tile.second)

        self.board.place_tile(first_tile, None, None,
                              self.board.WIDTH / 2, self.board.HEIGHT / 2)

        self.inc_turn_number(player_idx)

    def find_first_tile(self):
        player_idx = 0
        overall_min = Tile(0, 0)
        for i, player in enumerate(self.players):
            player_best_tile = min(player.hand.tiles)
            if player_best_tile < overall_min:
                overall_min = player_best_tile
                player_idx = i
        return player_idx, overall_min

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
        bazar_button = Button(self.take_from_bazar_for_player,
                              'sprites/bazar.png', position=Point(55, 0),
                              default_color='darkgoldenrod2')
        self.buttons.add(rotate_button)
        self.buttons.add(submit_button)
        self.buttons.add(bazar_button)

        for button in self.buttons:
            buttons_holder.add_sprite(button)

    def init_players(self):
        self.players = [RealPlayer(), NeuralNetwork()]
        for i, player in enumerate(self.players):
            if player.is_real_player():
                player.hand.set_dimension(SCREEN_WIDTH, Tile.SIZE * 6)
            else:
                player.hand.set_dimension(SCREEN_WIDTH, Tile.SIZE * 2)

            player.hand.set_position(*PLAYER_POSITIONS[i])
            self.sprites.add(player.hand)
            if not player.is_real_player():
                player.hand.rotate()

            for _ in range(TILES_IN_HAND):
                self.add_new_tile_for_player(player)

    def add_new_tile_for_player(self, player, tile_value=None):
        if not tile_value:
            tile_value = self.take_from_bazar()
        if not tile_value:
            raise RuntimeError('No tiles left')

        tile = Tile(tile_value[0], tile_value[1],
                    covered=(not player.is_real_player()))
        player.hand.add_tile(tile)

    def handle_frame(self):
        for event in pg.event.get():
            self.handle_event(event)

        self.handle_camera_movement()

        if not self.finished():
            self.make_turn()
        else:
            for player in self.players:
                player.hand.uncover()
        self.refresh()

    def finished(self):
        if self._finished:
            return self._finished

        for player in self.players:
            if not player.hand.tiles:
                self._finished = True
                if player.is_real_player():
                    self.player_won()
                else:
                    self.player_lost()
                return True

        if not self.possible_tiles and not any(
                find_possible_turn(player.hand, self.board)
                for player in self.players):
            # FISH
            self._finished = True

            players_with_minimum_points = []
            minimum_points = INF
            for player in self.players:
                player_points = sum(player.hand.tiles)
                if player_points < minimum_points:
                    minimum_points = player_points
                    players_with_minimum_points = []

                if minimum_points == player_points:
                    players_with_minimum_points.append(player)

            if len(players_with_minimum_points) == 1:
                if players_with_minimum_points[0].is_real_player():
                    self.player_won()
                else:
                    self.player_lost()
            if len(players_with_minimum_points) > 1:
                self.draw()

        return self._finished

    def _add_text(self, text):
        LOG.error("Adding text")
        text_surface = self.font.render(text, False, (0, 255, 0), (0, 0, 128))
        text = Printable.from_surface(text_surface)
        text.set_position(100, 100)
        self.texts.append(text)

    def player_won(self):
        self._add_text('You win!')
        # self._add_text('You win!\n Press R to restart')

    def player_lost(self):
        self._add_text('You lose!')
        # self._add_text('You lose!\n Press R to restart')

    def draw(self):
        self._add_text('Fish!!!')
        # self._add_text('Fish!!!\n Press R to restart')

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
            if event.key == pg.K_r:
                self.running = False
                self.restart = True
                return
            self.handle_key(event)
        elif event.type == pg.MOUSEBUTTONDOWN:
            self.handle_mouse_down(event)

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
        real_player = player.is_real_player()

        if not find_possible_turn(player.hand, self.board) and real_player:
            if self.possible_tiles:
                self.user_needs_tile = True
            else:
                self.inc_turn_number()
            return

        if real_player:
            if not player.is_ready():
                return
            player.not_ready()

        turn = player.turn(self.board)

        if not turn:
            if not real_player:
                if self.possible_tiles:
                    self.take_from_bazar_for_player(player)
                else:
                    self.inc_turn_number()
            return

        self.inc_turn_number()

        player.hand.remove_tile(turn.tile_from_hand)
        self.board.place_tile(turn.tile, turn.old_tile, turn.possible_rect,
                              turn.rect.x, turn.rect.y)
        self.board.clear_area()

    def inc_turn_number(self, initial_number=None):
        if initial_number is not None:
            self.turn_number = initial_number
        self.turn_number = (self.turn_number + 1) % len(self.players)

    def take_from_bazar_for_player(self, player=None):
        if not player:  # by default lets give to a real player
            if self.user_needs_tile and self.turn_number == REAL_PLAYER_NUMBER:
                player = self.players[REAL_PLAYER_NUMBER]
            else:
                return

        value = self.take_from_bazar()
        if not value or not player:
            return

        self.add_new_tile_for_player(player, value)
        self.user_needs_tile = False

    def take_from_bazar(self):
        if self.possible_tiles:
            value = random.choice(self.possible_tiles)
            self.possible_tiles.remove(value)
            return value
        return None

    def update_sprites(self):
        for sprite in self.sprites:
            sprite.rec_blit()
            self.screen.blit(sprite.surf, sprite.rect)
        for text in self.texts:
            self.screen.blit(text.surf, text.rect)

    def cleanup(self):
        for player in self.players:
            player.hand.cleanup()
        self.players = None

        for button in self.buttons:
            button.cleanup()

        for sprite in self.sprites:
            sprite.cleanup()

        self.texts = None
        self.board.cleanup()
        self.board.kill()

        self.screen = None


if __name__ == '__main__':
    new_game = True
    while new_game:
        game = Game()
        new_game = game.run()
        game.cleanup()
