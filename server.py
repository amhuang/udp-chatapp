import socket
import pickle
import threading
import select
from tabulate import tabulate
import time
import datetime

# client table. Data format: ['name','ip','port','status'],   

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lock = threading.Lock()

class Server:
    def __init__(self, server_port):
        self.ip = "127.0.0.1"  
        self.port = server_port
        self.table = [['b','10.162.0.2',7001,'no']] 
        self.saved = {}
    
    def run(self):
        sock.bind((self.ip, self.port))
        print("Server listening...")

        # Listen for messages from clients
        while True:
            buf, addr = sock.recvfrom(1024)
            print("from " +str(addr)+ ":", buf)
            if len(buf) < 4:
                next
            
            request, data = buf.decode().split("\n", 1)
            print("from " +str(addr)+ ":", request, data)

            if request == "reg":      # Register client
                self.register(addr, data)
            elif request == "dereg":    # Deregister client
                self.deregister(addr, data)
            elif request == "save":    # Offline message to be saved
                self.save_msg(addr, data)
    
    def register(self, addr, name):
        print("registering", name)
        # Check for client name in self.table
        for i in range(len(self.table)):
            if self.table[i][0] == name:
                self.table[i][3] = "yes"
                print("update registration\n", tabulate(self.table))
                self.send_saved(addr, name)
                self.broadcast_table()
                return
        
        # If client new, add to list of clients and client self.table
        entry = [name, addr[0], addr[1], 'yes']
        self.table.append(entry)
        print("new registration\n", tabulate(self.table))
        self.broadcast_table()
    
    def deregister(self, addr, name):
        print("Deregistering", name)
        for i in range(len(self.table)):
            if self.table[i][0] == name:
                self.table[i][3] = "no"
                sock.sendto(b"dereg\nOK", addr)
                print("Successful dereg of", name)
                self.broadcast_table()
                print(tabulate(self.table))

    def save_msg(self, addr, data):
        recipient, msg = data.split("\n", 1)
        for row in self.table:
            if row[0] == recipient and row[3] == "yes":
                sock.sendto(b"save\nERR", addr)  # recipient still active
                return
            if row[1] == addr[0] and row[2] == addr[1]:
                sender = row[0]
                sock.sendto(b"save\nOK", addr)  # ack msg saved

        print("saving message from", sender, "to", recipient, "\t", msg)
        if recipient not in self.saved:
            self.saved[recipient] = []  
        timestamp = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        self.saved[recipient].append((sender, timestamp, msg))
        print(self.saved)

    def send_saved(self, addr, name):
        if name in self.saved:

            sock.sendto(b"off\n|", addr)
            for entry in self.saved[name]:
                msg = "off\n" + entry[0] + ": [" + str(entry[1]) + "]  " + entry[2]
                sock.sendto(msg.encode(), addr)
            del self.saved[name]

    def broadcast_table(self):
        pkl = pickle.dumps(self.table)
        msg = b"table\n" + pkl
        for row in self.table:
            addr = (row[1], row[2])
            print(addr, msg)
            print("broadcasting to " + str(addr))
            sock.sendto(msg, addr)
        print("broadcast done")

    

        



    

    
'''
Deregisters client by marking them as offline in the client self.table.
Reads client name to be deregistered from buffer, ACKs dereg msg,
broadcasts changes.
'''



