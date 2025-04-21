import typing

from PyQt5 import QtWidgets

from data.app_gamestate import AppGameState
from data.esports_player import ESportsPlayer
from frontend.generated.waiting_menu import Ui_WaitingWindow
from stories.ready import SetReadyStatus

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class WaitingMenu(Ui_WaitingWindow):
    def __init__(self, client: 'AppClient', depth: int):
        super().__init__()
        self.ready_status = True
        self.client = client
        self.depth = depth

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def ready(self, flag: bool=True):
        self.ready_status = flag
        SetReadyStatus(self).action()

    def update_gamestate(self, gs: AppGameState):
        game = gs.game_at_depth(self.depth)
        players: typing.List[ESportsPlayer] = [p for p in game.players.values() if p.controller is not None]
        players = sorted(players, key=lambda p: p.controller)
        table = self.otherUserTableWidget
        table.setRowCount(len(players))
        for row_idx, player in enumerate(players):
            table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(player.controller))
            table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(player.name))
            is_ready = player.name in game.ready_players
            table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem('Ready' if is_ready else 'Not Ready'))
