from typing import Dict, Type

from stories.check_game_state import CheckGameState
from stories.choose_event import ChooseEventAction
from stories.join_server import JoinServer
from stories.ready import SetReadyStatus
from stories.start_server import StartServer
from stories.story import Story
from stories.take_action import TakeManagementAction

# for example host:port/json/JoinServer is a valid route if using the POST method
valid_post_routes: Dict[str, Type[Story]] = {
    story.__name__.strip().lower(): story for story in [JoinServer,
                                                        StartServer,
                                                        CheckGameState,
                                                        SetReadyStatus,
                                                        TakeManagementAction,
                                                        ChooseEventAction,]
}

read_only_routes = [CheckGameState]

push_message_types = set()
