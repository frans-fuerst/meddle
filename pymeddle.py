#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
#import os
#import zmq.backend.cython
##os.environ['PYZMQ_BACKEND'] = 'cython'
#import zmq
if sys.version_info < (2, 7,):
    print("please use only Python 2.7 an up")
    sys.exit(-1)
try:
    import zmq
except:
    print("you need the pyzmq package installed for your running python "
          "instance (version %s." % ".".join((str(x) for x in tuple(sys.version_info))))
    print("")
    print("go to https://pypi.python.org/pypi/pyzmq/14.4.0, get the wheel file "
          "and install with")
    print("")
    print("python[.exe] -m pip install /path/to/pyzmq-wheel-file.whl")
    print("")
    print("or use your package manager to install 'python3-zmq' or 'python-zmq'")
    sys.exit(-1)

import os
import getpass
from threading import Thread, Lock
import logging
from optparse import OptionParser
import json
import time
import ast
import socket
import pymeddle_common

def system_username():
    # todo: format (spaces, etc)
    return getpass.getuser()

def find_first_available_server(options):
    if 'servernames' in options:
        for s in options['servernames']:
            try:
                print(socket.gethostbyname_ex(s))
                return socket.gethostbyname_ex(s)[0]
            except:
                pass
    else:
        return 'scibernetic.de'

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

        _meddle_default_config_filename = os.path.join(
            pymeddle_common.meddle_directory(), '.meddle-default')

        self._meddle_config_filename = os.path.join(
            pymeddle_common.system_user_directory(), '.meddle')

        logging.info("using environment:")
        logging.info("    Python version       %s", tuple(sys.version_info))
        logging.info("    ZeroMQ version       %s", zmq.zmq_version())
        logging.info("    pyzmq version        %s", zmq.pyzmq_version())
        logging.info("    home directory:      %s", pymeddle_common.system_user_directory())
        logging.info("    meddle directory:    %s", pymeddle_common.meddle_directory())
        logging.info("    default config file: %s", _meddle_default_config_filename)
        logging.info("    user config file:    %s", self._meddle_config_filename)

        self._perstitent_settings = {}
        self._perstitent_settings['tags'] = []

        try:
            self._perstitent_settings.update(
                ast.literal_eval(open(_meddle_default_config_filename).read()))
        except Exception as e:
            print(e)

        try:
            self._perstitent_settings.update(
                ast.literal_eval(open(self._meddle_config_filename).read()))
        except Exception as e:
            print(e)

        # print(self._perstitent_settings)

        self.context = zmq.Context()
        self._handler = handler
        self._my_id = 0
        self._subscriptions = []
        self._preliminary_username = False

        if options.username:
            self._username = options.username
        else:
            if 'username' in self._perstitent_settings:
                self._username = self._perstitent_settings['username']
            else:
                self._username = system_username()
                self._preliminary_username = True

        if options.servername:
            self._servername = options.servername
        else:
            self._servername = find_first_available_server(self._perstitent_settings)
        self._serverport = options.serverport if options.serverport else 32100
        self._mutex_rpc_socket = Lock()
        self._connection_status = None
        self._version = pymeddle_common.get_version()

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
        if type(invited_users) in (list, tuple):
            _invited_users = [str(l) for l in invited_users]
        else:
            _invited_users = [str(invited_users)]
        with self._mutex_rpc_socket:
            self._rpc_socket.send_multipart(
                ["create_channel".encode(),
                 str(self._my_id).encode(),
                 json.dumps(_invited_users).encode()])
            return self._rpc_socket.recv_string()

    def join_channel(self, channel):
        if not channel in self._subscriptions:
            self._subscriptions.append(channel)
            self._handler.meddle_on_joined_channel(channel)
            logging.info("talking on channel '%s'" % channel)
            self._sub_socket.setsockopt(zmq.SUBSCRIBE, channel.encode('utf-8'))

    def leave_channel(self, channel):
        if channel in self._subscriptions:
            self._subscriptions.remove(channel)
            self._handler.meddle_on_leave_channel(channel)
            logging.info("leaving channel '%s'" % channel)
            self._sub_socket.setsockopt(zmq.UNSUBSCRIBE, channel.encode('utf-8'))

    def connect(self):
        self._set_connection_status(False)
        _thread = Thread(target=lambda: self._rpc_thread())
        _thread.daemon = True
        _thread.start()

    def shutdown(self):
        try:
            open(self._meddle_config_filename, 'w').write(str(self._perstitent_settings))
        except Exception as ex:
            logging.warn(ex)

    def set_tags(self, tags, force=False):
        _new_tags = set((t.lower() for t in tags))
        _old_tags = set() if force else set(self._perstitent_settings['tags'])
        for t in _new_tags - _old_tags:
            logging.info("subscribe '%s'" % t)
            self._sub_socket.setsockopt(zmq.SUBSCRIBE, ("tag#%s" % t).encode('utf-8'))
        for t in _old_tags - _new_tags:
            logging.info("unsubscribe '%s'" % t)
            self._sub_socket.setsockopt(zmq.UNSUBSCRIBE, ("tag#%s" % t).encode('utf-8'))
        self._perstitent_settings['tags'] = tags

    def get_tags(self):
        return self._perstitent_settings['tags']

    def get_users(self):
        answer = self._request("get_users")
        return json.loads(answer)

    def get_channels(self):
        answer = self._request(
            ("get_channels", 
             json.dumps({'user':self._my_id,
                         'count':2,
                         'tags':self._perstitent_settings['tags']})))
        _relevant_channels = json.loads(answer)
        for c in self._subscriptions:
            _relevant_channels[c] = 1000
        answer = self._request(("get_channel_info", 
                                json.dumps({'channels':_relevant_channels})))
        _my_channels = json.loads(answer)
        logging.info("channels: %s" % _my_channels)
        return _my_channels

    def get_active_tags(self):
        answer = self._request("get_active_tags")
        _tags = json.loads(answer)
        return _tags

    def search(self, search_term):
        answer = self._request(("search", json.dumps({'user': self._my_id,
                                                      'term': search_term})))
        print(answer)

    def get_log(self, channel):
        answer = self._request(("get_log", channel))
        return json.loads(answer)

    def get_connection_status(self):
        return bool(self._connection_status)

    def get_servername(self):
        return self._servername

    def subscriptions(self):
        return self._subscriptions

    def current_username(self):
        return self._username

    def set_username(self, name):
        self._username = name
        self._perstitent_settings['username'] = name

    def username_is_preliminary(self):
        return self._preliminary_username

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

    def _hello(self):
        _answer = self._request(("hello",
                                 json.dumps({'name':    self._username,
                                             'version': self._version})))
        _answer = json.loads(_answer)
        if 'accepted' in _answer and _answer['accepted']:
            self._my_id = _answer['id']
            logging.info("server: calls us '%s', has version %s (own: %s)",
                         self._my_id, _answer['version'], self._version)
        else:
            self._handler.meddle_on_version_check(
                False, _answer['version'], self._version, 'mismatch')

    def _rpc_thread(self):

        _rpc_server_address = "tcp://%s:%d" % (self._servername, self._serverport)
        logging.info("connect to %s" % _rpc_server_address)
        self._rpc_socket = self.context.socket(zmq.REQ)
        self._rpc_socket.connect(_rpc_server_address)

        self._sub_socket = self.context.socket(zmq.SUB)
        self._sub_socket.connect("tcp://%s:%d" % (self._servername, self._serverport + 1))

        self.set_tags(self._perstitent_settings['tags'], True)

        ## refactor! - should all go away
        if True:
            self._hello()

        _thread = Thread(target=lambda: self._receive_messages())
        _thread.daemon = True
        _thread.start()

        while True:
            time.sleep(2)
            answer = self._request(['ping', self._my_id])
            if answer != 'ok':
                logging.warn("we got '%s' as reply to ping, let's say hello again..", answer)
                self._hello()

    def _receive_messages(self):
        self._sub_socket.setsockopt(zmq.SUBSCRIBE, 'channels_update'.encode('utf-8'))
        self._sub_socket.setsockopt(zmq.SUBSCRIBE, 'user_update'.encode('utf-8'))
        self._sub_socket.setsockopt(zmq.SUBSCRIBE, 'tags_update'.encode('utf-8'))
        self._sub_socket.setsockopt(zmq.SUBSCRIBE, ('notify%s' % self._my_id).encode('utf-8'))
        #self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        while True:
            message = self._sub_socket.recv_string()
            if message.startswith("tag#"):
                _tag = message
                _channel = self._sub_socket.recv_string()
                _user = self._sub_socket.recv_string()
                _message = self._sub_socket.recv_string()
                self._handler.meddle_on_tag_notification(
                    _tag, _channel, _user, _message)
            elif message.startswith("notify"):
                _opcode = self._sub_socket.recv_string()
                if _opcode == 'join_channel':
                    _channel = self._sub_socket.recv_string()
                    self.join_channel(_channel)
                else:
                    logging.info("got strange '%s'", _opcode)
            elif message == "channels_update":
                self._handler.meddle_on_channels_update(
                    json.loads(self._sub_socket.recv_string()))
            elif message == "user_update":
                _extra_info = self._sub_socket.recv_string()
                self._handler.meddle_on_user_update(json.loads(_extra_info))
            elif message == "tags_update":
                _tags = json.loads(self._sub_socket.recv_string())
                self._handler.meddle_on_tags_update(_tags)
            else:
                _channel = message
                _msg = json.loads(self._sub_socket.recv_string())
                _name = _msg['user']
                _text = _msg['text']
                _time = _msg['time']
                logging.info("%s: incoming message on %s %s: '%s'",
                             _time, _channel, _name, _text)
                self._handler.meddle_on_message(_channel, _name, _text)


def main():
    print("this is the pymeddle library and does not do anything by it's own."
          "run meddle.py or meddle-ui.py or start a server with meddle-server.py")

if __name__ == "__main__":
    main()
