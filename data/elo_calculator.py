Elo = float
Score = float


class EloCalculator:
    def __init__(self, k_factor: int = 32):
        self.k_factor = k_factor

    def calculate_new_elo(self, player_elo: float, opponent_elo: float, score: Score):
        expected_score = self.expected_score(opponent_elo, player_elo)
        new_elo = player_elo + self.k_factor * (score - expected_score)
        return new_elo

    def expected_score(self, opponent_elo: float, player_elo: float):
        return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

    def calculate_win_probability(self, player_elo: float, opponent_elo: float):
        return self.expected_score(opponent_elo, player_elo)
