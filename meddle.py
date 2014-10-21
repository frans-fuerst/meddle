#!/usr/bin/env python3

import zmq
import getpass
from threading import Thread
import sys

def username():
    # todo: format (spaces, etc)
    return getpass.getuser()

def request(socket, text):
    socket.send_string(text)
    return socket.recv_string()

def recieve_messages(socket, channel):
    socket.setsockopt_string(zmq.SUBSCRIBE, channel)
    while True:
        message = socket.recv_string()
        name = socket.recv_string()
        text = message[10:]
        print("%s: '%s'" % (name, text))

def publish(socket, my_id, channel, text):
    socket.send_multipart([("publish %s %s" % (channel, text)).encode(),
                            my_id.encode(),])
    answer = socket.recv_string()
    return answer

def main():
    context = zmq.Context()

    print("connect to rpc")

    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:7001")

    rpc_socket = context.socket(zmq.REQ)
    rpc_socket.connect("tcp://localhost:7000")

    answer = request(rpc_socket, "hello %s" % username())
    my_id = answer[6:]
    print("server: calls us '%s'" % my_id)

    answer = request(rpc_socket, "get_channels")
    _channels = answer.split()
    print("channels: %s" % _channels)

    if _channels == []:
        answer = request(rpc_socket, "createChannel bob")
        channel = answer
    else:
        channel = _channels[0]

    print("talking on channel '%s'" % channel)
    _thread = Thread(target=lambda: recieve_messages(sub_socket, channel))
    _thread.daemon = True
    _thread.start()

    while True:
        text = sys.stdin.readline().strip('\n')
        if text in ('quit', 'exit'):
            sys.exit(0)
        if text.strip() == "":
            continue
        answer = publish(rpc_socket, my_id, channel, text)
   

if __name__ == "__main__":
    main()


