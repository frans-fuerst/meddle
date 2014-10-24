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

    def append_message(self, text):
        logging.info("appendMessage: " + text + str(type(text)))
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class chat_widget(QtGui.QWidget):
    def __init__(self, meddle_base, channel):
        super(chat_widget, self).__init__()
        self._channel = channel
        self._meddle_base = meddle_base
        self.init_ui()

    def init_ui(self):
        self._lbl_chat_room = QtGui.QLabel(self._channel)      
        self._txt_message_edit = QtGui.QLineEdit()
        self._txt_messages = chat_output_widget()      

        self._txt_message_edit.returnPressed.connect(self.on__txt_message_edit_returnPressed)

        _grid = QtGui.QVBoxLayout()
        #_grid.setSpacing(10)

        _grid.addWidget(self._lbl_chat_room)
        _grid.addWidget(self._txt_messages)
        _grid.addWidget(self._txt_message_edit)
        
        self.setLayout(_grid) 
        self._txt_message_edit.setFocus()

    def on__txt_message_edit_returnPressed(self):
        self._meddle_base.publish(self._channel, self._txt_message_edit.text())
        self._txt_message_edit.setText("")

    def on_message(self, name, text):
        self._txt_messages.append_message("%s: %s" % (name, text))

class MeddleWindow(QtGui.QWidget):
    
    def __init__(self):
        super(MeddleWindow, self).__init__()
        
        self.meddle_base = pymeddle.base(self)
        self._chats = {}
        self._init_ui()
        self.meddle_base.connect()
      
    def _init_ui(self):
        logging.info("init_ui")

        self._txt_tags = QtGui.QLineEdit()
        self._lst_rooms = QtGui.QListWidget()

        _layout = QtGui.QVBoxLayout()

        _layout.addWidget(self._txt_tags)
        _layout.addWidget(self._lst_rooms)

        self._txt_tags.textChanged.connect(self._on_tags_changed)
        
        self.setLayout(_layout) 
       
        self.setGeometry(800, 100, 500, 300)
        self.setWindowTitle('meddle:%s' % self.meddle_base.current_username())    
        self.show()

    @QtCore.pyqtSlot(str)
    def _on_tags_changed(self, text):
        _tags = [x.lower() for x in text.split(' ') if x.strip() != ""]
        self.meddle_base.set_tags(_tags)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    @QtCore.pyqtSlot(str, str, str)
    def _on_message(self, channel, name, text):
        self._chats[channel].on_message(name, text)

    def meddle_on_message(self, channel, name, text):
        QtCore.QMetaObject.invokeMethod(
                self, "_on_message", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, channel),
                QtCore.Q_ARG(str, name),
                QtCore.Q_ARG(str, text))

    def meddle_on_update(self):
        _chat_room = self.meddle_base.subscriptions()[0]
        QtCore.QMetaObject.invokeMethod(
                self, "_add_channel", 
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, _chat_room))

    def meddle_on_tag_notification(self, tag, channel):
        logging.info("tag '%s' has been mentioned on channel %s", tag, channel)

    @QtCore.pyqtSlot(str)
    def _add_channel(self, channel):
        _item1 = QtGui.QListWidgetItem()
        _item1.setSizeHint(QtCore.QSize(100,200))

        self._lst_rooms.addItem(_item1)    
        _chat_window = chat_widget(self.meddle_base, channel)
        self._chats[channel] = _chat_window
        self._lst_rooms.setItemWidget(_item1, _chat_window)


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

