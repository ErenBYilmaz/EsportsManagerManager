import math
import random
from typing import List, Literal

import numpy
from pydantic import BaseModel
from scipy.special import expit

from config import BASE_PLAYER_HEALTH, NUM_BOTS_IN_TOURNAMENT, BASE_PLAYER_MOTIVATION, BOT_RATING_STEP
from data.custom_trueskill import CustomTrueSkill
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event import ComposedEvent, SkillChange, MoneyChange, HealthChange, MotivationChange, HiddenSkillChange, EventAffectingOtherPlayer
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
                    description=f'After some analysis you just pick the standard nutrition plan that everyone else is on.',
                    events=[
                        HealthChange(health_change=+1),
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
                o.hidden_elo -= 90  # those randoms are simply not as good as us professionals
                if o.hidden_elo > player.visible_elo:
                    o.hidden_elo = player.visible_elo + random.normalvariate(0, 100)  # unless the professionals are also bad, then we pair them against bad players
                o.hidden_elo += random.normalvariate(sigma=100)  # there is some extra skill fluctuation
                o.visible_elo = o.hidden_skill()
                o.visible_elo_sigma /= 10
                opponent_ratings.append(o.visible_elo)

            match_players = [player] + random_opponents

            ts = CustomTrueSkill()
            visible_ratings = [(ts.create_rating(mu=player.visible_elo, sigma=player.visible_elo_sigma),) for player in match_players]
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in match_players]
            ranks = ts.sample_ranks(true_ratings)
            assert len(visible_ratings) == len(match_players) == len(ranks)
            new_ratings = ts.rate(visible_ratings, ranks)
            assert len(new_ratings) == len(match_players)
            for new_ratings, p in zip(new_ratings, match_players):
                assert len(new_ratings) == 1
                p.visible_elo = new_ratings[0].mu
                p.visible_elo_sigma = new_ratings[0].sigma

            player_placements.append(ranks[0] + 1)

        return [
            ComposedEvent(
                description=f'Ranked matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{numpy.mean(player_placements):.1f} average placement\n'
                            f'{player.visible_elo:.0f} performance in those games\n'
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
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo -= 90  # those randoms are simply not as good as us professionals
                if o.hidden_elo > player.visible_elo:
                    o.hidden_elo = player.visible_elo + random.normalvariate(0, 100)  # unless the professionals are also bad, then we pair them against bad players
                o.hidden_elo += random.normalvariate(sigma=100)  # there is some extra skill fluctuation

            match_players = [player] + random_opponents

            ts = CustomTrueSkill()
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in match_players]
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


class PlayBotMatchesSampler(ActionSampler):
    action_name: Literal['ranked'] = 'botMatch'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        ts = CustomTrueSkill()
        num_games = random.randint(5, 15)
        player = player.model_copy()  # dont change the original player
        player.visible_elo_sigma = ts.sigma
        player_placements = []
        bot_elo = round(player.visible_elo / BOT_RATING_STEP + random.normalvariate(sigma=1)) * BOT_RATING_STEP
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo = bot_elo
                o.visible_elo = o.hidden_skill()
                o.visible_elo_sigma /= 10

            match_players = [player] + random_opponents

            ts = CustomTrueSkill()
            visible_ratings = [(ts.create_rating(mu=player.visible_elo, sigma=player.visible_elo_sigma),) for player in match_players]
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in match_players]
            ranks = ts.sample_ranks(true_ratings)
            assert len(visible_ratings) == len(match_players) == len(ranks)
            new_ratings = ts.rate(visible_ratings, ranks)
            assert len(new_ratings) == len(match_players)
            for new_ratings, p in zip(new_ratings, match_players):
                assert len(new_ratings) == 1
                p.visible_elo = new_ratings[0].mu
                p.visible_elo_sigma = new_ratings[0].sigma

            player_placements.append(ranks[0] + 1)

        return [
            ComposedEvent(
                description=f'Bot-matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{bot_elo:.0f} official bot rating\n'
                            f'{numpy.mean(player_placements):.1f} average placement\n'
                            f'{player.visible_elo:.0f} performance in those games',
                events=[]
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
                            f'-----------------------\n'
                            f'{player.name}: {lessons_learned:.0f} lesson(s) learned\n\n',
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


class StreamingSampler(ActionSampler):
    action_name: Literal['streaming'] = 'streaming'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        sub_value_min = 1.49 / 1.12
        sub_value_max = 4.99 / 1.12
        num_subs = round(math.pow(10, random.expovariate(1.5))) + 1
        values = numpy.random.uniform(low=sub_value_min, high=sub_value_max, size=num_subs)
        values = numpy.around(values, decimals=2)
        value = numpy.sum(values).item()
        demonetization_reason = random.choice([
            'nudity',
            'inappropriate language',
            'copyright infringement',
            'drug-related content',
        ])
        common_events = [
            ComposedEvent(
                description=f'{player.name} was gifted {num_subs} subs.',
                events=[
                    MoneyChange(money_change=value),
                    MotivationChange(motivation_change=+random.randint(1, 3)),
                ]
            ),
            ComposedEvent(
                description=f'{player.name} had fun during the stream.',
                events=[
                    MotivationChange(motivation_change=+random.randint(1, 3)),
                ]
            ),
            ComposedEvent(
                description=f'Almost nobody visited the stream.',
                events=[
                    MotivationChange(motivation_change=-random.randint(1, 3)),
                ]
            ),
            ComposedEvent(
                description=f'{player.name} was not very entertaining today.',
                events=[]
            ),
            ComposedEvent(
                description=f'{player.name} learned something during the stream.',
                events=[
                    SkillChange(hidden_elo_change=+random.randint(1, 10) / 10),
                ]
            ),
        ]
        possible_events = [
            *(common_events * 2),
            ComposedEvent(
                description=f'Today\'s stream was demonetized with the following allegation:\n"{demonetization_reason}"',
                events=[
                    MoneyChange(money_change=-random.randint(2, 5)),
                ]
            ),
            ComposedEvent(
                description=f'{player.name} is being sued for playing the wrong music on stream (copyright infringement).',
                events=[
                    MoneyChange(money_change=-random.randint(50, 500)),
                ]
            ),
        ]
        return possible_events


class AnalyzeMetaSampler(ActionSampler):
    action_name: Literal['analyzeMeta'] = 'analyzeMeta'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        strategies = [
            'aggressive',
            'defensive',
            'balanced',
            'cheese',
        ]
        possible_findings = [
            'Getting sued for copyright infringement when streaming can cost a lot of money.',
            'Being gifted subs while streaming can yield insane amounts of money.',
            'Professional coaches typically seem to be expensive, but often worth it.',
            'Playing ranked matches outside of the tournament allows estimating a players skill without risk of losing points.',
            'Estimating skill from playing ranked matches can be difficult if opponents are much weaker (or stronger).',
            'Playing bot matches outside of the tournament allows estimating a players skill without risk of losing points.',
            f'Esports Manager Manager bots are available in skill rating steps of {BOT_RATING_STEP}.',
            'Opponents in ranked matches are typically weaker than in the tournament.',
            'Opponents in unranked matches are typically weaker than in the tournament.',
            'Free time can be relaxing.',
            'An optimized nutrition plan can improve well-being, but may also cost extra money.',
            'Highly motivated players typically perform better than less motivated players of the same skill level.',
            'Healthy players typically perform better than sick players of the same skill level.',
            'Tournament rankings are computed from played tournament games and not always accurate.',
            *[
                f'Recently, {s1} strategies seems to perform similarly well as {s2} strategies, maybe slightly {random.choice(["better", "worse"])}.'
                for s1 in strategies
                for s2 in strategies
                if s1 != s2
                if random.random() < 0.25
            ],
        ]
        usefulness = {
            'The found results seem to be very useful.': +2,
            'The found results seem to be moderately useful.': +0.5,
            f'{player.name} was already aware of these facts.': +0,
            'You were already aware of these facts.': +0,
            'You are unsure how useful this knowledge will be.': random.randint(-3, 3),
        }
        usefulness_str = random.choice(list(usefulness.keys()))

        description = f'Metagame analysis summary:\n\n'
        description += '\n'.join(f'  {f_idx + 1}. {f}'
                                 for f_idx, f in enumerate(random.sample(possible_findings, k=random.randint(2, 4))))
        description += '\n\n' + usefulness_str

        if 'unsure' in usefulness_str:
            change = HiddenSkillChange(hidden_elo_change=usefulness[usefulness_str], order=2)
        else:
            change = SkillChange(hidden_elo_change=usefulness[usefulness_str])

        common_events = [
            ComposedEvent(
                description=description,
                events=[change]
            ),
        ]
        return common_events


class NewStrategy(ActionSampler):
    action_name: Literal['newStrategy'] = 'newStrategy'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        strategies = [
            'aggressive',
            'defensive',
            'balanced',
            'cheese',
        ]
        resources = [
            'a lot of money',
            'a very good health condition',
            'a high motivation value',
            'skill improvements',
        ]
        new_strategy_messages = [
            'You have got an idea how to exploit the current meta.',
            f'You have got an idea for a strategy that may work well against {random.choice(strategies)} strategies.',
            f'You think you have found a way to improve your skill on {random.choice(strategies)} strategies.',
            f'You think you have found a method to get {random.choice(resources)} quickly.',
        ]
        return [
            ComposedEvent(
                description=random.choice(new_strategy_messages) + '\nYou are not sure if it will work, but you decide to use it in future matches anyways.',
                events=[
                    HiddenSkillChange(hidden_elo_change=random.randint(-9, 11), order=5),
                ]
            ),
            ComposedEvent(
                description='No matter how long you think, you just have no inspiring idea of what you could try out.',
                events=[
                    SkillChange(hidden_elo_change=+0),
                ]
            ),
        ]


class Sabotage(ActionSampler):
    action_name: Literal['sabotage'] = 'sabotage'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        opponents = [p for p in game.players.values() if p.name != player.name]
        opponent: ESportsPlayer = random.choice(opponents)
        return [
            ComposedEvent(
                description=f'{opponent.tag_and_name()} has no idea why, but their strategy suddenly does not work so well any more.',
                events=[
                    EventAffectingOtherPlayer(
                        player_name=opponent.name,
                        event=SkillChange(hidden_elo_change=-random.randint(5, 20))
                    ),
                ]
            ),
            ComposedEvent(
                description=f'{opponent.tag_and_name()} does not feel very well.',
                events=[
                    EventAffectingOtherPlayer(
                        player_name=opponent.name,
                        event=HealthChange(health_change=-random.randint(5, 20))
                    ),
                ]
            ),
            ComposedEvent(
                description=f'{opponent.tag_and_name()} caught you interfering with their game and is furious.',
                events=[
                    EventAffectingOtherPlayer(
                        player_name=opponent.name,
                        event=MotivationChange(motivation_change=+random.randint(10, 40))
                    ),
                ]
            ),
            ComposedEvent(
                description=f'You have almost been caught trying to sabotage {opponent.tag_and_name()} and decide not to to risk it today.',
                events=[]
            ),
        ]


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
            PlayBotMatchesSampler(),
            StreamingSampler(),
            AnalyzeMetaSampler(),
            NewStrategy(),
            Sabotage(),
        ]

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        for s in self.samplers():
            if s.action_name == action_name:
                return s.get_events_for_action(game, player, action_name)
        raise ValueError(f"Unknown action name '{action_name}'")

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return []
