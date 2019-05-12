
import socket
import select
import sys
import _thread
import coordinator


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123
game = coordinator.Game()

def runServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    IP_address = DEFAULT_ADDR
    Port = DEFAULT_PORT
    server.bind((IP_address, Port))
    
    server.listen(3)
    print("Blackjack room is open.")
    
    list_of_clients = []
    
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
                print("<" + addr[0] + ">: " + message.decode())
                if message:
                    print("<" + addr[0] + ">: " + message)
                    #We need to make sure the server is sending the msg associated with the user's choice
                    message_to_send = "<" + addr[0] + "> " + message
                    game_move(addr, message)
                    broadcast(message_to_send, conn)
                else:
                    remove(conn)
            except:
                continue

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

    #Call the game object's next move
    def game_move(addr, msg):
        return game.recv_from_client(addr, msg)

    while True:
        
        conn, addr = server.accept()
        list_of_clients.append(conn)

        # prints the address of the user that just connected
        print(addr[0] + " connected")
            # creates and individual thread for every user
        _thread.start_new_thread(clientthread,(conn,addr))
                
    conn.close()
    server.close()
