import typing
from typing import Optional, List

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QHeaderView, QMainWindow, QWidget, QTableWidgetItem, QTableWidget
from resources.tick_name import TICK_NAME

from data.crafting_machine import CraftingMachine
from data.crafting_materials import CraftingMaterials
from data.recipe import Recipe
from data.resource import Resource
from frontend.generated.crafting_menu import Ui_CraftingWindow
from stories.craft import Craft
from stories.error_message import ErrorMessage

if typing.TYPE_CHECKING:
    import frontend.app_client


class CraftingWindow(QMainWindow):
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        for obj in self.centralWidget().children():
            obj: QWidget
            if obj.objectName() == 'resource_table':
                obj: QTableWidget
                obj.resize(obj.geometry().width(), self.centralWidget().height() - 64)
                obj.setColumnWidth(0, obj.width() * 0.10)
                obj.setColumnWidth(1, obj.width() * 0.63)
                obj.setColumnWidth(2, obj.width() * 0.23)
            elif obj.objectName() == 'crafting_machine_table':
                obj.resize(obj.geometry().width(), self.centralWidget().height() - 114)
            elif obj.objectName() == 'craftingMachineInfoLabel':
                obj.move(obj.geometry().x(), self.centralWidget().height() - 75)
            elif obj.objectName() == 'hideUnavailableResourcesCheckBox':
                obj.move(obj.geometry().x(), self.centralWidget().height() - 25)


class CraftingMenu(Ui_CraftingWindow):
    def __init__(self, client: 'frontend.app_client.AppClient'):
        super().__init__()
        self.client = client
        self.added_resources = CraftingMaterials()
        self.selected_resource: Optional[Resource] = None
        self.selected_crafting_machine: Optional[CraftingMachine] = None

    def setupUi(self, MainWindow: CraftingWindow):
        super().setupUi(MainWindow)
        self.ResourceInfoLabel.setText('')
        MainWindow.setWindowTitle(f'TimeZone - {self.client.local_gamestate.game_state.game_name} - Crafting')
        self.resource_table.currentItemChanged.connect(self.update_resource_info)
        # self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.crafting_machine_table.currentItemChanged.connect(self.update_crafting_machine_info)
        self.crafting_machine_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.craftButton.clicked.connect(Craft(self))
        self.addResourceButton.clicked.connect(self.add_resource_for_crafting)
        self.removeResourceButton.clicked.connect(self.remove_resource_from_crafting)
        self.clearResourcesButton.clicked.connect(self.clear_added_resources)
        self.showRecipeButton.clicked.connect(self.client.open_default_recipe_window)
        self.pipelineBuilderButton.clicked.connect(self.client.open_pipeline_builder)
        self.hideUnavailableResourcesCheckBox.clicked.connect(self.client.check_game_state)
        self.coopButton.clicked.connect(self.client.open_multiplayer_window)
        self.showLastCraftedRecipeButton.clicked.connect(self.client.show_last_crafted_recipe)
        self.tradingButton.clicked.connect(self.client.open_trade_offer_creation_window)
        self.cheatsButton.clicked.connect(self.try_cheating)

        QtWidgets.QShortcut(QtCore.Qt.Key_O, self.resource_table, activated=self.show_recipes_by_selected_output)
        QtWidgets.QShortcut(QtCore.Qt.Key_U, self.resource_table, activated=self.show_recipes_by_selected_input)

    def add_resource_for_crafting(self):
        r = self.selected_resource
        if r is None:
            with self.client.handling_errors():
                raise ErrorMessage('Select a resource first')
            return
        self.added_resources.append(r, count=1)
        self.update_added_resource_text()

    def try_cheating(self):
            # noinspection PyUnusedLocal
        cheater = self.client.local_gamestate.main_user().username
        del cheater
        self.cheatsButton.setEnabled(False)
        self.information('Punishment for cheating',
                               'Your act of cheating has been recorded and the corresponding recording has been deleted.\n\n'
                               'You are permanently banned from using the cheat button again on this server until you restart the game or re-join the server.\n\n'
                               'Moderators do not have the power to lift this ban.\n\n'
                               'Asking for help from a moderator may result in a permanent ban from this button.')

    def update_resource_table(self):
        my_resources = self.client.local_gamestate.main_user().resource_inventory
        self.resource_table.setRowCount(len(self.displayed_resources()))
        for r_idx, r in enumerate(self.displayed_resources()):
            self.resource_table.setItem(r_idx, 0, QTableWidgetItem(str(r.tier())))
            self.resource_table.setItem(r_idx, 1, QTableWidgetItem(r.name))
            if r in my_resources:
                self.resource_table.setItem(r_idx, 2, QTableWidgetItem(str(my_resources[r])))
            else:
                self.resource_table.setItem(r_idx, 2, QTableWidgetItem('0'))

    def update_machine_info(self, my_machines: List[CraftingMachine]):
        self.crafting_machine_table.setRowCount(len(my_machines))
        for m_idx, m in enumerate(my_machines):
            self.crafting_machine_table.setItem(m_idx, 0, QTableWidgetItem(m.name))
            self.crafting_machine_table.setItem(m_idx, 1, QTableWidgetItem(f'{m.duration} {TICK_NAME}s'))

    def remove_resource_from_crafting(self):
        r = self.selected_resource
        if r is None:
            with self.client.handling_errors():
                raise ErrorMessage('Select a resource first')
            return
        self.added_resources.remove(r, count=1)
        self.update_added_resource_text()

    def show_recipes_by_selected_output(self):
        with self.client.handling_errors():
            r = self.selected_resource
            if r is None:
                raise ErrorMessage('Select a resource first')
            self.client.show_recipes_by_output(r.name)

    def show_recipes_by_selected_input(self):
        with self.client.handling_errors():
            r = self.selected_resource
            if r is None:
                raise ErrorMessage('Select a resource first')
            self.client.show_recipes_by_input(r.name)

    def clear_added_resources(self):
        self.added_resources.clear()
        self.update_added_resource_text()

    def update_added_resource_text(self):
        text = 'Resources added for crafting:\n'
        for r, n in self.added_resources.items():
            text += f' {r.name} ({n})\n'
        self.AddedResourceInfoLabel.setText(text)
        self.update_crafting_preview()

    def update_resource_info(self, item, previous):
        row_idx = item.row()
        resource: Resource = self.displayed_resources()[row_idx]
        self.selected_resource = resource
        self.ResourceInfoLabel.setText(resource.description())

    def displayed_resources(self) -> List[Resource]:
        if self.hideUnavailableResourcesCheckBox.isChecked():
            inv = self.client.local_gamestate.main_user().resource_inventory
            result = [r for r in self.client.local_gamestate.game_state.resources.values()
                      if r in inv and inv[r] > 0]
        else:
            result = list(self.client.local_gamestate.game_state.resources.values())
        result = sorted(result, key=lambda r: (r.tier(), r.name))
        return result

    def update_crafting_machine_info(self, previous):
        row_idx = self.crafting_machine_table.currentRow()
        if row_idx < 0:
            return
        machine: CraftingMachine = self.client.local_gamestate.my_crafting_machines()[row_idx]
        self.selected_crafting_machine = machine
        info_text = f'{machine.name}\n'
        info_text += '-' * len(machine.name) + f'\n'
        info_text += f'Duration: {machine.duration} {TICK_NAME}s\n'
        self.craftingMachineInfoLabel.setText(info_text)
        self.update_crafting_preview()

    def critical(self, title, msg):
        QtWidgets.QMessageBox.critical(self.centralwidget, title, msg)

    def information(self, title, msg):
        QtWidgets.QMessageBox.information(self.centralwidget, title, msg)

    def update_crafting_preview(self):
        if self.selected_crafting_machine is None:
            self.craftingPreviewLabel.setText(QtCore.QCoreApplication.translate("CraftingWindow", "Select a crafting machine to display information here"))
            return
        machine_name = self.selected_crafting_machine.name
        recipe = self.client.local_gamestate.main_user().recipe_by_inputs(machine_name, self.added_resources)
        if recipe is None:
            self.craftingPreviewLabel.setText(QtCore.QCoreApplication.translate("CraftingWindow", "You don\'t know this recipe yet. Click \"Craft\" to see results."))
            return
        self.craftingPreviewLabel.setText('Recipe Preview\n---------------\n' + recipe.description())
