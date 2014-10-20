#!/usr/bin/env python3

import zmq

#!/usr/bin/env python3

import zmq
#import capnp

def main():
    context = zmq.Context()

    # Socket to talk to server
    print("connect to rpc")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    socket.send_string("hello alice")
    message = socket.recv()
    print(message)

    socket.send_string("createChannel bob")
    message = socket.recv()
    print(message)

if __name__ == "__main__":
    main()


