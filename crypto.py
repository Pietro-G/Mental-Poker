import json
from sympy import sieve, ntheory, crypto

def generate_encodings(size: int) -> [int]:
    '''
    Generate the encodings for size number of cards.
    We use prime numbers so when multiplied together,
    no two cards would generate the encoding of a thrid card.
    '''
    sieve._reset()
    sieve.extend_to_no(size)
    return list(sieve._list)


class KeyPair:
    def __init__(self, e: int, d: int, p: int, q: int, size: int):
        self.e = e
        self.d = d
        self.p = p
        self.q = q
        self.n = p*q
        self.size = size

    def __eq__(self, other):
        return self.e == other.e\
            and self.d == other.d\
            and self.p == other.p\
            and self.q == other.q\
            and self.size == other.size

    def jsonify(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(data: str) -> 'KeyPair':
        data = json.loads(data)
        return KeyPair(data['e'], data['d'], data['p'], data['q'], data['size'])

    @staticmethod
    def new_key_pair(size: int = 2048) -> 'KeyPair':
        half = size // 2
        p = ntheory.generate.randprime(2**(half-1), 2**half)
        q = ntheory.generate.randprime(2**(half-1), 2**half)
        phi = (p-1)*(q-1)
        e = ntheory.generate.randprime(1, phi)
        _, d = crypto.crypto.rsa_private_key(p, q, e)

        return KeyPair(e, d, p, q, size)

    def generate_twin_pair(self, ed: (int, int) = None) -> 'KeyPair':
        if ed is None:
            phi = (self.p-1)*(self.q-1)
            e = ntheory.generate.randprime(1, phi)
            _, d = crypto.crypto.rsa_private_key(self.p, self.q, e)
        else:
            (e, d) = ed
        return KeyPair(e, d, self.p, self.q, self.size)

    def reset_key(self, e: int = None):
        if e is None:
            phi = (self.p-1)*(self.q-1)
            self.e = ntheory.generate.randprime(1, phi)
        _, self.d = crypto.crypto.rsa_private_key(self.p, self.q, self.e)

    def encrypt(self, b: int) -> int:
        assert b <= 2**self.size
        return crypto.crypto.encipher_rsa(b, (self.n, self.e))

    def decrypt(self, x: int) -> int:
        assert x <= self.n
        return crypto.crypto.decipher_rsa(x, (self.n, self.d))

    def data_size(self) -> int:
        return self.size // 8
