from typing import Dict, Optional, List, Set

from pydantic import BaseModel, field_validator

from data.esports_player import ESportsPlayer, PlayerName


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
