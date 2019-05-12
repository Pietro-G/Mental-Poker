import asyncio
from coordinator import Game, NotAllowedException
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
import aiohttp
import json
import logging
logging.basicConfig(level=logging.INFO)

from defs import *


def HandlerFactory(game):
    class Handler(BaseHTTPRequestHandler):
        def body_json(self):
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)
            return json.dumps(post_body)

        def broadcast(self, s: str):
            for player in game.players:
                task = aiohttp.request(
                    'BROADCAST',
                    player.url(),
                    data=json.dumps({'message': s}))
                asyncio.ensure_future(task)

        def do_JOIN(self):
            """
            A player wants to join the room.

            Body format: { name: , port: }
            IP is the same as this request is sent from.
            """
            try:
                addr, _ = self.client_address
                body = self.body_json()
                player = Player(body['name'], (addr, body['port']))
                game.join(player)
            except NotAllowedException:
                logging.log('Room full. Not allowed to join the game.')
                self.send_response(HTTPStatus.FORBIDDEN, 'Room full. You are not allowed to join.')

        def do_SHUFFLED(self):
            """
            A player has finished shuffling the deck.
            """
            try:
                body = self.body_json()
                game.recv_shuffled(body['name'], body['deck'])
            except NotAllowedException:
                msg = '<{} IS TRYING TO CHEAT ITS NOT UR TURN TO SHUFFLE MATE>'.format(body['name'])
                self.broadcast(msg)

        def do_ENCRYPTED(self):
            """
            A player has finished encrypting the deck.
            """
            try:
                body = self.body_json()
                game.recv_encrypt(body['name'], body['deck'])
                message_to_send = '{} has encrypted the deck'.format(body['name'])
                self.broadcast(message_to_send)
            except NotAllowedException:
                message_to_send = '{} IS TRYING TO CHEAT ITS NOT UR TURN TO ENCRYPT MATE'.format(body['name'])
                self.broadcast(message_to_send)

        def do_PLAYED(self):
            """
            A player has made a play decision.
            """
            try:
                body = self.body_json()
                game.recv_played(body['name'], body['decision'], body['key'])
            except NotAllowedException:
                message_to_send = '{} IS TRYING TO CHEAT ITS NOT UR TURN TO PLAY MATE'.format(body['name'])
                self.broadcast(message_to_send)

        def do_REQUEST(self):
            """
            Request to draw from a player.
            """
            body = self.body_json()
            game.recv_request_draw(body['name'], body['no'])

        def do_RELEASE(self):
            """
            A player is releasing a key
            """
            body = self.body_json()
            game.recv_release(body['name'], body['no'], body['key'])

    return Handler


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123


def run_server():
    game = Game(N_PLAYERS)

    httpd = HTTPServer((DEFAULT_ADDR, DEFAULT_PORT), HandlerFactory(game))
    logging.info('Blackjack room is open')
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
