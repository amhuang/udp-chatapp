import socket
import pickle
import threading
import select
from tabulate import tabulate

table = [['name','ip','port','status']]
ThreadCount = 0
host = "127.0.0.1"  #socket.gethostname()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = []

def run(server_port):
    s.bind((host, server_port))
    print("Server is listening...")
    s.listen()

    while True:
        connSock, addr = s.accept()
        clients.append((connSock, addr))

        print(f"Connected by {addr}")
        th = threading.Thread(target=new_client, args=(connSock, addr,))
        th.start()
        print("Threads:", threading.active_count())

    s.close()

def new_client(connSock, addr):
    while True:
        response = connSock.recv(1024).decode()
        print("response:", response)

        if response[0:4] == "reg ":
            name = response[4:].strip()
            register(connSock, addr, name)
            next

        elif response[0:6] == "dereg ":
            name = response[6:].strip()
            print(name)
            if dereg(connSock, name):
                connSock.sendall(b"OK")

def register(connSock, addr, name):
    for i in range(len(table)):
        if table[i][0] == name:
            connSock.sendall(b"OK")
            table[i][3] = "yes"

            broadcast_table(connSock)
            print(tabulate(table))
            return 
    
    connSock.sendall(b"OK")
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    broadcast_table(connSock)
    print(tabulate(table))

def broadcast_table(connSock):
    pkl = pickle.dumps(table)
    for sock, addr in clients:
        sock.sendall(b"table" + pkl)
        response = connSock.recv(2).decode()
        print("response to broadcast", response)
        if client_ack(connSock, timeout=1):
            next
        '''if not client_ack(connSock, timeout=1):
            for i in range(len(table)):
                if table[i][1] == addr[0] and table[i][2] == addr[1]:
                    table[i][3] == "no"
                    print(tabulate(table))
                    break'''

def client_ack(connSock, timeout=-1):
    response = connSock.recv(2).decode()
    if response == "OK":
        return True

    '''if timeout > 0:
        ready = select.select([connSock], [], [], timeout)
        if ready[0]:
            response = connSock.recv(2).decode()
            connSock.setblocking(1)
            if response == "OK":
                return True
    else: '''
        
        
    return False

def dereg(connSock, name):
    for i in range(len(table)):
        if table[i][0] == name:
            print("Deregistering " + name + " ...")
            table[i][3] = "no"
            broadcast_table(connSock)
            print(tabulate(table))
            return True
    return False
