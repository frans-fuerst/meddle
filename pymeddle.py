#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import getpass
from threading import Thread, Lock
import sys
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
        self._users = []
        self._mutex_rpc_socket = Lock()
        self._connection_status = None
                
    def request(self, text):
        with self._mutex_rpc_socket:
            self._rpc_socket.send_string(text)
            
            poller = zmq.Poller()
            poller.register(self._rpc_socket, zmq.POLLIN)
            while poller.poll(1000) == []:
                logging.warn("timeout!")
                self._set_connection_status(False)
                
            self._set_connection_status(True)
            return self._rpc_socket.recv_string()
    
   
    def publish(self, channel, text):
        with self._mutex_rpc_socket:
            self._rpc_socket.send_multipart(
                [("publish %s %s" % (self._subscriptions[0], text)).encode(),
                 self._my_id.encode(),])
            answer = self._rpc_socket.recv_string()
        return answer
    
    def _set_connection_status(self, status):
        if status != self._connection_status:
            self._connection_status = status
            self._handler.meddle_on_connection_established(status)

    def connect(self):
        self._set_connection_status(False)
        _thread = Thread(target=lambda: self.rpc_thread())
        _thread.daemon = True
        _thread.start()

    def set_tags(self, tags):
        for t in tags:
            self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "tag#%s" % t)
            
    def get_users(self):
        return self._users
    
    def get_connection_status(self):
        return bool(self._connection_status)
    
    def get_servername(self):
        return self._servername
        
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

        answer = self.request("hello %s" % self._username)
        self._my_id = answer[6:]
        logging.info("server: calls us '%s'" % self._my_id)

        answer = self.request("get_channels")
        _channels = answer.split()
        logging.info("channels: %s" % _channels)

        answer = self.request("get_users")
        self._users = json.loads(answer)

        if _channels == []:
            answer = self.request("create_channel bob")
            self._subscriptions.append(answer)
        else:
            self._subscriptions.append(_channels[0])

        self._handler.meddle_on_update()

        logging.info("talking on channel '%s'" % self._subscriptions[0])
        _thread = Thread(target=lambda: self.recieve_messages(self._subscriptions[0]))
        _thread.daemon = True
        _thread.start()
        
        while True:
            time.sleep(1)
            answer = self.request('ping')
            # logging.info("ping: " + answer )

    def recieve_messages(self, channel):
        self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, channel)
        self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, 'user_update')
        #self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        while True:
            message = self._sub_socket.recv_string()
            if message.startswith("tag#"):
                _tag = message
                _channel = self._sub_socket.recv_string()
                self._handler.meddle_on_tag_notification(_tag, _channel)
            elif message.startswith("user_update"):
                _extra_info = self._sub_socket.recv_string()
                self._handler.meddle_on_user_update(json.loads(_extra_info))
            else:
                name = self._sub_socket.recv_string()
                text = message[10:]
                logging.info("incoming message %s: '%s'" % (name, text))
                self._handler.meddle_on_message(channel, name, text)


def main():
    print("this is the pymeddle library and does not do anything by it's own."
          "run meddle.py or meddle-ui.py or start a server with meddle-server.py")

if __name__ == "__main__":
    main()


