from typing import Dict

from stories.chat import Chat
from stories.check_game_state import CheckGameState
from stories.craft import Craft
from stories.craft_recipe import CraftRecipe
from stories.create_pipeline import CreatePipeline
from stories.create_simple_pattern import CreateSimplePattern
from stories.create_trade_offer import CreateTradeOffer
from stories.delete_pattern import DeletePattern
from stories.join_server import JoinServer
from stories.send_resource import SendResource, Send10Resources, SendAllResources
from stories.start_server import StartServer

# for example host:port/json/JoinServer is a valid route if using the POST method
from stories.story import Story

valid_post_routes: Dict[str, Story] = {
    story.__name__.strip().lower(): story for story in [JoinServer,
                                                        StartServer,
                                                        CheckGameState,
                                                        Craft,
                                                        CreatePipeline,
                                                        CraftRecipe,
                                                        CreateSimplePattern,
                                                        Chat,
                                                        SendResource,
                                                        Send10Resources,
                                                        SendAllResources,
                                                        DeletePattern,
                                                        CreateTradeOffer]
}

push_message_types = set()