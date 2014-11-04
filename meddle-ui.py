#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
try:
    from PyQt4 import QtGui, QtCore, Qt
except:
    print("you need the PyQt4 package installed for your running python instance.")
    print()
    print("go to http://www.riverbankcomputing.co.uk/software/pyqt/download and"
          "get the package or use your package manager to install 'python3-pyqt4'")
    sys.exit(-1)

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

    close_window = QtCore.pyqtSignal(str)

    def __init__(self, parent, meddle_base, channel):
        super(chat_widget, self).__init__()
        self.parent_item = parent
        self._channel = channel
        self._meddle_base = meddle_base
        self.init_ui()

    def init_ui(self):
        self._lbl_chat_room = QtGui.QLabel(self._channel)

        self._pb_exit = QtGui.QPushButton('X')
        # self._pb_exit.setFlat(True)
        self._pb_exit.setMaximumSize(QtCore.QSize(40,100))
        self._pb_exit.setSizePolicy(
            QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Minimum )

        _layout1 = QtGui.QHBoxLayout()
        _layout1.setMargin(0)
        _layout1.addWidget(self._lbl_chat_room)
        _layout1.addWidget(self._pb_exit)

        _layout1_widget = QtGui.QWidget()
        _layout1_widget.setLayout(_layout1)
        #_layout1_widget.setMaximumSize(QtCore.QSize(3000,100))

        self._txt_message_edit = QtGui.QLineEdit()
        self._txt_messages = chat_output_widget()

        self._txt_message_edit.returnPressed.connect(self.on_txt_message_edit_returnPressed)
        self._pb_exit.pressed.connect(self.on_pb_exit_pressed)

        _grid = QtGui.QVBoxLayout()
        #_grid.setSpacing(10)

        _grid.addWidget(_layout1_widget)

        _grid.addWidget(self._txt_messages)
        _grid.addWidget(self._txt_message_edit)

        self.setLayout(_grid)
        self._txt_message_edit.setFocus()

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.QColor(100,100,0))
        self.setPalette(p)
        self.setAutoFillBackground(True)

    def on_pb_exit_pressed(self):
        self.close_window.emit(self._channel)

    def on_txt_message_edit_returnPressed(self):
        self._meddle_base.publish(self._channel, self._txt_message_edit.text())
        self._txt_message_edit.setText("")

    def on_message(self, name, text):
        self._txt_messages.append_message("%s: %s" % (name, text))

    def closeEvent(self, event):
        pass

class MeddleWindow(QtGui.QWidget):

    def __init__(self):
        super(MeddleWindow, self).__init__()

        self.meddle_base = pymeddle.base(self)
        self._chats = {}
        self._init_ui()
        self.meddle_base.connect()

        self._txt_tags.setText(" ".join(self.meddle_base.get_tags()))
        self._on_txt_tags_returnPressed()
        self._focus = True
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.WindowActivate:
            self._focus = True
        elif event.type()== QtCore.QEvent.WindowDeactivate:
            self._focus = False

        return False

    def _init_ui(self):
        logging.info("init_ui")

        _lbl_tags = QtGui.QLabel('your tags:')
        self._txt_tags = QtGui.QLineEdit()
        _hlayout2 = QtGui.QHBoxLayout()
        _hlayout2.setMargin(0)
        _hlayout2.addWidget(_lbl_tags)
        _hlayout2.addWidget(self._txt_tags)
        _hlayout2_widget = QtGui.QWidget()
        _hlayout2_widget.setLayout(_hlayout2)
        _hlayout2_widget.setMaximumSize(QtCore.QSize(3000,100))

        self._lst_users = QtGui.QListWidget()
        self._lst_channels = QtGui.QListWidget()
        self._lst_users.setMaximumSize(QtCore.QSize(200, 1000))
        _lbl_users = QtGui.QLabel('online:')
        _lbl_channels = QtGui.QLabel('channels:')
        _hlayout1 = QtGui.QGridLayout()
        _hlayout1.setMargin(0)
        _hlayout1.addWidget(_lbl_users,         0, 0)
        _hlayout1.addWidget(_lbl_channels,      0, 1)
        _hlayout1.addWidget(self._lst_users,    1, 0)
        _hlayout1.addWidget(self._lst_channels, 1, 1)
        _hlayout1_widget = QtGui.QWidget()
        _hlayout1_widget.setLayout(_hlayout1)
        _hlayout1_widget.setMaximumSize(QtCore.QSize(3000, 100))

        self._lst_rooms = QtGui.QListWidget()

        self._lst_notifications = QtGui.QListWidget()
        self._lst_notifications.setMaximumSize(QtCore.QSize(3000, 100))

        _layout = QtGui.QVBoxLayout()

        _layout.addWidget(_hlayout2_widget)
        #_layout.addWidget(self._lst_users)
        _layout.addWidget(_hlayout1_widget)
        _layout.addWidget(self._lst_rooms)
        _layout.addWidget(self._lst_notifications)

        self._txt_tags.textChanged.connect(self._on_txt_tags_textChanged)
        self._txt_tags.returnPressed.connect(self._on_txt_tags_returnPressed)

        self._lst_users.doubleClicked.connect(self._on_lst_users_doubleClicked)
        self._lst_channels.doubleClicked.connect(self._on_lst_channels_doubleClicked)
        self._lst_notifications.doubleClicked.connect(self._on_lst_notifications_doubleClicked)

        self.setLayout(_layout)

        self.setGeometry(800, 100, 500, 500)
        self._update_window_title()
        self.show()

        self._sys_icon = QtGui.QSystemTrayIcon()
        self._sys_icon.setIcon(QtGui.QIcon.fromTheme("document-save"))
        self._sys_icon.setVisible(True)

    @QtCore.pyqtSlot(str)
    def _on_txt_tags_textChanged(self, text):
        font = self._txt_tags.font()
        font.setWeight(QtGui.QFont.Bold)
        font.setBold(False)
        self._txt_tags.setFont(font)

    @QtCore.pyqtSlot()
    def _on_txt_tags_returnPressed(self):
        _tags = [x.lower() for x in self._txt_tags.text().split(' ') if x.strip() != ""]
        logging.info('set tags to %s', _tags)
        font = self._txt_tags.font()
        font.setWeight(QtGui.QFont.Bold)
        font.setBold(True)
        self._txt_tags.setFont(font)
        self.meddle_base.set_tags(_tags)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.meddle_base.shutdown()

    def _update_widgets(self):
        self._update_window_title()
        if self.meddle_base.get_connection_status():
            self._update_user_list(self.meddle_base.get_users())
            self._update_channel_list(self.meddle_base.get_channels())
        else:
            self._update_user_list([])
            self._update_channel_list([])

    def _update_window_title(self):
        _title = 'meddle:%s:%s : %s' % (
            self.meddle_base.current_username(),
            self.meddle_base.get_servername(),
            "connected" if self.meddle_base.get_connection_status() else "DISCONNECTED")
        self.setWindowTitle(_title)

    def _update_user_list(self, users):
        self._lst_users.clear()
        logging.info("users: %s" % users)
        for u in users:
            self._lst_users.addItem(u)

    def _update_channel_list(self, channels):
        self._lst_channels.clear()
        logging.info("channels: %s" % channels)
        for c in channels:
            self._lst_channels.addItem("%s: %s" % (c, ", ". join(channels[c])))

    def _on_lst_users_doubleClicked(self, index):
        _user = self._lst_users.item(index.row()).text()
        logging.debug("doubleclick on user %s" % _user)
        _channel = self.meddle_base.create_channel([_user])
        self.meddle_base.join_channel(_channel)

    def _on_lst_channels_doubleClicked(self, index):
        _channel = self._lst_channels.item(index.row()).text().split(':')[0]
        logging.debug("doubleclick on channel %s" % _channel)
        self.meddle_base.join_channel(_channel)

    def _on_lst_notifications_doubleClicked(self, index):
        _line = self._lst_notifications.item(index.row()).text()
        logging.debug("doubleclick on notification %s" % _line)
        _channel = _line.split(':')
        if len(_channel) > 0:
            _channel = _channel[0]
            self.meddle_base.join_channel(_channel)

    def _show_notification(self, text):
        if not self._focus:
            self._sys_icon.showMessage(
                'hey %s' % self.meddle_base.current_username(),
                text+"\n\n\n\n")

    @QtCore.pyqtSlot(str, str, str)
    def _meddle_on_message(self, channel, name, text):
        self._chats[channel].on_message(name, text)
        self._show_notification("%s on %s:\n%s" %(name, channel, text))

    @QtCore.pyqtSlot(str)
    def _meddle_on_joined_channel(self, channel):
        _item1 = QtGui.QListWidgetItem()
        _item1.setSizeHint(QtCore.QSize(100, 200))

        self._lst_rooms.addItem(_item1)
        _chat_window = chat_widget(_item1, self.meddle_base, channel)
        _chat_window.close_window.connect(self._on_chat_window_close_window)

        for t, name, text in self.meddle_base.get_log(channel):
            _chat_window.on_message(name, text)

        self._chats[channel] = _chat_window
        self._lst_rooms.setItemWidget(_item1, _chat_window)
        self._show_notification("you joined channel %s" % channel)

    def _on_chat_window_close_window(self, channel):
        self.meddle_base.leave_channel(channel)

    @QtCore.pyqtSlot(str)
    def _meddle_on_leave_channel(self, channel):
        _window = self._chats[channel]
        _list_item = _window.parent_item
        self._lst_rooms.takeItem(self._lst_rooms.row(_list_item))
        del self._chats[channel]
        del _window
        del _list_item
        #window.parent_item.setParent(None)
        #del window.parent_item
        #self._lst_rooms.removeItemWidget(window.parent_item)
        #window.setParent(None)

    @QtCore.pyqtSlot(bool)
    def _meddle_on_connection_established(self, status):
        logging.info("connection status changed: %s " % status)
        self._update_widgets()

    @QtCore.pyqtSlot(str, str, str, str)
    def _meddle_on_tag_notification(self, tag, channel, user, text):
        logging.info("tag '%s' has been mentioned on channel %s: %s",
                     tag, channel, text)
        self._lst_notifications.addItem("%s: %s: %s" % (channel, user, text))
        self._show_notification("%s: %s: %s" % (channel, user, text))

    @QtCore.pyqtSlot(list)
    def _meddle_on_user_update(self, users):
        self._update_user_list(users)

    @QtCore.pyqtSlot(dict)
    def _meddle_on_channels_update(self, channels):
        self._update_channel_list(channels)

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

    def meddle_on_leave_channel(self, channel):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_leave_channel",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, channel))

    def meddle_on_connection_established(self, status):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_connection_established",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, status))

    def meddle_on_tag_notification(self, tag, channel, user, text):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_tag_notification",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, tag),
                QtCore.Q_ARG(str, channel),
                QtCore.Q_ARG(str, user),
                QtCore.Q_ARG(str, text))

    def meddle_on_channels_update(self, channels):
        QtCore.QMetaObject.invokeMethod(
                self, "_meddle_on_channels_update",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(dict, channels))

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

import datetime
#st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

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

