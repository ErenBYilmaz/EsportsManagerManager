import math
import typing

from PyQt5 import QtWidgets

from data.app_gamestate import AppGameState
from data.esports_player import ESportsPlayer
from frontend.generated.manager_menu import Ui_ManagerWindow
from frontend.src.waiting_menu import WaitingCondition

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class ManagerMenu(Ui_ManagerWindow):
    def __init__(self, client: 'AppClient', depth: int):
        super().__init__()
        self.client = client
        self.depth = depth
        self.closed = False

    def closeEvent(self, _event):
        self.closed = True

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.stopMicroManageButton.setVisible(self.depth > 0)
        self.startMatchButton.clicked.connect(self.user_ready_for_next_tournament_game)
        self.stopMicroManageButton.clicked.connect(self.stop_micro_manage)

    def my_player(self):
        return self.game().player_controlled_by(self.client.local_gamestate.main_user().username)

    def game(self):
        return self.client.local_gamestate.game_state.game_at_depth(self.depth)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def user_ready_for_next_tournament_game(self):
        if self.game().ongoing_match is None:
            if not self.client.waiting_menu_open(depth=self.depth):
                wait_for: WaitingCondition = 'match_begin' if self.microManageRadioButton.isChecked() else 'match_end'
                waiting_ui = self.client.open_waiting_window(depth=self.depth, wait_for=wait_for)
                waiting_ui.ready(True)
        else:
            if self.client.manager_menu_open(depth=self.depth + 1) or self.client.waiting_menu_open(depth=self.depth + 1):
                self.information('Error', f'Cannot get ready for a match while one is already ongoing. {self.my_player().tag_and_name()} is already playing.')
            else:
                if self.microManageRadioButton.isChecked():
                    self.client.open_manager_window(depth=self.depth + 1)
                else:
                    self.client.open_waiting_window(depth=self.depth + 1, wait_for='match_end')
            return

    def user_ready_for_end_of_game(self):
        if self.game() is not None:
            waiting_ui = self.client.open_waiting_window(depth=self.depth, wait_for='match_end')
            waiting_ui.ready(True)

    def stop_micro_manage(self):
        if not self.client.waiting_menu_open(depth=self.depth):
            waiting_ui = self.client.open_waiting_window(depth=self.depth, wait_for='match_end')
            waiting_ui.ready(True)
        self.closed = True
        self.centralwidget.window().close()
        self.user_ready_for_end_of_game()

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
            self.leagueTableWidget.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(player.average_rank)))
            self.leagueTableWidget.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(round(player.visible_elo))))
