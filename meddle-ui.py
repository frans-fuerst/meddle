#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
#import capnp
import getpass
from threading import Thread
import sys
from PyQt4 import QtGui
import pymeddle


class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        self.meddle_base = pymeddle.base()
        self.meddle_base.connect("tcp://localhost:5555")

        
    def initUI(self):
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Icon')
        self.setWindowIcon(QtGui.QIcon('web.png'))        
    
        self.show()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
   

if __name__ == "__main__":
    main()


