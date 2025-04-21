import random
from typing import Dict, Optional, List

from pydantic import BaseModel, field_validator

from config import NUM_PLAYERS_IN_TOURNAMENT
from data.esports_player import ESportsPlayer, PlayerName
from resources.player_names import PLAYER_NAME_EXAMPLES


class ESportsGame(BaseModel):
    players: Dict[str, ESportsPlayer] = {}
    ongoing_match: Optional['ESportsGame'] = None
    ready_players: List[PlayerName] = []

    @field_validator('players')
    @classmethod
    def check_names(cls, v):
        for name, player in v.items():
            if name != player.name:
                raise ValueError(f"Player name '{player.name}' does not match key '{name}'")
        return v

    def create_players(self):
        player_names = random.sample(PLAYER_NAME_EXAMPLES, NUM_PLAYERS_IN_TOURNAMENT - len(self.players))
        for name in player_names:
            player = ESportsPlayer(controller=None,
                                   name=name,
                                   hidden_elo=1700,
                                   visible_elo=1700, )
            self.players[player.name] = player

    def phase(self):
        if self.ongoing_match is not None:
            return 'match'
        return 'management'

    def is_nested(self):
        return self.parent_game is not None

    def player_controlled_by(self, username):
        for player in self.players.values():
            if player.controller == username:
                return player
        return None

    def non_ai_players(self):
        return [player for player in self.players.values() if player.controller is not None]

    def everyone_ready(self):
        return set(p.name for p in self.non_ai_players()).issubset(self.ready_players)

    def start_match(self):
        if self.ongoing_match is not None:
            raise RuntimeError("Match is already ongoing")
        self.ready_players.clear()
        self.ongoing_match = ESportsGame()
        self.ongoing_match.create_players()
        for player, controller in zip(self.ongoing_match.players.values(), self.players.values()):
            player.controller = controller.controller
            player.manager = controller.name
