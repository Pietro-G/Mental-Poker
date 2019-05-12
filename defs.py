import crypto
import asyncio


class NotAllowedException(BaseException):
    def __init__(self):
        super().__init__('Not Allowed')


class Card:
    """
    A card with suit and rank (int of 1-13), and an encoding (its representation)
    """

    def __init__(self, encoding: int):
        self.encoding = encoding

        self.value = self.get_value()

        self.seen_decrypting_key = set()

    def get_value(self):
        raise NotImplementedError()

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
        return len(self.seen_decrypting_key) == N_CARDS


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


N_CARDS = 52
N_PLAYERS = 2
