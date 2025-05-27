import random
from typing import Optional, List

from pydantic import BaseModel, Field

from config import DAYS_BETWEEN_MATCHES, BASE_PLAYER_HEALTH, BASE_PLAYER_MOTIVATION
from data.clan_tag import clan_tag_from_name
from data.custom_trueskill import CustomTrueSkill
from data.manager_choice import ManagerChoice
from data.game_event_base import GameEvent
from data.player_name import PlayerName
from lib.util import EBCP
from network.my_types import UserName
from resources.player_names import PLAYER_NAME_EXAMPLES


class ESportsPlayer(EBCP):
    name: PlayerName
    controller: Optional[UserName] = None  # name of the user controlling the player, or None if bot-controlled
    manager: Optional[PlayerName] = None  # name of the manager controlling the player, or None if top-level

    average_rank: float = 0

    hidden_elo: float
    # below elo values are typically close to hidden_elo + health + motivation
    tournament_elo: float  = Field(default_factory=lambda: ESportsPlayer.starting_elo())
    tournament_elo_sigma: float  = Field(default_factory=lambda: ESportsPlayer.starting_sigma())
    ranked_elo: float = Field(default_factory=lambda: ESportsPlayer.starting_elo())
    ranked_elo_sigma: float = Field(default_factory=lambda: ESportsPlayer.starting_sigma())
    bot_match_elo: float = Field(default_factory=lambda: ESportsPlayer.starting_elo())
    bot_match_elo_sigma: float = Field(default_factory=lambda: ESportsPlayer.starting_sigma())

    money: float = 0
    health: float = 0
    motivation: float = 0
    days_until_next_match: int = DAYS_BETWEEN_MATCHES  # limits the number of actions that can be taken before the next match
    retired: bool = False
    event_history: List[GameEvent] = []
    pending_choices: List[ManagerChoice] = []

    def rank_sorting_key(self):
        return (self.average_rank, -self.tournament_elo, self.name[::-1][len(self.name) // 2:])

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

    @classmethod
    def create(cls):
        return ESportsPlayer(controller=None,
                             name=random.choice(PLAYER_NAME_EXAMPLES),
                             hidden_elo=cls.starting_elo() - BASE_PLAYER_HEALTH - BASE_PLAYER_MOTIVATION + random.normalvariate(0, 100),
                             tournament_elo=cls.starting_elo(),
                             tournament_elo_sigma=ESportsPlayer.starting_sigma(),
                             ranked_elo=cls.starting_elo(),
                             ranked_elo_sigma=ESportsPlayer.starting_sigma(),
                             bot_match_elo=cls.starting_elo(),
                             bot_match_elo_sigma=ESportsPlayer.starting_sigma(),
                             health=BASE_PLAYER_HEALTH + random.normalvariate(0, 5),
                             motivation=BASE_PLAYER_MOTIVATION + random.normalvariate(0, 10),
                             money=1000, )

    @classmethod
    def starting_sigma(cls):
        return CustomTrueSkill().sigma

    @classmethod
    def starting_elo(cls):
        return 1700
