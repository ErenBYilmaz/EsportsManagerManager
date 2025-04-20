from data.app_game_state import AppGameState
from data.local_game_state import LocalGameState


class AppLocalGameState(LocalGameState):
    game_state: AppGameState

    def game_to_show(self):
        return self.game_state.lowest_level_game()