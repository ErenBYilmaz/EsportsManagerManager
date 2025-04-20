import getpass
import typing

import PyQt5.QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QShortcut

from frontend.generated.main_menu import Ui_MainWindow
from frontend.generated.manager_menu import Ui_ManagerWindow

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class ManagerMenu(Ui_ManagerWindow):
    def __init__(self, client: 'AppClient'):
        super().__init__()
        self.client = client

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        if not self.client.local_gamestate.game_to_show().is_nested():
            self.replacePlayerButton_2.setVisible(False)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)
