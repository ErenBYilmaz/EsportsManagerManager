import typing
import uuid

from data import server_gamestate
from data.app_gamestate import AppGameState
from data.app_user import AppUser
from data.app_local_game_state import AppLocalGameState
from data.clan_tag import clan_tag_valid, CLAN_TAG_FORMATS
from lib.my_logger import logging
from network import connection
from network.my_types import JSONInfo
from stories.story import Story
if typing.TYPE_CHECKING:
    import frontend.src.main_menu


class JoinServer(Story):
    def __init__(self, ui: 'frontend.src.main_menu.MainMenu'):
        super().__init__(ui)
        self.ui = ui

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        session_id = str(uuid.uuid4())
        state = server_gamestate.gs
        user = state.user_by_name(json_info['username'])
        if user is None:
            user = AppUser(username=json_info['username'], session_id=session_id)
            logging.info(f'New user: {user.username}')
            state.new_user(user, initialize=True)
        else:
            user.session_id = session_id
        return {'session_id': user.session_id, 'game_name': state.game_name}

    def action(self):
        self.client().close_server_connection()
        connection.PORT = int(self.ui.portEdit.text())
        username = self.ui.usernameEdit.text()
        if not clan_tag_valid(username):
            self.ui.critical('Invalid username', self.username_format_description())
            return
        user = AppUser(username=username)
        response = self.to_server({'username': user.username})
        user.session_id = response['session_id']
        gs = AppGameState(game_name=response['game_name'])
        gs.new_user(user, initialize=False)
        self.client().local_gamestate = AppLocalGameState(gs, main_user_name=user.username)
        self.client().open_manager_window(depth=gs.depth())

    def username_format_description(self):
        return (
                'The username must fulfill at least one of the following conditions:'
                + '\n - '
                + '\n - '.join(e.usable_if() for e in CLAN_TAG_FORMATS)
        )
