import typing

from data import server_gamestate
from network.connection import precondition_failed
from network.my_types import JSONInfo
from stories.story import Story

if typing.TYPE_CHECKING:
    import frontend.src.waiting_menu


class SetReadyStatus(Story):
    def __init__(self, ui: 'frontend.src.waiting_menu.WaitingMenu'):
        super().__init__(ui)
        self.ui = ui

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        user = server_gamestate.gs.user_by_session_id(json_info['session_id'])
        ready = bool(json_info['ready'])
        game = server_gamestate.gs.game_at_depth(json_info['depth'])
        player_name = game.player_controlled_by(user.username).name
        if self.ongoing_match and json_info['depth'] == 0:
            return precondition_failed('Cannot get ready for match while a match is ongoing.')
        if ready:
            if player_name not in game.ready_players:
                game.ready_players.append(player_name)
        else:
            if player_name in game.ready_players:
                game.ready_players.remove(player_name)

        if game.everyone_ready():
            if game.ongoing_match is None:  # everyone ready for starting the match
                game.start_match()
            else:
                assert json_info['depth'] > 0
                parent_game = server_gamestate.gs.game_at_depth(json_info['depth'] - 1)
                parent_game.skip_to_end_of_ongoing_match()  # everyone ready for the end of the match
            ready = False
        assert not game.everyone_ready()

        return {'ready': ready, 'player_name': player_name}

    def action(self):
        self.to_server({'ready': self.ui.ready_status, 'depth': self.ui.depth})
        self.client().check_game_state()
