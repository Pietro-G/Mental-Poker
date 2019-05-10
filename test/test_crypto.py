import os

import crypto
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def test_encrypt():
    '''Test and see if encryption works'''
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())

    for i in range(1000):
        crypto.encrypt(key.public_key(), i)


def test_encrypt_decrypt():
    '''Test encrypt and then decrypt'''

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())

    for i in range(1000):
        c = crypto.encrypt(key.public_key(), i)
        d = crypto.decrypt(key, c)
        assert d == i