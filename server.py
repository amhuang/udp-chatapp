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
    
    def run(self):
        sock.bind((self.ip, self.port))
        print("Server listening...")

        # Listen for messages from clients
        while True:
            buf, addr = sock.recvfrom(2048)
            if len(buf) < 4:
                next
            
            action, data = buf.decode().split("\n", 1)
            print("from " +str(addr)+ ":", action, data)

            if action == "reg":             # Register client
                self.register(addr, data)
            elif action == "dereg":         # Deregister client
                self.deregister(addr, data)
            elif action == "save":          # Offline message to savve
                self.save_msg_recv(addr, data)
            elif action == "all":
                self.send_all(addr, data)
            elif action == "hello":         # Ack indicating client alive
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

    def save_msg_recv(self, addr, data):

        recipient, msg = data.split("\n", 1)
        sender = ""

        for i in range(len(self.table)):
            row = self.table[i]

            #  Get name of sender from addr
            if row[1] == addr[0] and row[2] == addr[1]:
                sender = row[0]

            # Check recipient status, save/send msg accordingly
            if row[0] == recipient:
                if row[3] == "no":
                    sock.sendto(b"save\nOK", addr)  # ack msg saved
                else:
                    alive = self.client_alive(addr=addr)
                    if alive:   # Client table inaccurate. Abort save, send most recent table
                        sock.sendto(b"save\nERR", addr)
                        pkl = pickle.dumps(self.table)
                        updated = b"table\n" + pkl
                        sock.sendto(updated, addr)
                        return
                    else:       # Server table inaccurate. Update table, broadcast, and save msg   
                        row[3] = "no"
                        self.broadcast_table() 
                        
        self.save_msg(recipient, sender, msg)

    def save_msg(self, recipient, sender, msg, channel=False):
        if recipient not in self.saved:
            self.saved[recipient] = []

        ts = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        if channel:
            formatted = "Channel-Message " + sender + ": " + "[" +  ts + "] " + msg
        else:
            formatted = sender + ": " + "[" +  ts + "] " + msg
        self.saved[recipient].append(formatted)

    def send_saved(self, addr, name):
        if name in self.saved:
            sock.sendto(b"stored\n|", addr)
            for entry in self.saved[name]:
                msg = "stored\n" + entry
                sock.sendto(msg.encode(), addr)
            del self.saved[name]

    def send_all(self, addr, data):
        sender, msg = data.split("\n", 1)
        if msg == "OK":
            self.channel_acks[sender] = True
            print(self.channel_acks)
            return
        else:
            self.broadcast_msg(addr, sender, msg)
            

    def broadcast_msg(self, addr, sender, msg):
        sock.sendto(b"all\nOK", addr)   # Ack send_all msg from client
        out = "all\n" + sender + "\n" + msg
        out_bytes = out.encode()

        self.channel_acks = {}
        for row in self.table:
            target = row[0]
            if target == sender:
                continue

            if row[3] == "yes":
                self.channel_acks[target] = False    # save boolean for checking if acked
                addr = (row[1], row[2])
                print("sending channel msg to", row[0])
                sock.sendto(out_bytes, addr)
            elif row[3] == "no":
                self.save_msg(target, sender, msg, channel=True)

        th = threading.Timer(0.5, self.check_channel, args=(sender, msg,))
        th.start()
        print("broadcast_msg done")


    def check_channel(self, sender, msg):
        print("checking acks")
        table_updated = False
        for name in self.channel_acks:
            if self.channel_acks[name] == False:
                # Get client addr and row num
                for i in range(len(self.table)):
                    row = self.table[i]
                    if row[0] == name:
                        addr = (row[1], row[2])
                        rownum = i

                # If client not alive, update table and broadcast
                if not self.client_alive(addr):
                    table_updated = True
                    self.save_msg(name, sender, msg)
                    self.table[rownum][3] = "no"
                    print("msg saved for", name, "from", sender, msg)
        
        if table_updated:
            self.broadcast_table()


    def broadcast_table(self):
        pkl = pickle.dumps(self.table)
        msg = b"table\n" + pkl
        for row in self.table:
            addr = (row[1], row[2])
            sock.sendto(msg, addr)


    def client_alive(self, addr):
        # Either add or name is required
        self.acked = False
        sock.sendto(b"hello\n", addr)
        timeout = time.time() + 0.5
        while time.time() < timeout:
            if self.acked:
                return True
        return False
        

