from typing import TYPE_CHECKING

from data.esports_player import ESportsPlayer
from data.game_event import GameEvent

if TYPE_CHECKING:
    from data.esports_game import ESportsGame


class ReplacePlayerWithNewlyGeneratedPlayer(GameEvent):
    def apply(self, game: 'ESportsGame', player: 'ESportsPlayer'):
        new_player = game.random_uncontrolled_player()
        assert new_player.controller is None

        # in case there was a bot managing the player, that guy now manages our previous player, but keeps their money
        new_player.manager, player.manager = player.manager, new_player.manager
        new_player.money, player.money = player.money, new_player.money
        new_player.days_until_next_match = player.days_until_next_match
        new_player.controller, player.controller = player.controller, new_player.controller

    def short_notation(self):
        return f"-> Player replacement"
