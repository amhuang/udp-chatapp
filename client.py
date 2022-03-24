import socket
import pickle
from tabulate import tabulate
import select
import threading

table = [['name','ip','port','status']]

def run(name, server_ip, server_port, client_port):
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostname(), client_port))
    sock.connect((server_ip, server_port))

    if register(name):
        #sock.setblocking(0)
        update_th = threading.Thread(target=table_updates, args=())
        update_th.start()

        while True:
            print(">>> ", end="")
            data = input()
            if data == "dereg " + name:
                dereg(name)
            elif data == "reg " + name:
                register(name)
            else:
                next

def table_updates():
    print("listening thread opened")
    while True:
        msg = sock.recv(2048)
        print("recv from tab thread:", msg)
        if msg[0:5] == b"table":
            table = pickle.loads(msg[5:])
            print(">>> [Client table updated.]")
            print(tabulate(table))
            sock.sendall(b"OK")
            print(">>> ", end="")
        elif msg == b'':
            sock.close()

def register(name):
    msg = "reg " + name
    sock.sendall(msg.encode())

    register_ack = sock.recv(2).decode()
    if register_ack == "OK":
        print(">>> [Welcome, You are registered.]")
    else: 
        print(">>> [Register failed]")
        sock.close()
        return False
    
    return True

def dereg(name):
    msg = "dereg " + name
    sock.sendall(msg.encode())
    response = sock.recv(2).decode()
    if response == "OK":
        print(">>> [You are Offline. Bye.]")