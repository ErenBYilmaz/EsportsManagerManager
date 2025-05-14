import json
import sys
import threading
from queue import Queue, Empty
from typing import Optional, Dict, List, Tuple
from uuid import uuid4

import websocket
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

import stories.check_game_state
from data.app_local_game_state import AppLocalGameState
from debug import debug
from frontend.src.main_menu import MainMenu
from lib.compact_dict_string import compact_object_string
from lib.infinite_timer import InfiniteTimer
from lib.print_exc_plus import print_exc_plus
from lib.util import EBC
from network.my_types import JSONInfo
from stories.error_message import ConnectionErrorMessage, ErrorMessage
from stories.success_message import SuccessMessage


class SignallableWindow(QtWidgets.QMainWindow):
    new_message = QtCore.pyqtSignal()


class Client(EBC):
    class ErrorHandling(EBC):
        def __init__(self, ui, client: 'Client'):
            self.client = client
            self.ui = ui

        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            e = exc_val
            supress_exception = True
            if e is None:
                return
            elif isinstance(e, SuccessMessage):
                self.ui.information('Success', '\n'.join(e.args))
                return supress_exception
            elif isinstance(e, ConnectionErrorMessage):
                self.ui.critical(e.title, e.msg)
                return supress_exception
            elif isinstance(e, ErrorMessage):
                self.ui.critical('Error', '\n'.join(e.args))
                return supress_exception
            elif isinstance(e, NotImplementedError) and 'abstract' not in str(e).lower():
                print_exc_plus()
                self.ui.critical('NotImplementedError', 'This functionality is not yet available')
                return supress_exception
            elif isinstance(e, ConnectionResetError):
                print_exc_plus()
                try:
                    self.client.websocket.close()
                except ConnectionResetError:
                    pass
                self.ui.critical('ConnectionResetError', 'Lost connection to server. Trying to reconnect...')
                return supress_exception
            elif isinstance(e, Exception):
                print_exc_plus()
                self.ui.critical('Unknown Error', type(e).__name__ + ': ' + str(e))
                return supress_exception
            return not supress_exception

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = SignallableWindow()
        self.ui = MainMenu(self)
        self.ui.setupUi(self.MainWindow)
        self.local_gamestate: Optional[AppLocalGameState] = None
        self.websocket: websocket.WebSocket = websocket.WebSocket()
        self.response_collection: Dict[str, JSONInfo] = {}
        self.host = None
        self.check_game_state = stories.check_game_state.CheckGameState(self.ui)
        self.check_game_state_timer = InfiniteTimer(seconds=5, target=self.check_game_state)
        self.check_game_state_timer.start()
        self.message_queue = Queue()
        self.MainWindow.new_message.connect(self.process_messages)
        self.last_crafted_recipe = None

    def handling_errors(self):
        return self.ErrorHandling(self.ui, self)

    def send_messages(self, messages: List[Tuple[str, str]]):
        for msg in messages:
            QMessageBox.information(self.ui.centralwidget, msg[0], msg[1])

    def process_messages(self):
        assert threading.current_thread() is threading.main_thread()
        try:
            message = self.message_queue.get(block=False)
        except Empty:
            return
        message()

    def run(self):
        self.MainWindow.show()
        sys.exit(self.app.exec_())

    def close_server_connection(self):
        self.websocket.close()
        self.host = None

    def server_request(self, host: str, route: str, data: JSONInfo) -> JSONInfo:
        if not self.websocket.connected:
            host = host.replace('http://', 'ws://')
            self.websocket.connect(host + '/websocket')
        token = str(uuid4())
        data = json.dumps({'route': route, 'body': data, 'request_token': token})
        if debug:
            print('Sending to websocket:', str(data).replace('{', '\n{')[1:])
        self.websocket.send(data, opcode=2)
        json_content = self._receive_answer(token)

        status_code = json_content['http_status_code']
        if status_code == 200:
            pass
        else:
            formatted_request = compact_object_string(json.loads(data), max_line_length=100)
            formatted_response = compact_object_string(json_content, max_line_length=100)
            if 'body' in json_content and 'error' in json_content['body'] and not debug:
                raise ConnectionErrorMessage(title=f'Failed request: Code {status_code}', msg=json_content['body']['error'])
            else:
                raise ConnectionErrorMessage(title=f'Failed request: Code {status_code}',
                                             msg=f'A network request to "{host}" failed.\nRequest was: \n```\n{formatted_request}\n```\nResponse was:\n```\n{formatted_response}\n```')

        return json_content['body']

    def _receive_answer(self, token: str):
        """Waits until the server sends an answer that contains the desired request_token.
        All intermediate requests are also collected for later use, or, if they contain no token, they are just printed out.
        """
        if token in self.response_collection:
            json_content = self.response_collection[token]
            del self.response_collection[token]
            return json_content

        json_content = {}
        while 'request_token' not in json_content or json_content['request_token'] != token:
            if 'request_token' in json_content:
                self.response_collection[json_content['request_token']] = json_content
            received = self.websocket.recv_data_frame()[1].data
            content = received.decode('utf-8')
            json_content = json.loads(content)
            if debug:
                print('Received through websocket:\n' + compact_object_string(json_content, max_line_length=200, max_depth=3))

        return json_content

    def after_state_update(self):
        pass

    def open_first_window(self):
        raise NotImplementedError('TODO')
