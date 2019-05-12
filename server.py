
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
        message_to_send = "<" + addr[0] + "> " + " has shuffled"
        print(message_to_send)
        broadcast(message_to_send, conn)
    
    def notice_encrypt(self):
        message_to_send = "<" + addr[0] + "> " + " has encrypted"
        print(message_to_send)
        broadcast(message_to_send, conn)
    
    def shuffled(message):
        shuffled_deck = message['shuffled_deck']
        game.shuffle(addr, shuffled_deck)
        message_to_send = "<" + addr[0] + "> " + " has the shuffled deck"
        broadcast(message_to_send, conn)
        print(message_to_send)
        return shuffled_deck
    
    def encrypted(message):
        encrypted_deck = message['encrypted_deck']
        message_to_send = "<" + addr[0] + "> " + " has the encrypted deck"
        broadcast(message_to_send, conn)
        print(message_to_send)
        return encrypted_deck
    
    def clientthread(conn, addr):
        # sends a message to the client whose user object is conn
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
