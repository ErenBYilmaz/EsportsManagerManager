from pydantic import BaseModel


class ESportsPlayer(BaseModel):
    name: str

    wins: int = 0
    losses: int = 0
    draws: int = 0
    tiebreaker: int = 0

    hidden_elo: float
    visible_elo: float

    def rank_sorting_key(self):
        return (-self.points(), -self.tiebreaker, self.name)

    def points(self):
        return self.wins + 0.5 * self.draws