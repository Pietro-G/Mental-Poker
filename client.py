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
from blackjack import Blackjack

import crypto

logging.basicConfig(level=logging.WARNING)

from defs import *

loop: asyncio.AbstractEventLoop = None


class GameData:
    def __init__(self, server_url: str, name: str):
        self.server_url = server_url
        self.name = name
        self.key_pair: crypto.KeyPair = None
        self.deck: [Card] = None
        self.card_keys: [crypto.KeyPair] = None
        self.players: [str] = []
        self.waiting_approval = False

        self.mechanics: Blackjack = None


def HandlerFactory(data: GameData):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return 'shhh'

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
            logging.info('Keys to use: %s, %s', body['p'], body['q'])
            data.players = body['players']
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
            logging.info('%s cards are individually encrypted', len(deck))

            encrypted_deck = []
            # Decrypt each card with the general key
            # then encrypt them with individual key
            for (key, card) in zip(data.card_keys, deck):
                processed_card = key.encrypt(data.key_pair.decrypt(card))
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
                     'deck': encrypted_deck})
            )
            th_ensure_future(loop, task)

        def do_PUBLISH(self):
            """
            When the shuffled and encrypted deck is published
            """
            data.deck = [Card(e) for e in self.body_json()['deck']]
            # We can do our round of decryption now
            for (key, card) in zip(data.card_keys, data.deck):
                card.decrypt(key)
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # Initialize game mechanics
            data.mechanics = Blackjack(data.players, data.deck, data.key_pair, data.name)

        def do_INITIALIZE(self):
            # Release my key for the first 2*N_PLAYERS cards
            for i in range(2 * N_PLAYERS):
                i = len(data.card_keys) - 1 - i
                logging.info('Releasing card %s', i)
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

        def restart(self):
            for i in range(data.mechanics.deck_top + 2 * N_PLAYERS, data.mechanics.deck_top, -1):
                logging.info('Releasing card %s', i)
                task = io.request(
                    'RELEASE',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'no': i,
                         'key': data.card_keys[i].d})
                )
                th_ensure_future(loop, task)

            data.waiting_approval = False
            threading.Thread(target=self.play).start()

        def play(self):
            # If not our turn
            if data.mechanics.players[data.mechanics.cur_player] != data.name:
                return

            try:
                choice, key_idx = data.mechanics.make_choice()
            except NewGameException as e:
                # tell everyone our choice
                task = io.request(
                    'PLAYED',
                    data.server_url,
                    data=json.dumps(
                        {'name': data.name,
                         'decision': e.last_decision,
                         'key': None})
                )
                th_ensure_future(loop, task)
                return self.restart()

            key = data.card_keys[key_idx]

            # tell everyone our choice
            task = io.request(
                'PLAYED',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'decision': choice,
                     'key': key.d if choice == 'h' else None})
            )
            th_ensure_future(loop, task)
            self.restart()

            task = io.request(
                'REQUEST',
                data.server_url,
                data=json.dumps(
                    {'name': data.name,
                     'no': key_idx})
            )
            th_ensure_future(loop, task)

            data.waiting_approval = choice == 'h'

        def do_RELEASE(self):
            """
            When somebody releases a key
            """
            body = self.body_json()
            no = body['no']

            self.send_response(HTTPStatus.OK)
            self.end_headers()

            # Generate a decrypting key from this key received
            decrypting_key = data.key_pair.generate_twin_pair((None, body['key']))

            # Decrypt
            # If we have unlocked every padlock
            prev_decrypted = data.deck[no].is_decrypted()
            if data.deck[no].decrypt(decrypting_key):
                if not prev_decrypted:
                    logging.info('We decrypt a card: %s (%s)', str(data.deck[no]), no)
                    data.mechanics.print_situation()
                try:
                    data.mechanics.check_all('s')
                except NewGameException:
                    return self.restart()
                if data.waiting_approval:
                    threading.Thread(target=self.play).start()

        def do_PLAY(self):
            """
            It's my turn to play!
            Checks the legality of every play, verifiable by other players
            """
            self.send_response(HTTPStatus.OK)
            self.end_headers()

            threading.Thread(target=self.play).start()

        def do_REQUEST(self):
            """
            A player requests to see a card
            """
            body = self.body_json()
            no = body['no']
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
                self.send_response(HTTPStatus.OK)
                self.end_headers()
            else:
                self.send_response(HTTPStatus.FORBIDDEN)
                self.end_headers()

        def do_DECISION(self):
            """
            A player made a play decision
            """
            body = self.body_json()
            name = body['name']
            try:
                self.send_response(HTTPStatus.OK)
                self.end_headers()
                try:
                    data.mechanics.decision(name, body['decision'], body['key'])
                except NewGameException:
                    return self.restart()
                # My turn
                if data.mechanics.players[data.mechanics.cur_player] == data.name:
                    threading.Thread(target=self.play).start()
            except NotAllowedException:
                self.send_response(HTTPStatus.FORBIDDEN)
                self.end_headers()
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
    name = ''
    while name == '':
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

    print('Waiting for others...')

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
