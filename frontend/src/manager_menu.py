import functools
import math
import typing

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QListWidgetItem

from data.app_gamestate import AppGameState
from data.custom_trueskill import CustomTrueSkill
from data.esports_player import ESportsPlayer
from data.game_event_base import GameEvent
from data.manager_choice import ManagerChoice
from frontend.event_dialog import ChoiceEventDialog
from frontend.generated.manager_menu import Ui_ManagerWindow
from stories.choose_event import ChooseEventAction
from stories.take_action import TakeManagementAction

if typing.TYPE_CHECKING:
    from frontend.app_client import AppClient


class ManagerMenu(Ui_ManagerWindow):
    def __init__(self, client: 'AppClient', depth: int):
        super().__init__()
        self.client = client
        self.depth = depth
        self.closed = False
        self.dialogs: typing.List[ChoiceEventDialog] = []

    def closeEvent(self, _event):
        self.closed = True

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.stopMicroManageButton.setVisible(self.depth > 0)
        self.startMatchButton.clicked.connect(self.user_ready_for_next_tournament_game)
        self.stopMicroManageButton.clicked.connect(self.stop_micro_manage)
        for button in [
            self.rankedButton,
            self.unrankedButton,
            self.botMatchButton,
            self.streamingButton,
            self.freeTimeButton,
            self.motivationalSpeechButton,
            self.analyzeMetaButton,
            self.nutritionPlanButton,
            self.newStrategyButton,
            self.hireCoachButton,
            self.sabotageButton,
            self.dopingButton,
            self.replacePlayerButton,
            self.analyzeMatchesButton,
        ]:
            button.clicked.connect(functools.partial(self.take_action, button.objectName()))

    def take_action(self, action_name: str):
        if self.my_player().pending_choices:
            for e in self.my_player().pending_choices:
                self.handle_game_event(e)
        if self.my_player().days_until_next_match <= 0:
            self.information('Tournament match today!',
                             'You don\'t have enough time to take this action before the next tournament match. '
                             'Better finish the preparations and get ready.')
            return
        with self.client.handling_errors():
            TakeManagementAction(self, action_name)()

    def my_player(self):
        return self.game().player_controlled_by(self.client.local_gamestate.main_user().username)

    def game(self):
        return self.client.local_gamestate.game_state.game_at_depth(self.depth)

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def user_ready_for_next_tournament_game(self):
        game = self.game()
        if game.ongoing_match is None:
            if not self.client.waiting_menu_open(depth=self.depth):
                if self.microManageRadioButton.isChecked():
                    wait_for = game.condition_to_wait_for_next_start_of_match()
                else:
                    wait_for = game.condition_to_wait_for_next_end_of_match()
                self.client.open_waiting_window(depth=self.depth, wait_for=wait_for)
            else:
                print('Waiting menu already open. Ignoring request to open it.')
        else:
            sub_game_window_open = self.client.manager_menu_open(depth=self.depth + 1) or self.client.waiting_menu_open(depth=self.depth + 1)
            if sub_game_window_open:
                self.information('Error', f'Cannot get ready for a match while one is already ongoing. {self.my_player().tag_and_name()} is already playing.')
            else:
                if self.microManageRadioButton.isChecked():
                    self.client.open_manager_window(depth=self.depth + 1)
                else:
                    self.client.open_waiting_window(depth=self.depth, wait_for=game.condition_to_wait_for_next_end_of_match())
            return

    def stop_micro_manage(self):
        with self.client.handling_errors():
            if not self.client.waiting_menu_open(depth=self.depth - 1):
                parent_game = self.client.local_gamestate.game_state.game_at_depth(self.depth - 1)
                self.client.open_waiting_window(depth=self.depth - 1, wait_for=parent_game.condition_to_wait_for_next_end_of_match())
            else:
                self.client.waiting_menu_at_depth(self.depth - 1).ready(True)
            self.try_close()

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
            print('Game ended, closing manager window')
            self.try_close()
            return
        players: typing.List[ESportsPlayer] = list(game.players.values())
        players = sorted(players, key=ESportsPlayer.rank_sorting_key)
        self.leagueTableWidget.setRowCount(len(players))
        my_player = self.my_player()
        self.playerNameLabel.setText(my_player.name)
        for row_idx, player in enumerate(players):
            place_string = '#' + str(row_idx + 1)
            add_leading_spaces = math.ceil(math.log(len(players), 10)) - len(str(row_idx + 1))
            place_string = ' ' * add_leading_spaces + place_string
            self.leagueTableWidget.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(place_string))
            self.leagueTableWidget.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(player.tag_and_name()))
            self.leagueTableWidget.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f'{player.average_rank:.1f}'))
            self.leagueTableWidget.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(round(player.tournament_elo))))
            self.leagueTableWidget.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(str(len(game.game_results))))
            self.leagueTableWidget.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(game.previous_ranks_string(n=3, player_name=player.name)))
        self.statusWidget.clear()
        self.statusWidget.addItem(QListWidgetItem(f'Managing {my_player.tag_and_name()}'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.days_until_next_match} days until next match'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.money:.2f} €'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.health:.0f} health'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.motivation:.0f} motivation'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.ranked_elo:.0f} ranked match rating'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.bot_match_elo:.0f} bot match performance'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.tournament_elo:.0f} tournament performance'))
        self.statusWidget.addItem(QListWidgetItem(f'{my_player.average_rank:.1f} avg. tournament ranking'))

        for dialog in self.dialogs.copy():
            if not any(choice == dialog.event_
                       for choice in my_player.pending_choices):
                dialog.close()
                self.dialogs.remove(dialog)

    def send_choice(self, choice_title: str, choice: GameEvent):
        with self.client.handling_errors():
            ChooseEventAction(self, choice_title=choice_title, choice=choice)()

    def handle_game_event(self, e: GameEvent):
        if isinstance(e, ManagerChoice):
            dialog = ChoiceEventDialog(e, completion_callback=self.send_choice, parent=self.centralwidget)
            dialog.show()
            self.dialogs.append(dialog)
        else:
            self.information(
                title='Esports Manager Manager',
                msg=e.text_description(),
            )
