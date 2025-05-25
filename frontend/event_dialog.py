import functools
from typing import Callable

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QDialogButtonBox

from data.game_event import ComposedEvent, SkillChange, MotivationChange, MoneyChange
from data.game_event_base import GameEvent
from data.manager_choice import ManagerChoice


class EventDialog(QDialog):
    def __init__(self, event: ManagerChoice, completion_callback: Callable[[GameEvent], None], parent=None):
        super().__init__(parent)

        self.completion_callback = completion_callback

        self.setWindowTitle(event.title)

        # Erstellen Sie benutzerdefinierte Schaltflächen mit Text und Tooltips
        self.buttonBox = QDialogButtonBox()
        buttons = []
        for choice in event.choices:
            button = self.buttonBox.addButton(self.format_button_text(choice.text_description()),
                                              QDialogButtonBox.AcceptRole)
            button.clicked.connect(functools.partial(self.select_choice, choice))
            buttons.append(button)

        layout = QVBoxLayout()
        message = QLabel(self.format_button_text(event.description))
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.final_choice = None

    def format_button_text(self, label:str):
        pad_before = 4
        pad_after = 4
        lines_before = 1
        lines_after = 1
        lines = [
            '\u2007' * pad_before + line.strip() + '\u2007' * pad_after
            for line in label.split('\n')
        ]
        lines = [''] * lines_before + lines + [''] * lines_after
        return '\n'.join(lines)

    def select_choice(self, choice: GameEvent):
        self.final_choice = choice
        self.accept()
        self.completion_callback(choice)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    event = ManagerChoice(choices=[
        ComposedEvent(events=[SkillChange(hidden_elo_change=+2)], description='Train harder'),
        ComposedEvent(events=[MotivationChange(motivation_change=-1)], description='Be lazy'),
        ComposedEvent(events=[MoneyChange(money_change=+5)], description='Sell the results. Very long button label!'),
    ], description="Test Event", title='Test Event Title')
    dialog = EventDialog(event, completion_callback=lambda choice: print(f"Choice selected: {choice}"))
    dialog.show()
    print(dialog.final_choice)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
