from typing import List, Literal

from data.app_user import AppUser
from data.esports_game import ESportsGame
from data.game_state import GameState


class AppGameState(GameState):
    type: Literal['AppGameState'] = 'AppGameState'
    users: List[AppUser] = []
    game: ESportsGame = ESportsGame()

    def lowest_level_game(self):
        game = self.game
        while game.ongoing_match is not None:
            game = game.ongoing_match
