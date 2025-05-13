import typing

from data import server_gamestate
from data.event_sampler import EventSampler
from data.game_event import GameEvent
from network.connection import precondition_failed
from network.my_types import JSONInfo
from stories.story import Story

if typing.TYPE_CHECKING:
    import frontend.src.waiting_menu


class TakeManagementAction(Story):
    MAX_GAMES_PER_REQUEST = 2

    def __init__(self, ui: 'frontend.src.waiting_menu.WaitingMenu', action_name: typing.Optional[str] = None):
        super().__init__(ui)
        self.ui = ui
        self.action_name = action_name  # on server side, the action name is None (indicating arbitrary action can be performed using the object)

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        user = server_gamestate.gs.user_by_session_id(json_info['session_id'])
        action_name: str = json_info['action_name']
        depth: int = json_info["depth"]
        game = server_gamestate.gs.game_at_depth(depth)
        player = game.player_controlled_by(user.username)

        if player.pending_choices:
            # pretend that the player did not know about that event yet and send it again
            return {'new_events': [e.model_dump() for e in player.pending_choices], 'player_name': player.name}
        if player.days_until_next_match <= 0:
            return precondition_failed('You don\'t have enough time to take this action before the next tournament match. Better get ready.')

        del game.ready_players[player.name]
        events_resulting_from_action = EventSampler().get_events_for_action(game, player, action_name)
        randomly_occurring_events = EventSampler().get_random_events(game, player)
        player.days_until_next_match -= 1

        new_events: typing.List[GameEvent] = events_resulting_from_action + randomly_occurring_events
        return {'new_events': [e.model_dump() for e in new_events], 'player_name': player.name}

    def action(self):
        self.to_server({'action_name': self.action_name, 'depth': self.ui.depth})
        self.client().check_game_state()
