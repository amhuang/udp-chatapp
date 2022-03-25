import socket
import pickle
from tabulate import tabulate
import select
import threading
import time

import sys

table = [['name','ip','port','status']]
lock = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
online = False
exit = False

def run(name, server_ip, server_port, client_port):
    global online
    sock.bind((socket.gethostname(), client_port))
    sock.connect((server_ip, server_port))
    register(name)

    receiving_th = threading.Thread(target=receiving, args=())
    receiving_th.start()

    while True:
        print(">>> ", end="", flush=True)
        data = input()
        if data == "dereg " + name and online:
            print("deregistering", name)
            dereg(name)
            
        elif data == "reg " + name:
            if not online:
                print("registering", name)
                register(name)
            else:
                print(">>> [Client already registered.]")

def receiving():
    global online, exit
    while True:

        if online:
            msg = sock.recv(4).decode()
            if exit: 
                sys.exit(1)
                
            print("from recving:", msg)
            lock.acquire()
            
            if msg == '':   # Server disconnected
                sock.close()
                break 

            if msg == "tab\n":
                table_updated()
            elif msg == "der\n":
                ack = sock.recv(2).decode()
                print("recieved dereg ack", ack)
                if ack == "OK":
                    online = False
            else: 
                msg = sock.recv(1024)
            lock.release()
            print("recv lock released")

def table_updated():
    msg = sock.recv(1024)
    table = pickle.loads(msg)
    print(">>> [Client table updated.]")
    print(tabulate(table))
            

def register(name):
    global online
    online = True

    lock.acquire()
    print("Registering", name)
    msg = "reg\n" + name
    sock.sendall(msg.encode())
    print(">>> [Welcome, You are registered.]", flush=True)
    '''else: 
        print(">>> [Register failed]", flush=True)
        sock.close()'''
    # Releases lock acquired when deregistering
    lock.release()

def dereg(name):
    global online, exit
    msg = ("der\n" + name).encode()

    def send_dereg():
        sock.sendall(msg)
        
    # Attempt to send dereg 5 times
    timeout = 1
    
    for i in range(5):
        t = threading.Timer(timeout, send_dereg)
        t.start()
        retry = time.time() + timeout
        while time.time() < retry:
            if not online:
                t.cancel()
                break
        print("retrying dereg", i+1)
        if not online:
            break
    
    if not online:
        print(">>> [You are Offline. Bye.]", flush=True)
    else: 
        print(">>> [Server not responding]", flush=True)
        print(">>> [Exiting]", flush=True)
        sock.close()
        exit = True
        sys.exit(1)
