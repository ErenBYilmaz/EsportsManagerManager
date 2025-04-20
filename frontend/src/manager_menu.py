import typing

from PyQt5 import QtWidgets

from data.app_game_state import AppGameState
from data.esports_player import ESportsPlayer
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
        self.stopMicroManageButton.setVisible(self.depth > 0)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def update_gamestate(self, gs: AppGameState):
        game = gs.game_at_depth(self.depth)
        players: typing.List[ESportsPlayer] = list(game.players.values())
        players = sorted(players, key=ESportsPlayer.rank_sorting_key)
        self.leagueTableWidget.setRowCount(len(players))
        for row_idx, player in enumerate(players):
            self.leagueTableWidget.setItem(row_idx, 0, QtWidgets.QTableWidgetItem('#'+str(row_idx + 1)))
            self.leagueTableWidget.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(player.name)))
            self.leagueTableWidget.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(player.points())))
            self.leagueTableWidget.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(player.tiebreaker)))
            self.leagueTableWidget.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f'{player.wins}/{player.draws}/{player.losses}'))
            self.leagueTableWidget.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(str(round(player.visible_elo))))