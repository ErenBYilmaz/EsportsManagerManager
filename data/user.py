import pydantic
from pydantic import BaseModel

from lib.util import EBCP
from network.my_types import UserName


class User(EBCP):
    username: UserName
    session_id: str = None

    @pydantic.field_validator('username')
    def validate_username(cls, value):
        if value == '':
            raise ValueError('Username must not be empty.')
        return value
