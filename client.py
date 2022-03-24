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


'''class Client:
    def __init__(self, name, server_ip, server_port, client_port):
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port
        self.table = [['name','ip','port','status']]

    def run(name, server_ip, server_port, client_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        if self.register():
            while True:
                print(">>> ", end="")
                data = input()
                if data == "dereg " + self.name:
                    self.dereg()
                    break
                else:
                    next

    def register(self):
        self.sock.connect((self.server_ip, self.server_port))
        self.sock.send(self.name.encode())
        
        register_ack = self.sock.recv(2).decode()
        if register_ack == "OK":
            print(">>> [Welcome, You are registered.]")
        else: 
            print(">>> [Register failed]")
            self.sock.close()
            return False
        
        response = self.sock.recv(1024)
        self.table = pickle.loads(response)
        print(">>> [Client table updated.]")
        print(tabulate(self.table))
        return True

    def dereg(self):
        msg = "dereg" + self.name
        self.sock.send(msg.encode())
        response = self.sock.recv(2).decode()
        if response == "OK":
            print(">>> [You are Offline. Bye.]")
            self.sock.close()'''

            
    