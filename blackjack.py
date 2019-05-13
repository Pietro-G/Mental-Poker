import os
import random
import crypto
from defs import *


class Blackjack:
    def __init__(self, players, deck, key_pair, local_player):
        self.deck: [Card] = deck
        self.deck_top = len(self.deck) - 1

        # Dealer is Alice (first arbitrary player in room) by default
        self.player_hands: [[Card]] = [[] for _ in players]
        self.players = players

        # Each player is dealt with two cards
        for i, name in enumerate(players):
            self.player_hands[i].append(self.deck[self.deck_top])
            self.deck_top -= 1
            self.player_hands[i].append(self.deck[self.deck_top])
            self.deck_top -= 1

        self.cur_player = 0
        self.local_player = local_player

        self.key_pair = key_pair

    def make_choice(self):
        self.print_situation()
        choice = None
        while choice not in ('h', 's'):
            choice = input().lower()
        key_idx = self.deck_top
        self.decision(self.players[self.cur_player], choice, None)
        return choice, key_idx

    def check_all(self, last_decision):
        self.check_bust(last_decision)
        self.check_blackjack(last_decision)

    def total_score(self, player):
        """
        Calculate the total
        """
        total = 0
        for card in self.player_hands[player]:
            try:
                rk = card.rank_name()
            except NotAllowedException:
                return '?'
            # JQK
            if rk in 'JQK':
                total += 10
            # A
            elif rk == 'A':
                if total < 11:
                    total += 11
                else:
                    total += 1
            else:
                total += int(rk)
        return total

    def decision(self, player_name: str, decision: str, key: int):
        """
        When some player makes a decision
        """
        if self.players[self.cur_player] != player_name:
            raise NotAllowedException()
        if decision == 'h':
            card = self.deck[self.deck_top]
            self.player_hands[self.cur_player].append(card)
            self.deck_top -= 1

            if key is not None:
                decrypting_key = self.key_pair.generate_twin_pair((None, key))
                if card.decrypt(decrypting_key):
                    self.print_situation()

            self.check_all(decision)
        elif decision == 's':
            self.cur_player = self.cur_player + 1
            if self.cur_player == len(self.players):
                self.score(decision)
        else:
            raise Exception('Sanity check')
        self.print_situation()

    def print_situation(self):
        clear()
        for idx, name in enumerate(self.players):
            print('%s has hand: %s for a total of %s'
                  % (name,
                     ''.join([str(c) for c in self.player_hands[idx]]),
                     self.total_score(idx)))
        print('Turn of ' + self.players[self.cur_player])
        if self.players[self.cur_player] == self.local_player:
            print('\u001b[47m\u001b[30m[H]it / [S]tand: \u001b[0m\n')

    def check_blackjack(self, last_decision):
        for idx, name in enumerate(self.players):
            if self.total_score(idx) == 21:
                print(name + " has Blackjack!")
                self.play_again(last_decision)

    def check_bust(self, last_decision):
        for idx, name in enumerate(self.players):
            score = self.total_score(idx)
            if isinstance(score, int) and score > 21:
                print(name + " bust!")
                self.play_again(last_decision)

    def score(self, last_decision):
        """
        In case of no blackjack/bust, score the hands
        """
        high_idx = None
        high_score = -1

        for idx, name in enumerate(self.players):
            score = self.total_score(idx)
            if score > high_score:
                high_idx = idx
                high_score = score

        print('%s wins with %s score' % (self.players[high_idx], high_score))
        self.play_again(last_decision)

    def has_access(self, name, no):
        return no > self.deck_top

    def play_again(self, last_decision):
        self.player_hands: [[Card]] = [[] for _ in self.players]
        for i, name in enumerate(self.players):
            self.player_hands[i].append(self.deck[self.deck_top])
            self.deck_top -= 1
            self.player_hands[i].append(self.deck[self.deck_top])
            self.deck_top -= 1

        self.cur_player = 0

        raise NewGameException(last_decision)
