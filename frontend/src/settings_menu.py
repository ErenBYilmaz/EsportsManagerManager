import frontend.app_client
from frontend.generated.settings_menu import Ui_SettingsWindow


class SettingsMenu(Ui_SettingsWindow):
    def __init__(self, client: 'frontend.app_client.AppClient'):
        super().__init__()
        self.client = client
