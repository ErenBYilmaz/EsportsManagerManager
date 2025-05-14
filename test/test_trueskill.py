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
        print(ts.win_probability((a,), (b,)))
        assert 0.73 <= ts.win_probability((a,), (b,)) <= 0.74

    def test_playing_against_slightly_higher_rated_player(self):
        ts = CustomTrueSkill()
        for difference in [1, 5, 10, 20, 50, 100, 200]:
            probability = ts.one_on_one_win_probability(difference)
            print(probability)
            assert probability > 0.5

        print()
        for difference in [1, 5, 10, 20, 50, 100, 200]:
            score_ratio = ts.one_on_one_score_ratio(difference)
            print(score_ratio)
            assert score_ratio > 1

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
        print(player_1_vs_2_estimated_win_probability)
        assert 0.35 <= player_1_vs_2_estimated_win_probability <= 0.65

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
        assert 0.35 <= player_1_vs_2_estimated_win_probability <= 0.65

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert 0.35 <= player_1_vs_63_estimated_win_probability <= 0.65

    def test_sampling_ranks_does_not_change_ratings_much(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games = 200
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
            delta_mu = new_rating.mu - old_rating.mu
            print(f"Player {i}: mu={new_rating.mu:.1f}, sigma={new_rating.sigma:.1f}, delta_mu={delta_mu :.1f}, delta_sigma={new_rating.sigma - old_rating.sigma:.1f}")
            tolerance = 100
            assert abs(delta_mu) < tolerance

        player_1_vs_63_estimated_win_probability = ts.win_probability(ratings[0], ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert player_1_vs_63_estimated_win_probability < 0.05

    def test_sampling_ranks_converges_to_true_values(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games = 200
        initial_spread = 640
        hidden_ratings = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
                          for player_idx in range(num_players)]
        visible_ratings = [(ts.create_rating(ts.mu),) for _ in range(num_players)]

        player_1_vs_63_estimated_win_probability = ts.win_probability(visible_ratings[0], visible_ratings[63])
        self.assertAlmostEqual(player_1_vs_63_estimated_win_probability, 0.5)
        player_1_vs_63_estimated_win_probability = ts.win_probability(hidden_ratings[0], hidden_ratings[63])
        assert player_1_vs_63_estimated_win_probability < 0.05

        for i in range(num_games):
            results = ts.sample_ranks(hidden_ratings)
            visible_ratings = ts.rate(visible_ratings, results)

        for i, ((hidden_rating,), (visible_rating,)) in enumerate(zip(hidden_ratings, visible_ratings)):
            delta_mu = hidden_rating.mu - visible_rating.mu
            print(f"Player {i}: mu={hidden_rating.mu:.1f}, sigma={hidden_rating.sigma:.1f}, delta_mu={delta_mu :.1f}, delta_sigma={hidden_rating.sigma - visible_rating.sigma:.1f}")
            tolerance = 100
            assert abs(delta_mu) < tolerance

        player_1_vs_63_estimated_win_probability = ts.win_probability(visible_ratings[0], visible_ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert player_1_vs_63_estimated_win_probability < 0.05

    # def test_sampling_ranks_does_not_systematically_misjudge_after_just_a_few_games(self):
    #     ts = CustomTrueSkill()
    #     num_players = 64
    #     num_games = 10
    #     num_tests = 100
    #     initial_spread = 640
    #     unrated_top_half_player_rating_index = random.randint(0, num_players // 2 - 1)
    #     hidden_ratings = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
    #                       for player_idx in range(num_players)]
    #     visible_ratings = [(ts.create_rating(hidden_ratings[player_idx][0].mu),)
    #                        # if player_idx != unrated_top_half_player_rating_index
    #                        # else (ts.create_rating(ts.mu),)
    #                        for player_idx in range(num_players)]
    #
    #     deltas = []
    #     for _ in tqdm.tqdm(range(num_tests)):
    #         for i in range(num_games):
    #             results = ts.sample_ranks(hidden_ratings)
    #             visible_ratings = ts.rate(visible_ratings, results)
    #
    #         delta_mus = []
    #         for i, ((hidden_rating,), (visible_rating,)) in enumerate(zip(hidden_ratings, visible_ratings)):
    #             delta_mu = hidden_rating.mu - visible_rating.mu
    #             # print(f"Player {i}: mu={hidden_rating.mu:.1f}, sigma={hidden_rating.sigma:.1f}, delta_mu={delta_mu :.1f}, delta_sigma={hidden_rating.sigma - visible_rating.sigma:.1f}")
    #             delta_mus.append(delta_mu)
    #
    #         good_player_delta_mu = delta_mus[unrated_top_half_player_rating_index]
    #         deltas.append(good_player_delta_mu)
    #     result = ttest_1samp(deltas, popmean=0, alternative='two-sided')
    #     print(result.statistic)
    #     print(result.confidence_interval(0.95))
    #     print(result.pvalue)
    #     self.assertGreater(result.pvalue, 0.05)


    def test_sampling_ranks_converges_again_after_skill_change_if_sigma_is_reset(self):
        ts = CustomTrueSkill()
        num_players = 64
        num_games_per_rating = 200
        initial_spread = 640
        hidden_ratings_1 = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
                            for player_idx in range(num_players)]
        random.shuffle(hidden_ratings_1)
        hidden_ratings_2 = [(ts.create_rating(ts.mu - initial_spread / 2 + player_idx * initial_spread / num_players),)
                            for player_idx in range(num_players)]
        visible_ratings = [(ts.create_rating(ts.mu),) for _ in range(num_players)]

        player_1_vs_63_estimated_win_probability = ts.win_probability(visible_ratings[0], visible_ratings[63])
        self.assertAlmostEqual(player_1_vs_63_estimated_win_probability, 0.5)

        for i in range(num_games_per_rating):
            results = ts.sample_ranks(hidden_ratings_1)
            visible_ratings = ts.rate(visible_ratings, results)

        visible_ratings = [(ts.create_rating(r[0].mu),) for r in visible_ratings]

        for i in range(num_games_per_rating):
            results = ts.sample_ranks(hidden_ratings_2)
            visible_ratings = ts.rate(visible_ratings, results)

        for i, ((hidden_rating,), (visible_rating,)) in enumerate(zip(hidden_ratings_2, visible_ratings)):
            delta_mu = hidden_rating.mu - visible_rating.mu
            print(f"Player {i}: mu={hidden_rating.mu:.1f}, sigma={hidden_rating.sigma:.1f}, delta_mu={delta_mu :.1f}, delta_sigma={hidden_rating.sigma - visible_rating.sigma:.1f}")
            tolerance = 100
            assert abs(delta_mu) < tolerance

        player_1_vs_63_estimated_win_probability = ts.win_probability(visible_ratings[0], visible_ratings[63])
        print(player_1_vs_63_estimated_win_probability)
        assert player_1_vs_63_estimated_win_probability < 0.05

    def print_ratings(self, ratings):
        for i, (new_rating,) in enumerate(ratings):
            print(f"Player {i}: mu={new_rating.mu:.1f}, sigma={new_rating.sigma:.1f}")
