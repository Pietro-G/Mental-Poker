import asyncio
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
import aiohttp
io = aiohttp.ClientSession()
import requests
import json
import logging
from defs import *

import crypto

logging.basicConfig(level=logging.INFO)

from defs import *


loop: asyncio.AbstractEventLoop = None

class GameData:
    def __init__(self, server_url: str, name: str):
        self.server_url = server_url
        self.name = name
        self.key_pair: crypto.KeyPair = None
        self.deck: [Card] = None
        self.card_keys: [crypto.KeyPair] = None
        self.players = dict()

        self.mechanics = None

    def analyze_player_list(self, l):
        for (i, player) in enumerate(l):
            self.players[player] = i


def HandlerFactory(data: GameData):
    class Handler(BaseHTTPRequestHandler):
        def body_json(self):
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)
            return json.loads(post_body)

        def do_BROADCAST(self):
            print('Broadcast: %s' % self.body_json()['message'])
            self.send_response(HTTPStatus.OK)
            self.end_headers()

        def do_SHUFFLE(self):
            logging.info('Received request to shuffle')
            body = self.body_json()

            data.key_pair = crypto.KeyPair.new_key_pair(body['p'], body['q'])
            players = body['players']
            data.analyze_player_list(players)
            deck = body['deck']

            # Shuffle and encrypt the deck
            random.shuffle(deck)
            for (i, card) in enumerate(deck):
                deck[i] = data.key_pair.encrypt(card)

            logging.info('Shuffled %s cards', len(deck))
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # Send shuffled deck back
            task = io.request(
                'SHUFFLED',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'deck': deck})
            )
            th_ensure_future(loop, task)

        def do_ENCRYPT(self):
            deck = self.body_json()['deck']

            # Initialize individual keys
            logging.info('Generating %s individual keys', len(deck))
            data.card_keys = [data.key_pair.generate_twin_pair() for _ in deck]
            logging.info('Cards are individually encrypted', len(deck))

            encrypted_deck = []
            # Decrypt each card with the general key
            # then encrypt them with individual key
            for (key, card) in zip(data.card_keys, deck):
                processed_card = data.key_pair.decrypt(key.encrypt(card))
                encrypted_deck.append(processed_card)

            logging.info('Encrypted %s cards', len(deck))
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # Send encrypted deck back
            task = io.request(
                'ENCRYPTED',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'deck': deck})
            )
            th_ensure_future(loop, task)

        def do_PUBLISH(self):
            """
            When the shuffled and ecrypted deck is published
            """
            data.deck = [Card(e) for e in self.body_json()['deck']]
            # We can do our round of decryption now
            for (key, card) in zip(data.card_keys, data.deck):
                card.decrypt(key)
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # Initialize game mechanics
            data.mechanics = Blackjack(data.players, data.deck)

        def do_INITIALIZE(self):
            # Release my key for the first 2*N_PLAYERS cards
            for i in range(2 * N_PLAYERS):
                task = io.request(
                    'RELEASE',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'no': i,
                         'key': data.card_keys[i].d})
                )
                th_ensure_future(loop, task)

            self.send_response(HTTPStatus.OK)
            self.end_headers()

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
                data.mechanics.fully_decrypt(no)  # TODO implement this

            self.send_response(HTTPStatus.OK)
            self.end_headers()

        def do_PLAY(self):
            """
            It's my turn to play!
            """
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # TODO print the situation here

            play = None
            while play not in ('h', 's'):
                play = input('[h]it / [s]tand: ')
            raise NotImplementedError()

        def do_REQUEST(self):
            """
            A player requests to see a card
            """
            body = self.body_json()
            no = body['no']
            # TODO implement check for access
            if data.mechanics.has_access(body['from'], no):
                task = io.request(
                    'RELEASE',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'no': no,
                         'key': data.card_keys[no].d})
                )
                th_ensure_future(loop, task)

        def do_DECISION(self):
            """
            A player made a play decision
            """
            body = self.body_json()
            name = body['name']
            try:
                # TODO implement decision making
                data.mechanics.decision(name, body['decision'], body['key'])
            except NotAllowedException:
                logging.info('%s is not allowed to make a decision now', name)

    return Handler


def get_open_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = get_open_port()


def run_client():
    name = input('Your name: ')
    server_addr = input('Server IP [localhost]: ')
    if server_addr == '':
        server_addr = 'localhost'
    server_port = input('Server IP [8123]: ')
    if server_port == '':
        server_port = 8123
    else:
        server_port = int(server_port)
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
            "Can't join the room: [%s] %s",
            res.status_code,
            res.content
        )
        return

    logging.info('Joined the room')

    game_data = GameData(server_url, name)
    httpd = HTTPServer((DEFAULT_ADDR, DEFAULT_PORT), HandlerFactory(game_data))
    logging.info('Callback server spinned up')
    httpd.serve_forever()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    threading.Thread(target=loop.run_forever).start()

    run_client()
