##################
# Blow ship server
#################
#Proof of concept, not feature complete.

import ast
import signal
import cPickle as pickle
import rsa
from multiprocessing import Process, Manager
import socket
import threading
import time
import sys

lock = threading.RLock()

def process_client(c, ID_KEY, ID_STATUS, ID_SOCK, ned):
    """
    This function servs as a thread that listens for user input
    """
    c_id = c.recv(1024)
    print c_id + " logged in"
    with lock:
        ID_STATUS[c_id] = True
        ID_SOCK[c_id] = ""

    c.send(str(ned[1])+"n"+str(ned[0]))

    #listen for user input and respond if need be
    running = True
    while running:
        v = c.recv(1024)
        #end user wishes to log out
        if v == ":bye":
            print c_id + " logged out"
            running = False
            c.send("bye")
        #user is sending their public key and n value
        elif v.startswith(":setkey"):
            v = v[7:]
            with lock:
                ID_KEY[c_id] = v
            c.send("reset key to: " + v)
            print c_id + " sent a new public key " + v
        #user wants to know who is online
        elif v.startswith(":ls"):
            print "list requested, sending: %s" % ID_STATUS
            c.send("%sEND" % filter(lambda x: ID_STATUS.get(x, False)  == True,ID_STATUS.keys()))
        #user wants to know all other users keys (including their own)
        elif v.startswith(":ks"):
            print "keys requested, sending: %s" % ID_KEY
            c.send("%sEND" % ID_KEY)


    with lock:
        ID_SOCK[c_id] = None
        ID_STATUS[c_id] = False
    c.close()


def process_circuit(c, ID_KEY, ID_STATUS, ID_SOCK, ned):
    """
    This thread moniters
    """
    c_id = c.recv(1024)

    #every second check if there is a message for user c_id
    #if so send it to them through their circuit socket
    #they will recieve decrypt the message and either
    #1) Keep it if it belongs to them
    #2) Send it back to the server through a new data connection if they cannot read it
    running = True
    while running:
        time.sleep(1)
        d = ID_SOCK[c_id] 
        if d == None:
            running = False
        elif d != "":
            c.send(d+"END")
            ID_SOCK[c_id] = ""

    with lock:
        del ID_SOCK[c_id]

def process_data(c, ID_SOCK, ned):
    """
    Data sent from a client that is being used as a relay
    Decrypt with the server key and look at the attached username
    Put the encrypted portion of the message into the SOCK dictionary
    for that user
    """

    #read data until END
    d = ""
    block = ""
    while block.find("END") == -1:
        block = str(c.recv(64))
        d += block
    d += block
    d = d[:d.find("END")]

    #reformat to integer list
    d = pickle.loads(str(d))
    d = rsa.decrypt(d, ned[0], ned[2], 15)
    d = d.split("||")
    
    name = d[0].lstrip("x")
    #write result to socket for another user to await transfer
    ID_SOCK[name] = d[1] 
    c.close()

def main(data):
    """
    Launches the server with given set of keys (data)
    """
    #this library needs to be replaced
    ned = rsa.newKey(10**100,10**101,50)
    print "Keys\nn = %s\ne = %s\nd = %s\n" % (ned[0],ned[1],ned[2])

    #create thread safe dictionaries
    manager = Manager()
    ID_KEY = manager.dict()
    ID_KEY.update(data) #get saved data
    ID_STATUS = manager.dict()
    ID_SOCK = manager.dict()

    #define an interupt catcher to save data
    def signal_handler(signal, frame):
        print('Saving data')
        #this is ugly but the only reasonable way I could find
        #to unroll a managed threadsafe dictionary to a normal one
        #that can interact with pickle correctly
        with lock:
            with open('serverdata.pkl', 'wb') as f:
                temp = ast.literal_eval(str(ID_KEY))
                pickle.dump( temp, f ) #save the keys
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    #listen on port 8000 (probably a bad choice, usually used for testing web servers) for incoming connections
    s = socket.socket()
    hostname = socket.gethostname()
    port = 8000
    s.bind(('',port))
    s.listen(5)
    
    #listen for incoming connections and start a thread based on what kind it is
    while True:
        c, addr =  s.accept()
        c.send("init")
        v = c.recv(4)
        if "user" == v:
            #incomming connection is a user which will send queries
            Process(target=process_client, args=(c,ID_KEY,ID_STATUS,ID_SOCK, ned)).start()
        elif "circ" == v:
            #incoming connection is to be used as part of a circuit
            Process(target=process_circuit, args=(c,ID_KEY,ID_STATUS,ID_SOCK,ned)).start()
        elif "data" == v:
            #incoming connection has some data for the server to process
            Process(target=process_data, args=(c,ID_SOCK,ned)).start()


if __name__ == "__main__":
    """
    Main function reads previous keys if they exist before launcing the main listening thread
    """
    try: #try to read key data
        with open('serverdata.pkl', 'rb') as f:
            data = pickle.load(f)
    except: #data failed to read
        print "Data not found"
        data = {}

    main(data)
