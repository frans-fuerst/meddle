#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import getpass
from threading import Thread
import sys
import pymeddle
import logging
from optparse import OptionParser

def username():
    # todo: format (spaces, etc)
    return getpass.getuser()

def request(socket, text):
    socket.send_string(text)
    return socket.recv_string()


class base:

    def __init__(self, handler):
        self.context = zmq.Context()
        self._handler = handler
        self._my_id = 0
        self._subscriptions = []

    def connect(self, server, port):
        _thread = Thread(target=lambda: self.rpc_thread(server, port))
        _thread.daemon = True
        _thread.start()

    def subscriptions(self):
        return self._subscriptions

    def rpc_thread(self, server, port):

        logging.info("connect to rpc tcp://%s:%d" % (server, port))
        self._rpc_socket = self.context.socket(zmq.REQ)
        self._rpc_socket.connect("tcp://%s:%d" % (server, port))

        sub_socket = self.context.socket(zmq.SUB)
        sub_socket.connect("tcp://%s:%d" % (server, port + 1))

        answer = request(self._rpc_socket, "hello %s" % username())
        self._my_id = answer[6:]
        logging.info("server: calls us '%s'" % self._my_id)

        answer = request(self._rpc_socket, "get_channels")
        _channels = answer.split()
        logging.info("channels: %s" % _channels)

        if _channels == []:
            answer = request(self._rpc_socket, "createChannel bob")
            self._subscriptions.append(answer)
        else:
            self._subscriptions.append(_channels[0])

        self._handler.meddle_on_update()

        logging.info("talking on channel '%s'" % self._subscriptions[0])
        _thread = Thread(target=lambda: self.recieve_messages(sub_socket, self._subscriptions[0]))
        _thread.daemon = True
        _thread.start()

        while True:
            text = sys.stdin.readline().strip('\n')
            if text in ('quit', 'exit'):
                sys.exit(0)
            if text.strip() == "":
                continue
            answer = self.publish(self._subscriptions[0], text)

    def publish(self, channel, text):
        self._rpc_socket.send_multipart([("publish %s %s" % (self._subscriptions[0], text)).encode(),
                                self._my_id.encode(),])
        answer = self._rpc_socket.recv_string()
        return answer

    def recieve_messages(self, socket, channel):
        socket.setsockopt_string(zmq.SUBSCRIBE, channel)
        while True:
            message = socket.recv_string()
            name = socket.recv_string()
            text = message[10:]
            logging.info("incoming message %s: '%s'" % (name, text))
            self._handler.meddle_on_message(name, text)


def main():
    pass   

if __name__ == "__main__":
    main()


