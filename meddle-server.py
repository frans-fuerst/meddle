#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import random
import string
import logging
import json
import time
import os
import sys
import glob
import datetime
import pymeddle_common
from threading import Thread

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

def timestamp_str():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S%f')

def from_timestamp(time_string):
    try:
        x = time.strptime(time_string,'%Y%m%d%H%M%S%f')
        return time.mktime(x)
    except:
        return 0

def publish(socket, timestamp, participant, channel, text):
    logging.debug("%s publishes to '%s': '%s'" % (participant, channel, text))
    # socket.send_multipart([(channel + text).encode(), participant.encode()])

    socket.send_multipart(
        tuple(str(x).encode()
              for x in (channel, json.dumps(
                  {'user':participant,
                   'time':timestamp,
                   'text':text}))))

    with open('_%s.log' % channel, 'a') as f:
        f.write("%s: %s: %s: %s" % (timestamp, channel, participant, text))
        f.write("\n")

def find_logs():
    _ret = []
    for i in glob.glob('_*.log'):
        _ret.append(i[1:-4])
    return _ret

def get_log(channel):
    _return = []
    try:
        _filename = '_%s.log' % channel
        for l in open(_filename).readlines():
            _t = from_timestamp(l[: l.find(':')].strip())
            l = l[l.find(':')+1:]
            _c = l[: l.find(':')].strip()
            l = l[l.find(':')+1:]
            _p = l[: l.find(':')].strip()
            _x = l[l.find(':')+1:].strip()
            _l = (_t, _p, _x)
            _return.append(_l)
    except Exception as ex:
        logging.warning("could not open '%s' %s", _filename, ex)
    return _return

def random_string(N, chars=None):
    if not chars:
        chars = string.ascii_uppercase + string.digits
    return ''.join(
        random.choice(chars)
        for _ in range(N))

def create_uid():
    """ creates a 16 digit uid with 9 time based and 7 random characters """
    return random_string(5, string.hexdigits.lower())
    # return ("%x" % (int(time.time()) * 0x10 % 0x1000000000)
    #         + random_string(7, string.hexdigits.lower()))

def replace(in_str, src_characters, tgt_characters=' '):
    for c in src_characters:
        in_str = in_str.replace(c, tgt_characters)
    return in_str

def extract_tags(text):
    return [x.lower() for x in replace(text, '.,;?!:\'"').split(' ')
            if len(x) > 1 and x[0] == '#']

def handle_tags(socket, channel, user, text):
    _contained_tags = extract_tags(text)
    logging.info("tags mentioned: %s", _contained_tags)
    for t in _contained_tags:
        socket.send_multipart(
            tuple(str(x).encode()
                  for x in ("tag%s" % t, channel, user, text)))

    return _contained_tags

def store_tags(all_tags, tags, channel, user):
    """ 0: no changes,
        1<<2: minor tagging (same channel and user),
        1<<4: new tag on user,
        1<<6: new tag this day,
        1<<8: new tag on channel,
        1<<16: new tag """
    _result = 0
    if tags == []:
        return False
    for t in tags:
        if t not in all_tags:
            _result += 1<<16
            all_tags[t] = []
        all_tags[t].append((time.time(), channel, user))
        _result += 1<<2
    return _result

def publish_user_list(socket, users):
    socket.send_multipart(
            ["user_update".encode(),
             json.dumps(users.users_online()).encode()])

def publish_channel_list(socket, channels):
    socket.send_multipart(
            ["channels_update".encode(),
             json.dumps(
                 {x:list(y.participants) for x, y in channels.items()}).encode()])

def publish_tags(socket, all_tags):
    socket.send_multipart(
            ["tags_update".encode(),
             json.dumps(all_tags).encode()])

def notify_user(socket, user_id, msg):
    socket.send_multipart(
        tuple(str(x).encode()
              for x in ("notify%d" % user_id,) + tuple(msg)))

def start_search(socket, search_spec):
    notify_user(socket, search_spec['user'], ("found nothing",))

def load_channels(filename):
    try:
        _res = {}
        _data = json.load(open(filename))
        for n, c in _data.items():
            _res[n] = channel(n, c)
        return _res
    except FileNotFoundError:
        logging.debug("file '%s' was not found - start with empty channel db",
                      filename)
        return {}
    except KeyError:
        logging.debug("missing content in file '%s' - start with empty channel db",
                      filename)
        return {}

def load_tags(filename):
    try:
        _res = {}
        _data = json.load(open(filename))
        for c, t in _data.items():
            _res[c] = [(_a, _b, _c) for _a, _b, _c in t ]
        return _res
    except FileNotFoundError:
        return {}

def persist(users, channels, tags):
    logging.info("write persistent data..")

    users.save('server-user.db')
    assert users == user_container().load('server-user.db')

    json.dump({n:c.to_JSON() for n, c in channels.items()},
              open('server-channels.db', 'w'))
    assert channels == load_channels('server-channels.db')

    json.dump(tags, open('server-tags.db', 'w'))
    t = load_tags('server-tags.db')
    assert tags == t


def refresh_channel_information(channels, all_tags, force=False):
    _available_channels = find_logs()
    _information_complete = not force
    if _information_complete:
        for c in _available_channels:
            if not c in channels:
                logging.info("missing information about channel '%s' - rebuild db", c)
                _information_complete = False
                break
    if _information_complete:
        return

    channels.clear()
    all_tags.clear()

    for c in _available_channels:
        logging.info("    load channel '%s'", c)
        channels[c] = channel(c)
        _logs = get_log(c)
        for t, u, x in _logs:
            _tags = extract_tags(x)
            channels[c].add_participant(u, t)
            channels[c].add_tags(_tags)
            store_tags(all_tags, _tags, c, u)

def filter_channels(channels, all_tags, user, hint):
    _channel_list = [[n, c, 0] for n, c in channels.items()]
    _count = hint['count']
    for i, t in enumerate(_channel_list):
        if user in t[1].last_contributors:
            _since = (int(time.time()) - t[1].last_contributors[user])/3600.
            t[2] += max(0, int(100 - _since))
        if user in t[1].participants:
            t[2] += 5
        for tag in hint['tags']:
            if tag not in t[1].tags: continue
            t[2] += t[1].tags[tag] * 1

    _channel_list = sorted(_channel_list, key=lambda x: x[2], reverse=True)[:_count]
    _channel_list = [(n, s) for n, _, s in _channel_list]

    print('hint:  %s' % hint)
    for n, s in _channel_list:
        print('   - %d: %s' % (s, n))
    return _channel_list

class channel(object):

    def __init__(self, friendly_name, json=None):
        if json and isinstance(json, dict):
            self.participants = set(json['participants'])
            self.tags = json['tags']
            self.last_contributors = json['last_contributors']
            self.friendly_name = json['friendly_name']
            if self.friendly_name == "":
                self.friendly_name = friendly_name
        else:
            self.participants = set()
            self.tags = {}
            self.last_contributors = {}
            self.friendly_name = friendly_name

    def __eq__(self, other):
        return (self.participants == other.participants and
                self.tags == other.tags)

    def to_JSON(self):
        return { 'participants': list(self.participants),
                 'tags': self.tags,
                 'last_contributors': self.last_contributors,
                 'friendly_name': self.friendly_name}

    def add_participant(self, name, time):
        self.last_contributors[name] = int(time)
        self.last_contributors = {n:t for n, t in
                                  sorted(self.last_contributors.items(),
                                         key=lambda x: x[1], reverse=True)[:4]}
        if not name in self.participants:
            self.participants.add(name) #todo: should be id
            return True
        return False

    def add_tags(self, tags):
        if len(tags) == 0: return
        for t in tags:
            if not t in self.tags:
                self.tags[t] = 0
            self.tags[t] += 1
        return


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

    def __eq__(self, other):
        return (self._next_id == other._next_id and
                self._associated_ids == other._associated_ids)

    def load(self, filename):
        try:
            with open(filename) as f:
                _data = json.loads(f.read())
                self._next_id = _data['next_id']
                self._associated_ids = _data['user_data']
                return self
        except Exception as ex:
            print(ex)

    def save(self, filename):
        #try:
            #print(json.dumps(data))
        #except Exception as ex:
            #print(ex)

        try:
            with open(filename, 'w') as f:
                f.write(self.to_JSON())

        except Exception as ex:
            print(ex)

    def to_JSON(self):
        return json.dumps(
            { 'next_id': self._next_id,
              'user_data': self._associated_ids },
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)

    def from_JSON(self, json_data):
        imported_data = json.loads(json_data)
        self._associated_ids = imported_data['user_data']
        self._next_id = imported_data['next_id']

    def find_or_create_name(self, name):
        #_result = [(id, item) for id, item in self._users_online.items() if item[1] == name]

        if name in self._associated_ids:
            _id = self._associated_ids[name]['id']
        else:
            _id = self._next_id
            self._next_id += 1
            self._associated_ids[name] = {'id':_id}

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

    def get_id(self, name):
        return self._associated_ids[name]['id']

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
        if len(_result) > 0:
            logging.info("users %s timeouted" % _result)
        return _result


def main():

    _context = zmq.Context()

    _own_version = pymeddle_common.get_version()
    _port_rpc = 32100
    _port_pub = 32101

    _rpc_socket = _context.socket(zmq.REP)
    _rpc_socket.bind("tcp://*:%d" % _port_rpc)

    _pub_socket = _context.socket(zmq.PUB)
    _pub_socket.bind("tcp://*:%d" % _port_pub)

    _poller = zmq.Poller()
    _poller.register(_rpc_socket, zmq.POLLIN)
    logging.info("meddle version:      %s", '.'.join((str(x) for x in _own_version)))
    logging.info("using Python version %s", '.'.join((str(x) for x in sys.version_info)))
    logging.info("using ZeroMQ version %s", zmq.zmq_version())
    logging.info("using pyzmq version  %s", zmq.pyzmq_version())
    logging.info("meddle server listening on port %d, sending on port %d",
                 _port_rpc, _port_pub)

    _channels = load_channels('server-channels.db')
    _all_tags = load_tags('server-tags.db')
    _users = user_container()
    _users.load('server-user.db')

    refresh_channel_information(_channels, _all_tags, _all_tags==[])

    while True:

        try:
            dead_users = _users.find_dead()
            _users.set_offline(dead_users)
            if not dead_users == []:
                publish_user_list(_pub_socket, _users)

            if _poller.poll(3000) == []:
                # logging.debug("waiting..")
                continue

            _message = _rpc_socket.recv_string()
            # logging.debug("got '%s' (%s)" % (_message, type(_message)))

            if _message == "hello":
                _answer = json.loads(_rpc_socket.recv_string())
                _name = _answer['name']
                _version = tuple(_answer['version'])
                logging.debug("hello from '%s' with client version %s" % (
                    _name, _version))
                if _version < pymeddle_common.get_min_client_version():
                    _rpc_socket.send_string(json.dumps({'accepted': False,
                                                        'version': _own_version}))
                else:
                    _is_new, _id, _user = _users.find_or_create_name(_name)

                    _rpc_socket.send_string(json.dumps({'accepted': True,
                                                        'id': _id,
                                                        'version': _own_version,
                                                        'sub_port': _port_pub}))

                    if _is_new:
                         # todo: send only update-info
                        publish_user_list(_pub_socket, _users)

            elif _message.startswith("ping"):
                # todo: handle users
                _sender_id = int(_rpc_socket.recv_string())
                if _users.refresh(_sender_id):
                    _rpc_socket.send_string('ok')
                else:
                    logging.warn("user with id %d marked offline but sending",
                                 _sender_id)
                    _rpc_socket.send_string('nok')

            elif _message == "create_channel":
                _sender_id = int(_rpc_socket.recv_string())
                _invited_users = json.loads(_rpc_socket.recv_string())
                _name = _users.get_name(_sender_id)
                if not _name:
                    logging.warn("user with id %d marked offline but sending",
                                 _sender_id)
                    _rpc_socket.send_string("nok")
                else:
                    logging.debug("%s creates channel and invites '%s'",
                                  _sender_id, _invited_users)
                    _channel_name = create_uid()
                    # todo - check collisions
                    _rpc_socket.send_string(_channel_name)
                    _channels[_channel_name] = channel(_channel_name)
                    _channels[_channel_name].participants.add(_name)
                    for _uid in [_users.get_id(u) for u in _invited_users]:
                        notify_user(_pub_socket,
                                    _uid, ('join_channel', _channel_name))
                    # publish_channel_list(_pub_socket, _channels)

            elif _message == "get_channels":
                _hint = json.loads(_rpc_socket.recv_string())
                _user = 'frans'
                _user = _users.get_name(_hint['user'])
                _hot_channels = filter_channels(_channels, _all_tags, _user, _hint)
                _rpc_socket.send_string(
                    json.dumps(
                        {_name: _score for _name, _score in _hot_channels}))
                
            elif _message == "get_channel_info":
                try:
                    _request = json.loads(_rpc_socket.recv_string())
                    _result = [(n, _channels[n].friendly_name, 
                                list(_channels[n].participants)) 
                               for n in _request['channels']]
                    _rpc_socket.send_string(json.dumps(_result))
                except:
                    _rpc_socket.send_string(json.dumps({}))

            elif _message == "get_users":
                _rpc_socket.send_string(json.dumps(_users.users_online()))

            elif _message == "get_active_tags":
                _rpc_socket.send_string(json.dumps(_all_tags))

            elif _message.startswith("get_log"):
                _channel = _rpc_socket.recv_string()
                _rpc_socket.send_string(json.dumps(get_log(_channel)))

            elif _message == "search":
                _search_term = json.loads(_rpc_socket.recv_string())
                _rpc_socket.send_string(json.dumps({'ok':'True', 'id':0}))
                logging.info("user %d wants us to search for '%s'",
                             _search_term['user'], _search_term['term'])
                _thread = Thread(target=lambda: start_search(
                    _pub_socket, _search_term))
                _thread.daemon = True
                _thread.start()

            elif _message.startswith("rename_channel"):
                _rename_info = json.loads(_rpc_socket.recv_string())
                if not ('cuid' in _rename_info and 'name' in _rename_info
                        and len(_rename_info['name'].strip())>3):
                    _rpc_socket.send_string('nok')
                    return
                _channels[_rename_info['cuid']].friendly_name = _rename_info['name'].strip()
                _rpc_socket.send_string('ok')
                
            elif _message == "publish":
                _sender_id = int(_rpc_socket.recv_string())
                _channel = _rpc_socket.recv_string()
                _text = _rpc_socket.recv_string()
                _name = _users.get_name(_sender_id)
                if not _name:
                    logging.warn("user with id %d marked offline but sending",
                                 _sender_id)
                    _rpc_socket.send_string("nok")
                elif _channel not in _channels:
                    logging.warn("tried to send on channel %s which is currently not known",
                                 _channel)
                    _rpc_socket.send_string("nok")
                elif _text == 'persist':
                    _rpc_socket.send_string('ok')
                    persist(_users, _channels, _all_tags)
                elif _text == 'server shutdown':
                    persist(_users, _channels, _all_tags)
                    _rpc_socket.send_string('ok')
                    time.sleep(1)
                    sys.exit(0)
                else:
                    _rpc_socket.send_string('ok')
                    # todo: handle wrong user
                    if _channels[_channel].add_participant(_name, time.time()):
                        # publish_channel_list(_pub_socket, _channels)
                        pass
                    _tags = handle_tags(_pub_socket, _channel, _name, _text)
                    _channels[_channel].add_tags(_tags)
                    if store_tags(_all_tags, _tags, _channel, _sender_id) > 0: #1<<2:
                        publish_tags(_pub_socket, _all_tags)
                    publish(_pub_socket, timestamp_str(), _name, _channel, _text)

        except Exception as ex:
            logging.error("something bad happened: %s", ex)
            time.sleep(3)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)            
            raise ex

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
