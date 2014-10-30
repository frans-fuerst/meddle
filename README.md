meddle
======

A based self hosted chat with hash invitation, logging and searching


How it works
------------

* start client
  - register for tags
  - get notified when tag is mentioned
  - start chatting with persons or alone
  - search for tags or plain text

* on command line
  - meddle send martin <message>


Under the hood
--------------

* Base language Python3
* zeromq for communication
* Clients: CLI, PyQt (later: web, Android)
* no capnproto/protobuf: complicated, binary dependencies


Installation
------------

Windows:

* Python3: https://www.python.org/download/
* json
* pyzmq: https://pypi.python.org/pypi/pyzmq/14.4.0
    c:\Python34\python.exe -m pip install c:\Users\fuerst\Downloads\pyzmq-14.4.0-cp34-none-win_amd64.whl
    https://github.com/zeromq/pyzmq/downloads
* PyQt4: http://www.riverbankcomputing.co.uk/software/pyqt/download


Linux:

* install zeromq `apt-get install python3-zmq`
* install PyQt4 `apt-get install python3-pyqt4`

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

=== before public release
- [ ] refactor: server: one thread
- [ ] log messages (+timestamp)
- [ ] Search in logs
- [ ] Leave room
- [ ] setup.py file
- [ ] reconnect
- [ ] load conversation on join
- [ ] system notifications (on message/tag notification)
- [ ] cookie based user verification
- [x] join an existing channel
- [x] notify/join on tag notification
- [x] config file (server, tags)
- [x] Invite on hashtags
- [x] Multi room
- [x] unsubscribe hashtags + tagging on enter + bold on active
- [x] instructions on startup when missing libs (zmq/qt4/json)
- [x] refactor: multipart-message concept
- [x] refactor: client instant invoke
- [x] Named messages
- [x] Qt interface
- [x] Recognize hashtags
- [x] list users
- [x] Watchdog / connection status

=== after public release
- [ ] sync/async cleanup: make all calls fast and async where needed
- [ ] Send files
- [ ] WebClient (to circumvent http/proxy restrictions)
- [ ] Android Client
- [ ] encryption / authentication


Architecture:
-------------

Server:

* Users {Id, Name, Interests(Tags)}
* Active connections to users
    - with heartbeat
* Channels (Rooms/Conversations)
* Tags {name: {[user:count], [channel:count]}}
    - for statistics, context
    - points to Users and channels


Client:
* Connection to a server
* Interests [tag:count]
* Active subscriptions


Reference
---------

* Nice Qt4 Tutorial: http://zetcode.com/gui/pyqt4/
* Unicode with pyzmq: http://zeromq.github.io/pyzmq/unicode.html
