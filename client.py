import socket
import json
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
        self.port = client_port

        self.table = []     # Data format: ['name','ip', port,'status']
        self.online = False
        self.server_connected = True
        self.acked = False
        self.receiving = False
        self.prompt = False

    def run(self):
        sock.bind((socket.gethostname(), self.port))
        print(">>> ", end="")
        recv_th = threading.Thread(target=self.recv)
        recv_th.start()
        self.register()
        self.process_input()

    def process_input(self):
        while True:
            cmd = input(">>> ")
            if self.receiving:
                continue

            if len(cmd) > 6 and cmd[:6] == "dereg ":
                if cmd[6:].strip() == self.name and self.online:
                    self.deregister()
                else:
                    print(">>> [You can only deregister yourself.]")
                
            elif len(cmd) > 4 and cmd[:4] == "reg ":
                if cmd[4:].strip() == self.name and not self.online:
                    self.register()
                elif self.online:
                    print(">>> [Client already registered.]", flush=True)
                else:
                    print(">>> [You can only register as yourself.]", flush=True)
            
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
        timeout = time.time() + 0.5
        while time.time() < timeout:
            if self.table != []:
                print("[Welcome, You are registered.]", flush=True)
                return
        print("[Register failed.]")
        self.online = False
        

    def deregister(self):
        msg = b"dereg\n" + self.name.encode()
        
        # Attempt to send dereg 5 times
        for i in range(5):
            sock.sendto(msg, self.server_addr)
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if not self.online:
                    print(">>> [You are offline. Bye.]", flush=True)
                    return
            print("retrying dereg", i+2)
        
        if self.online:
            print(">>> [Server not responding]", flush=True)
            self.quit()

    def send(self, name, msg):
        self.dest = []
        self.acked = False
        
        # Check recipient status
        for row in self.table:
            if row[0] == name:
                self.dest = row
        if len(self.dest) == 0:
            print(">>> [Recipient",name,"unknown.]")
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

        # Up to 5 attempts to get an ack from server
        for i in range(5):
            sock.sendto(formatted.encode(), self.server_addr)
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if self.acked:
                    print(">>> [Message received by Server.]")
                    return
        if not self.acked:
            print(">>> [Server not responding.]")
    
    def send_offline(self, msg):
        self.acked = False

        msg = "save\n" + self.dest[0] + "\n" + msg
        
        for i in range(5):
            sock.sendto(msg.encode(), self.server_addr)
            timeout = time.time() + 0.5
            while time.time() < timeout:
                if self.acked:
                    print(">>> [Messages received by the server and saved]", flush=True)
                    return
            
        if not self.acked:
            print(">>> [Server not responding]", flush=True)
            self.quit()
            
    # Run by server_comm thread. Processes UDP messages from server
    def recv(self):
        while True:
            buf, addr = sock.recvfrom(2048)
            if self.online and addr == self.server_addr:
                self.recv_server(buf)
            elif self.online:
                self.recv_client(buf, addr)
    
    def recv_server(self, buf):
        head, data = buf.decode().split("\n", 1)

        if head == "table":       
            self.table_update(data)
        
        elif head == "reg":
            if data == "ERR":
                print("[The client name", self.name, "is taken. Try a different name.]")
                self.quit()
        
        elif head == "dereg":       # Server acks dereg (successful)  
            if data == "ACK":
                self.online = False
        
        elif head == "save":        # Receive saved messages, acks for saving msgs
            if data == "ACK":
                self.acked = True
            elif data == "ERR":
                print("[Client %s exists!!]" % self.dest[0], flush=True)
            #print(">>> ", end="", flush=True)
        
        elif head == "saved":     # Saved messages upon returning online
            if data == "\t":        # indicates start of a batch of saved msgs
                print("[You have messages]")
                self.receiving = True
            elif data == "\n":
                self.receiving = False
            else:
                print(">>>", data)
        
        elif head == "all":  
            if data == "ACK":        # Server acks send_all
                self.acked = True
            else:
                ack = "all\n" + self.name + "\nACK"
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
        elif head == "ack" and self.dest[1] == addr[0] and self.dest[2] == addr[1]:
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
        print("[Client table updated.]", flush=True)
        print(">>> ", end="", flush=True)
    
    def quit(self):
        print(">>> [Exiting]")
        sock.close()
        os._exit(1)
        