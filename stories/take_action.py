import typing

from data import server_gamestate
from data.event_sampler import EventSampler
from data.game_event import MotivationChange, HealthChange, MoneyChange, SkillChange, ComposedEvent, GameEvent
from data.replace_player import ReplacePlayerWithNewlyGeneratedPlayer
from data.game_event_base import GameEvent
from data.manager_choice import ManagerChoice
from network.connection import precondition_failed
from network.my_types import JSONInfo
from stories.story import Story

if typing.TYPE_CHECKING:
    import frontend.src.manager_menu


class TakeManagementAction(Story):
    MAX_GAMES_PER_REQUEST = 2

    def __init__(self, ui: 'frontend.src.manager_menu.ManagerMenu', action_name: typing.Optional[str] = None):
        super().__init__(ui)
        self.ui = ui
        self.action_name = action_name  # on server side, the action name is None (indicating arbitrary action can be performed using the object)

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        user = server_gamestate.gs.user_by_session_id(json_info['session_id'])
        action_name: str = json_info['action_name']
        depth: int = json_info["depth"]
        game = server_gamestate.gs.game_at_depth(depth)
        player = game.player_controlled_by(user.username)

        if game.ongoing_match:
            return precondition_failed('The match has already started. You can do that after the match.')
        if player.pending_choices:
            # pretend that the player did not know about that event yet and send it again
            return {'new_events': [e.model_dump() for e in player.pending_choices], 'player_name': player.name}
        if player.days_until_next_match <= 0:
            return precondition_failed('You don\'t have enough time to take this action before the next tournament match. Better get ready.')

        if player.name in game.ready_players:
            del game.ready_players[player.name]
        if action_name.endswith('Button'):
            action_name = action_name[:-len('Button')]
        events_resulting_from_action = EventSampler().get_events_for_action(game, player, action_name)
        randomly_occurring_events = EventSampler().get_random_events(game, player)
        player.days_until_next_match -= 1

        new_events: typing.List[GameEvent] = events_resulting_from_action + randomly_occurring_events
        for e in new_events:
            e.apply(game, player)
        return {'new_events': [e.to_json() for e in new_events], 'player_name': player.name}

    def known_event_types(self) -> typing.Dict[str, typing.Type[GameEvent]]:
        types = [
            GameEvent,
            ComposedEvent,
            SkillChange,
            MoneyChange,
            HealthChange,
            MotivationChange,
            ReplacePlayerWithNewlyGeneratedPlayer,
            ManagerChoice,
        ]
        return {t.__name__: t for t in types}

    def action(self):
        response = self.to_server({'action_name': self.action_name, 'depth': self.ui.depth})
        new_events = response['new_events']
        self.client().check_game_state()
        for event_data in new_events:
            e = GameEvent.from_json(event_data)
            assert isinstance(e, GameEvent)
            self.ui.handle_game_event(e)
