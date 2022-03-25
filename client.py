import socket
import pickle
from tabulate import tabulate
import select
import threading
import time

import sys

table = [['name','ip','port','status']]
lock = threading.Lock()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
online = True
msg_ack = False
recipient = []

def run(name, server_ip, server_port, client_port):
    global online
    udp.bind((socket.gethostname(), client_port))
    s.bind((socket.gethostname(), client_port))
    s.connect((server_ip, server_port))
    
    # starts thread for receiving msgs from server
    server_comm = threading.Thread(target=recv_server)
    server_comm.start()

    # starts thread for direct chat
    dir_chat = threading.Thread(target=recv_client, args=())
    dir_chat.start()

    register(name)

    # Processes user input
    while True:
        print(">>>", end=" ", flush=True)
        cmd = input()
        
        if len(cmd) > 5 and cmd[:5] == "send ":
            print(cmd[5:])
            name, msg = clean_input(cmd[5:])
            if name and msg:
                send_chat(name, msg)
        
        elif len(cmd) > 9 and cmd[0:9] == "send_all ":
            name = clean_input(cmd[9:], group=True)

        elif cmd == "dereg " + name and online:
            print("deregistering", name)
            dereg_timeout(name)
            
        elif cmd == "reg " + name:
            if not online:
                register(name)
            else:
                print(">>> [Client already registered.]")

        elif cmd == "help":
            help_msg = 'CHATAPP COMMANDS\n\tsend <name> <message>   Direct chat: end a message to one user\n\tsend_all <message>      Group chat: send message to all clients\n\tdereg <nickname>        Deregister (go offline)\n\treg <nickname>          Re-register (return online)'
            print(help_msg)


# Run by server_comm thread. Processes TCP messages from server
def recv_server():
    global online
    while True:
        if online:
            buf = s.recv(4).decode()
            print("from recving:", buf)
            lock.acquire()
            
            if buf == '':   # Server disconnected
                s.close()
                break 

            if buf == "tab\n":
                table_updated()
            
            elif buf == "der\n":
                ack = s.recv(2).decode()
                if ack == "OK":
                    online = False

            elif buf == "err\n":
                s.sendall(b"err\nOK")

            else: 
                buf = s.recv(1024)

            lock.release()

# Receives UDP from other clients
def recv_client():
    global recipient, msg_ack
    while True:
        buf, addr = udp.recvfrom(1024)
        buf = buf.decode()
        print("udp recvd", buf)

        if buf == "ack\n" and recipient[1] == addr[0] and recipient[2] == addr[1]:
            msg_ack = True
        elif len(buf) > 4 and buf[0:4] == "msg\n":
            new_chat(buf[4:], addr)

        print(">>>", end=" ", flush=True)

def new_chat(msg, addr):
    udp.sendto(b"ack\n", addr)      # ack message received
    for row in table:
        if row[1] == addr[0] and row[2] == addr[1]:
            print(row[0], end=": ")
    print(msg)
    

def send_chat(name, msg):
    global msg_ack, recipient
    lock.acquire()
    msg_ack = False
    
    for row in table:
        if row[0] == name:
            recipient = row

    if recipient == []:
        print(">>> [Recipient not found.]")
        lock.release()
        return
    
    elif recipient[3] == "no":
        pass    # offline message
    
    msg = b"msg\n" + msg.encode()
    udp.sendto(msg, (recipient[1], recipient[2]))
    timeout = time.time() + 0.5
    while time.time() < timeout:
        if msg_ack:
            print("message sent to", str((recipient[1], recipient[2])))
            break
    if not msg_ack:
        print("message not delivered")
    
    lock.release()
            


def register(name):
    global online
    online = True

    lock.acquire()
    msg = "reg\n" + name
    s.sendall(msg.encode())
    print(">>> [Welcome, You are registered.]", flush=True)
    # Releases lock acquired when deregistering
    lock.release()


def dereg_timeout(name):
    global online
    msg = ("der\n" + name).encode()

    def send_dereg():
        s.sendall(msg)
        
    # Attempt to send dereg 5 times
    timeout = 1
    send_dereg()
    for i in range(5):
        t = threading.Timer(timeout, send_dereg)
        t.start()
        timeout = time.time() + 0.5
        while time.time() < timeout:
            if not online:
                t.cancel()
                break
        print("retrying dereg", i+2)
        if not online:
            break
    
    if not online:
        print(">>> [You are Offline. Bye.]", flush=True)
    else: 
        print(">>> [Server not responding]", flush=True)
        print(">>> [Exiting]", flush=True)
        s.close()
        exit = True
        sys.exit(1)


def table_updated():
    global table
    msg = s.recv(1024)
    table = pickle.loads(msg)
    print(">>> [Client table updated.]")
    print(tabulate(table))
    print(">>>", end=" ", flush=True)


def clean_input(data, group=False):
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