#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import getpass
from threading import Thread
import sys
import pymeddle
import logging
from optparse import OptionParser


def system_username():
    # todo: format (spaces, etc)
    return getpass.getuser()

def request(socket, text):
    socket.send_string(text)
    return socket.recv_string()

class base:

    def __init__(self, handler):
        usage = "usage: %prog [options] <start|stop|restart|quit>"
        parser = OptionParser(usage=usage)

        parser.add_option("-u", "--username", dest="username", 
                          metavar="USERNAME",
                          help="name of the login to be used")
        parser.add_option("-s", "--server", dest="servername", 
                          metavar="SERVER-IP",
                          help="meddle server domain or address")
        parser.add_option("-p", "--port", dest="serverport", 
                          metavar="PORT-NR",
                          help="meddle server tcp port")

        (options, args) = parser.parse_args()

        self.context = zmq.Context()
        self._handler = handler
        self._my_id = 0
        self._subscriptions = []
        self._username = options.username if options.username else system_username()
        self._servername = options.servername if options.servername else "localhost"
        self._serverport = options.serverport if options.serverport else 32100

    def connect(self):
        _thread = Thread(target=lambda: self.rpc_thread())
        _thread.daemon = True
        _thread.start()

    def set_tags(self, tags):
        for t in tags:
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "tag#%s" % t)

    def subscriptions(self):
        return self._subscriptions

    def current_username(self):
        return self._username

    def rpc_thread(self):

        _rpc_server_address = "tcp://%s:%d" % (self._servername, self._serverport)
        logging.info("connect to %s" % _rpc_server_address)
        self._rpc_socket = self.context.socket(zmq.REQ)
        self._rpc_socket.connect(_rpc_server_address)

        self._sub_socket = self.context.socket(zmq.SUB)
        self._sub_socket.connect("tcp://%s:%d" % (self._servername, self._serverport + 1))

        answer = request(self._rpc_socket, "hello %s" % self._username)
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
        _thread = Thread(target=lambda: self.recieve_messages(self._subscriptions[0]))
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

    def recieve_messages(self, channel):
        self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, channel)
        #self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        while True:
            message = self._sub_socket.recv_string()
            if message.startswith("tag#"):
                _tag = message
                _channel = self._sub_socket.recv_string()
                self._handler.meddle_on_tag_notification(_tag, _channel)
                continue
            name = self._sub_socket.recv_string()
            text = message[10:]
            logging.info("incoming message %s: '%s'" % (name, text))
            self._handler.meddle_on_message(channel, name, text)


def main():
    pass   

if __name__ == "__main__":
    main()


