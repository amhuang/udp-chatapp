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

def run(name, server_ip, server_port, client_port):
    global online
    udp.bind((socket.gethostname(), client_port))
    s.bind((socket.gethostname(), client_port))
    s.connect((server_ip, server_port))
    
    # starts thread for receiving msgs from server
    server_comm = threading.Thread(target=recv_server)
    server_comm.start()

    # starts thread for direct chat
    dir_chat = threading.Thread(target=recv_chat, args=())
    dir_chat.start()

    register(name)

    # Processes user input
    while True:
        print(">>>", end=" ", flush=True)
        cmd = input()

        
        if len(cmd) > 5 and cmd[:5] == "send ":
            name, msg = clean_send(cmd[5:])
            send_chat(name, msg)
        
        elif len(cmd) > 9 and cmd[0:9] == "send_all ":
            name = clean_send(cmd[9:], group=True)

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


# Run by server_comm thread. Processes messages from server
def recv_server():
    global online
    while True:
        if online:
            buf = s.recv(4).decode()
            print("from recving:", msg)
            lock.acquire()
            
            if buf == '':   # Server disconnected
                s.close()
                break 

            if buf == "tab\n":
                table_updated()
            
            elif buf == "der\n":
                ack = s.recv(2).decode()
                print("recieved dereg ack", ack)
                if ack == "OK":
                    online = False

            elif buf == "err\n":
                s.sendall(b"err\nOK")

            else: 
                buf = s.recv(1024)
                
            lock.release()

def recv_chat():
    while True:
        buf, addr = udp.recvfrom(1024)
        for row in table:
            if row[1] == addr[0] and row[2] == addr[1]:
                print(row[0], end=": ")
        print(buf.decode())
        print(">>>", end=" ", flush=True)

def send_chat(name, msg):
    recipient = []
    for row in table:
        if row[0] == name:
            recipient = row

    if recipient == []:
        print(">>> [Recipient not found.]")
        return
    elif recipient[3] == "no":
        pass
    
    msg = msg.encode()
    udp.sendto(msg, (recipient[1], recipient[2]))
    print("message sent to", str((recipient[1], recipient[2])))

def register(name):
    global online
    online = True

    lock.acquire()
    print("Registering", name)
    msg = "reg\n" + name
    s.sendall(msg.encode())
    print(">>> [Welcome, You are registered.]", flush=True)
    '''else: 
        print(">>> [Register failed]", flush=True)
        s.close()'''
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
        retry = time.time() + timeout
        while time.time() < retry:
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


def clean_send(data, group=False):
    # strips whitespace off name for group chats
    if group:
        return data.strip()

    # Returns name and msg for direct chats
    data = data.split(" ", 1)
    if len(data) != 2:
        print(">>> [Please specify a message and a recipient.]")
    name = data[0].strip()
    msg = data[1].strip()
    if len(name) == 0:
        print(">>> [Please specify a recipient.]")
    if len(msg) == 0:
        print(">>> [Please enter a message to send.]")
    return name, msg