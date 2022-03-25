import socket
import pickle
import threading
import select
from tabulate import tabulate
import time

table = [['name','ip','port','status'], ['b','10.162.0.2',7003,'yes']]     # client table
clients = []    # stores all connected clients as tuples: (clientSock, addr, name)
saved_msgs = {}
host = "127.0.0.1"  
s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lock = threading.Lock()
client_connected = True     # true when acks received from client

# Called by app.py to start server
def run(server_port):
    s_sock.bind((host, server_port))
    s_sock.listen()
    print("Server is listening...")

    # Listen for new connections
    while True:
        c_sock, addr = s_sock.accept()
        print(f"Connected by {addr}")
        client_th = threading.Thread(target=recv_client, args=(c_sock, addr,))
        client_th.start()

    s_sock.close()

def recv_client(c_sock, addr):
    global client_connected
    while True:
        try:
            buf = c_sock.recv(4).decode()
            print(buf)
        except ConnectionResetError:
            if not check_client(c_sock):
                close_conn(c_sock)
                break

        if buf == "":
            print("empty msg disconnect")
            close_conn(c_sock)
            break

        # Stop threads to proceess input one client at time
        lock.acquire()
        print("from " +str(addr)+ ":", buf)

        # Register client
        if buf == "reg\n":
            register(c_sock, addr)
        
        # Deregister client
        elif buf == "der\n":
            dereg(c_sock)

        # Offline message to be saved
        elif buf == "sav\n":
            save_msg(c_sock, addr)
        
        # ack from client to confirm still connected
        elif buf == "err\n":
            ack = c_sock.recv(2).decode()
            if ack == "OK":
                client_connected = True

        lock.release()

def save_msg(c_sock, addr):
    buf = c_sock.recv(1024).decode()
    
    recipient, msg = buf.split("\n", 1)

    for row in table:
        if row[1] == addr[0] and row[2] == addr[1]:
            sender = row[0]
            c_sock.sendall(b"sav\nOK")  # ack msg saved
        if row[0] == recipient and row[3] == "yes":
            c_sock.sendall(b"sav\nERR")  # recipient still active
            return

    print("saving message from", sender, "to", recipient, "\t", msg)

    if recipient not in saved_msgs:
        saved_msgs[recipient] = []  
    saved_msgs[recipient].append((sender, time.time(), msg))
    print(saved_msgs)
    

def register(c_sock, addr):
    name = c_sock.recv(1024).decode()
    print("registering", name)
    
    # Check for client name in table
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "yes"
            print("update registration\n", tabulate(table))
            broadcast_table()
            return
    
    # If client new, add to list of clients and client table
    clients.append((c_sock, addr, name))
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    print("new registration\n", tabulate(table))
    broadcast_table()
    
'''
Deregisters client by marking them as offline in the client table.
Reads client name to be deregistered from buffer, ACKs dereg msg,
broadcasts changes.
'''
def dereg(c_sock):
    name = c_sock.recv(1024).decode()
    print("Deregistering", name)
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "no"
            c_sock.sendall(b"der\nOK")
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

def check_client(c_sock):
    global client_connected
    print("checking if", c_sock, "still online")
    client_connected = False
    msg = b"err\n"
    try:
        c_sock.sendall(msg)
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

'''
Close connection and removes client data if client disconnects
or leaves silently.
'''
def close_conn(c_sock):
    lock.acquire()
    name = ""
    for client in clients:
        if client[0] == c_sock:
            name = client[2]
            clients.remove(client)
            break
    for i in range(len(table)):
        if table[i][0] == name:
            del table[i]
            break
    
    if name in saved_msgs:
        del saved_msgs[name]

    print(name, " disconnected.")
    print(tabulate(table))
    print(saved_msgs)
    c_sock.close()
    lock.release()
    
