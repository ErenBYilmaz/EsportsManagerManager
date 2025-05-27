import math
import random
from typing import List, Literal

import numpy
from scipy.special import expit

from config import BASE_PLAYER_HEALTH, NUM_BOTS_IN_TOURNAMENT, BOT_RATING_STEP, BASE_PLAYER_MOTIVATION
from data.custom_trueskill import CustomTrueSkill
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event import ComposedEvent, MoneyChange, SkillChange, HealthChange, MotivationChange, HiddenSkillChange, EventAffectingOtherPlayer
from data.game_event_base import GameEvent
from data.manager_choice import ManagerChoice
from data.replace_player import ReplacePlayerWithNewlyGeneratedPlayer
from data.unknown_outcome import UnknownOutcome
from lib.util import EBCP


class ActionSampler(EBCP):
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
            *(common * 5),
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
        num_games = random.randint(3, 10)
        rating_before = player.ranked_elo
        performance_tracker = player.model_copy()  # measures performance from played games only
        performance_tracker.ranked_elo_sigma = ts.sigma
        player_placements = []
        opponent_ratings = []
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo -= 90  # those randoms are simply not as good as us professionals
                if o.hidden_elo > player.ranked_elo:
                    o.hidden_elo = player.ranked_elo + random.normalvariate(0, 100)  # unless the professionals are also bad, then we pair them against bad players
                o.hidden_elo += random.normalvariate(sigma=100)  # there is some extra skill fluctuation
                o.ranked_elo = o.hidden_skill()
                o.ranked_elo_sigma /= 10
                opponent_ratings.append(o.ranked_elo)

            match_players = [player] + random_opponents

            ts = CustomTrueSkill()
            visible_ratings = [(ts.create_rating(mu=player.ranked_elo, sigma=player.ranked_elo_sigma),) for player in match_players]
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in match_players]
            ranks = ts.sample_ranks(true_ratings)
            assert len(visible_ratings) == len(match_players) == len(ranks)
            new_ratings = ts.rate(visible_ratings, ranks)
            assert len(new_ratings) == len(match_players)
            for new_ratings, p in zip(new_ratings, match_players):
                assert len(new_ratings) == 1
                p.ranked_elo = new_ratings[0].mu
                p.ranked_elo_sigma = new_ratings[0].sigma

            visible_ratings_recent_matches = [(ts.create_rating(mu=player.ranked_elo, sigma=player.ranked_elo_sigma),) for player in [performance_tracker] + random_opponents]
            new_ratings = ts.rate(visible_ratings_recent_matches, ranks)
            performance_tracker.ranked_elo = new_ratings[0][0].mu
            performance_tracker.ranked_elo_sigma = new_ratings[0][0].sigma

            player_placements.append(ranks[0] + 1)

        return [
            ComposedEvent(
                description=f'Ranked matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{numpy.mean(player_placements):.1f} average placement\n'
                            f'{performance_tracker.ranked_elo:.0f} performance in those games\n'
                            f'{numpy.mean(opponent_ratings):.0f} average opponent rating'
                            f'-> {player.ranked_elo:.0f} skill rating ({player.ranked_elo - rating_before:+.0f})',
                events=[]
            ),
        ]


class PlayUnrankedMatchesSampler(ActionSampler):
    action_name: Literal['ranked'] = 'unranked'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        num_games = random.randint(3, 10)
        player_placements = []
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT)]
            for o in random_opponents:
                o.hidden_elo -= 90  # those randoms are simply not as good as us professionals
                if o.hidden_elo > player.ranked_elo:
                    o.hidden_elo = player.ranked_elo + random.normalvariate(0, 100)  # unless the professionals are also bad, then we pair them against bad players
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
        rating_before = player.bot_match_elo
        performance_tracker = player.model_copy()  # measures performance from played games only
        performance_tracker.bot_match_elo_sigma = ts.sigma
        player_placements = []
        bot_elo = round(player.bot_match_elo / BOT_RATING_STEP + random.normalvariate(sigma=1)) * BOT_RATING_STEP
        for _ in range(num_games):
            random_opponents = [ESportsPlayer.create() for _ in range(NUM_BOTS_IN_TOURNAMENT - 1)]
            for o in random_opponents:
                o.hidden_elo = bot_elo
                o.bot_match_elo = o.hidden_skill()
                o.bot_match_elo_sigma /= 10

            match_players = [player] + random_opponents

            ts = CustomTrueSkill()
            visible_ratings = [(ts.create_rating(mu=player.bot_match_elo, sigma=player.bot_match_elo_sigma),) for player in match_players]
            true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in match_players]
            ranks = ts.sample_ranks(true_ratings)
            assert len(visible_ratings) == len(match_players) == len(ranks)
            new_ratings = ts.rate(visible_ratings, ranks)
            assert len(new_ratings) == len(match_players)
            for new_rating, p in zip(new_ratings, match_players):
                assert len(new_rating) == 1
                p.bot_match_elo = new_rating[0].mu
                p.bot_match_elo_sigma = new_rating[0].sigma

            visible_ratings_recent_matches = [(ts.create_rating(mu=player.bot_match_elo, sigma=player.bot_match_elo_sigma),) for player in [performance_tracker] + random_opponents]
            new_ratings = ts.rate(visible_ratings_recent_matches, ranks)
            performance_tracker.bot_match_elo = new_ratings[0][0].mu
            performance_tracker.bot_match_elo_sigma = new_ratings[0][0].sigma

            player_placements.append(ranks[0] + 1)

        return [
            ComposedEvent(
                description=f'Bot-matches summary:\n\n'
                            f'{num_games} matches played\n'
                            f'{bot_elo:.0f} official bot rating\n'
                            f'{numpy.mean(player_placements):.1f}/{NUM_BOTS_IN_TOURNAMENT + 1} average placement\n'
                            f'{performance_tracker.bot_match_elo:.0f} performance in those games\n'
                            f'-> {player.bot_match_elo:.0f} skill rating ({player.bot_match_elo - rating_before:+.0f})',
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


class EmptySampler(ActionSampler):
    action_name: Literal['empty'] = 'empty'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return [
            ComposedEvent(
                description=f'{player.name} did nothing.',
                events=[]
            ),
        ]


class FreeTimeSampler(ActionSampler):
    action_name: Literal['freeTime'] = 'freeTime'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        samplers = {
            'play some ranked matches': PlayRankedMatchesSampler(),
            'play some unranked matches': PlayUnrankedMatchesSampler(),
            'play some bot matches': PlayBotMatchesSampler(),
            'analyze some matches': AnalyzeMatches(),
            'stream some games publicly': StreamingSampler(),
            'do nothing worth mentioning': EmptySampler(),
        }
        activity = random.choice(list(samplers.keys()))
        chosen_event_result: ComposedEvent = random.choice(samplers[activity].possible_events(game, player))
        modified_event_result = ComposedEvent(
            description=f'{player.name} uses their free time to {activity}.\n\n{chosen_event_result.description}',
            events=[chosen_event_result]
        )
        possible_events = [
            modified_event_result,
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

    def statements(self):
        return [
            "Stay focused and trust in your preparation. You've trained for this moment.",
            "Mistakes happen, but it's how you recover that defines you. Keep pushing forward.",
            "You have the skills to win. Believe in yourself!",
            "Every match is a new opportunity to prove your worth. Seize it.",
            "Take a deep breath and stay calm. Pressure is just part of the game.",
            "Your hard work and dedication will pay off. Keep giving your best.",
            "Learn from every game, whether you win or lose. Growth is the real victory.",
            "We expect improvement, but remember, progress takes time. Keep at it.",
            "You're doing great. Keep up the momentum and finish strong.",
            "Even if things don't go as planned, stay composed and adapt.",
            "Remember why you started playing. Enjoy the game and give it your all.",
            "Your effort inspires everyone around you. Keep leading by example.",
            "The tournament is tough, but so are you. Show them what you're made of.",
            "Relax, focus, and play your game. The results will follow.",
            "Every match is a chance to learn and improve. Embrace the challenge."

            "Your recent performance has been outstanding. Build on that momentum.",
            "You've shown great improvement in the last matches. Keep it up.",
            "Remember the clutch plays you made earlier. You can do it again.",
            "Even if the last match didn't go as planned, focus on what you did well and improve.",
            "Your consistency in the last games has been impressive. Stay focused.",
            "Think about how far you've come in this tournament. Keep pushing forward.",
            "You bounced back from tough situations before. You can do it again.",
            "The way you adapted in the last game was brilliant. Use that same mindset now.",
            "You’ve already proven you belong here. Play with confidence.",

            "Your recent performance has been disappointing. We need to see improvement.",
            "You let the fans down in the last match. Reflect on your mistakes and do better.",
            "This is not the level of play we expect from you. Step up your game.",
            "You seem distracted. Focus on the task at hand.",
            "We can't afford such mistakes in critical moments. Be more careful.",
            "Your decision-making has been questionable lately. Think before you act.",
            "I am counting on you, but you're not delivering. Take responsibility.",
            "You need to take this more seriously. This is not a casual game.",
            "Your lack of preparation is evident. Put in the effort.",
            "We expected more from you. This is not acceptable.",
            "You seem to be underestimating the competition. Stay sharp.",
            "Your performance today was shocking. What happened out there?",
            "This is not the time for excuses. Fix your mistakes.",
            "You need to control your emotions better. Stay composed.",
        ]

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        statements = random.sample(self.statements(), k=4)

        return [
            ManagerChoice(
                title='Motivational Speech',
                description=f'You are planning how to motivate {player.name}.',
                choices=[
                    UnknownOutcome(
                        description=f'"{statement}"',
                        possibilities=[
                            ComposedEvent(description=f'{player.name} is inspired :)', events=[MotivationChange(motivation_change=+2), ]),
                            ComposedEvent(description=f'{player.name} does not care :|', events=[MotivationChange(motivation_change=+0), ]),
                            ComposedEvent(description=f'{player.name} is bored :(', events=[MotivationChange(motivation_change=-2), ]),
                        ],
                        probability_weights=[0.5, 0.1, 0.1],
                    )
                    for statement in statements
                ]
            )
        ]


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
            'Tournament rankings are computed from played tournament games only and are not always accurate.',
            'Sabotaging opponents seems to be worth the time in the long run, as it is risky to get caught.',
            'Analyzing the meta can give valuable insights about Esports Manager Manager that can be used by the player to improve their strategies.',
            'Doping is generally not regarded as a viable strategy.',
            'One forum user says: "Kill yourself".',
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


class NewStrategySampler(ActionSampler):
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


class SabotageSampler(ActionSampler):
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
                description=f'You have almost been caught trying to sabotage {opponent.tag_and_name()} and decide not to continue risking it today.',
                events=[]
            ),
        ]


class DopingSampler(ActionSampler):
    action_name: Literal['doping'] = 'doping'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return [
            ComposedEvent(
                description=f'''
The integrity of esports relies not only on skill and strategy, but also on fairness and respect for the rules of competition. Any use of performance-enhancing substances undermines this foundation and compromises both the credibility of the sport and the health of its participants.

Doping—whether for increased reaction time, focus, or endurance—distorts competition and violates the principles of equal opportunity. It can lead to disciplinary actions, including suspensions, disqualification, and permanent bans, as enforced by tournament organizers and esports governing bodies. Beyond competitive consequences, such practices pose serious risks to physical and mental health, particularly under long-term or unsupervised use.

Esports continues to evolve as a professional discipline, with increasing attention on the ethical and physical standards expected of its players. Maintaining a clean, fair, and responsible competitive environment is essential for the future of the game.
''',
                events=[
                    MotivationChange(motivation_change=-0.5),
                ]
            ),
        ]


class ReplacePlayerSampler(ActionSampler):
    action_name: Literal['replacePlayer'] = 'replacePlayer'

    def possible_events(self, game: ESportsGame, player: ESportsPlayer) -> List[GameEvent]:
        return [
            ComposedEvent(
                description=f'''You end the contract with {player.tag_and_name()}.''',
                events=[
                    ReplacePlayerWithNewlyGeneratedPlayer(),
                ]
            ),
        ]
