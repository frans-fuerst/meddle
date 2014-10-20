#!/usr/bin/env python3

import zmq
import random
import string
#import capnp


def publish(socket, participant, channel, text):
    print("%s publishes to '%s': '%s'" % (participant, channel, text))
    socket.send_multipart([(channel + text).encode(), participant.encode()])

def random_string(N):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def main():
    _context = zmq.Context()
    _next_id = 0
    _names = {}
    
    _pub_socket = _context.socket(zmq.PUB)
    _pub_socket.bind("tcp://*:5556")

    _rpc_socket = _context.socket(zmq.REP)
    _rpc_socket.bind("tcp://*:5555")

    print("meddle server up")

    while True:
        _message = _rpc_socket.recv_string()
        print("got '%s' (%s)" % (_message, type(_message)))
        if _message.startswith("hello "):
            _name = _message[6:].strip()
            print("'%s'" % _name)
            _names[_next_id] = _name
            _rpc_socket.send_string("hello %d" % _next_id)
            _next_id += 1
        elif _message.startswith("createChannel "):
            _rpc_socket.send_string(random_string(10))
        elif _message.startswith("publish "):
            _sender_id = int(_rpc_socket.recv_string())
            _name = _names[_sender_id]
            _rpc_socket.send_string("ok")
            _channel = _message[8:8 + 10]
            _text = _message[8 + 10 + 1:]
            publish(_pub_socket, _name, _channel, _text)
        else:
            _rpc_socket.send_string('nok')


if __name__ == "__main__":
    main()


