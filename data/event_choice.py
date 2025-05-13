from typing import List

from data.game_event_base import GameEventBase


class ManagerChoice(GameEventBase):
    choices: List[GameEventBase] = []
    description: str = ''

    def apply(self):
        self.affected_player.event_choices.append(self)

    def short_notation(self):
        return '\nOR\n'.join(event.short_notation() for event in self.choices)

    def text_description(self):
        if self.description == '':
            return self.short_notation()
        else:
            return self.description + '\n\n' + self.short_notation()
