from typing import List, Literal

from pydantic import BaseModel

from data.user import User


class GameState(BaseModel):
    game_name: str
    users: List[User] = []