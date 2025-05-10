import typing

from data import server_gamestate
from data.waiting_condition import WaitingCondition
from network.my_types import JSONInfo
from stories.story import Story

if typing.TYPE_CHECKING:
    import frontend.src.waiting_menu


class SetReadyStatus(Story):
    MAX_GAMES_PER_REQUEST = 2


    def __init__(self, ui: 'frontend.src.waiting_menu.WaitingMenu'):
        super().__init__(ui)
        self.ui = ui

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        user = server_gamestate.gs.user_by_session_id(json_info['session_id'])
        ready = bool(json_info['ready'])
        depth = json_info["depth"]
        game = server_gamestate.gs.game_at_depth(depth)
        wait_for: WaitingCondition = WaitingCondition.model_validate(json_info['wait_for'])
        player_name = game.player_controlled_by(user.username).name
        if ready:
            game.ready_players[player_name] = wait_for
        else:
            if player_name in game.ready_players:
                del game.ready_players[player_name]

        for _ in range(self.MAX_GAMES_PER_REQUEST):
            if game.ongoing_match is None:
                if game.everyone_ready_for_match_start():
                    print(f'Start of match {len(game.game_results)} at depth {depth}')
                    game.start_match()
            if game.ongoing_match is not None and game.everyone_ready_for_match_end():
                print(f'End of match {len(game.game_results)} at depth {depth}')
                game.skip_to_end_of_ongoing_match()
        assert not game.everyone_ready_for_match_start()
        assert not game.everyone_ready_for_match_end()

        return {'ready': ready, 'player_name': player_name}

    def action(self):
        self.to_server({'ready': self.ui.ready_status, 'wait_for': self.ui.wait_for.model_dump(), 'depth': self.ui.depth})
        self.client().check_game_state()
