import typing

from data import server_gamestate
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
        if ready:
            if player_name not in game.ready_players:
                game.ready_players.append(player_name)
        else:
            if player_name in game.ready_players:
                game.ready_players.remove(player_name)

        if game.everyone_ready():
            game.start_match()

        return {'ready': ready, 'player_name': player_name, 'everyone_ready': game.everyone_ready()}

    def action(self):
        self.to_server({'ready': self.ui.ready_status, 'depth': self.ui.depth})
        self.client().check_game_state()
