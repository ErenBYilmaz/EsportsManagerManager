from typing import TYPE_CHECKING

from lib.util import EBC, EBCP
if TYPE_CHECKING:
    from data.esports_game import ESportsGame
    from data.esports_player import ESportsPlayer


class GameEvent(EBCP):
    def apply(self, game: 'ESportsGame', player: 'ESportsPlayer'):
        raise NotImplementedError("Abstract method")

    def text_description(self):
        return self.short_notation()

    def short_notation(self):
        raise NotImplementedError(f"Abstract method (type is {type(self).__name__})")
