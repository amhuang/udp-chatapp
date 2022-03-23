import socket
import pickle
from _thread import *
from tabulate import tabulate

table = [['name','ip','port','status']]
ThreadCount = 0
host = "127.0.0.1"  #socket.gethostname()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def run(server_port):
    s.bind((host, server_port))
    print("Server is listening...")
    s.listen()

    while True:
        connSock, addr = s.accept()
        print(f"Connected by {addr}")
        name = connSock.recv(1024).decode()
        connSock.sendall(b"OK")
        entry = [name, addr[0], addr[1], 'yes']
        table.append(entry)
        connSock.sendall(pickle.dumps(table))
        
        response = connSock.recv(1024).decode()
        if response == "dereg":
            connSock.send(b"OK")
            name = connSock.recv(1024).decode()
            if dereg(name):
                connSock.send(b"OK")

            
def dereg(name):
    for i in range(len(table)):
        if table[i][0] == name:
            print("Deregistering " + name + " ...")
            table[i][3] = "no"
            return True
    return False
