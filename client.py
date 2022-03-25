import socket
import pickle
from tabulate import tabulate
import select
import threading
import time
import sys

s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lock = threading.Lock()

table = [['name','ip','port','status']]
online = True
msg_ack = False

recipient = []

def run(name, server_ip, server_port, client_port):
    global online
    c_sock.bind((socket.gethostname(), client_port))
    s_sock.bind((socket.gethostname(), client_port))
    s_sock.connect((server_ip, server_port))
    
    # starts thread for receiving msgs from server
    server_comm = threading.Thread(target=recv_server)
    server_comm.start()

    # starts thread for direct chat
    dir_chat = threading.Thread(target=recv_client, args=())
    dir_chat.start()

    register(name)

    # Processes user input
    while True:
        cmd = input(">>> ")
        
        if len(cmd) > 5 and cmd[:5] == "send ":
            name, msg = clean_input(cmd[5:])
            if name and msg:
                send_msg(name, msg)
        
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
            try:
                buf = s_sock.recv(4).decode()
            except ConnectionResetError:
                print("recv server err")
                server_disconnect()

            print("from recving:", buf)
            lock.acquire()
            
            if buf == '':   # Server disconnected
                s_sock.close()
                break 

            # Updated table
            if buf == "tab\n":
                table_updated()
            
            # Deregister ack (successful)
            elif buf == "der\n":
                ack = s_sock.recv(2).decode()
                if ack == "OK":
                    online = False
            
            # Receive saved messages or acks for saving msgs
            elif buf == "sav\n":
                recv_saved()

            # Error message from server
            elif buf == "err\n":
                server_error()
            else: 
                buf = s_sock.recv(1024)

            lock.release()

# Receives udp msgs from other clients
def recv_client():
    global recipient, msg_ack, online
    while True:
        buf, addr = c_sock.recvfrom(1024)
        if online:
            buf = buf.decode()
            print("udp recvd", buf)

            # ack for a message just sent
            if buf == "ack\n" and recipient[1] == addr[0] and recipient[2] == addr[1]:
                msg_ack = True

            # receive new message
            elif len(buf) > 4 and buf[0:4] == "msg\n":
                recv_msg(buf[4:], addr)

def recv_msg(msg, addr):
    c_sock.sendto(b"ack\n", addr)      # ack message received
    known = False
    for row in table:
        if row[1] == addr[0] and row[2] == addr[1]:
            print(row[0], ": ", msg, sep="")
            known = True
    if not known:
        print("Unknown sender:", msg)

def recv_saved():
    global recipient
    buf = s_sock.recv(1024).decode()
    print("server ack received", buf)
    if buf == "OK":
        print(">>> [Messages received by the server and saved]\n>>> ")
    elif buf == "ERR":
        print(">>> [Client %s exists!!]" % recipient[0])

def server_error():
    try:
        s_sock.sendall(b"err\nOK")
    except:
        server_disconnect()


def send_msg(name, msg):
    global msg_ack, recipient

    lock.acquire()
    recipient = []
    msg_ack = False
    
    # Check recipient status
    for row in table:
        if row[0] == name:
            recipient = row
    if len(recipient) == 0:
        print(">>> [Recipient unknown.]")
        lock.release()
        return
    if True:
    #if recipient[3] == "no":
        save_msg(msg)    # offline message
        lock.release()
        return
    
    msg_bytes = b"msg\n" + msg.encode()
    c_sock.sendto(msg_bytes, (recipient[1], recipient[2]))
    timeout = time.time() + 0.5
    while time.time() < timeout:
        if msg_ack:
            print("message sent to", str((recipient[1], recipient[2])))
            break
    
    if msg_ack:
        print(">>> [Message received by %s.]" % recipient[0])
    else:
        print(">>> [No ACK from %s, message sent to server.]" % recipient[0])
        save_msg(msg)
    lock.release()
            
def save_msg(msg):
    global recipient, msg_ack
    msg_ack = False

    msg = "sav\n" + recipient[0] + "\n" + msg
    print("sending server",msg)
    
    try:
        s_sock.sendall(msg.encode())
    except:
        server_disconnect()


def register(name):
    global online
    online = True

    lock.acquire()
    msg = "reg\n" + name
    try:
        s_sock.sendall(msg.encode())
    except:
        server_disconnect()
    print(">>> [Welcome, You are registered.]", flush=True)
    # Releases lock acquired when deregistering
    lock.release()


def dereg_timeout(name):
    global online
    msg = b"der\n" + name.encode()
    def send_dereg():
        try:
            s_sock.sendall(msg)
        except:
            server_disconnect()
        
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
        if not online:  # dereg attempt successful
            break
    
    if not online:
        print(">>> [You are Offline. Bye.]", flush=True)
    else: 
        server_disconnect()


def table_updated():
    global table
    msg = s_sock.recv(1024)
    table = pickle.loads(msg)
    print(">>> [Client table updated.]")
    print(tabulate(table))
    print(">>>", end=" ", flush=True)

def server_disconnect():
    print(">>> [Server not responding]", flush=True)
    print(">>> [Exiting]", flush=True)
    s_sock.close()
    exit(1)

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