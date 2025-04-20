from typing import Union

from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem, QListWidget

from data.app_user import AppUser
from data.recipe import Recipe, RecipeIdentifier
from data.trade import Trade
from frontend.client import Client
from frontend.src.crafting_menu import CraftingMenu, CraftingWindow
from frontend.src.create_trade_offer_menu import CreateTradeOfferMenu, CreateTradeOfferWindow
from frontend.src.multiplayer_menu import MultiplayerMenu
from frontend.src.pipeline_menu import PipelineMenu
from frontend.src.recipe_menu import RecipeMenu
from frontend.src.settings_menu import SettingsMenu
from lib.util import EBC
from network.my_types import ResourceName
from stories.error_message import ErrorMessage


class NotAPattern(EBC):
    pass


class AppClient(Client):
    def __init__(self):
        super().__init__()
        self.crafting_windows: List[QtWidgets.QMainWindow] = []
        self.crafting_uis: List[CraftingMenu] = []
        self.multiplayer_windows: List[QtWidgets.QMainWindow] = []
        self.multiplayer_uis: List[MultiplayerMenu] = []
        self.recipe_windows: List[QtWidgets.QMainWindow] = []
        self.recipe_uis: List[RecipeMenu] = []
        self.pipeline_builder_windows: List[QtWidgets.QMainWindow] = []
        self.pipeline_builder_uis: List[PipelineMenu] = []
        self.trade_offer_creation_windows: List[QtWidgets.QMainWindow] = []
        self.trade_offer_creation_uis: List[CreateTradeOfferMenu] = []
        self.settings_windows: List[SettingsMenu] = []

    def open_first_window(self):
        self.open_crafting_window()

    def open_crafting_window(self):
        with self.handling_errors():
            crafting_window = CraftingWindow()
            crafting_ui = CraftingMenu(self)
            crafting_ui.setupUi(crafting_window)
            crafting_window.show()
            self.crafting_windows.append(crafting_window)
            self.crafting_uis.append(crafting_ui)
            self.check_game_state()

    def open_settings_window(self):
        with self.handling_errors():
            settings_window = QtWidgets.QMainWindow()
            settings_ui = SettingsMenu(self)
            settings_ui.setupUi(settings_window)
            settings_window.show()
            self.settings_windows.append(settings_window)

    def open_multiplayer_window(self):
        with self.handling_errors():
            multiplayer_window = QtWidgets.QMainWindow()
            multiplayer_ui = MultiplayerMenu(self)
            multiplayer_ui.setupUi(multiplayer_window)
            multiplayer_window.show()
            self.multiplayer_windows.append(multiplayer_window)
            self.multiplayer_uis.append(multiplayer_ui)
            self.check_game_state()

    def show_last_crafted_recipe(self):
        with self.handling_errors():
            if self.last_crafted_recipe is None:
                raise ErrorMessage('You have not crafted a recipe yet.')
            self.last_crafted_recipe: Recipe
            self.open_recipe_window(recipe_id=self.last_crafted_recipe.identifier())

    def open_default_recipe_window(self):
        self.open_recipe_window()

    def show_recipes_by_output(self, name: ResourceName):
        self.open_recipe_window(output_resource=name)

    def show_recipes_by_input(self, name: ResourceName):
        self.open_recipe_window(input_resource=name)

    def open_recipe_window(self, output_resource: ResourceName = None, input_resource: ResourceName = None, pattern_name: Union[str, NotAPattern] = None,
                           crafting_machine_name: str = None,
                           recipe_id: RecipeIdentifier = None):
        with self.handling_errors():
            if crafting_machine_name is not None and pattern_name is not None and not isinstance(pattern_name, NotAPattern):
                raise ValueError
            if recipe_id is not None and pattern_name is not None and not isinstance(pattern_name, NotAPattern):
                raise ValueError
            if crafting_machine_name is not None and pattern_name is None:
                pattern_name = NotAPattern()
            recipe_window = QtWidgets.QMainWindow()
            recipe_ui = RecipeMenu(self)
            recipe_ui.setupUi(recipe_window)
            recipe_window.show()
            self.recipe_windows.append(recipe_window)
            self.recipe_uis.append(recipe_ui)
            self.check_game_state()
            if output_resource is not None:
                recipe_ui.set_output_resource_filter(output_resource)
            if input_resource is not None:
                recipe_ui.set_input_resource_filter(input_resource)
            if crafting_machine_name is not None:
                recipe_ui.select_crafting_machine_name(crafting_machine_name)
            if isinstance(pattern_name, NotAPattern):
                recipe_ui.show_recipes()
            elif pattern_name is not None and isinstance(pattern_name, str):
                recipe_ui.show_pattern(pattern_name)
            if recipe_id is not None:
                recipe_ui.show_specific_recipe(recipe_id)

    def open_pipeline_builder(self):
        with self.handling_errors():
            new_window = QtWidgets.QMainWindow()
            new_ui = PipelineMenu(self)
            new_ui.setupUi(new_window)
            new_window.show()
            self.pipeline_builder_windows.append(new_window)
            self.pipeline_builder_uis.append(new_ui)
            self.check_game_state()

    def open_trade_offer_creation_window(self):
        with self.handling_errors():
            new_window = CreateTradeOfferWindow()
            new_ui = CreateTradeOfferMenu(self)
            new_ui.setupUi(new_window)
            new_window.show()
            self.trade_offer_creation_windows.append(new_window)
            self.trade_offer_creation_uis.append(new_ui)
            self.check_game_state()

    def after_state_update(self):
        my_resources = self.local_gamestate.main_user().resource_inventory
        gs = self.local_gamestate.game_state
        chat_messages_before = gs._old_chat_messages
        my_machines = self.local_gamestate.my_crafting_machines()

        for ui in self.crafting_uis:
            ui.update_resource_table()
            ui.update_machine_info(my_machines)
            ui.update_crafting_preview()

        for ui in self.recipe_uis:
            ui.update_display(gs)

        for ui in self.pipeline_builder_uis:
            my_patterns = self.local_gamestate.patterns(only_craftable_by_me=ui.onlyCraftableCheckBox.isChecked(), )
            widget: QListWidget = ui.availableRecipesListWidget
            if widget.count() != len(my_patterns):
                widget.clear()
                widget.addItems([p.name for p in my_patterns])
                for i in range(widget.count()):
                    if isinstance(my_patterns[i], Trade):
                        color = '#95d4ff'
                        widget.item(i).setBackground(QColor(color))

        for ui in self.trade_offer_creation_uis:
            ui.update_available_recipes()
            ui.update_resource_table()

        for ui in self.multiplayer_uis:
            if gs.chat_messages != chat_messages_before or len(chat_messages_before) != ui.chatListWidget.count():
                ui.chatListWidget.clear()
                ui.chatListWidget.addItems(m.display_text() for m in gs.chat_messages)
            if len(gs.users) != ui.otherUserTableWidget.rowCount():
                ui.otherUserTableWidget.setRowCount(len(gs.users))
            for r_idx, user in enumerate(gs.users):
                user: AppUser
                ui.otherUserTableWidget.setItem(r_idx, 0, QTableWidgetItem(user.username))
                ui.otherUserTableWidget.setItem(r_idx, 1, QTableWidgetItem(f'{gs.user_tier(user.username): 3d}'))
                ui.otherUserTableWidget.setItem(r_idx, 2, QTableWidgetItem(f'{user.crafts: 12d}'))
                ui.otherUserTableWidget.setItem(r_idx, 3, QTableWidgetItem(f'{len(gs.resource_discoveries[user.username]):6d}'))
                ui.otherUserTableWidget.setItem(r_idx, 4, QTableWidgetItem(f'{len(gs.property_discoveries[user.username]):6d}'))
            if len(my_resources) != ui.sendResourceBox.count():
                ui.sendResourceBox.clear()
                ui.sendResourceBox.addItems(my_resources.names_sorted_by_tier())
