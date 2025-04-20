import typing

from PyQt5 import QtWidgets

from data.app_game_state import AppGameState
from frontend.generated.manager_menu import Ui_ManagerWindow

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class ManagerMenu(Ui_ManagerWindow):
    def __init__(self, client: 'AppClient', depth: int):
        super().__init__()
        self.client = client
        self.depth = depth

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.replacePlayerButton_2.setVisible(self.depth > 0)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def update_gamestate(self, gs: AppGameState):
        pass
