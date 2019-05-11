import os
import random

deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4

def resetDeck():
    deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4

def deal(deck):
    hand = []
    random.shuffle(deck)
    card = deck.pop()
    if card == 1:
        card = "A"
    if card == 11:
        card = "J"
    if card == 12:
        card = "Q"
    if card ==13:
        card = "K"
    hand.append(card)
    return hand

def play_again():
    replay = input("Do you want play again (Y/N): ").lower()
    if replay == "y":
        dealer_hand = []
        player_hand = []
        resetDeck()
        playGame()
    else:
        print("Thanks for playing")
        exit()

def total(hand):
    total = 0
    for card in hand:
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

def hit(hand):
    card = deck.pop()
    if card == 1:
        card = "A"
    if card == 11:
        card = "J"
    if card == 12:
        card = "Q"
    if card == 13:
        card = "K"
    hand.append(card)
    return hand

def clear():
    if os.name == 'nt':
        os.system('CLS')
    if os.name == 'posix':
        os.system('clear')

def print_results(dealer_hand, player_hand):
    clear()
    print( "The dealer has a " + str(dealer_hand) + " for a total of: " +str(total(dealer_hand)))
    print( "You have a " + str(player_hand) + " for a total of: " + str(total(player_hand)) + "\n")

def checkBlackJack(dealer_hand, player_hand):
    if total(player_hand) == 21:
        print_results(dealer_hand, player_hand)
        print( "Player has Blackjack!\n")
        play_again()

    elif total(dealer_hand) == 21:
        print_results(dealer_hand, player_hand)
        print ("Dealer got Blackjack. \n")
        play_again()

def checkBust(dealer_hand, player_hand):
    if total(player_hand) > 21:
        print_results(dealer_hand, player_hand)
        print("Player Bust. \n")
        play_again()

    elif total(dealer_hand) > 21:
        print_results(dealer_hand, player_hand)
        print("Dealer Bust, player wins\n")
        play_again()

def score(dealer_hand, player_hand):
    if total(player_hand) > total(dealer_hand):
        print_results(dealer_hand, player_hand)
        print("Player has a higher score, Player wins\n")
    elif total(player_hand) < total (dealer_hand):
        print_results(dealer_hand, player_hand)
        print("Dealer has a higher score, Dealer wins\n")
    elif total(player(hand) == total(dealer_hand)):
        pritn_results()
        print("Ties goes to the house, Dealer wins")
        play_again()

def playGame():
    choice = 0
    clear()
    print("Welcome to Blackjack\n")
    dealer_hand = deal(deck)
    player_hand = deal(deck)
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

if __name__ == "__main__":
    playGame()
