from typing import Optional

from pydantic import BaseModel

from data.clan_tag import clan_tag_from_name
from network.my_types import UserName


class ESportsPlayer(BaseModel):
    name: str
    controller: Optional[UserName] = None  # name of the user controlling the player, or None if bot-controlled

    wins: int = 0
    losses: int = 0
    draws: int = 0
    tiebreaker: int = 0

    hidden_elo: float
    visible_elo: float

    def rank_sorting_key(self):
        return (-self.points(), -self.tiebreaker, self.name)

    def points(self):
        return self.wins + 0.5 * self.draws

    def clan_tag(self):
        if self.controller is None:
            return 'BOT'
        return clan_tag_from_name(self.controller)

    def tag_and_name(self):
        return f'[{self.clan_tag()}] {self.name}'
