import pydantic
from pydantic import BaseModel

from network.my_types import UserName


class User(BaseModel):
    username: UserName
    session_id: str = None

    @pydantic.field_validator('username')
    def validate_username(cls, value):
        if value == '':
            raise ValueError('Username must not be empty.')
        return value
