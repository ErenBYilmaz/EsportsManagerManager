import unittest

from data.game_state import GameState
from data.user import User


class TestGameState(unittest.TestCase):
    def test_creating_game_state(self):
        GameState(game_name='test', users=[User(username='user1'), User(username='user2')], phase='management')

    def test_mutable_default_argument(self):
        state_1 = GameState(game_name='test')
        state_2 = GameState(game_name='test')
        assert state_1.users == []
        assert state_2.users == []
        assert state_1.users is not state_2.users
        user = User(username='user1')
        state_1.users.append(user)
        assert user not in state_2.users
