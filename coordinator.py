import asyncio
import json
from enum import Enum
import aiohttp
from crypto import generate_encodings
from defs import *
import logging
logging.basicConfig(level=logging.INFO)

import crypto
from defs import *


class Stage(Enum):
    Waiting = 0
    Shuffling = 1
    Encrypting = 2
    Playing = 3


class NotAllowedException(BaseException):
    def __init__(self):
        super().__init__('Not Allowed')


class Game:
    def __init__(self, n_players: int):
        self.key_pair = crypto.KeyPair.new_key_pair()

        self.deck: [int] = generate_encodings(N_CARDS)
        self.key_pair = crypto.KeyPair.new_key_pair()

        self.n_players = n_players
        self.players: [Player] = []
        self.cur_player_i = 0

        self.stage = Stage.Shuffling

    def cur_player(self) -> Player:
        return self.players[self.cur_player_i]

    def next_player(self):
        self.cur_player_i = (self.cur_player_i + 1) % self.n_players

    def new_round(self) -> bool:
        """
        If has completed a round
        """
        return self.cur_player_i == 0

    def join(self, player: Player):
        """
        Request to join the game
        """
        if self.stage != Stage.Waiting:
            raise NotAllowedException()
        i = len(self.players)
        self.players.append(player)
        logging.info('Player %s %s joined the game.', player.name, player.addr)

        # If we have enough people
        if len(self.players) == self.n_players:
            self.stage = Stage.Shuffling
            # Notice the first player that they need to do a shuffle
            self.notice_shuffle()

        return i

    def notice_shuffle(self):
        """
        Notice the current player to shuffle.
        """
        asyncio.ensure_future(aiohttp.request(
            'SHUFFLE',
            self.cur_player().url(),
            data=json.dumps(
                {'key_pair': self.key_pair,
                 'deck': self.deck}
            )
        ))

    def recv_shuffled(self, name: str, new_deck: [int]):
        """
        Received response from current player and the shuffled cards
        """
        if self.stage != Stage.Shuffling or self.cur_player().name != name:
            raise NotAllowedException()

        self.deck = new_deck
        self.next_player()

        # If everyone has shuffled
        if self.new_round():
            # Proceed to the next stage
            self.stage = Stage.Encrypting
            # Notice the first player to do encryption
            self.notice_encrypt()
        else:
            # Ask next player to shuffle
            self.notice_shuffle()

    def notice_encrypt(self):
        """
        Give current player cards to encrypt
        """
        asyncio.ensure_future(aiohttp.request(
            'ENCRYPT',
            self.cur_player().url(),
            data=json.dumps({'deck': self.deck})
        ))

    def recv_encrypt(self, name: str, new_deck: [int]):
        """
        Received response from current player and the encrypted cards
        """
        if self.stage != Stage.Encrypting or self.cur_player().name != name:
            raise NotAllowedException()
        self.deck = new_deck
        self.next_player()

        # If everyone has encrypted the cards
        if self.new_round():
            for player in self.players:
                # Proceed to publish the deck
                asyncio.ensure_future(aiohttp.request(
                    'PUBLISH',
                    player.url(),
                    data=json.dumps(
                        {'deck': self.deck}
                    )
                ))
                # Initialize the game (public the first 2*n keys)
                asyncio.ensure_future(aiohttp.request(
                    'INITIALIZE',
                    player.url()
                ))

            # and let the first player play the game
            self.notice_play()
            self.stage = Stage.Playing
        else:
            # Ask next player to encrypt
            self.notice_encrypt()

    def notice_play(self):
        """
        Notice current player to make a decision
        """
        asyncio.ensure_future(aiohttp.request(
            'PLAY',
            self.cur_player().url()
        ))

    def recv_played(self, name: str, decision: str, key: int):
        """
        Receive the play from the player
        """
        # Tell others what this player is doing
        for player in self.players:
            if player.name != name:
                asyncio.ensure_future(aiohttp.request(
                    'DECISION',
                    player.url(),
                    data=json.dumps(
                        {'key': key,
                         'decision': decision})
                ))

        self.next_player()
        self.notice_play()

    def recv_request_draw(self, name: str, no: int):
        """
        Receive the request to open the current top card.
        Simply relay it to every other server.
        """
        for player in self.players:
            if player.name != name:
                asyncio.ensure_future(aiohttp.request(
                    'REQUEST',
                    player.url(),
                    data=json.dumps(
                        {'from': name,
                         'no': no})
                ))

    def recv_release(self, name: str, no: int, key: int):
        """
        Receive the approval to open the current top card.
        Simply relay it to every other server.
        """
        for player in self.players:
            if player.name != name:
                asyncio.ensure_future(aiohttp.request(
                    'RELEASE',
                    player.url(),
                    data=json.dumps(
                        {'name': name,
                         'no': no,
                         'key': key})
                ))
