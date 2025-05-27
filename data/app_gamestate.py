import random
from typing import List, Literal, Optional, Dict, Any

from data.app_user import AppUser
from data.esports_game import ESportsGame
from data.game_state import GameState


class AppGameState(GameState):
    type: Literal['AppGameState'] = 'AppGameState'
    users: List[AppUser] = []
    game: ESportsGame = ESportsGame()

    def lowest_level_game(self) -> ESportsGame:
        game = self.game
        while game.ongoing_match is not None:
            game = game.ongoing_match
        return game

    def depth(self):
        depth = 0
        game = self.game
        while game.ongoing_match is not None:
            depth += 1
            game = game.ongoing_match
        return depth

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
            player = self.random_uncontrolled_player()
            assert player.controller is None
            player.controller = user.username

    @classmethod
    def create(cls, game_name):
        state = AppGameState(users=[], game_name=game_name)
        state.game.create_players()
        return state

    def update_from_json(self, json_info: Dict[str, Any]):
        super().update_from_json(json_info)
        if 'game' in json_info:
            self.game = ESportsGame.from_json(json_info['game'])

    def random_uncontrolled_player(self):
        return self.game.random_uncontrolled_player()
