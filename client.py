import socket
import json
import select
import threading
import time
import sys
import os
from tabulate import tabulate

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lock = threading.Lock()

class Client:
    def __init__(self, name, server_ip, server_port, client_port):
        self.name = name
        self.server_addr = (server_ip, server_port)
        self.port = client_port

        self.table = []     # Data format: ['name','ip', port,'status']
        self.online = True
        self.server_connected = True
        self.acked = False
        #self.dest = []

    def run(self):
        sock.bind((socket.gethostname(), self.port))
        
        recv_th = threading.Thread(target=self.recv)

        self.register()
        recv_th.start()
        self.process_input()

    def process_input(self):
        while True:
            cmd = input(">>> ")
            if cmd == "dereg " + self.name and self.online:
                self.deregister()
                
            elif cmd == "reg " + self.name:
                if not self.online:
                    self.register()
                else:
                    print(">>> [Client already registered.]", flush=True)
            
            elif len(cmd) > 5 and cmd[:5] == "send ":
                name, msg = self.clean_msg(cmd[5:])
                if name and msg:
                    self.send(name, msg)
            
            elif len(cmd) > 9 and cmd[0:9] == "send_all ":
                msg = self.clean_msg(cmd[9:], group=True)
                self.send_all(msg)

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
            sock.sendto(msg, self.server_addr)
            
        # Attempt to send dereg 5 times
        send_dereg()
        for i in range(5):
            t = threading.Timer(0.5, send_dereg)
            t.start()
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if not self.online:
                    t.cancel()
                    break
            if not self.online:  # dereg attempt successful
                break
            print("retrying dereg", i+2)
        
        if not self.online:
            print(">>> [You are offline. Bye.]", flush=True)
        else: 
            self.quit()

    def send(self, name, msg):
        self.dest = []
        self.acked = False
        
        # Check recipient status
        for row in self.table:
            if row[0] == name:
                self.dest = row
        if len(self.dest) == 0:
            print(">>> [Recipient unknown.]")
            return
        if self.dest[3] == "no":
            self.send_offline(msg)    # offline message
            return
        
        formatted = "msg\n" + self.name + "\n" + msg
        sock.sendto(formatted.encode(), (self.dest[1], self.dest[2]))
        timeout = time.time() + 0.5
        while time.time() < timeout:
            if self.acked:
                print(">>> [Message received by %s.]" % self.dest[0])
                break
        
        if not self.acked:
            print(">>> [No ACK from %s, message sent to server.]" % self.dest[0], flush=True)
            self.send_offline(msg)

    def send_all(self, msg):
        self.acked = False
        formatted = "all\n" + self.name + "\n" + msg

        def send_server():
            sock.sendto(formatted.encode(), self.server_addr)
        
        # Up to 5 attempts to get an ack from server
        send_server()
        for i in range(5):
            t = threading.Timer(0.5, send_server)
            t.start()
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if self.acked:
                    print(">>> [Message received by Server.]")
                    t.cancel()
                    break
            if self.acked:  # sendall attempt successful
                break
            print("attempt", i, "at sendall")
        if not self.acked:
            print(">>> [Server not responding.]")
    
    def send_offline(self, msg):
        self.acked = False
        msg = "save\n" + self.dest[0] + "\n" + msg
        try:
            sock.sendto(msg.encode(), self.server_addr)
        except:
            self.quit()
    
    # Run by server_comm thread. Processes UDP messages from server
    def recv(self):
        while True:
            buf, addr = sock.recvfrom(2048)
            lock.acquire()
            if self.online and addr == self.server_addr:
                self.recv_server(buf)
            elif self.online:
                self.recv_client(buf, addr)
            lock.release()
    
    def recv_server(self, buf):
        head, data = buf.split(b"\n", 1)
        head = head.decode()

        if head == "table": 
            data = data.decode()        
            self.table_update(data)
        
        elif head == "dereg":       # Server acks dereg (successful)  
            if data.decode() == "OK":
                self.online = False
        
        elif head == "save":        # Receive saved messages, acks for saving msgs
            data = data.decode()
            if data == "OK":
                print("[Messages received by the server and saved]\n>>>", end="", flush=True)
            elif data == "ERR":
                print("[Client %s exists!!]" % self.dest[0], flush=True)
            #print(">>> ", end="", flush=True)
        
        elif head == "stored":     # Saved messages upon returning online
            data = data.decode()
            if data == "|":        # indicates start of a batch of saved msgs
                print("[You have messages]")
            else:
                print(">>>", data)
        
        elif head == "all":  
            data = data.decode()       
            if data == "OK":        # Server acks send_all
                self.acked = True
            else:
                ack = "all\n" + self.name + "\nOK"
                sock.sendto(ack.encode(), self.server_addr)
                sender, msg = data.split("\n", 1)
                print("[Channel-Message %s: %s]" % (sender, msg))
                print(">>> ", end="", flush=True)
        
        elif head == "hello":       # Server checking if client alive
            sock.sendto(b"hello\n", self.server_addr)

    # Receives udp msgs from other clients
    def recv_client(self, buf, addr):
        head, data = buf.decode().split("\n", 1)

        # receive new message
        if head == "msg":
            sock.sendto(b"ok\n", addr)      # ack message received
            known = False
            name, msg = data.split("\n", 1)
            print(name, ": ", msg, "\n>>> ", sep="", end="")

        # ack for a message just sent
        elif head == "ok" and self.dest[1] == addr[0] and self.dest[2] == addr[1]:
            self.acked = True

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
        self.table = json.loads(data)
        print("[Client table updated.]")
        print(tabulate(self.table))
        print(">>> ", end="", flush=True)
    
    def quit(self):
        print(">>> [Server not responding]", flush=True)
        print(">>> [Exiting]", flush=True)
        sock.close()
        os._exit(1)
        