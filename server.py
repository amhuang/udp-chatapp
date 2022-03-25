import socket
import pickle
import threading
import select
from tabulate import tabulate
import time

table = [['name','ip','port','status']]     # client table
clients = []    # stores all connected clients as tuples: (clientSock, addr, name)
host = "127.0.0.1"  
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lock = threading.Lock()
client_connected = True

# Called by app.py to start server
def run(server_port):
    s.bind((host, server_port))
    s.listen()
    print("Server is listening...")

    # Listen for new connections
    while True:
        connSock, addr = s.accept()
        print(f"Connected by {addr}")
        client_th = threading.Thread(target=recv_client, args=(connSock, addr, lock,))
        client_th.start()

    s.close()

def check_client(connSock):
    global client_connected
    print("checking if", connSock, "still online")
    client_connected = False
    print("conn reset", connSock)
    msg = b"err\n"
    try:
        connSock.sendall(msg)
    except BrokenPipeError:
        print("brokenpipe")
        return False

    # Wait for ack from user
    timeout = time.time() + 3
    while time.time() < timeout:
        if client_connected:
            return True
    print("conn reset no ack")
    return False

def recv_client(connSock, addr, lock):
    global client_connected
    while True:
        try:
            buf = connSock.recv(4).decode()
            print(buf)
        except ConnectionResetError:
            if not check_client(connSock):
                close_conn(connSock)
                break

        if buf == "":
            print("empty msg disconnect")
            close_conn(connSock)
            break

        # Stop threads to proceess input one client at time
        lock.acquire()
        print("from " +str(addr)+ ":", buf)

        if buf == "reg\n":
            register(connSock, addr)
        
        elif buf == "der\n":
            dereg(connSock)
        
        elif buf == "err\n":
            ack = connSock.recv(2).decode()
            if ack:
                client_connected
        lock.release()


def register(connSock, addr):
    name = connSock.recv(1024).decode()
    print("registering", name)
    
    # Check for client name in table
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "yes"
            print("update registration\n", tabulate(table))
            broadcast_table()
            return
    
    # If client new, add to list of clients and client table
    clients.append((connSock, addr, name))
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    print("new registration\n", tabulate(table))
    broadcast_table()
    
'''
Deregisters client by marking them as offline in the client table.
Reads client name to be deregistered from buffer, ACKs dereg msg,
broadcasts changes.
'''
def dereg(connSock):
    name = connSock.recv(1024).decode()
    print("Deregistering", name)
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "no"
            connSock.sendall(b"der\n")
            connSock.sendall(b"OK")
            print("Successful dereg of", name)
            broadcast_table()
            print(tabulate(table))

def broadcast_table():
    global clients
    pkl = pickle.dumps(table)
    for client in clients:
        sock, addr = client[0], client[1]
        print("broadcasting to " + str(addr))
        sock.sendall(b"tab\n")
        sock.sendall(pkl)
    print("broadcast done")

'''
Close connection and removes client data if client disconnects
or leaves silently.
'''
def close_conn(connSock):
    lock.acquire()
    name = ""
    for client in clients:
        if client[0] == connSock:
            name = client[2]
            clients.remove(client)
            break
    for i in range(len(table)):
        if table[i][0] == name:
            del table[i]
            break
    print(name, " disconnected.")
    print(tabulate(table))
    connSock.close()
    lock.release()
    
