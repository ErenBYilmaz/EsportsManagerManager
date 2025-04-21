import math
import typing

from PyQt5 import QtWidgets

from data.app_gamestate import AppGameState
from data.esports_player import ESportsPlayer
from frontend.generated.manager_menu import Ui_ManagerWindow
from stories.ready import SetReadyStatus

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
        self.startMatchButton.clicked.connect(self.user_ready)

    def my_player(self):
        return self.client.local_gamestate.game_state.game_at_depth(self.depth).player_controlled_by(self.client.local_gamestate.main_user().username)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def user_ready(self):
        waiting_ui = self.client.open_waiting_window(depth=self.depth)
        waiting_ui.ready(True)

    def update_gamestate(self, gs: AppGameState):
        game = gs.game_at_depth(self.depth)
        players: typing.List[ESportsPlayer] = list(game.players.values())
        players = sorted(players, key=ESportsPlayer.rank_sorting_key)
        self.leagueTableWidget.setRowCount(len(players))
        self.playerNameLabel.setText(self.my_player().name)
        for row_idx, player in enumerate(players):
            place_string = '#' + str(row_idx + 1)
            add_leading_spaces = math.ceil(math.log(len(players), 10)) - len(str(row_idx + 1))
            place_string = ' ' * add_leading_spaces + place_string
            self.leagueTableWidget.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(place_string))
            self.leagueTableWidget.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(player.tag_and_name()))
            self.leagueTableWidget.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(player.points())))
            self.leagueTableWidget.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(player.tiebreaker)))
            self.leagueTableWidget.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f'{player.wins}/{player.draws}/{player.losses}'))
            self.leagueTableWidget.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(str(round(player.visible_elo))))
