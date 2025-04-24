import random
import unittest

from data.custom_trueskill import CustomTrueSkill


class TestTrueSkill(unittest.TestCase):
    def test_trueskill(self):
        ts = CustomTrueSkill()
        a = ts.create_rating()
        b = ts.create_rating()

        # Test rating
        self.assertAlmostEqual(a.mu, ts.mu)
        self.assertAlmostEqual(a.sigma, ts.sigma)

        # Test skill difference
        self.assertAlmostEqual(ts.win_probability([a], [b]), ts.win_probability([b], [a]))
        print(ts.win_probability([a], [b]))

        # Test rating update
        (new_a,), (new_b,) = ts.rate([(a,), (b,)], [0, 1])
        self.assertGreater(new_a.mu, a.mu)
        self.assertLess(new_b.mu, b.mu)

    def test_playing_against_higher_rated_player(self):
        ts = CustomTrueSkill()
        a = ts.create_rating(mu=1800)
        b = ts.create_rating(mu=1600)
        assert 0.75 <= ts.win_probability([a], [b]) <= 0.77

    def test_playing_ffa(self):
        ts = CustomTrueSkill()
        num_players = 64
        ratings = [(ts.create_rating(),) for _ in range(num_players)]
        new_ratings = ts.rate(ratings, [i for i in range(len(ratings))])
        for i, (new_rating,) in enumerate(new_ratings):
            print(f"Place {i}: mu={new_rating.mu:.1f}, sigma={new_rating.sigma:.1f}")

    def test_playing_multiple_ffa_games(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games = 100
        ratings = [(ts.create_rating(),) for _ in range(num_players)]
        for i in range(num_games):
            results = [i for i in range(len(ratings))]
            random.shuffle(results)
            ratings = ts.rate(ratings, results)
        self.print_ratings(ratings)

        player_1_vs_2_estimated_win_probability = ts.win_probability(ratings[0], ratings[1])
        assert 0.4 <= player_1_vs_2_estimated_win_probability <= 0.6
        print(player_1_vs_2_estimated_win_probability)

    def test_playing_multiple_ffa_starting_from_uneven_ratings_but_with_equal_win_probabilities_should_go_back_to_similar_ratings(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games = 100
        initial_spread = 640
        ratings = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
                   for player_idx in range(num_players)]

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        assert player_1_vs_63_estimated_win_probability < 0.05

        for i in range(num_games):
            results = [i for i in range(len(ratings))]
            random.shuffle(results)
            ratings = ts.rate(ratings, results)

        self.print_ratings(ratings)

        player_1_vs_2_estimated_win_probability = ts.win_probability(ratings[0], ratings[1])
        print(player_1_vs_2_estimated_win_probability)
        assert 0.4 <= player_1_vs_2_estimated_win_probability <= 0.6

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert 0.4 <= player_1_vs_63_estimated_win_probability <= 0.6

    def test_sampling_ranks_does_not_change_ratings_much(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games = 100
        initial_spread = 640
        ratings = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
                   for player_idx in range(num_players)]
        ratings_before = ratings.copy()

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        assert player_1_vs_63_estimated_win_probability < 0.05

        for i in range(num_games):
            results = ts.sample_ranks(ratings_before)
            ratings = ts.rate(ratings, results)

        for i, ((new_rating,), (old_rating,)) in enumerate(zip(ratings, ratings_before)):
            print(f"Player {i}: mu={new_rating.mu:.1f}, sigma={new_rating.sigma:.1f}, delta_mu={new_rating.mu - old_rating.mu:.1f}, delta_sigma={new_rating.sigma - old_rating.sigma:.1f}")

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert player_1_vs_63_estimated_win_probability < 0.05


    def print_ratings(self, ratings):
        for i, (new_rating,) in enumerate(ratings):
            print(f"Player {i}: mu={new_rating.mu:.1f}, sigma={new_rating.sigma:.1f}")
