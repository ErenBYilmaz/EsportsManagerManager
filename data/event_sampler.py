from typing import List

from pydantic import BaseModel

from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer


class EventSampler(BaseModel):
    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[ESportsGame]:
        return []

    def get_random_events(self, game: ESportsGame, player: ESportsPlayer) -> List[ESportsGame]:
        return []
