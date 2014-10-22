#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
import sys
from PyQt4 import QtGui, QtCore, Qt
import logging

import pymeddle


class chat_widget(QtGui.QPlainTextEdit):

    def __init__(self):
        super(chat_widget, self).__init__()

        self._log_file = open('logfile', 'a')
        self.setReadOnly(True)

    @QtCore.pyqtSlot(str)
    def append_message(self, text):
        logging.info("appendMessage: " + text + str(type(text)))
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self._log_file.write(text)
        self._log_file.write('\n')
        self._log_file.flush()


class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.init_ui()
        self.meddle_base = pymeddle.base(self)
        _server = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        self.meddle_base.connect(_server, 32100)
        self._txt_message_edit.setFocus()
      
    def init_ui(self):
        logging.info("init_ui")
          
        self._lbl_chat_room = QtGui.QLabel('<channelname>')      
        self._txt_message_edit = QtGui.QLineEdit()
        self._txt_messages = chat_widget()      

        print(self._txt_message_edit.objectName())
        #print(dir(self._txt_messages))
        self._txt_message_edit.returnPressed.connect(self.on__txt_message_edit_returnPressed)

        _grid = QtGui.QGridLayout()
        _grid.setSpacing(10)

        _grid.addWidget(self._lbl_chat_room,    0, 0)
        _grid.addWidget(self._txt_messages,     1, 0, 5, 1)
        _grid.addWidget(self._txt_message_edit, 6, 0, 2, 1)
        
        self.setLayout(_grid) 
        
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('meddle')    
        self.show()

    @QtCore.pyqtSlot(str, name='on__txt_message_edit_returnPressed') 
    def on__txt_message_edit_returnPressed(self):
        self.meddle_base.publish("todo", self._txt_message_edit.text())
        self._txt_message_edit.setText("")

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def meddle_on_message(self, name, text):
        QtCore.QMetaObject.invokeMethod(
                self._txt_messages, "append_message", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, "%s: %s" % (name,text)))

    def meddle_on_update(self):
        self._lbl_chat_room.setText(self.meddle_base.subscriptions()[0])      

def main():
    logging.info("main")
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
   

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

