import socket
import pickle
import threading
import select
from tabulate import tabulate

table = [['name','ip','port','status']]
table_updated = False     
ThreadCount = 0
host = "127.0.0.1"  #socket.gethostname()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = []
buf = ""
lock = threading.Lock()


# Called by app.py to start server
def run(server_port):
    s.bind((host, server_port))
    s.listen()
    print("Server is listening...")

    # Listen for new connections
    while True:
        connSock, addr = s.accept()
        print(f"Connected by {addr}")
        '''register(connSock, addr)
        broadcast_table()'''

        client_th = threading.Thread(target=new_client, args=(connSock, addr, lock,))
        client_th.start()

    '''while True:
        response = connSock.recv(1024).decode()
        if response[0:4] == "reg ":
            name = response[4:].strip()
            register(connSock, addr, name)
            broadcast_table()
        
        th = threading.Thread(target=new_client, args=(connSock, addr, lock,))
        th.start()
        print("Threads:", threading.active_count())'''
    #s.close()

def broadcast_table():
    #lock.acquire()
    print("table broacasted\n", tabulate(table))
    pkl = pickle.dumps(table)

    for client in clients:
        sock, addr = client[0], client[1]
        print("broadcasting to " + str(addr))
        sock.sendall(b"tab\n" + pkl)
        '''buf = sock.recv(3)
        print("response from broadcast" , buf)'''
    print("broadcast done")
    
    #lock.release()


def new_client(connSock, addr, lock):
    global buf
    while True:
        buf = connSock.recv(4)
        # Stop threads to proceess input one client at time
        lock.acquire()

        if not buf:
            close_conn(connSock)
            break
        
        buf = buf.decode()
        print("from " +str(addr)+ ":", buf)

        if buf == "reg\n":
            register(connSock, addr)
            broadcast_table()

        '''elif response[0:6] == "der\n":
            name = connSock.recv(1024).decode()
            print(name)
            if dereg(connSock, name):
                connSock.sendall(b"OK")'''
        lock.release()


def register(connSock, addr):
    #lock.acquire()
    buf = name = connSock.recv(1024).decode()
    print("registering", name)
    clients.append((connSock, addr, name))
    
    # Check for client name in table
    for i in range(len(table)):
        if table[i][0] == name:
            table[i][3] = "yes"
            print("update registration\n", tabulate(table))
            connSock.sendall(b"OK")
            lock.release()
            return
    
    # If client new, add entry to table
    entry = [name, addr[0], addr[1], 'yes']
    table.append(entry)
    print("new registration\n", tabulate(table))
    connSock.sendall(b"OK")
    #lock.release()
    
def dereg(connSock, name):
    for i in range(len(table)):
        if table[i][0] == name:
            print("Deregistering " + name + " ...")
            table[i][3] = "no"
            broadcast_table()
            print(tabulate(table))
            return True
    return False

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

def close_conn(connSock):
    lock.acquire()
    name = ""
    for client in range(len(clients)):
        if client[0] == connSock:
            name = client[2]
            clients.remove(client)
    for row in table:
        if row[0] == name:
            row[3] = "no"
    lock.release()
    connSock.close()
