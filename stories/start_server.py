import subprocess

from network.my_types import JSONInfo
from stories.error_message import ErrorMessage
from stories.story import Story


class StartServer(Story):
    def from_client(self, json_info: JSONInfo) -> JSONInfo:
        raise NotImplementedError

    def action(self):
        import run_server
        game_name = self.ui.gameNameEdit.text()
        if game_name == '':
            raise ErrorMessage('Invalid game name')
        cmd = ['start'] + run_server.server_call(game_name=game_name, port=self.ui.portEdit.text())
        subprocess.call(" ".join(cmd), shell=True)
