from typing import List

from pydantic import BaseModel

from data.player_name import PlayerName


class EsportsGameResult(BaseModel):
    ranking: List[PlayerName] = []
    rating_before: List[float] = []
    rating_after: List[float] = []

    def ranks_dict(self):
        return {name: rank + 1 for rank, name in enumerate(self.ranking)}

    def rating_changes_dict(self):
        assert len(self.rating_before) == len(self.rating_after) == len(self.ranking)
        return {name: rating_after - rating_before for name, rating_before, rating_after in zip(self.ranking, self.rating_before, self.rating_after)}

    def rating_after_dict(self):
        assert len(self.rating_before) == len(self.rating_after)
        return {name: rating_after for name, rating_after in zip(self.ranking, self.rating_after)}
