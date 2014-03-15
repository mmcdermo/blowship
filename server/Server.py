from multiprocessing import Process, Manager
import socket
import threading
import time
import sys

lock = threading.RLock()

def decrypt(data):
    return data

def process_client(c, ID_KEY, ID_STATUS, ID_SOCK):
    c_id = c.recv(1024)
    print c_id + " logged in"
    with lock:
        ID_STATUS[c_id] = True
        ID_SOCK[c_id] = ""

    running = True
    while running:
        v = c.recv(1024)
        if v == ":bye":
            print c_id + " logged out"
            running = False
            c.send("bye")
        elif v.startswith(":setkey"):
            v = v[7:]
            v = v.strip()
            with lock:
                ID_KEY[c_id] = v
            c.send("reset key to: " + v)
            print c_id + " sent a new public key " + v
        elif v.startswith(":ls"):
            print "list requested, sending: %s" % ID_STATUS
            c.send("%s" % filter(lambda x: ID_STATUS.get(x, False)  == True,ID_STATUS.keys()))
        elif v.startswith(":ks"):
            print "keys requested, sending: %s" % ID_KEY
            c.send("%s" % ID_KEY)
        else:
            print "Got message: " + v
            v = decrypt(v)
            index = v.find("||")
            forward,body = v[:index],v[index+2:]
            print "sending " + body
            with lock:
                ID_SOCK[forward] = body


    with lock:
        ID_SOCK[c_id] = None
        ID_STATUS[c_id] = False
    c.close()


def process_circuit(c, ID_KEY, ID_STATUS, ID_SOCK):
    c_id = c.recv(1024)

    running = True
    while running:
        time.sleep(1)
        d = ID_SOCK[c_id] 
        if d == None:
            running = False
        elif d != "":
            c.send(d)
            ID_SOCK[c_id] = ""

    with lock:
        del ID_SOCK[c_id]

def process_data(c, ID_SOCK):
    c_id = c.recv(4)
    d = c.recv(1024)
    ID_SOCK[c_id] = decrypt(d)
    c.close()

def main():
    manager = Manager()
    ID_KEY = manager.dict()
    ID_STATUS = manager.dict()
    ID_SOCK = manager.dict()

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    hostname = socket.gethostname()
    port = 8000
    s.bind((hostname,port))
    s.listen(5)
    
    while True:
        c, addr =  s.accept()
        c.send("init")
        v = c.recv(4)
        if "user" == v:
            Process(target=process_client, args=(c,ID_KEY,ID_STATUS,ID_SOCK)).start()
        elif "circ" == v:
            print "starting circ thread"
            Process(target=process_circuit, args=(c,ID_KEY,ID_STATUS,ID_SOCK)).start()
        elif "data" == v:
            Process(target=process_data, args=(c,ID_SOCK))


if __name__ == "__main__":
    main()
