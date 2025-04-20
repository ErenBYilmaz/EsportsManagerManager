import random
from typing import List, Literal, Optional

from data.app_user import AppUser
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_state import GameState
from resources.player_names import PLAYER_NAME_EXAMPLES


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

    def user_by_name(self, user_name) -> AppUser:
        return super().user_by_name(user_name)

    def new_user(self, user: AppUser, initialize):
        super().new_user(user, initialize)
        if initialize:
            player = ESportsPlayer(controller=user.username,
                                   name=f'[{user.clan_tag()}] {random.choice(PLAYER_NAME_EXAMPLES)}',
                                   hidden_elo=1700,
                                   visible_elo=1700,)
