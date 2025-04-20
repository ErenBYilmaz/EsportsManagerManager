from data import server_gamestate
from network.connection import bad_request
from network.my_types import JSONInfo
from stories.story import Story


class CheckGameState(Story):
    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        if self.missing_attributes(json_info, ['session_id']):
            return bad_request(self.missing_attributes(json_info, ['session_id']))
        return {
            'game_state': server_gamestate.gs.info_for_user(json_info['username']),
        }

    def action(self):
        if not self.client().message_queue.empty():
            return
        if not self.client().websocket.connected:
            return
        if self.client().local_gamestate is None:
            return
        response = self.to_server()
        if 'error' in response:
            print('Could not update game state:', response)
            return
        gs = self.client().local_gamestate.game_state
        gs.update_from_json(response['game_state'])
        self.client().after_state_update()
