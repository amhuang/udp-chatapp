import socket
import pickle
import threading
import select
from tabulate import tabulate

table = [['name','ip','port','status']]
ThreadCount = 0
host = "127.0.0.1"  #socket.gethostname()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = []

def run(server_port):
    s.bind((host, server_port))
    print("Server is listening...")
    s.listen()
    lock = threading.Lock()

    while True:
        connSock, addr = s.accept()
        clients.append((connSock, addr))

        response = connSock.recv(1024).decode()
        if response[0:4] == "reg ":
            name = response[4:].strip()
            register(connSock, addr, name)
            broadcast_table()
        
        print(f"Connected by {addr}")
        th = threading.Thread(target=new_client, args=(connSock, addr, lock,))
        th.start()
        print("Threads:", threading.active_count())

    s.close()

def new_client(connSock, addr, lock):
    while True:
        
        response = connSock.recv(1024)
        if not response:
            connSock.close()
            break
        else:
            response = response.decode()

        print("from " +str(addr)+ ":", response)

        if response[0:4] == "reg ":
            name = response[4:].strip()
            register(connSock, addr, name)
            lock.acquire()
            broadcast_table()
            lock.release()

        elif response[0:6] == "dereg ":
            name = response[6:].strip()
            print(name)
            if dereg(connSock, name):
                connSock.sendall(b"OK")
        
            

def register(connSock, addr, name):
    for i in range(len(table)):
        if table[i][0] == name:
            connSock.sendall(b"OK")
            table[i][3] = "yes"
            print("update registration\n", tabulate(table))
    
    connSock.sendall(b"OK")
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    print("new registration\n", tabulate(table))
    

def broadcast_table():
    print("table broacasted\n", tabulate(table))
    pkl = pickle.dumps(table)
    for sock, addr in clients:
        #try:
        print("broadcasting to " + str(addr))
        sock.sendall(b"table" + pkl)
        response = sock.recv(2).decode()
        print("response from broadcast" , response)
        if response == "OK":
            next
            '''if not client_ack(connSock, timeout=1):
                for i in range(len(table)):
                    if table[i][1] == addr[0] and table[i][2] == addr[1]:
                        table[i][3] == "no"
                        print(tabulate(table))
                        break'''

        '''except OSError:
            for i in range(len(table)):
                if table[i][1] == addr[0] and table[i][2] == addr[1]:
                    table[i][3] == "no"
                    print(tabulate(table))
                    break'''
    print("done broadcasting")
    return
    '''if not client_ack(connSock, timeout=1):
        for i in range(len(table)):
            if table[i][1] == addr[0] and table[i][2] == addr[1]:
                table[i][3] == "no"
                print(tabulate(table))
                break'''

def client_ack(connSock, timeout=-1):
    response = connSock.recv(2).decode()
    print("response from broadcast" , response)
    if response == "OK":
        return True

    '''if timeout > 0:
        ready = select.select([connSock], [], [], timeout)
        if ready[0]:
            response = connSock.recv(2).decode()
            connSock.setblocking(1)
            if response == "OK":
                return True
    else: '''
        
        
    return False

def dereg(connSock, name):
    for i in range(len(table)):
        if table[i][0] == name:
            print("Deregistering " + name + " ...")
            table[i][3] = "no"
            broadcast_table()
            print(tabulate(table))
            return True
    return False
