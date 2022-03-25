import socket
import pickle
from tabulate import tabulate
import select
import threading
import time
import sys
import os

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lock = threading.Lock()

class Client:
    def __init__(self, name, server_ip, server_port, client_port):
        self.name = name
        self.server_addr = (server_ip, server_port)
        self.client_port = client_port

        self.table = [['name','ip','port','status']]
        self.online = True
        self.server_connected = True
        self.acked = False
        #self.dest = []

    def run(self):
        sock.bind((socket.gethostname(), self.client_port))
        
        # starts thread for receiving msgs from server and other clients
        recv_th = threading.Thread(target=self.receive)
        recv_th.start()

        # Registers client
        self.register()
        
        # Processes user input
        while True:
            cmd = input(">>> ")
            if cmd == "dereg " + self.name and self.online:
                print("deregistering", self.name)
                self.deregister()
                
            elif cmd == "reg " + self.name:
                if not self.online:
                    self.register()
                else:
                    print(">>> [Client already registered.]")
            
            elif len(cmd) > 5 and cmd[:5] == "send ":
                name, msg = self.clean_msg(cmd[5:])
                if name and msg:
                    self.send_msg(name, msg)
            
            elif len(cmd) > 9 and cmd[0:9] == "send_all ":
                name = clean_msg(cmd[9:], group=True)

            elif cmd == "help":
                help_msg = 'CHATAPP COMMANDS\n\tsend <name> <message>   Direct chat: end a message to one user\n\tsend_all <message>      Group chat: send message to all clients\n\tdereg <nickname>        Deregister (go offline)\n\treg <nickname>          Re-register (return online)'
                print(help_msg)

    def register(self):
        self.online = True
        msg = "reg\n" + self.name
        sock.sendto(msg.encode(), self.server_addr)
        # Perhaps want to check updated table being in it. Need a delay
        print(">>> [Welcome, You are registered.]", flush=True)

    def deregister(self):
        msg = b"dereg\n" + self.name.encode()
        def send_dereg():
            try:
                sock.sendto(msg, self.server_addr)
            except:
                print("sendto server failed")
            
        # Attempt to send dereg 5 times
        timeout = 1
        send_dereg()
        for i in range(5):
            t = threading.Timer(timeout, send_dereg)
            t.start()
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if not self.online:
                    t.cancel()
                    break
            print("retrying dereg", i+2)
            if not self.online:  # dereg attempt successful
                break
        
        if not self.online:
            print(">>> [You are Offline. Bye.]", flush=True)
        else: 
            self.quit()

    # Run by server_comm thread. Processes UDP messages from server
    def receive(self):
        while True:
            buf, addr = sock.recvfrom(1024)
            lock.acquire()
            if addr == self.server_addr and self.online:
                self.process_server(buf)
            elif self.online:
                self.process_client(buf, addr)
            lock.release()

    def send_msg(self, name, msg):
        self.dest = []
        self.acked = False
        
        # Check recipient status
        for row in self.table:
            if row[0] == name:
                self.dest = row
        if len(self.dest) == 0:
            print(">>> [Recipient unknown.]")
            return
        if True:
        #if self.dest[3] == "no":
            self.send_offline(msg)    # offline message
            return
        
        msg_bytes = b"msg\n" + msg.encode()
        sock.sendto(msg_bytes, (self.dest[1], self.dest[2]))
        timeout = time.time() + 3
        while time.time() < timeout:
            if self.acked:
                print(">>> [Message received by %s.]" % self.dest[0])
                break
        
        if not self.acked:
            print(">>> [No ACK from %s, message sent to server.]" % self.dest[0])
            self.send_offline(msg)
    
    def send_offline(self, msg):
        self.acked = False
        msg = "save\n" + self.dest[0] + "\n" + msg
        print("sending server",msg)
        try:
            sock.sendto(msg.encode(), self.server_addr)
        except:
            self.quit()
    
    def process_server(self, buf):
        head, data = buf.split(b"\n", 1)
        head = head.decode()
        if head == "table":      # Updated table
            self.table_update(data)
        elif head == "dereg":        # Deregister ack (successful)
            if data.decode() == "OK":
                self.online = False
        elif head == "save":       # Receive saved messages or acks for saving msgs
            
            data = data.decode()
            if data == "OK":
                print(">>> [Messages received by the server and saved]", end="", flush=True)
            elif data == "ERR":

                print(">>> [Client %s exists!!]" % self.dest[0], end="", flush=True)

    # Receives udp msgs from other clients
    def process_client(self, buf, addr):
        head, data = buf.decode().split("\n", 1)

        # receive new message
        if head == "msg":
            sock.sendto(b"ok\n", addr)      # ack message received
            known = False
            for row in self.table:
                if row[1] == addr[0] and row[2] == addr[1]:
                    print(row[0], ": ", data, sep="")
                    known = True
            if not known:
                print("Unknown sender:", msg)

        # ack for a message just sent
        elif head == "ok" and self.dest[1] == addr[0] and self.dest[2] == addr[1]:
            self.acked = True
    
    def process_saved(self, data):
        global recipient
        

    def clean_msg(self, data, group=False):
        # strips whitespace off name for group chats
        if group:
            return data.strip()

        # Returns name and msg for direct chats
        data = data.strip().split(" ", 1)
        if len(data) != 2:
            print(">>> [Please specify a message and a recipient.]")
            return None, None
        
        name = data[0].strip()
        msg = data[1].strip()
        if len(name) == 0:
            print(">>> [Please specify a recipient.]")
            return None, None
        if len(msg) == 0:
            print(">>> [Please enter a message to send.]")
            return None, None
        return name, msg
    
    def table_update(self, data):
        self.table = pickle.loads(data)
        print(">>> [Client table updated.]")
        print(tabulate(self.table))
        print(">>>", end=" ", flush=True)
    
    def quit(self):
        print(">>> [Server not responding]", flush=True)
        print(">>> [Exiting]", flush=True)
        sock.close()
        os._exit(1)
        