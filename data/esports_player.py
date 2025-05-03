from typing import Optional

from pydantic import BaseModel

from data.clan_tag import clan_tag_from_name
from network.my_types import UserName

PlayerName = str


class ESportsPlayer(BaseModel):
    name: PlayerName
    controller: Optional[UserName] = None  # name of the user controlling the player, or None if bot-controlled
    manager: Optional[PlayerName] = None  # name of the manager controlling the player, or None if top-level

    average_rank: float = 0

    hidden_elo: float
    visible_elo: float
    visible_elo_sigma: float

    def rank_sorting_key(self):
        return (self.average_rank, -self.visible_elo, self.name[::-1][len(self.name)//2:])

    def clan_tag(self):
        if self.controller is not None:
            return clan_tag_from_name(self.controller)
        elif self.manager is not None:
            return clan_tag_from_name(self.manager)
        return 'BOT'

    def tag_and_name(self):
        return f'[{self.clan_tag()}] {self.name}'
