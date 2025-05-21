from typing import TYPE_CHECKING

from data.esports_player import ESportsPlayer
from data.game_event import GameEvent

if TYPE_CHECKING:
    from data.esports_game import ESportsGame


class ReplacePlayerWithNewlyGeneratedPlayer(GameEvent):
    def apply(self, game: 'ESportsGame', player: 'ESportsPlayer'):
        new_player = ESportsPlayer.create()
        new_player.controller = player.controller
        new_player.manager = player.manager
        new_player.hidden_elo = player.hidden_elo
        new_player.visible_elo = player.visible_elo
        new_player.visible_elo_sigma = player.visible_elo_sigma
        new_player.money = player.money
        del game.players[player.name]
        game.players[new_player.name] = new_player

    def short_notation(self):
        return f"Player replacement"
