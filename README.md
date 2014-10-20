zero_chat
=========

zeromq based self hosted chat with hash invitation logging and searching


How it works
------------


Under the hood
--------------

zeromq, capnproto, python


Installation
------------

* python3-zmq
* for capnproto: python3-Cython.x86_64
* for capnproto: python3-devel
* for capnproto: python3-pip http://jparyani.github.io/pycapnp/

Sequence
--------

* server initializes and listens on port 12345

* client1 initializes with name "alice" and connects to 12345

* client2 initializes with name "bob" and connects to 12345

* client1 sends a createChannel(invite: [bob])


ToDo
----

- [x] Named messages
- [ ] Join rooms
- [ ] Log messages
- [ ] Recognize hashtags
- [ ] Invite on hashtags
- [ ] Search in logs
- [ ] Leave room
- [ ] Qt interface
- [ ] Multi room
- [ ] Watchdog
- [ ] Send files

