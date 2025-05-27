from typing import Literal

from lib.util import EBCP


class WaitingCondition(EBCP):
    match_state: Literal['match_begin', 'match_end']
    match_idx: int
