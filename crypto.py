from sympy import sieve
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# So no two cards, when multiplied together, would generate
# the encoding another card. This is just to be safe.
def generate_encodings(size: int) -> [int]:
    sieve._reset()
    sieve.extend_to_no(size)
    return list(sieve._list)


def encrypt(pub: rsa.RSAPublicKey, n: int) -> bytes:
    byte_n = n.to_bytes(16, 'big')
    return pub.encrypt(
        byte_n,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt(pri: rsa.RSAPrivateKey, byte_n: bytes) -> int:
    encoded_n = pri.decrypt(
        byte_n,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return int.from_bytes(encoded_n, 'big')