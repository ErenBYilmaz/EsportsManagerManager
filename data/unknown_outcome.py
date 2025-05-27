import random
from typing import List, TYPE_CHECKING, Optional

from data.game_event_base import GameEvent

if TYPE_CHECKING:
    from data.esports_game import ESportsGame
    from data.esports_player import ESportsPlayer


class UnknownOutcome(GameEvent):
    possibilities: List[GameEvent]
    probability_weights: Optional[List[float]] = None
    description: str = ''

    def apply(self, game: 'ESportsGame', player: 'ESportsPlayer'):
        event: GameEvent = self.sample_event()
        event.apply(game, player)

    def sample_event(self) -> GameEvent:
        return random.choices(
            self.possibilities,
            weights=self.probability_weights if self.probability_weights else None,
            k=1
        )[0]

    def short_notation(self):
        return 'Unknown outcome'

    def text_description(self):
        if self.description == '':
            return self.short_notation()
        else:
            return self.description + '\n\n' + self.short_notation()
