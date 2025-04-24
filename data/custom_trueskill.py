import itertools
import math
from typing import List, Iterable

from trueskill import TrueSkill, Rating


class CustomTrueSkill(TrueSkill):
    def __init__(self, mu=1700, sigma=200, draw_probability=0):
        beta = sigma / 2
        tau = sigma / 100
        super().__init__(mu=mu, sigma=sigma, beta=beta, tau=tau, draw_probability=draw_probability)

    def win_probability(self, team1: Iterable[Rating], team2: Iterable[Rating]):
        # https://trueskill.org/#win-probability
        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
        size = len(team1) + len(team2)
        denominator = math.sqrt(size * (self.beta * self.beta) + sum_sigma)
        return self.cdf(delta_mu / denominator)
