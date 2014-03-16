import rsa
from multiprocessing import Process, Manager
import socket
import threading
import sys
import ast

lock = threading.RLock()
hostname = socket.gethostname()

def readFromSocketUntil(s, signal="END"):
    data_from_server = ""
    block = ""
    while block.find(signal) == -1:
        block = str(s.recv(64))
        data_from_server += block
    data_from_server += block
        
    data_from_server = data_from_server[:data_from_server.find(signal)]
    return data_from_server
    

def encrypt(message, n, e, userId, svrkey):
    """
    Concatenate the userid with the current message and encrypt it with the keys
    for userId
    """
    
    def pad(s):
        return "x" * (15 - len(s) % 15)

    #encrypt and prepend the username
    msg = rsa.encrypt(pad(message) + message, n, e, 15)
    msg = userId + "||" + ":".join(map(str,msg))

    #encrypt for server second, no name required since every other decryption goes through server anyway
    msg = rsa.encrypt(pad(msg) + msg, svrkey[1], svrkey[0], 15)
    msg = ":".join(map(str,msg))
    return msg
    
def sendData(data):
    tsock = socket.socket()
    port = 8000
    tsock.connect((hostname,port))
    
    if "init" == tsock.recv(4):
        tsock.send("data"+data+"END")
    tsock.close()

def generateCircuit(n, enduser, message, keys, svrkeys):
    if enduser not in keys.keys():
        return None

    #first encrypt for the intended recipient
    ct = encrypt(message, keys[enduser][1], keys[enduser][0], enduser, svrkeys)
    return ct


def user(name, p, msgs, ned):
    """
    Presents user with a menu of options
    Maintains a socket to the server to send requests for data.
    Should open a new connection when sending a message for the first time
    so that the server cannot tell the difference between a relay and 
    the origin of a message
    """
    keys = {}
    s = socket.socket()
    port = 8000
    s.connect((host,port))
    
    if "init" == s.recv(1024):
        print "connection started"
        s.send("user"+name)
        
    svrkeys = map(int,s.recv(1024).split("n")) #e, n

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
        if words == ":ks" or words == ":keys":
            s.send(words)


            #read keylist from server
            keys_from_server = readFromSocketUntil(s)
            keys = ast.literal_eval(keys_from_server)
            for k in keys.keys():
                keys[k] = tuple(map(int,keys[k].split("n")))

            print "Downloaded " + str(len(keys.keys()))  + " keys"

        if words == ":ls":
            s.send(words)
            print "Server: " + s.recv(1024)
        if words.startswith(":send"):
            words = words[6:]
            index = words.find(" ")
            target,msg = words[:index],words[index+1:]
            
            circuit = generateCircuit(5, target, "msg"+name+": "+msg, keys, svrkeys)
            if circuit == None:
                print "Do not have that user's key, try :ks"
            else:
                sendData(circuit)

        if words.startswith(":setkey"):
            with lock:
                s.send(":setkey " + str(ned[1])+"n"+str(ned[0]))
            print "Keys: %s" % s.recv(1024)
        if words.startswith(":genkey"):
            with lock:
                ned = rsa.newKey(10**100,10**101,50)
            print "n = %s\ne = %s\nd = %s\n" % (ned[0],ned[1],ned[2])
            with open('%s.keys' % name, 'w') as f:
                f.write("%d\n%s\n%s\n" %(ned[0],ned[1],ned[2]))

    s.close()
    p.terminate() #kill the worker thread


def decrypt(data,ned):
    """
    decrypt if you know what I mean wink wink nudge nudge
    """
    data = map(int,data.split(":"))
    return rsa.decrypt(data, ned[0], ned[2], 15)


def circuit(name, msgs, ned):
    """This thread listens to the server waiting for data
    The data will always be encrypted with this users public key
    the user should decrypt with private key.
    If the message is intended for this user the result will start with the
    letters msg and the rest will be the message
    otherwise it will be a number encrypted with RSA for the server
    """
    s = socket.socket()
    port = 8000
    s.connect((host,port))

    svrkeys = s.recv(1024)
    if svrkeys.startswith("init"):
        svrkeys = svrkeys[4:]
        s.send("circ"+name)
        
    running = True
    while running:
        d = readFromSocketUntil(s)
        d = decrypt(d, ned)
        d = d.lstrip("x")
        if "msg" == d[:3]: #this message is for us
            msgs.append(d[3:])
        else:
            sendData(d) #this message is still encrypted and should be fowarded

if __name__ == "__main__":
    name = sys.argv[1]
    try:
        hostname = sys.argv[2]
    except:
        hostname = "localhost"
    
    manager = Manager()
    msgs = manager.list()
    
    try:
        with open("%s.keys" % name) as f:
            ned = tuple(map(int,f.read().split("\n")[0:-1]))
            
    except IOError:
        ned = (0,0,0)
        print "No keys found, consider making some with :genkey"

    p = Process(target=circuit,args=(name,msgs,ned))
    p.start()
    user(name, p, msgs, ned)
    
