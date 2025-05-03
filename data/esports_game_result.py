from typing import List

from pydantic import BaseModel

from data.esports_player import PlayerName


class EsportsGameResult(BaseModel):
    ranking: List[PlayerName] = []

    def ranks_dict(self):
        return {name: rank + 1 for rank, name in enumerate(self.ranking)}
