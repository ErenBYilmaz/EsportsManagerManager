import random
from typing import List, Literal

from pydantic import BaseModel

from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event import ComposedEvent, SkillChange, MoneyChange
from data.game_event_base import GameEvent


class ActionSampler(BaseModel):
    action_name: str

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        if action_name != self.action_name:
            raise ValueError(f"Action name '{action_name}' does not match expected action name '{self.action_name}'")
        return [random.choice(self.possible_events(game, player))]

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        raise NotImplementedError('abstract method')


class HireCoachSampler(ActionSampler):
    action_name: Literal['hireCoach'] = 'hireCoach'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return [
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, and it actually seems to improve {player.name}\'s skill at Esports Manager Manager.',
                events=[
                    MoneyChange(affected_game=game, affected_player=player, money_change=-50),
                    SkillChange(affected_game=game, affected_player=player, hidden_elo_change=+3),
                ]
            ),
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, but it does not seem to improve {player.name}\'s skill at Esports Manager Manager.',
                events=[
                    MoneyChange(affected_game=game, affected_player=player, money_change=-50),
                    SkillChange(affected_game=game, affected_player=player, hidden_elo_change=+0),
                ]
            ),
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, and in the end {player.name} is more confused than smarter.',
                events=[
                    MoneyChange(affected_game=game, affected_player=player, money_change=-50),
                    SkillChange(affected_game=game, affected_player=player, hidden_elo_change=-1),
                ]
            ),
        ]


class EventSampler(BaseModel):
    def samplers(self) -> List[ActionSampler]:
        return [
            HireCoachSampler(),
        ]

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        for s in self.samplers():
            if s.action_name == action_name:
                return s.get_events_for_action(game, player, action_name)
        raise ValueError(f"Unknown action name '{action_name}'")

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return []