#!/usr/bin/env python3

import zmq
import random
import string
#import capnp


def publish(socket, channel, text):
    print("publish to '%s': '%s'" %(channel, text))
    socket.send_string(channel + text)

def random_string(N):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def main():
    context = zmq.Context()
    
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind("tcp://*:5556")

    print("meddle server up")
    rpc_socket = context.socket(zmq.REP)
    rpc_socket.bind("tcp://*:5555")

    while True:
        message = rpc_socket.recv_string()
        print("got '%s' (%s)" % (message, type(message)))
        if message.startswith("hello "):
            rpc_socket.send_string("hello " + message[6:])
        elif message.startswith("createChannel "):
            print("hello")
            rpc_socket.send_string(random_string(10))
        elif message.startswith("publish "):
            rpc_socket.send_string("ok")
            channel = message[8:8 + 10]
            text = message[8 + 10 + 1:]
            publish(pub_socket, channel, text)
        else:
            rpc_socket.send_string('nok')

    for i in range(3):
        time.sleep(1)
        publish(pub_socket, channel, text)

if __name__ == "__main__":
    main()


