import socket
import pickle
from tabulate import tabulate
import select

table = [['name','ip','port','status']]

def run(name, server_ip, server_port, client_port):
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostname(), client_port))
    sock.connect((server_ip, server_port))

    if register(name):
        #sock.setblocking(0)
        while True:
            print(">>> ", end="")
            data = input()
            if data == "dereg " + name:
                dereg(name)
            elif data == "reg " + name:
                register(name)
            else:
                next

def register(name):
    msg = "reg " + name
    sock.send(msg.encode())

    register_ack = sock.recv(2).decode()
    if register_ack == "OK":
        print(">>> [Welcome, You are registered.]")
    else: 
        print(">>> [Register failed]")
        sock.close()
        return False
    
    response = sock.recv(1024)
    table = pickle.loads(response)
    print(">>> [Client table updated.]")
    print(tabulate(table))
    return True

def dereg(name):
    msg = "dereg " + name
    sock.send(msg.encode())
    response = sock.recv(2).decode()
    if response == "OK":
        print(">>> [You are Offline. Bye.]")