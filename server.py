import socket
import pickle
import threading
import select
from tabulate import tabulate
import time

# client table. Data format: ['name','ip','port','status'], 
table = [['b','10.162.0.2',7003,'yes']]     
saved_msgs = {}
host = "127.0.0.1"  

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lock = threading.Lock()
client_connected = True     # true when acks received from client

# Called by app.py to start server
def run(server_port):
    global client_connected
    sock.bind((host, server_port))
    print("Server listening...")

    # Listen for messages from clients
    while True:
        buf, addr = sock.recvfrom(1024)
        if len(buf) < 4:
            next

        
        request, data = buf.decode().split("\n", 1)
        print("from " +str(addr)+ ":", request, data)

        if request == "reg":      # Register client
            register(addr, data)
        elif request == "dereg":    # Deregister client
            deregister(addr, data)
        elif request == "save":    # Offline message to be saved
            save_msg(addr, data)
        

def save_msg(addr, data):
    recipient, msg = data.split("\n", 1)
    for row in table:
        if row[0] == recipient and row[3] == "yes":
            sock.sendto(b"save\nERR", addr)  # recipient still active
            return
        if row[1] == addr[0] and row[2] == addr[1]:
            sender = row[0]
            sock.sendto(b"save\nOK", addr)  # ack msg saved

    print("saving message from", sender, "to", recipient, "\t", msg)

    if recipient not in saved_msgs:
        saved_msgs[recipient] = []  
    saved_msgs[recipient].append((sender, time.time(), msg))
    print(saved_msgs)
    
def register(addr, name):
    print("registering", name)
    # Check for client name in table
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "yes"
            print("update registration\n", tabulate(table))
            broadcast_table()
            return
    
    # If client new, add to list of clients and client table
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    print("new registration\n", tabulate(table))
    broadcast_table()
    
'''
Deregisters client by marking them as offline in the client table.
Reads client name to be deregistered from buffer, ACKs dereg msg,
broadcasts changes.
'''
def deregister(addr, name):
    print("Deregistering", name)
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "no"
            sock.sendto(b"dereg\nOK", addr)
            print("Successful dereg of", name)
            broadcast_table()
            print(tabulate(table))


def broadcast_table():
    global clients
    pkl = pickle.dumps(table)
    msg = b"table\n" + pkl
    for row in table:
        addr = (row[1], row[2])
        print(addr, msg)
        print("broadcasting to " + str(addr))
        sock.sendto(msg, addr)
    print("broadcast done")