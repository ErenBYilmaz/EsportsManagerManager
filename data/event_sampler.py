import random
from typing import List, Literal

import numpy
from pydantic import BaseModel
from scipy.special import expit

from config import BASE_PLAYER_HEALTH, NUM_BOTS_IN_TOURNAMENT, BASE_PLAYER_MOTIVATION
from data.custom_trueskill import CustomTrueSkill
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


class PlayRankedMatchesSampler(ActionSampler):
    action_name: Literal['ranked'] = 'ranked'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        ts = CustomTrueSkill()
        num_games = random.randint(5, 15)
        player = player.model_copy()  # dont change the original player
        player.visible_elo_sigma = ts.sigma
        player_placements = []
        opponent_ratings = []
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo -= 100  # those randoms are simply not as good as us professionals
                o.visible_elo = o.hidden_skill()
                o.visible_elo_sigma /= 10
                opponent_ratings.append(o.visible_elo)

            unranked_game_players = [player] + random_opponents

            ts = CustomTrueSkill()
            visible_ratings = [(ts.create_rating(mu=player.visible_elo, sigma=player.visible_elo_sigma),) for player in unranked_game_players]
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in unranked_game_players]
            ranks = ts.sample_ranks(true_ratings)
            assert len(visible_ratings) == len(unranked_game_players) == len(ranks)
            new_ratings = ts.rate(visible_ratings, ranks)
            assert len(new_ratings) == len(unranked_game_players)
            for new_ratings, p in zip(new_ratings, unranked_game_players):
                assert len(new_ratings) == 1
                p.visible_elo = new_ratings[0].mu
                p.visible_elo_sigma = new_ratings[0].sigma

            player_placements.append(ranks[0] + 1)

        return [
            ComposedEvent(
                description=f'Ranked matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{numpy.mean(player_placements):.1f} average placement\n'
                            f'{player.visible_elo:.0f} performance\n'
                            f'{numpy.mean(opponent_ratings):.0f} average opponent rating',
                events=[]
            ),
        ]


class PlayUnrankedMatchesSampler(ActionSampler):
    action_name: Literal['ranked'] = 'unranked'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        ts = CustomTrueSkill()
        num_games = random.randint(2, 6)
        player = player.model_copy()  # dont change the original player
        player.visible_elo_sigma = ts.sigma
        player_placements = []
        opponent_ratings = []
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo -= 100  # those randoms are simply not as good as us professionals
                opponent_ratings.append(o.visible_elo)

            unranked_game_players = [player] + random_opponents

            ts = CustomTrueSkill()
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in unranked_game_players]
            ranks = ts.sample_ranks(true_ratings)
            player_placements.append(ranks[0] + 1)

        avg_placement = numpy.mean(player_placements)
        avg_placement_percentile = (avg_placement - 1) / (NUM_BOTS_IN_TOURNAMENT + 1 - 1)
        fun = 0
        if avg_placement_percentile < 0.25:
            fun += 1
        if avg_placement_percentile < 0.05:
            fun += 1
        if avg_placement_percentile > 0.6:
            fun -= 1
        if avg_placement_percentile > 0.8:
            fun -= 1
        fun += random.randint(a=-2, b=2)
        fun_rating = expit(numpy.array(fun) / 2) * 7
        return [
            ComposedEvent(
                description=f'Unranked matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{avg_placement :.1f} average placement\n'
                            f'{fun_rating:.0f}/7 fun rating\n\n',
                events=[
                    MotivationChange(motivation_change=fun),
                ]
            ),
        ]


class AnalyzeMatches(ActionSampler):
    action_name: Literal['analyzeMatches'] = 'analyzeMatches'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        num_games_analyzed = random.randint(1, 5)
        blunders = 0
        questionable_decisions = 0
        excellent_decisions = 0
        for _ in range(num_games_analyzed):
            blunders += random.randint(0, 2)
            questionable_decisions += random.randint(0, 3)
            excellent_decisions += random.randint(0, 12)
        lessons_learned = random.uniform(0, blunders + 0.4 * questionable_decisions + 0.05 * excellent_decisions)
        boredom = random.uniform(-1, 0) * num_games_analyzed
        return [
            ComposedEvent(
                description=f'Computer analysis of {num_games_analyzed} matches:\n\n'
                            f'{blunders} blunders\n'
                            f'{questionable_decisions} questionable decisions\n'
                            f'{excellent_decisions} excellent decisions\n'
                            f'{lessons_learned:.0f} lessons learned\n\n',
                events=[
                    MotivationChange(motivation_change=boredom),
                    SkillChange(hidden_elo_change=lessons_learned),
                ]
            ),
        ]


class FreeTimeSampler(ActionSampler):
    action_name: Literal['freeTime'] = 'freeTime'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        ranked_result_event = random.choice(PlayRankedMatchesSampler().possible_events(game, player))
        ranked_event = ComposedEvent(
            description=f'{player.name} uses their free time to play some ranked matches.\n\n{ranked_result_event.text_description()}',
            events=PlayRankedMatchesSampler().possible_events(game, player)
        )
        possible_events = [
            ranked_event,
            ComposedEvent(
                description=f'{player.name} uses their free time to party hard.',
                events=[
                    HealthChange(health_change=-1),
                    MotivationChange(motivation_change=+1),
                ]
            ),
        ]
        if player.motivation > BASE_PLAYER_MOTIVATION:
            possible_events.append(
                ComposedEvent(
                    description=f'{player.name} uses their free time to study.',
                    events=[
                        SkillChange(hidden_elo_change=+1),
                    ]
                )
            )
        return possible_events


class MotivationalSpeechSampler(ActionSampler):
    action_name: Literal['freeTime'] = 'motivationalSpeech'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        common_events = [
            ComposedEvent(
                description=f'{player.name} is inspired.',
                events=[
                    MotivationChange(motivation_change=+2),
                ]
            ),
        ]
        possible_events = [
            *(common_events * 2),
            ComposedEvent(
                description=f'{player.name} is bored.',
                events=[
                    MotivationChange(motivation_change=-2),
                ]
            ),
        ]
        return possible_events


class EventSampler(BaseModel):
    def samplers(self) -> List[ActionSampler]:
        return [
            HireCoachSampler(),
            OptimizeNutritionPlanSampler(),
            PlayRankedMatchesSampler(),
            PlayUnrankedMatchesSampler(),
            FreeTimeSampler(),
            MotivationalSpeechSampler(),
            AnalyzeMatches(),
        ]

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        for s in self.samplers():
            if s.action_name == action_name:
                return s.get_events_for_action(game, player, action_name)
        raise ValueError(f"Unknown action name '{action_name}'")

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return []
