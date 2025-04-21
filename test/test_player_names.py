import unittest

from resources.player_names import PLAYER_NAME_EXAMPLES


class TestPlayerNames(unittest.TestCase):
    def test_unique(self):
        names = PLAYER_NAME_EXAMPLES
        assert len(names) == len(set(names)), "Player names are not unique"

    def test_available(self):
        print(len(PLAYER_NAME_EXAMPLES))
        assert len(PLAYER_NAME_EXAMPLES) > 100
