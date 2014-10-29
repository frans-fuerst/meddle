#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
if sys.version_info < (3,1,):
    print("please use only Python 3.1 an up")
    sys.exit(-1)

import zmq
import getpass
from threading import Thread, Lock
import pymeddle
import logging
from optparse import OptionParser
import json
import time


def system_username():
    # todo: format (spaces, etc)
    return getpass.getuser()

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
        self._servername = options.servername if options.servername else "scibernetic.de"
        self._serverport = options.serverport if options.serverport else 32100
        self._mutex_rpc_socket = Lock()
        self._connection_status = None

    def publish(self, channel, text):
        with self._mutex_rpc_socket:
            self._rpc_socket.send_multipart(
                tuple(str(x).encode() for x in (
                    "publish", self._my_id, channel, text)))
            answer = self._rpc_socket.recv_string()
            if answer != 'ok':
                logging.warn("we got '%s' as reply to publish", answer)
        return answer

    def create_channel(self, invited_users=[]):
        with self._mutex_rpc_socket:
            self._rpc_socket.send_multipart(
                ["create_channel".encode(),
                 self._my_id.encode(),
                 json.dumps(invited_users).encode()])
            _new_channel = self._rpc_socket.recv_string()
            self._join_channel(_new_channel)

    def connect(self):
        self._set_connection_status(False)
        _thread = Thread(target=lambda: self._rpc_thread())
        _thread.daemon = True
        _thread.start()

    def set_tags(self, tags):
        for t in tags:
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "tag#%s" % t)

    def get_users(self):
        answer = self._request("get_users")
        return json.loads(answer)

    def get_channels(self):
        answer = self._request("get_channels")
        _channels = answer.split()
        logging.info("channels: %s" % _channels)
        return _channels

    def get_connection_status(self):
        return bool(self._connection_status)

    def get_servername(self):
        return self._servername

    def subscriptions(self):
        return self._subscriptions

    def current_username(self):
        return self._username

    def _request(self, text):
        with self._mutex_rpc_socket:
            if type(text) in (list, tuple):
                self._rpc_socket.send_multipart([str(i).encode() for i in text])
            else:
                self._rpc_socket.send_string(text)

            poller = zmq.Poller()
            poller.register(self._rpc_socket, zmq.POLLIN)
            while poller.poll(1000) == []:
                logging.warn("timeout!")
                self._set_connection_status(False)

            self._set_connection_status(True)
            return self._rpc_socket.recv_string()

    def _set_connection_status(self, status):
        if status != self._connection_status:
            self._connection_status = status
            self._handler.meddle_on_connection_established(status)

    def _rpc_thread(self):

        _rpc_server_address = "tcp://%s:%d" % (self._servername, self._serverport)
        logging.info("connect to %s" % _rpc_server_address)
        self._rpc_socket = self.context.socket(zmq.REQ)
        self._rpc_socket.connect(_rpc_server_address)

        self._sub_socket = self.context.socket(zmq.SUB)
        self._sub_socket.connect("tcp://%s:%d" % (self._servername, self._serverport + 1))

        ## refactor! - should all go away
        if True:

            answer = self._request("hello %s" % self._username)
            self._my_id = answer[6:]
            logging.info("server: calls us '%s'" % self._my_id)

            """
            answer = self._request("get_channels")
            _channels = answer.split()
            logging.info("channels: %s" % _channels)

            if _channels == []:
                answer = self.create_channel()
                _channel_to_join = answer
            else:
                _channel_to_join = _channels[0]

            self._join_channel(_channel_to_join)
            """

        _thread = Thread(target=lambda: self._recieve_messages())
        _thread.daemon = True
        _thread.start()

        while True:
            time.sleep(2)
            answer = self._request(['ping', self._my_id])
            if answer != 'ok':
                logging.warn("we got '%s' as reply to ping", answer)

    def _join_channel(self, channel):
        if not channel in self._subscriptions:
            self._subscriptions.append(channel)
            self._handler.meddle_on_joined_channel(channel)
            logging.info("talking on channel '%s'" % channel)
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, channel)

    def _recieve_messages(self):
        self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'user_update')
        self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'notify%s' % self._my_id)
        #self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        while True:
            message = self._sub_socket.recv_string()
            if message.startswith("tag#"):
                _tag = message
                _channel = self._sub_socket.recv_string()
                _message = self._sub_socket.recv_string()
                self._handler.meddle_on_tag_notification(_tag, _channel, _message)
            elif message.startswith("notify"):
                _opcode = self._sub_socket.recv_string()
                if _opcode == 'join_channel':
                    _channel = self._sub_socket.recv_string()
                    self._join_channel(_channel)
                else:
                    pass

            elif message.startswith("user_update"):
                _extra_info = self._sub_socket.recv_string()
                self._handler.meddle_on_user_update(json.loads(_extra_info))
            else:
                _channel = message[:10]
                _name = self._sub_socket.recv_string()
                _text = message[10:]
                logging.info("incoming message on %s %s: '%s'" % (_channel, _name, _text))
                self._handler.meddle_on_message(_channel, _name, _text)


def main():
    print("this is the pymeddle library and does not do anything by it's own."
          "run meddle.py or meddle-ui.py or start a server with meddle-server.py")

if __name__ == "__main__":
    main()
