#!/usr/bin/env python3

import zmq
#import capnp

def request(socket, text):
    socket.send_string(text)
    return socket.recv_string()

def main():
    context = zmq.Context()

    print("connect to rpc")
    rpc_socket = context.socket(zmq.REQ)
    rpc_socket.connect("tcp://localhost:5555")

    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5556")

    answer = request(rpc_socket, "hello alice")
    print(answer)

    answer = request(rpc_socket, "createChannel bob")
    channel = answer

    print("talking on channel '%s'" % channel)

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, channel)

    text = "Text Message"
    answer = request(rpc_socket, "publish %s %s" % (channel, text))

 
#    while True:
    message = sub_socket.recv_string()
    text = message[10:]
    print("got: '%s'" % text)
   

if __name__ == "__main__":
    main()


