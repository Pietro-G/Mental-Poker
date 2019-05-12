
import socket
import select
import sys
import _thread
import coordinator


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123
game = coordinator.Game()

class Player:
    def __init__(self, ip):
        self.ip = ip
    
    def start(self):
        _thread.start_new_thread(clientthread,(conn,addr))
    
    def finalize_deck(self):
        raise NotImplementedError()

    def notice_shuffle(self):
        message_to_send = {action: "shuffle", deck: game.deck}
        print(message_to_send)
        #THIS MAY NEED NEED TO BE ENCODED BEFORE IT CAN BE SENT. UNSURE
        conn.send(message_to_send)
    
    def notice_encrypt(self):
        message_to_send = {action: "encrypt", deck: shuffled_deck}
        print(message_to_send)
        #THIS MAY NEED NEED TO BE ENCODED BEFORE IT CAN BE SENT. UNSURE
        conn.send(message_to_send)
    
    def notice_play(self):
        message_to_send = {action: "play"}
        print(message_to_send)
        #THIS MAY NEED NEED TO BE ENCODED BEFORE IT CAN BE SENT. UNSURE
        conn.send(message_to_send)
    
    def notice_approval(self, addr, key):
        message_to_send = {action: "approval", key = key, player_ip = addr}
        print(message_to_send)
        #THIS MAY NEED NEED TO BE ENCODED BEFORE IT CAN BE SENT. UNSURE
        conn.send(message_to_send)
    
    def publish_deck(self, deck):
        message_to_send = {action: "publish", deck = deck}
        print(message_to_send)
        #THIS MAY NEED NEED TO BE ENCODED BEFORE IT CAN BE SENT. UNSURE
        conn.send(message_to_send)
    
    def request_draw(message):
        game.recv_request_draw(addr)
    
    def receive_approval(message):
        key = message['key']
        game.recv_approval(addr, key)

    
    def shuffled(message):
        shuffled_deck = message['deck']
        try:
            game.recv_shuffle(addr, shuffled_deck)
            message_to_send = "<" + addr[0] + "> " + " has the shuffled deck"
            broadcast(message_to_send, conn)
            print(message_to_send)
            return shuffled_deck
        except:
            message_to_send = "<" + addr[0] + "> " + " IS TRYING TO CHEAT ITS NOT UR TURN TO SHUFFLE MATE"
    
    def encrypted(message):
        encrypted_deck = message['deck']
        try:
            message_to_send = "<" + addr[0] + "> " + " has the encrypted deck"
            broadcast(message_to_send, conn)
            print(message_to_send)
            return encrypted_deck
        except:
            message_to_send = "<" + addr[0] + "> " + " IS TRYING TO CHEAT ITS NOT UR TURN TO ENCRYPT MATE"

    
    def clientthread(conn, addr):
        conn.send("Welcome to Blackjack!".encode())
        try:
            game.join(coordinator.Player(addr))
        except:
            conn.send("Failure to join. Disconnecting.".encode())
            remove(conn)
        
        while True:
            try:
                message = conn.recv(2048)
                json.loads(message)
                if message['action'] == 'shuffled':
                    shuffled(message)
                elif message['action'] == 'encrypted':
                    encrypted(message)
            except:
                continue


def runServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    IP_address = DEFAULT_ADDR
    Port = DEFAULT_PORT
    server.bind((IP_address, Port))
    
    server.listen(3)
    print("Blackjack room is open.")
    
    list_of_clients = []
    

    def broadcast(message, connection):
        for clients in list_of_clients:
            if clients!=connection:
                try:
                    clients.send(message)
                except:
                    clients.close()
                    
                    # if the link is broken, we remove the client
                    remove(clients)
    
    def remove(connection):
        if connection in list_of_clients:
            list_of_clients.remove(connection)


    while True:
        
        conn, addr = server.accept()
        list_of_clients.append(conn)

        # prints the address of the user that just connected
        print(addr[0] + " connected")
            # creates and individual thread for every user
        player = Player(addr)
        player.start()
    
    conn.close()
    server.close()
