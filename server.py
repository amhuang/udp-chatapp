import socket
import json
import threading
import select
import time
import datetime

# client table. Data format: ['name','ip','port','status'],   

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class Server:
    def __init__(self, server_port):
        self.ip = "127.0.0.1"  
        self.port = server_port
        self.table = []#[['b','10.162.0.2',7001,'yes']] 
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
        # Check for client is known in self.table
        for i in range(len(self.table)):
            row = self.table[i]
            if row[0] == name:
                # Client with different address trying to register w same name
                if row[1] != addr[0] or row[2] != addr[1]:
                    sock.sendto(b"reg\nERR", addr)
                
                # Client returning online
                if row[3] == "no":
                    row[3] = "yes"
                    self.broadcast_table()
                    self.send_saved(addr, name) 
                    print("Client", name, "returned online")
                
                # Client online but has same address (server table might not have known about it going offline)
                elif row[1] == addr[0] and row[2] == addr[1]:
                    self.broadcast_table()

                return
        
        # If client new, add to list of clients and client self.table
        entry = [name, addr[0], addr[1], 'yes']
        self.table.append(entry)
        print("Registered", name)
        self.broadcast_table()
    
    def deregister(self, addr, name):
        for i in range(len(self.table)):
            row = self.table[i]
            if row[0] == name:
                row[3] = "no"
                sock.sendto(b"dereg\nACK", addr)
                print("Deregistered", name)
                self.broadcast_table()

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
                    sock.sendto(b"save\nACK", addr)  # ack msg saved
                    print("Saving message from", sender, "to", recipient, ":", msg)
                else:
                    alive = self.client_alive(addr=addr)
                    if alive:   # Client table inaccurate. Abort save, send most recent table
                        print(recipient, "tried to save message for active client. Sending table to update.")
                        sock.sendto(b"save\nERR", addr)
                        json_list = json.dumps(self.table)
                        updated = b"table\n" + json_list.encode()
                        sock.sendto(updated, addr)
                        return
                    else:       # Server table inaccurate. Update table, broadcast, and save msg   
                        print(recipient, "unresponsive. Updating and broadcasting table.")
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
        print("Saving message for ", recipient, ": ", msg, sep="")
        self.saved[recipient].append(formatted)

    def send_saved(self, addr, name):
        if name in self.saved:
            sock.sendto(b"saved\n\t", addr)
            for entry in self.saved[name]:
                msg = "saved\n" + entry
                sock.sendto(msg.encode(), addr)
            sock.sendto(b"saved\n\n", addr)
            del self.saved[name]


    def send_all(self, addr, data):
        sender, msg = data.split("\n", 1)
        if msg == "ACK":
            self.channel_acks[sender] = True
        else:
            print("Sending message from", sender, "to channel:", msg)
            self.broadcast_msg(addr, sender, msg)
            

    def broadcast_msg(self, addr, sender, msg):
        sock.sendto(b"all\nACK", addr)   # Ack send_all msg from client
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
                sock.sendto(out_bytes, addr)
            elif row[3] == "no":
                self.save_msg(target, sender, msg, channel=True)

        th = threading.Timer(0.5, self.check_channel, args=(sender, msg,))
        th.start()


    def check_channel(self, sender, msg):
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
                    self.save_msg(name, sender, msg, channel=True)
                    self.table[rownum][3] = "no"
                    print(name, "unresponsive. Updating table, saving message:", msg)
        
        if table_updated:
            self.broadcast_table()


    def broadcast_table(self):
        print("Broadcasting client table")
        json_list = json.dumps(self.table)
        msg = b"table\n" + json_list.encode()
        for row in self.table:
            if row[3] == "yes":
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
        

