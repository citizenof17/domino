#! /usr/bin/python3

import logging
import random

import pygame as pg

from player import NeuralNetwork, RealPlayer
from printables import (
    Tile, Board, ButtonHolder, Button, Printable, find_possible_turn,
)
from utils import in_it, get_sprite_path, Point


LOG = logging.getLogger(__name__)


def init_logging():
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
NUMBER_OF_TILES_IN_HAND = 7

ROTATE_BUTTON_FILEPATH = get_sprite_path('rotate_button')
SUBMIT_BUTTON_FILEPATH = get_sprite_path('submit_button')
BAZAR_FILEPATH = get_sprite_path('bazar')


class Game:
    def __init__(self):
        pg.font.init()
        self.font = pg.font.SysFont('freesansbold.ttf', 32)

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._running = True
        self.sprites = pg.sprite.Group()
        self.texts = []
        self.buttons = pg.sprite.Group()
        self.board = None
        self.players = None
        self.turn_number = 0
        self.possible_tiles = POSSIBLE_TILES.copy()
        self._right_mouse_pressed = False
        self._mouse_position = (0, 0)
        self.restart = False
        self._user_needs_tile = False
        self._finished = False

    def run(self):
        self._init_sprites()
        self._init_game_start()
        while self._running:
            self._handle_frame()
        pg.quit()
        return self.restart

    def _init_sprites(self):
        self._init_board()
        self.sprites.add(self.board)

        self._init_players()
        self._init_buttons()

    def _init_board(self):
        x_shift = -(Board.WIDTH - SCREEN_WIDTH) / 2
        y_shift = -(Board.HEIGHT - SCREEN_HEIGHT) / 2
        self.board = Board(position=Point(x_shift, y_shift))

    def _init_players(self):
        self.players = [RealPlayer(), NeuralNetwork()]

        for i, player in enumerate(self.players):
            is_real_player = player.is_real_player()
            if is_real_player:
                player.hand.set_dimension(SCREEN_WIDTH, Tile.SIZE * 6)
            else:
                player.hand.set_dimension(SCREEN_WIDTH, Tile.SIZE * 2)

            player.hand.set_position(*PLAYER_POSITIONS[i])
            self.sprites.add(player.hand)
            if not is_real_player:
                player.hand.rotate()

            for _ in range(NUMBER_OF_TILES_IN_HAND):
                self._add_new_tile_for_player(player)

    def _add_new_tile_for_player(self, player, tile_value=None):
        if not tile_value:
            tile_value = self._take_from_bazar()
        if not tile_value:
            raise RuntimeError('No tiles left')

        tile = Tile(tile_value[0], tile_value[1],
                    covered=(not player.is_real_player()))
        player.hand.add_tile(tile)

    def _init_buttons(self):
        buttons_holder = ButtonHolder('sprites/button_holder.png',
                                      position=Point(SCREEN_WIDTH - 100,
                                                     SCREEN_HEIGHT - 100))

        player = self.players[REAL_PLAYER_NUMBER]
        self.buttons = [
            Button(player.hand.rotate_chosen_tile, ROTATE_BUTTON_FILEPATH,
                   position=Point(5, 0)),
            Button(player.ready, SUBMIT_BUTTON_FILEPATH,
                   position=Point(5, 50)),
            Button(self._take_from_bazar_for_player, BAZAR_FILEPATH,
                   position=Point(55, 0))
        ]

        for button in self.buttons:
            buttons_holder.add_sprite(button)
        self.sprites.add(buttons_holder)

    def _init_game_start(self):
        player_idx, first_tile = self._find_first_tile()
        self.players[player_idx].hand.remove_tile(first_tile)

        # Workaround to not care about tile's surface (covered or not)
        if player_idx != REAL_PLAYER_NUMBER:
            first_tile = Tile(first_tile.first, first_tile.second)

        self.board.place_tile(first_tile, None, None,
                              self.board.WIDTH / 2, self.board.HEIGHT / 2)

        self._inc_turn_number(player_idx)

    def _find_first_tile(self):
        player_idx = 0
        overall_min = Tile(0, 0)
        for i, player in enumerate(self.players):
            player_best_tile = min(player.hand.tiles)
            if player_best_tile < overall_min:
                overall_min = player_best_tile
                player_idx = i
        return player_idx, overall_min

    def _handle_frame(self):
        for event in pg.event.get():
            self._handle_event(event)

        self._handle_board_movement()

        if not self.finished():
            self.make_turn()

        self._update_sprites()
        pg.display.flip()

    def _handle_event(self, event):
        if event.type == pg.QUIT:
            self._running = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                self._running = False
                self.restart = True
                return
        elif event.type == pg.MOUSEBUTTONDOWN:
            self._handle_mouse_down(event)

    def _handle_mouse_down(self, mouse_button):
        def chose_tile_for_real_player(position):
            chosen_tile = None
            player = self.players[REAL_PLAYER_NUMBER]
            for tile in player.hand.tiles:
                if tile.in_it(position):
                    chosen_tile = tile
                    break
            if chosen_tile:
                player.hand.chose_tile(chosen_tile)

        def chose_region_for_tile(position):
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

        def press_buttons(pos):
            for button in self.buttons:
                if button.in_it(pos):
                    button.press()

        if mouse_button.button == MB_LEFT:
            if self.turn_number == REAL_PLAYER_NUMBER:
                chose_tile_for_real_player(mouse_button.pos)
                chose_region_for_tile(mouse_button.pos)
            press_buttons(mouse_button.pos)
        if mouse_button.button == MB_RIGHT:
            self._mouse_position = pg.mouse.get_pos()

    def _handle_board_movement(self):
        pressed_mouse = pg.mouse.get_pressed()
        # We want to react on right click, but pressed_mouse is zero indexed
        if pressed_mouse[MB_RIGHT - 1]:
            new_pos = pg.mouse.get_pos()
            self.board.rect.move_ip(new_pos[0] - self._mouse_position[0],
                                    new_pos[1] - self._mouse_position[1])
            self._mouse_position = new_pos

    def make_turn(self):
        def player_needs_tile_or_skip():
            if self.possible_tiles:
                if real_player:
                    self._user_needs_tile = True
                else:
                    self._take_from_bazar_for_player(player)
            else:
                self._inc_turn_number()

        player = self.players[self.turn_number]
        real_player = player.is_real_player()

        if real_player:
            if not find_possible_turn(player.hand, self.board):
                player_needs_tile_or_skip()
                return

            if not player.is_ready():
                return
            player.not_ready()

        turn = player.turn(self.board)

        if not turn:
            if not real_player:
                player_needs_tile_or_skip()
            return

        self._inc_turn_number()

        player.hand.remove_tile(turn.tile_from_hand)
        self.board.place_tile(turn.tile, turn.old_tile, turn.possible_rect,
                              turn.rect.x, turn.rect.y)
        self.board.clear_area()

    def _inc_turn_number(self, initial_number=None):
        if initial_number is not None:
            self.turn_number = initial_number
        self.turn_number = (self.turn_number + 1) % len(self.players)

    def _take_from_bazar_for_player(self, player=None):
        if not player:  # by default lets give to a real player
            if self._user_needs_tile and self.turn_number == REAL_PLAYER_NUMBER:
                player = self.players[REAL_PLAYER_NUMBER]
            else:
                return

        value = self._take_from_bazar()
        if not value:
            return

        self._add_new_tile_for_player(player, value)
        self._user_needs_tile = False

    def _take_from_bazar(self):
        if self.possible_tiles:
            value = random.choice(self.possible_tiles)
            self.possible_tiles.remove(value)
            return value
        return None

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

        if self._finished:
            # Show all cards
            for player in self.players:
                player.hand.uncover()

        return self._finished

    def player_won(self):
        self._add_text('You win!')

    def player_lost(self):
        self._add_text('You lose!')

    def draw(self):
        self._add_text('Fish!!!')

    def _add_text(self, text):
        text_surface = self.font.render(text, False, (0, 255, 0), (0, 0, 128))
        text = Printable.from_surface(text_surface)
        text.set_position(100, 100)
        self.texts.append(text)

    def _update_sprites(self):
        for sprite in self.sprites:
            sprite.rec_blit()
            self.screen.blit(sprite.surf, sprite.rect)
        for text in self.texts:
            self.screen.blit(text.surf, text.rect)

    def cleanup(self):
        # There is a known bug in pygame for Mac which resulted in unexpected
        # SIGSEGV. First idea was that there were some references stored in pygame
        # (maybe in display), which were not cleaned when restarting (but hopefully
        # this idea is wrong).
        # This is the reason for this method. Leave it for history

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
    init_logging()
    pg.init()
    clock = pg.time.Clock()
    clock.tick(30)

    new_game = True
    while new_game:
        game = Game()
        new_game = game.run()
