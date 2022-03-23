import socket
import pickle
from tabulate import tabulate

TABLE = [['name','ip','port','status']]

def run(server_port):
    HOST = "127.0.0.1"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, server_port))
    s.listen()

    print("The server is ready.")
    while True:
        connSock, addr = s.accept()
        print(f"Connected by {addr}")
        name = connSock.recv(1024).decode()
        if not name:
            print("No data received")
        else:
            entry = [name, addr[0], addr[1], 'yes']
            TABLE.append(entry)
        
        print(tabulate(TABLE))
        msg = pickle.dumps(TABLE)
        connSock.sendall(msg)
        #connSock.close()
