import socket
import select
import sys
import _thread
import crypto


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123
conn = server.connect((IP_address, Port))

key_pair = None
individual_key_list = []

def runClient():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    IP_address = DEFAULT_ADDR
    Port = DEFAULT_PORT


    while True:

        # maintains a list of possible input streams
        sockets_list = [sys.stdin, server]
        read_sockets,write_socket, error_socket = select.select(sockets_list,[],[])

        for socks in read_sockets:
            if socks == server:
                message = socks.recv(2048)
                print(message)
            else:
                message = sys.stdin.readline()
                server.send(message.encode())
                sys.stdout.write("<You>")
                sys.stdout.write(message)
                sys.stdout.flush()
    server.close()

def recvMessage(msg):
    global key_pair
    encryptedDeck = []
    if(msg['action']] == "shuffle"):
        key_pair = KeyPair.new_key_pair(msg["p"],msg["q"])
        random.shuffle(msg["deck"])
        for card in msg["deck"]:
            cipherText = key_pair.encrypt(card)
            encryptedDeck.append(cipherText)
        message_to_send = {action: "shuffled", deck: encryptedDeck}

    elif(msg['action'] == "encrypt"):
        for card in deck:
            individual_key = KeyPair.new_key_pair()
            individual_key.encrypt(card)
            individual_key_list += individual_key_list
        message_to_send = {action: "encrypted", deck: encryptedDeck}

    elif(msg['action'] == "play"):
        playerDecision()
        if (msg[decision] == "hit"):
            #Player gets a card
        else:
            #Player doesn't get card

    elif(msg['action'] == "approval"):


    elif(msg['action'] == "publish"):

    elif(msg['action'] == "reqDraw"):

    else:
        print("Unrecognized action by client")

    conn.send(message_to_send)

def playerDecision():
    #Client is prompted with a decision to play or not
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

if __name__ == "__main__":
    runClient()
