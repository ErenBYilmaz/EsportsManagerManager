import getpass
import typing

import PyQt5.QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QShortcut

from frontend.generated.main_menu import Ui_MainWindow
if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class MainMenu(Ui_MainWindow):
    def __init__(self, client: 'AppClient'):
        super().__init__()
        self.client = client

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        from stories.join_server import JoinServer
        from stories.start_server import StartServer
        self.joinServerButton.clicked.connect(JoinServer(self))
        self.startServerButton.clicked.connect(StartServer(self))
        self.settingsButton.clicked.connect(self.client.open_settings_window)
        self.usernameEdit.setText(getpass.getuser())
        self.hotkeys = [
            QShortcut(PyQt5.QtCore.Qt.Key_Return, self.usernameEdit, JoinServer(self))
        ]

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)
