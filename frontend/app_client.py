from typing import List

from PyQt5 import QtWidgets

from frontend.client import Client
from frontend.src.manager_menu import ManagerMenu
from frontend.src.settings_menu import SettingsMenu
from lib.util import EBC


class NotAPattern(EBC):
    pass


class AppClient(Client):
    def __init__(self):
        super().__init__()
        self.manager_menus: List[ManagerMenu] = []
        self.settings_menus: List[SettingsMenu] = []
        self.open_windows: List[QtWidgets.QMainWindow] = []

    def open_first_window(self):
        self.open_manager_window()

    def open_manager_window(self, depth=0):
        with self.handling_errors():
            crafting_window = QtWidgets.QMainWindow()
            crafting_ui = ManagerMenu(self, depth=depth)
            crafting_ui.setupUi(crafting_window)
            crafting_window.show()
            self.manager_menus.append(crafting_ui)
            self.open_windows.append(crafting_window)
            self.check_game_state()

    def open_settings_window(self):
        with self.handling_errors():
            settings_window = QtWidgets.QMainWindow()
            settings_ui = SettingsMenu(self)
            settings_ui.setupUi(settings_window)
            settings_window.show()
            self.settings_menus.append(settings_ui)
            self.open_windows.append(settings_window)

    def after_state_update(self):
        gs = self.local_gamestate.game_state
        for ui in self.manager_menus:
            ui.update_gamestate(gs)
        for ui in self.settings_menus:
            ui.update_gamestate(gs)
