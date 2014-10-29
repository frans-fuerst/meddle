#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import random
import string
import logging
import json
import time


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
        
def publish_user_list(socket, users):
    socket.send_multipart(
            ["user_update".encode(),
             json.dumps(users.users_online()).encode()])

class user:
    def __init__(self):
        self.last_ping = time.time()

class user_container:

    def __init__(self):
        #[item for item in a if item[0] == 1]
        #[(id, item) for id, item in a.items() if item[1] == 'user2']
        # users (id, name, user)
        self._next_id = 0
        self._users_online = {}     # {id: (name, user)}
        self._associated_ids = {}   # {name: id}, permanent
        
    def find_or_create_name(self, name):
        #_result = [(id, item) for id, item in self._users_online.items() if item[1] == name]
        
        if name in self._associated_ids:
            _id = self._associated_ids[name]
        else:
            _id = self._next_id
            self._next_id += 1
            self._associated_ids[name] = _id
            
        _new_user = False
        if _id not in self._users_online:
            self._users_online[_id] = (name, user())
            _new_user = True
        _, _user = self._users_online[_id]
        return (_new_user, _id, _user)

    def get_name(self, id):
        """ returns name """
        if id in self._users_online:
            return self._users_online[id][0]
        return None
    
    def set_offline(self, user_ids):
        for i in user_ids: del self._users_online[i]
        
    def users_online(self):
        return [self._users_online[u][0] for u in self._users_online]

    def refresh(self, user_id):
        if not user_id in self._users_online:
            return False
        self._users_online[user_id][1].last_ping = time.time()
        return True
    
    def find_dead(self):
        _result = []
        _now = time.time()
        for _id, _user in self._users_online.items():
            if _now - _user[1].last_ping > 5:
                _result.append(_id)
        return _result
    
def main():
    _users = user_container()
    _context = zmq.Context()

    _channels = {}
    _port_rpc = 32100
    _port_pub = 32101

    _rpc_socket = _context.socket(zmq.REP)
    _rpc_socket.bind("tcp://*:%d" % _port_rpc)

    _pub_socket = _context.socket(zmq.PUB)
    _pub_socket.bind("tcp://*:%d" % _port_pub)

    _poller = zmq.Poller()
    _poller.register(_rpc_socket, zmq.POLLIN)

    logging.info("meddle server listening on port %d, sending on port %d",
                 _port_rpc, _port_pub)

    while True:

        try:
            dead_users = _users.find_dead()
            _users.set_offline(dead_users)
            if not dead_users == []:
                publish_user_list(_pub_socket, _users)
    
            if _poller.poll(3000) == []:
                logging.debug("waiting..")
                continue
            
            _message = _rpc_socket.recv_string()
            logging.debug("got '%s' (%s)" % (_message, type(_message)))
    
            if _message.startswith("hello "):
                _name = _message[6:].strip()
                logging.debug("using name '%s'" % _name)
                _is_new, _id, _user = _users.find_or_create_name(_name)
    
                _rpc_socket.send_string("hello %d" % _id)
                if _is_new:
                     # todo: send only update-info
                    publish_user_list(_pub_socket, _users)
    
            elif _message.startswith("create_channel"):
                _sender_id = int(_rpc_socket.recv_string())
                _invited_users = _rpc_socket.recv_string()
                _channel_name = random_string(10)
                # todo - check collisions
                _rpc_socket.send_string(_channel_name)
                _channels[_channel_name] = None
    
            elif _message.startswith("get_channels"):
                _rpc_socket.send_string(" ".join(_channels.keys()))
    
            elif _message.startswith("get_users"):
                print(_users.users_online())
                _rpc_socket.send_string(json.dumps(_users.users_online()))
    
            elif _message.startswith("ping"):
                # todo: handle users
                _sender_id = int(_rpc_socket.recv_string())
                if _users.refresh(_sender_id):
                    _rpc_socket.send_string('ok')
                else:
                    _rpc_socket.send_string('nok')
                
            elif _message.startswith("publish "):
                _sender_id = int(_rpc_socket.recv_string())
                _rpc_socket.send_string("ok")
                _name = _users.get_name(_sender_id)
                # todo: handle wrong user
                _channel = _message[8:8 + 10]
                _text = _message[8 + 10 + 1:]
                handle_tags(_pub_socket, _channel, _text)
                publish(_pub_socket, _name, _channel, _text)
    
            else:
                _rpc_socket.send_string('nok')
                
        except Exception as ex:
            logging.error("something bad happened: %s", ex)
            time.sleep(3)
            raise
            
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
