
import logging

from printables import Hand, find_possible_turn
from utils import Point, Turn

LOG = logging.getLogger('__main__')

MOVING = False


def get_player():
    # if MOVING:
    #     return MovingPlayer()
    return RealPlayer()


class Player:
    def __init__(self, *args, **kwargs):
        self.hand = Hand(*args, **kwargs)
        self._ready = False

    def turn(self, board):
        raise NotImplementedError()

    def is_ready(self):
        return self._ready

    def ready(self):
        self._ready = True

    def not_ready(self):
        self._ready = False


# class MovingPlayer(Printable):
#     def __init__(self):
#         super(MovingPlayer, self).__init__()
#         self.surf.fill(pg.Color('darkcyan'))
#
#     def move(self, pressed_keys):
#         dirs = {
#             pg.K_w: (0, -5),
#             pg.K_s: (0, 5),
#             pg.K_a: (-5, 0),
#             pg.K_d: (5, 0)
#         }
#
#         for key, direction in dirs.items():
#             if pressed_keys[key]:
#                 LOG.info('PRESSED %s', key)
#                 self.rect.move_ip(*direction)
#
#         if self.rect.left < 0:
#             self.rect.left = 0
#         if self.rect.right > SCREEN_WIDTH:
#             self.rect.right = SCREEN_WIDTH
#         if self.rect.top <= 0:
#             self.rect.top = 0
#         if self.rect.bottom >= SCREEN_HEIGHT:
#             self.rect.bottom = SCREEN_HEIGHT


class NeuralNetwork(Player):
    def turn(self, board):
        return find_possible_turn(self.hand, board)


class RealPlayer(Player):
    def turn(self, board):
        chosen_tile = self.hand.chosen_tile
        if not chosen_tile:
            return None

        # TODO: FIX IT TO normalized_area to reflect actual tile placement and
        #  orientation
        area = board.chosen_area
        normalized_rect = board.is_valid_turn(chosen_tile)
        if normalized_rect:
            return Turn(chosen_tile, area.tile, normalized_rect, area.rect)
        return None
