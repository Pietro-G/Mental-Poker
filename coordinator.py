from enum import Enum 
from crypto import generate_encodings
from types import *

class Stage(Enum):
    Waiting = 0
    Shuffling = 1
    Encrypting = 2
    Playing = 3


class NotAllowedException(BaseException):
    def __init__(self):
        super().__init__('Not Allowed')


class Player:
    def finalize_deck(self):
        raise NotImplementedError()


class Game:
    def __init__(self, n_players: int):
        self.deck: [int] = generate_encodings(N_CARDS)

        self.n_players = n_players
        self.cur_player = 0
        self.players: [Player] = []

        self.stage = Stage.Shuffling

    def join(self, player: Player) -> int:
        if self.stage != Stage.Waiting:
            raise NotAllowedException()
        i = self.cur_player
        self.players.append(player)
        self.cur_player += 1
        if self.cur_player == self.n_players:
            self.cur_player = 0
            self.stage == Stage.Shuffling
        return i

    def shuffle(self, player: int, new_deck: [int]):
        if self.stage != Stage.Shuffling or self.cur_player != player:
            raise NotAllowedException()
        self.deck = new_deck
        self.cur_player = (self.cur_player+1) % self.n_players
        if self.cur_player == 0:
            self.stage = Stage.Encrypting

    def encrypt(self, player: int, new_deck: [int]):
        if self.stage != Stage.Encrypting or self.cur_player != player:
            raise NotAllowedException()
        self.deck = new_deck
        self.cur_player = (self.cur_player+1) % self.n_players
        if self.cur_player == 0:
            self.publish_deck()
            # Deal two times because each player gets two cards
            for _ in range(self.n_players):
                self.deal()
                self.deal()
            self.stage = Stage.Encrypting

    def publish_deck(self):
        for player in self.players:
            player.finalize_deck(self.deck)

    def deal(self):
        self.players[self.cur_player].deal()
        self.cur_player += 1

    def report(self, player: int, card: Card):
        for other_player in self.players:
            self.players[other_player].report_dealing(player, card)
