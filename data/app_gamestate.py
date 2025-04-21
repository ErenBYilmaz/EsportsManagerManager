import random
from typing import List, Literal, Optional, Dict, Any

from config import NUM_PLAYERS_IN_TOURNAMENT
from data.app_user import AppUser
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_state import GameState
from resources.player_names import PLAYER_NAME_EXAMPLES


class AppGameState(GameState):
    type: Literal['AppGameState'] = 'AppGameState'
    users: List[AppUser] = []
    game: ESportsGame = ESportsGame()

    def lowest_level_game(self) -> ESportsGame:
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
            player = self.random_uncontrolled_player()
            assert player.controller is None
            player.controller = user.username

    @classmethod
    def create(cls, game_name):
        state = AppGameState(users=[], game_name=game_name)
        player_names = random.sample(PLAYER_NAME_EXAMPLES, NUM_PLAYERS_IN_TOURNAMENT)
        for name in player_names:
            player = ESportsPlayer(controller=None,
                                   name=name,
                                   hidden_elo=1700,
                                   visible_elo=1700, )
            state.game.players[player.name] = player
        return state

    def update_from_json(self, json_info: Dict[str, Any]):
        super().update_from_json(json_info)
        if 'game' in json_info:
            self.game = ESportsGame.model_validate(json_info['game'])

    def random_uncontrolled_player(self):
        player_names = [name for name in self.game.players if self.game.players[name].controller is None]
        if len(player_names) == 0:
            return None
        name = random.choice(player_names)
        return self.game.players[name]