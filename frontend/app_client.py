from typing import List

from PyQt5 import QtWidgets

from frontend.client import Client
from frontend.src.manager_menu import ManagerMenu
from frontend.src.settings_menu import SettingsMenu
from frontend.src.waiting_menu import WaitingMenu
from data.waiting_condition import WaitingCondition
from lib.util import EBC


class NotAPattern(EBC):
    pass


class AppClient(Client):
    def __init__(self):
        super().__init__()
        self.manager_menus: List[ManagerMenu] = []
        self.settings_menus: List[SettingsMenu] = []
        self.waiting_menus: List[WaitingMenu] = []
        self.open_windows: List[QtWidgets.QMainWindow] = []
        self.closed = False

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

    def manager_menu_open(self, depth: int):
        for m in self.manager_menus:
            if m.depth == depth:
                return True

    def waiting_menu_open(self, depth: int):
        return self.waiting_menu_at_depth(depth) is not None

    def waiting_menu_at_depth(self, depth: int):
        for m in self.waiting_menus:
            if m.depth == depth:
                return m

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
        for menu_list in [self.manager_menus, self.settings_menus, self.waiting_menus]:
            self.cleanup_closed_menus(menu_list)
            for ui in menu_list:
                ui.update_gamestate(gs)
            self.cleanup_closed_menus(menu_list)

    def cleanup_closed_menus(self, menu_list):
        for ui in menu_list.copy():
            if ui.closed:
                menu_list.remove(ui)
                self.open_windows.remove(ui.centralwidget.window())

    def open_waiting_window(self, depth: int, wait_for: WaitingCondition):
        with self.handling_errors():
            waiting_window = QtWidgets.QMainWindow()
            waiting_ui = WaitingMenu(self, depth=depth, wait_for=wait_for)
            waiting_ui.setupUi(waiting_window)
            waiting_window.show()
            self.waiting_menus.append(waiting_ui)
            self.open_windows.append(waiting_window)
            waiting_ui.ready(True)
            self.check_game_state()
        return waiting_ui
