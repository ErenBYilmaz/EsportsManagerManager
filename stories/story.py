import threading
from typing import Dict, List, Union

from data import server_gamestate
import network.connection
from network.my_types import JSONInfo
from lib.util import EBC


class Story(EBC):
    def __init__(self, ui):
        import frontend.src
        self.ui: Union[frontend.src.crafting_menu.CraftingMenu, frontend.src.main_menu.MainMenu, None] = ui

    def client(self):
        return self.ui.client

    def to_server(self, json_info=None) -> JSONInfo:
        if json_info is None:
            json_info = {}
        json_info['route'] = type(self).__name__
        if 'username' not in json_info:
            if self.client().local_gamestate is not None:
                json_info['username'] = self.client().local_gamestate.main_user_name
                if self.client().local_gamestate.main_user() is not None:
                    json_info['session_id'] = self.client().local_gamestate.main_user().session_id
        if self.client().host is None:
            self.client().host = 'http://' + self.ui.serverIPEdit.text() + ':' + str(network.connection.PORT)
        response = self.client().server_request(host=self.client().host,
                                                route=type(self).__name__,
                                                data=json_info)
        if 'messages' in response:
            self.client().send_messages(response['messages'])
        return response

    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        raise NotImplementedError

    def __call__(self):
        if threading.current_thread() is not threading.main_thread():
            self.client().message_queue.put(lambda: self())
            self.client().MainWindow.new_message.emit()
            return
        with self.client().handling_errors():
            self.action()

    def action(self):
        raise NotImplementedError

    @staticmethod
    def missing_attributes(request_json: Dict, attributes: List[str]):
        for attr in attributes:
            if attr not in request_json:
                if str(attr) == 'session_id':
                    return 'You are not signed in.'
                return 'Missing value for attribute ' + str(attr)
            if str(attr) == 'session_id':
                if not server_gamestate.gs.valid_session_id(request_json['session_id']):
                    return 'You are not signed in.'
        return False
