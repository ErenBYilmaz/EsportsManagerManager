import typing

from data import server_gamestate
from data.game_event_base import GameEvent
from data.unknown_outcome import UnknownOutcome
from network.connection import precondition_failed, bad_request
from network.my_types import JSONInfo
from stories.story import Story

if typing.TYPE_CHECKING:
    import frontend.src.manager_menu


class ChooseEventAction(Story):
    def __init__(self, ui: 'frontend.src.manager_menu.ManagerMenu', choice_title: str = None, choice: GameEvent = None):
        super().__init__(ui)
        self.ui = ui
        self.choice_title = choice_title
        self.choice = choice

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        user = server_gamestate.gs.user_by_session_id(json_info['session_id'])
        depth: int = json_info["depth"]
        game = server_gamestate.gs.game_at_depth(depth)
        player = game.player_controlled_by(user.username)

        if game.ongoing_match:
            return precondition_failed('The match has already started. You can do that after the match.')

        if player.name in game.ready_players:
            del game.ready_players[player.name]

        choice_title = json_info['choice_title']
        choice_description = json_info['choice_description']
        for choice in player.pending_choices:
            if choice.title == choice_title:
                break
        else:
            return bad_request(f'No choice with title "{choice_title}" available.')
        for event in choice.choices:
            if event.text_description() == choice_description:
                break
        else:
            return bad_request(f'No option with description "{choice_description}" available in choice "{choice_title}".')

        if isinstance(event, UnknownOutcome): # the outcome was unknown before the choice was made, now we know it
            event = event.sample_event()
        player.pending_choices.remove(choice)
        event.apply(game, player)

        return {'new_events': [event.to_json()], 'player_name': player.name}

    def action(self):
        response = self.to_server({'choice_title': self.choice_title, 'choice_description': self.choice.text_description(), 'depth': self.ui.depth})
        new_events = response['new_events']
        self.client().check_game_state()
        for event_data in new_events:
            e = GameEvent.from_json(event_data)
            assert isinstance(e, GameEvent)
            self.ui.handle_game_event(e)
