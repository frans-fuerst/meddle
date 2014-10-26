#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import random
import string
import logging
import json


def publish(socket, participant, channel, text):
    logging.debug("%s publishes to '%s': '%s'" % (participant, channel, text))
    socket.send_multipart([(channel + text).encode(), participant.encode()])
    with open('_%s.log' % channel, 'a') as f:
        f.write("%s: %s: %s: %s" % ("time", channel, participant, text))
        f.write("\n")

def random_string(N):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def handle_tags(socket, channel, text):
    print((text.replace('.', ' ')).split(' '))
    _contained_tags = [x for x in (text.replace('.', ' ')).split(' ') if x[0] == '#']
    logging.info("tags mentioned: %s", _contained_tags)
    for t in _contained_tags:
        socket.send_multipart([("tag%s" % t).encode(), channel.encode()])

def main():
    _context = zmq.Context()
    _next_id = 0

    # todo: should be one structure
    _names = {}  # id   -> name
    _ids = {}    # name -> id

    _channels = {}
    _port_rpc = 32100
    _port_pub = 32101
    
    _rpc_socket = _context.socket(zmq.REP)
    _rpc_socket.bind("tcp://*:%d" % _port_rpc)

    _pub_socket = _context.socket(zmq.PUB)
    _pub_socket.bind("tcp://*:%d" % _port_pub)

    logging.info("meddle server listening on port %d, sending on port %d" %
                    (_port_rpc, _port_pub))

    while True:
        logging.debug("waiting..")
        _message = _rpc_socket.recv_string()
        logging.debug("got '%s' (%s)" % (_message, type(_message)))

        if _message.startswith("hello "):
            _name = _message[6:].strip()
            logging.debug("using name '%s'" % _name)
            if _name in _ids:
                _id = _ids[_name]
            else:
                _id = _next_id
                _next_id += 1
                _names[_id] = _name
                _ids[_name] = _id
            _rpc_socket.send_string("hello %d" % _id)

        elif _message.startswith("create_channel "):
            _channel_name = random_string(10)
            # todo - check collisions
            _rpc_socket.send_string(_channel_name)
            _channels[_channel_name] = None

        elif _message.startswith("get_channels"):
            _rpc_socket.send_string(" ".join(_channels.keys()))

        elif _message.startswith("get_users"):
            print(_ids.keys())
            _rpc_socket.send_string(json.dumps(list(_ids.keys())))

        elif _message.startswith("publish "):
            _sender_id = int(_rpc_socket.recv_string())
            _rpc_socket.send_string("ok")
            _name = _names[_sender_id]
            _channel = _message[8:8 + 10]
            _text = _message[8 + 10 + 1:]
            handle_tags(_pub_socket, _channel, _text)
            publish(_pub_socket, _name, _channel, _text)
            
        else:
            _rpc_socket.send_string('nok')


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (%(thread)d) %(levelname)s %(message)s",
        datefmt="%y%m%d-%H%M%S",
        level=logging.DEBUG)
    logging.addLevelName(logging.CRITICAL, "(CRITICAL)")
    logging.addLevelName(logging.ERROR,    "(EE)")
    logging.addLevelName(logging.WARNING,  "(WW)")
    logging.addLevelName(logging.INFO,     "(II)")
    logging.addLevelName(logging.DEBUG,    "(DD)")
    logging.addLevelName(logging.NOTSET,   "(NA)")
    
    main()


