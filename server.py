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
        self.table = [['b','10.162.0.2',7001,'yes']] 
        self.saved = {}
        self.acked = False
    
    def run(self):
        sock.bind((self.ip, self.port))
        print("Server listening...")

        # Listen for messages from clients
        while True:
            buf, addr = sock.recvfrom(1024)
            print("from " +str(addr)+ ":", buf)
            if len(buf) < 4:
                next
            
            action, data = buf.decode().split("\n", 1)
            print("from " +str(addr)+ ":", action, data)

            if action == "reg":      # Register client
                self.register(addr, data)
            elif action == "dereg":    # Deregister client
                self.deregister(addr, data)
            elif action == "save":    # Offline message to be saved
                self.save_msg(addr, data)
            elif action == "hello":
                self.acked = True
    
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

        for i in range(len(self.table)):
            row = self.table[i]
            sender = row[0]
            if row[0] == recipient:
                if row[3] == "no":
                    sock.sendto(b"save\nOK", addr)  # ack msg saved
                else:
                    alive = self.client_alive(addr)
                    if alive:   
                        # Client table inaccurate. Abort save, send most recent table
                        sock.sendto(b"save\nERR", addr)
                        pkl = pickle.dumps(self.table)
                        updated = b"table\n" + pkl
                        sock.sendto(updated, addr)
                        return
                    else:  
                        # Server table inaccurate. Update table, broadcast, and save msg     
                        row[3] = "no"
                        self.broadcast_table() 

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
            print("broadcasting to " + str(addr))
            sock.sendto(msg, addr)
        print("broadcast done")

    def client_alive(self, addr):
        self.acked = False
        sock.sendto(b"hello\n", addr)
        timeout = time.time() + 1
        while time.time() < timeout:
            if self.acked:
                return True
        return False

        



    

    
'''
Deregisters client by marking them as offline in the client self.table.
Reads client name to be deregistered from buffer, ACKs dereg msg,
broadcasts changes.
'''



