#!/usr/bin/env python3

import zmq
#import capnp

def main():
    context = zmq.Context()

    print("bla")
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        message = socket.recv()
        socket.send(b'ok')

if __name__ == "__main__":
    main()


