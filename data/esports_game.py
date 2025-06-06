import random
from typing import Dict, Optional, List

from pydantic import BaseModel, field_validator

from config import NUM_BOTS_IN_TOURNAMENT, DAYS_BETWEEN_MATCHES
from data.custom_trueskill import CustomTrueSkill
from data.esports_game_result import EsportsGameResult
from data.esports_player import ESportsPlayer
from data.player_name import PlayerName
from data.waiting_condition import WaitingCondition
from lib.util import EBCP


class ESportsGame(EBCP):
    players: Dict[PlayerName, ESportsPlayer] = {}
    ongoing_match: Optional['ESportsGame'] = None
    ready_players: Dict[PlayerName, WaitingCondition] = {}
    game_results: List[EsportsGameResult] = []

    @field_validator('players')
    @classmethod
    def check_names(cls, players):
        for name, player in players.items():
            if name != player.name:
                raise ValueError(f"Player name '{player.name}' does not match key '{name}'")
        return players

    def create_players(self):
        for _ in range(NUM_BOTS_IN_TOURNAMENT):
            player = ESportsPlayer.create()
            self.players[player.name] = player

    def phase(self):
        if self.ongoing_match is not None:
            return 'match'
        return 'management'

    def is_nested(self):
        return self.parent_game is not None

    def player_controlled_by(self, username):
        for player in self.players.values():
            if player.controller == username:
                return player
        return None

    def non_ai_players(self):
        return [player for player in self.players.values() if player.controller is not None]

    def everyone_ready(self):
        return set(p.name for p in self.non_ai_players()).issubset(self.ready_players)

    def everyone_ready_for_match_start(self):
        next_match_start_idx = len(self.game_results)
        for player in self.non_ai_players():
            not_ready_for_anything = player.name not in self.ready_players
            if not_ready_for_anything:
                return False
            waiting_for = self.ready_players[player.name]
            waits_for_already_finished_match_and_is_therefore_not_ready = waiting_for.match_idx < next_match_start_idx
            if waits_for_already_finished_match_and_is_therefore_not_ready:
                return False
        return True

    def everyone_ready_for_match_end(self):
        next_match_end_idx = len(self.game_results)
        if self.ongoing_match is not None:
            next_match_end_idx -= 1
        for player in self.non_ai_players():
            not_ready_for_anything = player.name not in self.ready_players
            if not_ready_for_anything:
                return False
            waiting_for = self.ready_players[player.name]
            waits_for_already_finished_match_and_is_therefore_not_ready = waiting_for.match_idx < next_match_end_idx
            if waits_for_already_finished_match_and_is_therefore_not_ready:
                return False
        return True

    def start_match(self):
        if self.ongoing_match is not None:
            raise RuntimeError("Match is already ongoing")
        self.ongoing_match = ESportsGame()
        self.ongoing_match.create_players()
        for player, controller in zip(self.ongoing_match.players.values(), self.players.values()):
            player.controller = controller.controller
            player.manager = controller.name
        self.cleanup_ready_players()

    def skip_to_end_of_ongoing_match(self):
        if self.ongoing_match is None:
            raise RuntimeError("No ongoing match to skip")
        ts = CustomTrueSkill()
        players = list(self.players.values())
        true_ratings = [(ts.create_rating(mu=player.hidden_skill()),) for player in players]
        ranks = ts.sample_ranks(true_ratings)

        # update average rank
        assert len(ranks) == len(self.players)
        sorted_player_ranks = sorted(zip(ranks, players), key=lambda x: x[0])
        for rank, player in sorted_player_ranks:
            player.average_rank = (player.average_rank * len(self.game_results) + rank) / (len(self.game_results) + 1)

        # update visible ratings
        old_ratings = [(ts.create_rating(mu=player.tournament_elo, sigma=player.tournament_elo_sigma),) for player in players]
        assert len(old_ratings) == len(self.players) == len(ranks)
        new_ratings = ts.rate(old_ratings, ranks)
        assert len(new_ratings) == len(players)
        for new_rating, player in zip(new_ratings, players):
            assert len(new_rating) == 1
            player.tournament_elo = new_rating[0].mu
            player.tournament_elo_sigma = new_rating[0].sigma

        for player in players:
            player.days_until_next_match = DAYS_BETWEEN_MATCHES

        self.game_results.append(EsportsGameResult(ranking=[player.name for _, player in sorted_player_ranks],
                                                   rating_before=[old_ratings[players.index(player)][0].mu for _, player in sorted_player_ranks],
                                                   rating_after=[new_ratings[players.index(player)][0].mu for _, player in sorted_player_ranks]))
        self.ongoing_match = None
        self.cleanup_ready_players()

    def cleanup_ready_players(self):
        for player_name, ready_for in list(self.ready_players.items()):
            last_ended_game_idx = len(self.game_results) - 1
            if ready_for.match_idx <= last_ended_game_idx:
                print('Clearing ready status of player', player_name, ' because game has already ended.')
                del self.ready_players[player_name]
                continue
            if ready_for.match_state == 'match_begin':
                if ready_for.match_idx == last_ended_game_idx + 1:
                    if self.ongoing_match is not None:
                        print('Clearing ready status of player', player_name, ' because game has already started.')
                        del self.ready_players[player_name]
                        continue

    def condition_to_wait_for_next_start_of_match(self):
        matches_played = len(self.game_results)
        if self.ongoing_match:
            matches_played += 1
        return WaitingCondition(
            match_state='match_begin',
            match_idx=matches_played
        )

    def condition_to_wait_for_next_end_of_match(self):
        matches_played = len(self.game_results)
        return WaitingCondition(
            match_state='match_end',
            match_idx=matches_played
        )

    def previous_ranks(self, n: int, player_name: str):
        relevant_results = self.game_results[-n:]
        rankings = []
        for result in reversed(relevant_results):
            if player_name in result.ranking:
                rankings.append(result.ranking.index(player_name) + 1)
        assert len(rankings) <= n
        return rankings

    def previous_ranks_string(self, n: int, player_name: str):
        ranks = self.previous_ranks(n, player_name)
        if len(ranks) == 0:
            return 'N/A'
        return ' <- '.join(str(rank) for rank in ranks)

    def match_summary(self, match_idx: int, focus_on_player: str) -> str:
        match_result = self.game_results[match_idx]
        changes = match_result.rating_changes_dict()
        new_ratings = match_result.rating_after_dict()
        assert focus_on_player in new_ratings
        assert focus_on_player in match_result.ranking
        summary = 'Rankings:\n'
        for rank, player_name in enumerate(match_result.ranking):
            player = self.players[player_name]
            rating_info = f'rating {new_ratings[player_name]:.0f} ({changes[player_name]:+.0f})'
            name_info = player.tag_and_name()
            if player_name == focus_on_player:
                name_info = f'**{name_info}**'
            summary += f'{rank + 1: 2d}: {name_info}, {rating_info}\n'
        return summary

    def random_uncontrolled_player(self):
        player_names = [name for name in self.players if self.players[name].controller is None]
        if len(player_names) == 0:
            return None
        name = random.choice(player_names)
        return self.players[name]