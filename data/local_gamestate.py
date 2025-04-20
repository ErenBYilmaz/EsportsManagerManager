from typing import Optional

from data.game_state import GameState
from data.app_user import AppUser
from lib.util import EBC


class LocalGameState(EBC):
    client_gamestate: Optional['LocalGameState'] = None

    def __init__(self, game_state: GameState, main_user_name: str):
        for user in game_state.users:
            if user.username == main_user_name:
                break
        else:
            raise ValueError(main_user_name)

        self.main_user_name = main_user_name
        self.game_state = game_state

    def main_user(self) -> AppUser:
        return self.game_state.user_by_name(self.main_user_name)

    def __enter__(self):
        if LocalGameState.client_gamestate is not None:
            raise RuntimeError
        LocalGameState.client_gamestate = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if LocalGameState.client_gamestate is not self:
            raise RuntimeError
        LocalGameState.client_gamestate = None


