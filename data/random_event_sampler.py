import random
from typing import List

from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event import ComposedEvent, MoneyChange, MotivationChange, SkillChange
from data.game_event_base import GameEvent
from data.manager_choice import ManagerChoice
from data.replace_player import ReplacePlayerWithNewlyGeneratedPlayer
from data.take_action_event import TakeActionEvent
from data.unknown_outcome import UnknownOutcome
from lib.util import EBCP


class RandomEventSampler(EBCP):
    event_probability: float = 1 / 6

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        events: List[GameEvent] = []
        day_idx = (len(game.game_results) * 7 + player.days_until_next_match)
        if random.random() < self.event_probability:
            randomly_occurring_events = []
            requested_money = random.randint(10, 50)
            randomly_occurring_events.append(
                ManagerChoice(
                    title='Pay rise',
                    description=f'{player.name} wants a pay rise.',
                    choices=[
                        ComposedEvent(description='Grant it.', events=[MoneyChange(money_change=-requested_money)]),
                        ComposedEvent(description='Deny it.', events=[MotivationChange(motivation_change=-random.randint(5, 10))]),
                        UnknownOutcome(description='Haggle.', possibilities=[
                            ComposedEvent(description=f'You talk {player.name} out of it.', events=[MoneyChange(money_change=+0)]),
                            ComposedEvent(description=f'{player.name} accepts a one-time bonus of {round(requested_money * 0.75)}.', events=[MoneyChange(money_change=-round(requested_money * 0.75))]),
                            ComposedEvent(description=f'{player.name} is sticking with their demands.', events=[MoneyChange(money_change=-requested_money)]),
                        ]),
                        ComposedEvent(description='Fire them.', events=[ReplacePlayerWithNewlyGeneratedPlayer()]),
                    ],
                )
            )
            new_version = f'{day_idx // (4 * 30)}.{day_idx % (4 * 30) // 7}.{day_idx % 7}'
            metric = random.choice(['skill', 'motivation', 'health', 'money'])
            randomly_occurring_events.append(
                ManagerChoice(
                    title='Patch notes',
                    description=f'Update {new_version} has just been released.',
                    choices=[
                        ComposedEvent(description='Thoroughly analyze.', events=[SkillChange(hidden_elo_change=+0.5)]),
                        TakeActionEvent(description='Try it out against bots.', action_name='botMatch'),
                        TakeActionEvent(description='Try it out in ranked games.', action_name='ranked'),
                        UnknownOutcome(
                            description='Search for bugs and exploits.',
                            possibilities=[
                                ManagerChoice(
                                    title='Exploit found!',
                                    description=f'You find a way to get unreasonably large {metric} values (in-game of course).',
                                    choices=[
                                        ComposedEvent(description='Exploit it', events=[SkillChange(hidden_elo_change=+15)]),
                                        ComposedEvent(description='Sell the knowledge to the highest bidder', events=[MoneyChange(money_change=+150)]),
                                    ]
                                ),
                                ComposedEvent(description=f'You find nothing.', events=[MotivationChange(motivation_change=-1)]),
                            ],
                            probability_weights=[0.1, 1]),
                    ],
                )
            )

            events.append(random.choice(randomly_occurring_events))
        if day_idx % 30 == 0:
            if player.money < 0:
                interest = 0.05 * player.money
                assert interest < 0
                events.append(
                    ComposedEvent(
                        description=f'Interest payment day!',
                        events=[
                            MoneyChange(money_change=interest),
                        ]
                    )
                )
        return events
