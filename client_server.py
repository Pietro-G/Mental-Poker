
import socket
import select
import sys
import _thread


DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 8123

def runServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    IP_address = DEFAULT_ADDR
    Port = DEFAULT_PORT
    server.bind((IP_address, Port))

    """
        listens for 100 active connections. This number can be
        increased as per convenience.
        """
    server.listen(100)
    print("Blackjack room is open.")

    list_of_clients = []

    def clientthread(conn, addr):
        # sends a message to the client whose user object is conn
        conn.send("Welcome to Blackjack!".encode())
        while True:
            try:
                message = conn.recv(2048)
                print("<" + addr[0] + ">: " + message.decode())
                if message:
                    print("<" + addr[0] + ">: " + message)
                            # Calls broadcast function to send message to all
                    message_to_send = "<" + addr[0] + "> " + message
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

    while True:
        
        conn, addr = server.accept()
        list_of_clients.append(conn)
        
        # prints the address of the user that just connected
        print(addr[0] + " connected")
        # creates and individual thread for every user
        # that connects
        _thread.start_new_thread(clientthread,(conn,addr))

    conn.close()
    server.close()

def runClient():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    IP_address = DEFAULT_ADDR
    Port = DEFAULT_PORT
    server.connect((IP_address, Port))

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



def onStartup():
    print("Type [s] to host a session or [c] to connect to an existing session")
    start_command = input()
    while start_command is not "s" and start_command is not "c":
        print("Type [s] to host a session or [c] to connect to an existing session")
        start_command = input()
    if start_command == "s":
        runServer()
    else:
        runClient()

if __name__ == "__main__":
    onStartup()

