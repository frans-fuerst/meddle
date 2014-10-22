#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import sys
import logging

import pymeddle


class client_cli:
    
    def __init__(self):
        self._meddle_base = pymeddle.base(self)
        _server = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        self._meddle_base.connect(_server, 32100)

    def meddle_on_message(self, name, text):
        logging.info("%s said: '%s'" % (name, text))

    def meddle_on_update(self):
        logging.info("subscription: %s" % self._meddle_base.subscriptions()[0])

    def run(self):

        while True:
            text = sys.stdin.readline().strip('\n')
            if text in ('quit', 'exit'):
                sys.exit(0)
            if text.strip() == "":
                continue
            self._meddle_base.publish("todo", text)
   
def main():
    client_cli().run()

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


