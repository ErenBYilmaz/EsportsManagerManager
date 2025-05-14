import itertools
import math
import random
from typing import List, Iterable, Tuple

import numpy.random
from trueskill import TrueSkill, Rating


class CustomTrueSkill(TrueSkill):
    def __init__(self, mu=1700, sigma=200, draw_probability=0):
        beta = sigma / 2
        tau = sigma / 100
        super().__init__(mu=mu, sigma=sigma, beta=beta, tau=tau, draw_probability=draw_probability)

    def win_probability(self, team1: Tuple[Rating], team2: Tuple[Rating]):
        # https://trueskill.org/#win-probability
        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
        size = len(team1) + len(team2)
        denominator = math.sqrt(size * (self.beta * self.beta) + sum_sigma)
        return self.cdf(delta_mu / denominator)

    def one_on_one_win_probability(self, delta_mu: float):
        # https://trueskill.org/#one-on-one-win-probability
        denominator = math.sqrt(2 * self.beta * self.beta)
        return self.cdf(delta_mu / denominator)

    def one_on_one_score_ratio(self, delta_mu: float):
        win_probability = self.one_on_one_win_probability(delta_mu)
        lose_probability = 1 - win_probability
        return win_probability / lose_probability

    def sample_ranks(self, rating_groups: List[Tuple[Rating]]):
        performances = [
            sum([
                self.sample_performance(rating.mu)
                for rating in rating_group
            ])
            for rating_group in rating_groups
        ]
        sorted_performances = sorted(performances, reverse=True)
        ranks = [
            sorted_performances.index(p)
            for p in performances
        ]
        return ranks

    def sample_performance(self, mu: float):
        return random.normalvariate(mu, self.beta)
