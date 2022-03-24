import socket
import pickle
from tabulate import tabulate
import select
import threading

table = [['name','ip','port','status']]
lock = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def run(name, server_ip, server_port, client_port):
    sock.bind((socket.gethostname(), client_port))
    sock.connect((server_ip, server_port))
    register(name)

    receiving_th = threading.Thread(target=receiving, args=())
    receiving_th.start()

    while True:
        print(">>> ", end="")
        data = input()
        if data == "dereg " + name:
            dereg(name)
        elif data == "reg " + name:
            register(name)
        else:
            next

def receiving():
    while True:
        msg = sock.recv(4).decode()
        lock.acquire()
        print("recv code:", msg)
        if msg == '':
            sock.close()
            break 

        if msg == "tab\n":
            table_updated()
        else: 
            msg = sock.recv(1024)
        lock.release()

def table_updated():
    msg = sock.recv(1024)
    print("recv from tab thread:", msg)
    table = pickle.loads(msg)
    #sock.sendall(b"OK")
    #print("sent OK")
    print(">>> [Client table updated.]")
    print(tabulate(table))
    print(">>> ", end="", flush=True)
            

def register(name):
    msg = "reg\n" + name
    sock.sendall(msg.encode())
    register_ack = sock.recv(2).decode()
    if register_ack == "OK":
        print(">>> [Welcome, You are registered.]")
    else: 
        print(">>> [Register failed]")
        sock.close()

def dereg(name):
    msg = "der\n" + name
    sock.sendall(msg.encode())
    response = sock.recv(2).decode()
    if response == "OK":
        print(">>> [You are Offline. Bye.]")