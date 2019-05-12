import os
import random
import crypto
from defs import *

class Blackjack:
    def __init__(self, players, deck):
        self.deck = crypto.generate_encodings(N_CARDS)
        #Generate encoding for every card in the deck
        actual_deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4
        self.encoding_mapping = dict()
        for (card, encoding) in zip(actual_deck, crypto.generate_encodings(N_CARDS)):
            encoding_mapping[encoding] = card
        self.hand = []
        self.dealer_hand = [] #Dealer is Alice (first arbitrary player in room) by default
        self.player_hands = []
        self.players = players #Received from do_SHUFFLE in client.py

    def resetDeck():
        actual_deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4

    def deal(self): #Client
        random.shuffle(actual_deck)
        card = actual_deck.pop()
        if card == 1:
            card = "A"
        if card == 11:
            card = "J"
        if card == 12:
            card = "Q"
        if card ==13:
            card = "K"
        self.hand.append(card)
        return self.hand

    def play_again(self): #Client
        replay = input("Do you want play again (Y/N): ").lower()
        if replay == "y":
            self.dealer_hand = []
            self.player_hand = []
        resetDeck()
        playGame()
        else:
            print("Thanks for playing")
            exit()

    def total(self):
        total = 0
        for card in self.hand:
            if card == "J" or card == "Q" or card == "K":
                total+=10
            elif card == "A":
                if total < 11:
                    total+= 11
                else:
                    total+=1
            else:
                total += card

        return total

    def hit(self):
        card = actual_deck.pop()
        if card == 1:
            card = "A"
        if card == 11:
            card = "J"
        if card == 12:
            card = "Q"
        if card == 13:
            card = "K"
        self.hand.append(card)

    def clear():
        if os.name == 'nt':
            os.system('CLS')
        if os.name == 'posix':
            os.system('clear')

    def print_results(dealer_hand, player_hands):
        clear()
        print( "The " + self.players[0] "has hand: " + str(dealer_hand) + " for a total of: " +str(total(dealer_hand)))
        for idx, player_hand in enumerate(player_hands):
            print(self.player[idx] + " has a " + str(player_hand) + " for a total of: " + str(total(player_hand)) + "\n")

    def checkBlackJack(dealer_hand, player_hands):
        for idx, player_hand in enumerate(player_hands):
            if total(player_hand) == 21:
                print_results(dealer_hand, player_hands)
            print( self.player[idx] + " has Blackjack!\n")
            play_again()

        if total(dealer_hand) == 21:
            print_results(dealer_hand, player_hand)
            print ( self.player[0] + " got Blackjack. \n")
            play_again()

    def checkBust(dealer_hand, player_hands):
        for idx, player_hand in enumerate(player_hands):
            if total(player_hand) > 21:
                print_results(dealer_hand, player_hand)
                print( self.player[idx] " Bust. \n")
            play_again()

        if total(dealer_hand) > 21:
            print_results(dealer_hand, player_hand)
            print( self.player[0] + " Bust, other players won\n")
            play_again()

    def score(dealer_hand, player_hands):
        for idx, player_hand in enumerate(player_hands):
            if total(player_hand) > total(dealer_hand):
                print_results(dealer_hand, player_hand)
                print(self.player[idx] + " has a higher score, Player wins\n")
            elif total(player_hand) < total (dealer_hand):
                print_results(dealer_hand, player_hand)
                print(self.player[0] + "  has a higher score, Dealer wins\n")
            elif total(player_hand) == total(dealer_hand)):
                pritn_results()
                print("Ties goes to the house's dealer, " + self.player[0] + " wins")
                play_again()

    #This function plays a local human vs streotipical dealer blackjack game instance
    def playGame():
        choice = 0
        clear()
        print("Welcome to Blackjack\n")
        dealer_hand = deal(actual_deck)
        player_hand = deal(actual_deck)
        hit(player_hand)
        hit(dealer_hand)
        while choice != "q":
            print("The dealer is showing a: " + str(dealer_hand[0]))
            print("You have a: " + str(player_hand) + " for a total of: " + str(total(player_hand)))
            checkBlackJack(dealer_hand, player_hand)
            choice = input("Do you want to [H]it, [S]tand, or [Q]uit: ").lower()
            clear()
            if choice == "h":
                hit(player_hand)
                print_results(dealer_hand,player_hand)
                if(checkBust(dealer_hand,player_hand)):
                    choice == "q"
            elif choice == "s":
                while total(dealer_hand) < total(player_hand):
                    hit(dealer_hand)
                    checkBust(dealer_hand, player_hand)
                    print_results(dealer_hand,player_hand)
            elif choice == "q":
                play_again()
                print("Bye!")
                exit()
                
    #Left for legacy purposes
    if __name__ == "__main__":
        playGame()
