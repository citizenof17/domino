from printables import Hand, find_possible_turn
from utils import Turn

MOVING = False


class Player:
    real_player = False

    def __init__(self, *args, **kwargs):
        self.hand = Hand(*args, **kwargs)
        self._ready = False

    def is_real_player(self):
        return self.real_player

    def turn(self, board):
        raise NotImplementedError()

    def is_ready(self):
        return self._ready

    def ready(self):
        self._ready = True

    def not_ready(self):
        self._ready = False


class NeuralNetwork(Player):
    def turn(self, board):
        return find_possible_turn(self.hand, board)


class RealPlayer(Player):
    real_player = True

    def turn(self, board):
        chosen_tile = self.hand.chosen_tile
        if not chosen_tile:
            return None

        area = board.chosen_area
        normalized_rect = board.is_valid_turn(chosen_tile)
        if normalized_rect:
            return Turn(chosen_tile, area.tile, normalized_rect, area.rect)
        return None
