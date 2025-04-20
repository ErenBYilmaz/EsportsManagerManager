from typing import List, Literal, Optional

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

    def game_at_depth(self, depth: int) -> Optional[ESportsGame]:
        game = self.game
        for _ in range(depth):
            if game.ongoing_match is None:
                return None
            game = game.ongoing_match
        return game