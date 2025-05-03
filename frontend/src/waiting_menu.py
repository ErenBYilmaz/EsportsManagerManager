import typing
from typing import Literal

from PyQt5 import QtWidgets

from data.app_gamestate import AppGameState
from data.esports_player import ESportsPlayer
from frontend.generated.waiting_menu import Ui_WaitingWindow
from stories.ready import SetReadyStatus

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient

WaitingCondition = Literal['match_begin', 'match_end']


class WaitingMenu(Ui_WaitingWindow):
    def __init__(self, client: 'AppClient', depth: int, wait_for: WaitingCondition):
        super().__init__()
        # examples:
        # depth=0, wait_for='match_begin': waiting for the match to begin
        # depth=0, wait_for='match_end': waiting for the match to end
        # depth=1, wait_for='match_begin': waiting for a submatch of the match to begin
        # depth=2, wait_for='match_end': waiting for a submatch of a submatch of the match to end
        self.ready_status = True
        self.client = client
        self.depth = depth
        self.wait_for = wait_for
        self.closed = False

    def closeEvent(self, _event):
        self.closed = True

    def setupUi(self, WaitingWindow):
        super().setupUi(WaitingWindow)
        self.readyToggleButton.clicked.connect(self.toggle_ready)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def ready(self, flag: bool = True):
        self.ready_status = flag
        SetReadyStatus(self)()

    def toggle_ready(self):
        self.ready(not self.ready_status)

    def update_button_text(self):
        if self.ready_status:
            self.readyToggleButton.setText('Your status: Ready')
        else:
            self.readyToggleButton.setText('Your status: Not Ready')

    def try_close(self):
        self.closed = True
        try:
            self.centralwidget.window().close()
        except RuntimeError as e:
            if 'wrapped C/C++ object of type QWidget has been deleted' in str(e):
                print('Window already closed. Ignoring error.')
                return
            raise

    def update_gamestate(self, gs: AppGameState):
        game = gs.game_at_depth(self.depth)
        if game is None:
            print(f'Game ended at d={self.depth}, closing waiting window')
            self.try_close()
            return
        if self.wait_for == 'match_begin':
            if game.ongoing_match is not None:
                print(f'Match begins at d={self.depth}, closing waiting window')
                self.client.open_manager_window(depth=self.depth + 1)
                self.try_close()
                return
        if self.wait_for == 'match_end':
            if game.ongoing_match is None:
                print(f'Match ended at d={self.depth}, closing waiting window')
                if not self.client.manager_menu_open(depth=self.depth):
                    print(f'Re-opening manager window at d={self.depth}')
                    self.client.open_manager_window(depth=self.depth)
                self.try_close()
                return
        players: typing.List[ESportsPlayer] = [p for p in game.players.values() if p.controller is not None]
        players = sorted(players, key=lambda p: p.controller)
        table = self.otherUserTableWidget
        table.setRowCount(len(players))
        for row_idx, player in enumerate(players):
            table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(player.controller))
            table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(player.name))
            is_ready = player.name in game.ready_players
            table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem('Ready' if is_ready else 'Not Ready'))
        self.update_button_text()
