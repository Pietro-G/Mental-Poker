import asyncio
import random
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
import aiohttp
import requests
import json
import logging
import blackjack

import crypto

logging.basicConfig(level=logging.INFO)

from defs import *


class GameData:
    def __init__(self, server_url: str, name: str, i: int):
        self.server_url = server_url
        self.name = name
        self.key_pair: crypto.KeyPair = None
        self.deck: [Card] = None
        self.card_keys: [crypto.KeyPair] = None
        self.players = dict()
        self.i = i

    def analyze_player_list(self, l):
        for (i, player) in enumerate(l):
            self.players[player] = i


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
            data.analyze_player_list(body['players'])
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
            data.card_keys = [data.key_pair.generate_twin_pair() for _ in deck]

            encrypted_deck = []
            # Decrypt each card with the general key
            # then encrypt them with individual key
            for (key, card) in zip(data.card_keys, deck):
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
            """
            When the shuffled and ecrypted deck is published
            """
            data.deck = [Card(None, None, e) for e in self.body_json()['deck']]
            # We can do our round of decryption now
            for (key, card) in zip(data.card_keys, data.deck):
                card.decrypt(key)
            self.send_response(HTTPStatus.OK)

        def do_INITIALIZE(self):
            # Release my key for the first 2*N_PLAYERS cards
            for i in range(2 * N_PLAYERS):
                asyncio.ensure_future(aiohttp.request(
                    'RELEASE',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'no': i,
                         'key': data.card_keys[i].d})
                ))

            self.send_response(HTTPStatus.OK)

        def do_RELEASE(self):
            """
            When somebody releases a key
            """
            body = self.body_json()
            no = body['no']

            # Generate a decrypting key from this key received
            decrypting_key = data.key_pair.generate_twin_pair((None, body['key']))

            # Decrypt
            # If we have unlocked every padlock
            if data.deck[no].decrypt(decrypting_key):
                logging.log('We decrypt a card: %s (%s)', data.deck[no], no)

            self.send_response(HTTPStatus.OK)

        def do_PLAY(self):
            """
            Checks the legality of every play, verifiable by other players
            """
            self.send_response(HTTPStatus.OK)

            choice = None
            while choice not in ('h', 's'):
                choice = input('[H]it / [S]tand: ').lower()
                if (choice == 'h'):
                    #TODO: Tell every other player about "h"
                    blackjack.hit()

                elif (choice == 's'):
                    #TODO: Tell every other player bout "s"

            raise NotImplementedError()

        def do_REQUEST(self):
            raise NotImplementedError()

    return Handler


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123


def run_client():
    name = input('Your name: ')
    server_addr = input('Server IP: ')
    server_port = int(input('Server Port: '))
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
