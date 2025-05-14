import random
from typing import List, Literal, Tuple

from pydantic import BaseModel

from config import BASE_PLAYER_HEALTH
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event import ComposedEvent, SkillChange, MoneyChange, HealthChange, MotivationChange
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
        common = [
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, and it actually seems to improve {player.name}\'s skill at Esports Manager Manager.',
                events=[
                    MoneyChange(money_change=-50),
                    SkillChange(hidden_elo_change=+3),
                ]
            ),
        ]
        return [
            *(common * 3),
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, but it does not seem to improve {player.name}\'s skill at Esports Manager Manager.',
                events=[
                    MoneyChange(money_change=-50),
                    SkillChange(hidden_elo_change=+0),
                ]
            ),
            ComposedEvent(
                description=f'You pay a lot of money to hire an instructor, and in the end {player.name} is more confused than smarter.',
                events=[
                    MoneyChange(money_change=-50),
                    SkillChange(hidden_elo_change=-1),
                ]
            ),
            ComposedEvent(
                description=f'You were not able to find an instructor to hire.',
                events=[
                    MoneyChange(money_change=-0),
                    SkillChange(hidden_elo_change=+0),
                ]
            ),
        ]


class OptimizeNutritionPlanSampler(ActionSampler):
    action_name: Literal['nutritionPlan'] = 'nutritionPlan'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        common_events = [
            ComposedEvent(
                description=f'{player.name} is feeling well.',
                events=[
                    HealthChange(health_change=+1),
                    MotivationChange(motivation_change=+0.5),
                ]
            ),
        ]
        conditional_events = []
        if player.health < BASE_PLAYER_HEALTH:
            conditional_events.append(
                ComposedEvent(
                    description=f'After some analysis, you just pick the standard nutrition plan that everyone else is on.',
                    events=[
                        MoneyChange(money_change=-20),
                        HealthChange(health_change=+1),
                        MotivationChange(motivation_change=+0.5),
                    ]
                )
            )
        if player.health >= BASE_PLAYER_HEALTH + 5:
            conditional_events.append(
                ComposedEvent(
                    description=f'You are already very satisfied with the current plan. You were even able to make some money by sell it online.',
                    events=[
                        MoneyChange(money_change=+10),
                    ]
                )
            )
        results = [
            *(common_events * 3),
            *conditional_events,
            ComposedEvent(
                description=f'{player.name} shows an allergic response.',
                events=[
                    HealthChange(health_change=-3),
                ]
            ),
            ComposedEvent(
                description=f'The optimized nutrition plan is more expensive than the previous plan. But it works!',
                events=[
                    MoneyChange(money_change=-20),
                    HealthChange(health_change=+1),
                    MotivationChange(motivation_change=+0.5),
                ]
            ),
            ComposedEvent(
                description=f'While it did not help much with {player.name}\'s performance, you were able to save some money on groceries.',
                events=[
                    MoneyChange(money_change=+10),
                ]
            ),
        ]
        return results


class EventSampler(BaseModel):
    def samplers(self) -> List[ActionSampler]:
        return [
            HireCoachSampler(),
            OptimizeNutritionPlanSampler(),
        ]

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        for s in self.samplers():
            if s.action_name == action_name:
                return s.get_events_for_action(game, player, action_name)
        raise ValueError(f"Unknown action name '{action_name}'")

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return []