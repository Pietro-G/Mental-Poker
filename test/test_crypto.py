import crypto
import utils

import random
import os

def test_encrypt():
    '''Test and see if encryption works'''
    key = utils.key

    for r in crypto.generate_encodings(52):
        key.encrypt(r)


def test_encrypt_decrypt():
    '''Test encrypt and then decrypt'''
    key = utils.key

    for r in crypto.generate_encodings(52):
        assert r == key.decrypt(key.encrypt(r))


def test_encrypt_commutative():
    '''Test the commutativity of the cipher'''
    k1 = crypto.KeyPair.new_key_pair()
    k2 = k1.generate_twin_pair()

    for r in crypto.generate_encodings(52):
        c1 = k1.encrypt(k2.encrypt(r))
        c2 = k2.encrypt(k1.encrypt(r))
        assert c1 == c2

        m1 = k1.decrypt(k2.decrypt(c1))
        m2 = k2.decrypt(k1.decrypt(c1))
        assert m1 == m2

def test_json_serialization():
    '''Test json (de)serialization'''
    key = utils.key
    assert crypto.KeyPair.from_json(key.jsonify()) == key
    
def test_reset_key():
    key = utils.key
    key.reset_key()
    for r in crypto.generate_encodings(5):
        assert r == key.decrypt(key.encrypt(r))
