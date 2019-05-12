from enum import Enum


class Suit(Enum):
    Spade = 0
    Heart = 1
    Diamond = 2
    Club = 3


class Card:
    """
    A card with suit and rank (int of 1-13), and an encoding (its representation)
    """

    def __init__(self, suit: Suit, rank: int, encoding: int):
        self.suit = suit
        self.rank = rank
        self.encoding = encoding

        self.value = self.get_value()

    def get_value(self):
        raise NotImplementedError()


class Player:
    def __init__(self, name: str, addr: (str, int)):
        self.name = name
        self.addr = addr

    def url(self):
        (ip, port) = self.addr
        return 'http://{}:{}/{}'.format(ip, port, self.name)


N_CARDS = 52
N_PLAYERS = 3
