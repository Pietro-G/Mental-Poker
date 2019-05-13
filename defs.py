import crypto
import os
import asyncio

N_CARDS = 52
N_PLAYERS = 2


class NotAllowedException(BaseException):
    def __init__(self):
        super().__init__('Not Allowed')


class NewGameException(BaseException):
    def __init__(self, last_decision):
        super().__init__('New Game')
        self.last_decision = last_decision


encoding_idx_mapping = dict()
for i, encoding in enumerate(crypto.generate_encodings(N_CARDS)):
    encoding_idx_mapping[encoding] = i


class Card:
    """
    A card with suit and rank (int of 1-13), and an encoding (its representation)
    """

    def __init__(self, encoding: int):
        self.encoding = encoding
        self.seen_decrypting_key = set()

    def decrypt(self, key: crypto.KeyPair) -> bool:
        """
        Decrypt with key with check for duplication.
        Return True if this card has been fully decrypted.
        """
        if key.d not in self.seen_decrypting_key:
            self.encoding = key.decrypt(self.encoding)
            self.seen_decrypting_key.add(key.d)
        return self.is_decrypted()

    def is_decrypted(self):
        return len(self.seen_decrypting_key) == N_PLAYERS

    def rank_name(self):
        rk = self.index() // 4
        if rk == 1-1:
            return "A"
        elif rk == 11-1:
            return "J"
        elif rk == 12-1:
            return "Q"
        elif rk == 13-1:
            return "K"
        return str(rk)

    def index(self):
        if not self.is_decrypted():
            raise NotAllowedException()
        return encoding_idx_mapping[self.encoding]

    def __str__(self):
        if not self.is_decrypted():
            return '?'
        suite = '♠♥♦♣'[self.index() % 4]
        return suite + self.rank_name()


class Player:
    def __init__(self, name: str, addr: (str, int)):
        self.name = name
        self.addr = addr

    def url(self):
        (ip, port) = self.addr
        return 'http://{}:{}/{}'.format(ip, port, self.name)


def th_ensure_future(loop: asyncio.AbstractEventLoop, task):
    def f():
        asyncio.ensure_future(task)

    loop.call_soon_threadsafe(f)


def clear():
    if os.name == 'nt':
        os.system('CLS')
    if os.name == 'posix':
        os.system('clear')
