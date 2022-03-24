import socket
import pickle
import threading
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
        th = threading.Thread(target=new_client, args=(connSock, addr,))
        th.start()
        print("Threads:", threading.active_count())

    s.close()

def new_client(connSock, addr):
    while True:
        response = connSock.recv(1024).decode()
        print("response:", response)

        if response[0:4] == "reg ":
            name = response[4:].strip()
            register(connSock, addr, name)
            next

        elif response[0:6] == "dereg ":
            name = response[6:].strip()
            print(name)
            if dereg(name):
                connSock.send(b"OK")

def register(connSock, addr, name):
    for i in range(len(table)):
        if table[i][0] == name:
            connSock.send(b"OK")
            table[i][3] = "yes"
            connSock.sendall(pickle.dumps(table))
            print(tabulate(table))
            return 
    
    connSock.send(b"OK")
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    connSock.sendall(pickle.dumps(table))
    print(tabulate(table))
            
def dereg(name):
    for i in range(len(table)):
        if table[i][0] == name:
            print("Deregistering " + name + " ...")
            table[i][3] = "no"
            print(tabulate(table))
            return True
    return False
