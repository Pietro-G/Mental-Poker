import asyncio
import random
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
import aiohttp
import requests
import json
import logging

import crypto

logging.basicConfig(level=logging.INFO)

from defs import *

class GameData:
    def __init__(self, server_url: str, name: str, i: int):
        self.server_url = server_url
        self.name = name
        self.key_pair: crypto.KeyPair = None
        self.deck: [Card] = None
        self.card_keys: [[crypto.KeyPair]] = None
        self.i = i


def HandlerFactory(data: GameData):
    class Handler(BaseHTTPRequestHandler):
        def body_json(self):
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)
            return json.dumps(post_body)

        def do_BROADCAST(self):
            print('Broadcast: %s' % self.body_json()['message'])
            self.send_response(HTTPStatus.OK)

        def do_SHUFFLE(self):
            body = self.body_json()

            data.key_pair = crypto.KeyPair.from_json(body['key_pair']).generate_twin_pair()
            deck = body['deck']

            random.shuffle(deck)
            for (i, card) in enumerate(data.deck):
                deck[i] = data.key_pair.encrypt(card)

            logging.info('Shuffled {} cards', len(deck))
            self.send_response(HTTPStatus.OK)

            # Send shuffled deck back
            asyncio.ensure_future(aiohttp.request(
                'SHUFFLED',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'deck': deck})
            ))

        def do_ENCRYPT(self):
            deck = self.body_json()['deck']

            # Initialize individual keys
            data.card_keys = [[None] * N_PLAYERS] * len(deck)
            for key_list in data.card_keys:
                key_list[0] = data.key_pair.generate_twin_pair()

            encrypted_deck = []
            # Decrypt each card with the general key
            # then encrypt them with individual key
            for ([key], card) in zip(data.card_keys, deck):
                encrypted_deck.append(
                    data.key_pair.decrypt(key.encrypt(card.encoding)))

            logging.info('Encrypted {} cards', len(deck))
            self.send_response(HTTPStatus.OK)

            # Send encrypted deck back
            asyncio.ensure_future(aiohttp.request(
                'ENCRYPTED',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'deck': deck})
            ))

        def do_PUBLISH(self):
            data.deck = self.body_json()['deck']
            # We can totally do our round of decryption now
            for (i, card) in data.deck:
                data.deck[i] = data.card_keys[i][0].decrypt(card)
            self.send_response(HTTPStatus.OK)

        def do_INITIALIZE(self):
            # Release my key for the first 2*N_PLAYERS cards
            for i in range(2*N_PLAYERS):
                asyncio.ensure_future(aiohttp.request(
                    'RELEASE',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'no': i,
                         'key': data.card_keys[i][0].d})
                ))

            self.send_response(HTTPStatus.OK)

        def do_RELEASE(self):
            body = self.body_json()
            raise NotImplementedError()



    return Handler

DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123


def run_client():
    name = input('Your name: ')
    server_addr = input('Server IP: ')
    server_port = int(input('Server IP: '))
    server_url = 'http://{}:{}/'.format(server_addr, server_port)

    # Try to join the party
    res = requests.request(
        'JOIN',
        server_url,
        data=json.dumps({
            'name': name,
            'port': DEFAULT_PORT
        })
    )
    if res.status_code != HTTPStatus.OK:
        logging.error(
            "Can't join the room: [{}] {}",
            res.status_code,
            res.content
        )
        return

    i = int(res.content)
    logging.info('Joined the room as player {}!', i)

    game_data = GameData(server_url, name, i)
    httpd = HTTPServer((DEFAULT_ADDR, DEFAULT_PORT), HandlerFactory(game_data))
    logging.info('Callback server spinned up')
    httpd.serve_forever()

if __name__ == "__main__":
    run_client()
