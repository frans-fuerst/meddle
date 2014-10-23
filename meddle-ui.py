#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
import sys
from PyQt4 import QtGui, QtCore, Qt
import logging

import pymeddle


class chat_output_widget(QtGui.QPlainTextEdit):

    def __init__(self):
        super(chat_output_widget, self).__init__()
        self.setReadOnly(True)

    @QtCore.pyqtSlot(str)
    def append_message(self, text):
        logging.info("appendMessage: " + text + str(type(text)))
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class chat_widget(QtGui.QWidget):
    def __init__(self):
        super(chat_widget, self).__init__()
        self.init_ui()

    def init_ui(self):
        self._lbl_chat_room = QtGui.QLabel('<channelname>')      
        self._txt_message_edit = QtGui.QLineEdit()
        self._txt_messages = chat_output_widget()      

        self._txt_message_edit.returnPressed.connect(self.on__txt_message_edit_returnPressed)

        _grid = QtGui.QVBoxLayout()
        #_grid.setSpacing(10)

        _grid.addWidget(self._lbl_chat_room)
        _grid.addWidget(self._txt_messages)
        _grid.addWidget(self._txt_message_edit)
        
        self.setLayout(_grid) 

    def on__txt_message_edit_returnPressed(self):
        #self.meddle_base.publish("todo", self._txt_message_edit.text())
        self._txt_message_edit.setText("")
        pass


class MeddleWindow(QtGui.QWidget):
    
    def __init__(self):
        super(MeddleWindow, self).__init__()
        
        self.init_ui()
        self.meddle_base = pymeddle.base(self)
        _server = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        self.meddle_base.connect(_server, 32100)
        #self._txt_message_edit.setFocus()
      
    def init_ui(self):
        logging.info("init_ui")

        #self._lst_rooms = chat_widget()
        self._lst_rooms = QtGui.QListWidget()

        for i in range(2):
            _item1 = QtGui.QListWidgetItem()
            _item1.setSizeHint(QtCore.QSize(100,200))

            self._lst_rooms.addItem(_item1)    
            self._lst_rooms.setItemWidget(_item1, chat_widget())
          
        _grid = QtGui.QVBoxLayout()
        #_grid.setSpacing(10)

        _grid.addWidget(self._lst_rooms)
        
        self.setLayout(_grid) 
       
        self.setGeometry(800, 100, 500, 300)
        self.setWindowTitle('meddle')    
        self.show()


    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def meddle_on_message(self, name, text):
        QtCore.QMetaObject.invokeMethod(
                self._txt_messages, "append_message", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, "%s: %s" % (name,text)))

    def meddle_on_update(self):
        _chat_room = self.meddle_base.subscriptions()[0]

def main():
    logging.info("main")
    app = QtGui.QApplication(sys.argv)
    ex = MeddleWindow()
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

