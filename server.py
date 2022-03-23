import socket
import pickle
from _thread import *
from tabulate import tabulate

TABLE = [['name','ip','port','status']]
ThreadCount = 0

def run(server_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), server_port))
    print("Server is listening...")
    s.listen()

    while True:
        connSock, addr = s.accept()
        print(f"Connected by {addr}")
        name = connSock.recv(1024).decode()
        connSock.sendall(b"ACK")
        entry = [name, addr[0], addr[1], 'yes']
        TABLE.append(entry)
        msg = pickle.dumps(TABLE)
        connSock.sendall(msg)
        
        #connSock.close()
