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

- [ ] bugfix: Wenn man einen Kanal öffnet und das Fenster nicht groß genug +
      ist, dann verschwindet der Kanal beim Großziehen des Fensters +
      Auch durch Doppelklick in der channels-Liste kommt er nicht. Man muss +
      erst nochmal mit der Fenstergröße rumspielen.
- [ ] server: persistence (user IDs, tags, channel stats, etc.)
- [ ] search in logs
- [ ] sort channels by importance (activity, contribution, hashtags)
- [ ] names for channels
- [ ] remove comma etc from tags on edit
- [ ] @name notification
- [ ] resizable UI elements
- [ ] show channel subscribers (currently only contributors)
- [ ] show timestamps with the posts
- [ ] run on startup

=== after public release

- [ ] cookie based user verification
- [ ] server: refactor: server: one thread
- [ ] concept for getting missed notification
- [ ] server: use DB
- [ ] email when 'lot of things happened'
- [ ] UI: use rich text to bold tags/names/etc.
- [ ] option modification dialog
- [ ] sync/async cleanup: make all calls fast and async where needed
- [ ] Send files
- [ ] WebClient (to circumvent http/proxy restrictions)
- [ ] Android Client
- [ ] encryption / authentication
- [ ] find contexts on a graphical map

=== done

- [x] Python 2.7+ compatibility for pyinstaller
- [x] see available tags
- [x] case insensitivity for tags
- [x] optional notification on messages
- [x] see users with channel names
- [x] reconnect
- [x] server: log messages (+timestamp)
- [x] leave room
- [x] load conversation on join
- [x] system notifications (on message/tag notification)
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
- [x] server: user id persistence
- [x] save/load configuration files on correct location
- [x] setup.py file / http://www.pyinstaller.org/
- [x] check server/client versions
- [x] program icon
- [x] set username on first startup


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
