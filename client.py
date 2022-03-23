import socket
import pickle
from tabulate import tabulate



class Client:
    def __init__(self, name, server_ip, server_port, client_port):
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port
        self.table = [['name','ip','port','status']]

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_ip, self.server_port))
        s.send(self.name.encode())
        
        register_ack = s.recv(2).decode()
        if register_ack == "OK":
            print(">>> [Welcome, You are registered.]")
        else: 
            print(">>> [Register failed]")
        
        response = s.recv(1024)
        self.table = pickle.loads(response)
        print(">>> [Client table updated.]")
        print(tabulate(self.table))

        while True:
            print(">>> ", end="")
            data = input()
            if data == "dereg " + self.name:
                s.send(b"dereg")
                response = s.recv(2).decode()
                if response == "OK":
                    s.send(self.name.encode())
                    response = s.recv(2).decode()
                    if response == "OK":
                        print(">>> [You are Offline. Bye.]")
                        s.close()
                        break
            else:
                next
            
    