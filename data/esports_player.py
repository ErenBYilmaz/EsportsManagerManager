import random
from typing import Optional, List

from pydantic import BaseModel

from config import DAYS_BETWEEN_MATCHES, BASE_PLAYER_HEALTH
from data.clan_tag import clan_tag_from_name
from data.custom_trueskill import CustomTrueSkill
from data.manager_choice import ManagerChoice
from data.game_event_base import GameEvent
from data.player_name import PlayerName
from network.my_types import UserName
from resources.player_names import PLAYER_NAME_EXAMPLES


class ESportsPlayer(BaseModel):
    name: PlayerName
    controller: Optional[UserName] = None  # name of the user controlling the player, or None if bot-controlled
    manager: Optional[PlayerName] = None  # name of the manager controlling the player, or None if top-level

    average_rank: float = 0

    hidden_elo: float
    visible_elo: float  # typically close to hidden_elo + health + motivation
    visible_elo_sigma: float

    money: float = 0
    health: float = 0
    motivation: float = 0
    days_until_next_match: int = DAYS_BETWEEN_MATCHES  # limits the number of actions that can be taken before the next match
    retired: bool = False
    event_history: List[GameEvent] = []
    pending_choices: List[ManagerChoice] = []

    def rank_sorting_key(self):
        return (self.average_rank, -self.visible_elo, self.name[::-1][len(self.name) // 2:])

    def clan_tag(self):
        if self.controller is not None:
            return clan_tag_from_name(self.controller)
        elif self.manager is not None:
            return clan_tag_from_name(self.manager)
        return 'BOT'

    def tag_and_name(self):
        return f'[{self.clan_tag()}] {self.name}'

    def hidden_skill(self):
        return self.hidden_elo + self.health + self.motivation

    @staticmethod
    def create():
        return ESportsPlayer(controller=None,
                             name=random.choice(PLAYER_NAME_EXAMPLES),
                             hidden_elo=1700 - 85 - 70 + random.normalvariate(0, 100),
                             visible_elo=1700,
                             health=BASE_PLAYER_HEALTH + random.normalvariate(0, 5),
                             motivation=70 + random.normalvariate(0, 10),
                             visible_elo_sigma=CustomTrueSkill().sigma,
                             money=1000, )
