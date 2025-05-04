from typing import Literal

from pydantic import BaseModel


class WaitingCondition(BaseModel):
    match_state: Literal['match_begin', 'match_end']
    match_idx: int
