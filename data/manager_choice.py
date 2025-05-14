from typing import List, TYPE_CHECKING

from data.game_event_base import GameEvent

if TYPE_CHECKING:
    from data.esports_game import ESportsGame
    from data.esports_player import ESportsPlayer


class ManagerChoice(GameEvent):
    choices: List[GameEvent]
    description: str = ''

    def apply(self, game: 'ESportsGame', player: 'ESportsPlayer'):
        player.pending_choices.append(self)

    def short_notation(self):
        return '\nOR\n'.join(event.short_notation() for event in self.choices)

    def text_description(self):
        if self.description == '':
            return self.short_notation()
        else:
            return self.description + '\n\n' + self.short_notation()
