import random
from typing import Dict, Optional, List

from pydantic import BaseModel, field_validator

from config import NUM_PLAYERS_IN_TOURNAMENT
from data.custom_trueskill import CustomTrueSkill
from data.esports_game_result import EsportsGameResult
from data.esports_player import ESportsPlayer, PlayerName
from resources.player_names import PLAYER_NAME_EXAMPLES


class ESportsGame(BaseModel):
    players: Dict[str, ESportsPlayer] = {}
    ongoing_match: Optional['ESportsGame'] = None
    ready_players: List[PlayerName] = []
    game_results: List[EsportsGameResult] = []

    @field_validator('players')
    @classmethod
    def check_names(cls, v):
        for name, player in v.items():
            if name != player.name:
                raise ValueError(f"Player name '{player.name}' does not match key '{name}'")
        return v

    def create_players(self):
        player_names = random.sample(PLAYER_NAME_EXAMPLES, NUM_PLAYERS_IN_TOURNAMENT - len(self.players))
        for name in player_names:
            player = ESportsPlayer(controller=None,
                                   name=name,
                                   hidden_elo=1700,
                                   visible_elo=1700,
                                   visible_elo_sigma=CustomTrueSkill().sigma,)
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

    def start_match(self):
        if self.ongoing_match is not None:
            raise RuntimeError("Match is already ongoing")
        self.ready_players.clear()
        self.ongoing_match = ESportsGame()
        self.ongoing_match.create_players()
        for player, controller in zip(self.ongoing_match.players.values(), self.players.values()):
            player.controller = controller.controller
            player.manager = controller.name

    def skip_to_end_of_ongoing_match(self):
        if self.ongoing_match is None:
            raise RuntimeError("No ongoing match to skip")
        ts = CustomTrueSkill()
        players = list(self.players.values())
        true_ratings = [(ts.create_rating(mu=player.hidden_elo),) for player in players]
        ranks = ts.sample_ranks(true_ratings)

        # update average rank
        assert len(ranks) == len(self.players)
        sorted_player_ranks = sorted(zip(ranks, players), key=lambda x: x[0])
        for rank, player in sorted_player_ranks:
            player.average_rank = (player.average_rank * len(self.game_results) + rank) / (len(self.game_results) + 1)

        # update visible ratings
        visible_ratings = [(ts.create_rating(mu=player.visible_elo, sigma=player.visible_elo_sigma),) for _, player in sorted_player_ranks]
        assert len(visible_ratings) == len(self.players) == len(ranks)
        new_ratings = ts.rate(visible_ratings)
        assert len(new_ratings) == len(players)
        for new_ratings, player in zip(new_ratings, players):
            assert len(new_ratings) == 1
            player.visible_elo = new_ratings[0].mu
            player.visible_elo_sigma = new_ratings[0].sigma

        self.game_results.append(EsportsGameResult(ranking=[player.name for _, player in sorted_player_ranks]))
        self.ongoing_match = None
        self.ready_players.clear()
