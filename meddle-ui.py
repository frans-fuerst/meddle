#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.QColor(100,100,0))
        self.setPalette(p)
        self.setAutoFillBackground(True)


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
        self._lst_users = QtGui.QListWidget()
        self._lst_users.setMaximumSize(QtCore.QSize(200,100))

        self._lst_rooms = QtGui.QListWidget()

        _layout = QtGui.QVBoxLayout()

        _layout.addWidget(self._txt_tags)
        _layout.addWidget(self._lst_users)
        _layout.addWidget(self._lst_rooms)

        self._txt_tags.textChanged.connect(self._on_tags_changed)
        self._lst_users.doubleClicked.connect(self._on_lst_users_doubleClicked)

        self.setLayout(_layout)

        self.setGeometry(800, 100, 500, 500)
        self._update_window_title()
        self.show()

    @QtCore.pyqtSlot(str)
    def _on_tags_changed(self, text):
        _tags = [x.lower() for x in text.split(' ') if x.strip() != ""]
        self.meddle_base.set_tags(_tags)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def _update_window_title(self):
        _title = 'meddle:%s:%s : %s' % (
            self.meddle_base.current_username(),
            self.meddle_base.get_servername(),
            "connected" if self.meddle_base.get_connection_status() else "DISCONNECTED")
        self.setWindowTitle(_title)

    def _on_lst_users_doubleClicked(self, index):
        _user = self._lst_users.item(index.row()).text()
        logging.debug("doubleclick on user %s" % _user)
        _channel = self.meddle_base.create_channel([_user])
        print(_channel)
        
    def _update_user_list(self, users):
        self._lst_users.clear()
        logging.info("users: %s" % users)
        for u in users:
            self._lst_users.addItem(u)

    @QtCore.pyqtSlot(str, str, str)
    def _meddle_on_message(self, channel, name, text):
        self._chats[channel].on_message(name, text)

    @QtCore.pyqtSlot(str)
    def _meddle_on_joined_channel(self, channel):
        #should not be nessessary
        self._update_user_list(self.meddle_base.get_users())

        _item1 = QtGui.QListWidgetItem()
        _item1.setSizeHint(QtCore.QSize(100, 200))

        self._lst_rooms.addItem(_item1)
        _chat_window = chat_widget(self.meddle_base, channel)
        self._chats[channel] = _chat_window
        self._lst_rooms.setItemWidget(_item1, _chat_window)

    @QtCore.pyqtSlot(bool)
    def _meddle_on_connection_established(self, status):
        logging.info("connection status changed: %s " % status)
        self._update_window_title()

    @QtCore.pyqtSlot(str, str)
    def _meddle_on_tag_notification(self, tag, channel):
        logging.info("tag '%s' has been mentioned on channel %s", tag, channel)

    @QtCore.pyqtSlot(list)
    def _meddle_on_user_update(self, users):
        self._update_user_list(users)

    def meddle_on_message(self, channel, name, text):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_message",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, channel),
                QtCore.Q_ARG(str, name),
                QtCore.Q_ARG(str, text))

    def meddle_on_joined_channel(self, channel):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_joined_channel",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, channel))

    def meddle_on_connection_established(self, status):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_connection_established",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, status))

    def meddle_on_tag_notification(self, tag, channel):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_tag_notification",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, tag),
                QtCore.Q_ARG(str, channel))

    def meddle_on_user_update(self, users):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_user_update",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(list, users))


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

