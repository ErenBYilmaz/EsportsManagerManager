import unittest

from data.esports_player import ESportsPlayer
from data.action_event_sampler import StreamingSampler
from data.game_event import ComposedEvent


class TestStreamingSampler(unittest.TestCase):
    def test_average_money_return(self):
        results = []
        sampler = StreamingSampler()
        player = ESportsPlayer.create()
        for _ in range(20000):
            for e in sampler.possible_events(game=None, player=player):
                assert isinstance(e, ComposedEvent)
                for event in e.events:
                    if hasattr(event, 'money_change'):
                        results.append(event.money_change)
        avg = sum(results) / len(results)
        print("Average money change:", avg)
        self.assertGreater(avg, 0)