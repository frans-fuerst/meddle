#!/usr/bin/env python3

import zmq
#import capnp

def main():
    context = zmq.Context()

    print("bla")
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        message = socket.recv().decode()
        print(message)
        if message.startswith("hello"):
            socket.send_string("hello " + message[5:])
        if message.startswith("createChannel"):
            print("hello")
            socket.send('abcdef')
        else:

            socket.send('nok')

if __name__ == "__main__":
    main()


