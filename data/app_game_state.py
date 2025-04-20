from typing import List

from data.app_user import AppUser
from data.esports_game import ESportsGame
from data.game_state import GameState


class AppGameState(GameState):
    users: List[AppUser] = []
    game: ESportsGame = ESportsGame()
