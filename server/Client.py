from multiprocessing import Process, Manager
import socket
import threading
import sys
import ast

lock = threading.RLock()

def encrypt(data, key):
    return data

def generateCircuit(n, enduser, message, keys):
    if enduser not in keys.keys():
        return None

    msg = enduser+"||"+encrypt("msg"+message, keys[enduser])
    return msg    

def user(name, p, msgs):
    keys = {}
    s = socket.socket()
    host = socket.gethostname()
    port = 8000
    s.connect((host,port))
    
    if "init" == s.recv(1024):
        print "connection started"
        s.send("user"+name)

    running = True
    while running:

        with lock:
            for m in msgs:
                print m
            del msgs[:]
        words = raw_input("Enter a command: ")
        if words == ":bye" or words == ":logoff" or words == ":logout":
            s.send(":bye")
            running = False
        if words == ":flush":
            keys = {}
            print "flushed keys"
        if words == ":ks":
            s.send(words)
            keys_from_server = s.recv(1024)
            print "Server: " + keys_from_server
            keys = ast.literal_eval(keys_from_server)
        if words == ":ls":
            s.send(words)
            print "Server: " + s.recv(1024)
        if words.startswith(":send"):
            words = words[6:]
            index = words.find(" ")
            target,msg = words[:index],words[index+1:]
            
            circuit = generateCircuit(5, target, name+": "+msg, keys)
            if circuit == None:
                print "Do not have that user's key, try :ks"
            else:
                s.send(circuit)
        if words.startswith(":setkey"):
            s.send(words)
            print "Keys: %s" % s.recv(1024)

    s.close()
    p.terminate()


def decrypt(data):
    """
    decrypt if you know what I mean wink wink nudge nudge
    """
    return data

def circuit(name, msgs):
    s = socket.socket()
    host = socket.gethostname()
    port = 8000
    s.connect((host,port))

    if "init" == s.recv(4):
        s.send("circ"+name)
        
    running = True
    while running:
        d = s.recv(1024)
        d = decrypt(d)
        if "msg" == d[0:3]:
            message = d[3:]
            with lock:
                msgs.append(message)
        else:
            tsock = socket.socket()
            tsock.connect((host,port))
            
            if "init" == tsock.recv(4):
                tsock.send("data"+d)
            tsock.close()
        

if __name__ == "__main__":
    name = sys.argv[1]
    
    manager = Manager()
    msgs = manager.list()

    p = Process(target=circuit,args=(name,msgs))
    p.start()
    user(name, p, msgs)
    
