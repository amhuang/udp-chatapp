import socket
import pickle
from tabulate import tabulate

class Client:
    def __init__(self, name, server_ip, server_port, client_port):
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_ip, self.server_port))
        s.send(self.name.encode())
        
        response = s.recv(1024)
        table = pickle.loads(response)
        print(tabulate(table))
        s.close()

        '''print(">>> ", end="")
        data = input()
        s.send(data.encode())
        response = s.recv(1024).decode()
        print(f"Received {response!r}")
'''
        
            
    