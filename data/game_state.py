import json
import os
import pickle
from typing import List, Literal, Any, Dict

from pydantic import BaseModel

from data.user import User
from lib.util import EBCP
from network.my_types import UserName


class GameState(EBCP):
    type: str = 'GameState'
    game_name: str
    users: List[User] = []

    def valid_session_id(self, session_id: str):
        for u in self.users:
            if u.session_id == session_id:
                return True
        else:
            return False

    def user_by_name(self, user_name):
        for user in self.users:
            if user.username == user_name:
                return user

    def username_by_session_id(self, session_id: str):
        u = self.user_by_session_id(session_id)
        if u is not None:
            return u.username

    def user_by_session_id(self, session_id: str):
        for u in self.users:
            if u.session_id == session_id:
                return u

    def commit(self):
        save_name = self.save_file_name()
        tmp_file_name = save_name + '.tmp'
        with open(tmp_file_name, 'w') as save_file:
            json.dump(self.to_json(), save_file, indent=2)
        if os.path.isfile(save_name):
            os.remove(save_name)
        os.rename(tmp_file_name, save_name)

    def rollback(self):
        if not os.path.isfile(self.save_file_name()):
            return
        loaded: GameState = self.load(self.game_name)
        assert type(self) == type(loaded)
        self.__dict__ = loaded.__dict__

    def save_file_name(self):
        game_name = self.game_name
        return self.save_name_by_game_name(game_name)

    @staticmethod
    def save_name_by_game_name(game_name):
        return game_name + '.sav.json'

    @staticmethod
    def save_file_exists(game_name) -> bool:
        return os.path.isfile(GameState.save_name_by_game_name(game_name))

    @classmethod
    def load(cls, game_name) -> 'GameState':
        with open(cls.save_name_by_game_name(game_name), 'r') as save_file:
            data = save_file.read()
        result = cls.from_json(json.loads(data))
        assert type(result).__name__ == 'AppGameState'
        return result

    def info_for_user(self, username: str):
        json_info = self.to_json()
        for user_info in json_info['users']:
            if user_info['username'] != username:
                del user_info['session_id']
        return json_info

    def update_from_json(self, json_info: Dict[str, Any]):
        if 'users' in json_info:
            for user_info in json_info['users']:
                if not self.user_name_exists(user_info['username']):
                    self.new_user(User(username=user_info['username']), initialize=False)
                user = self.user_by_name(user_info['username'])
                for k, v in user_info.items():
                    if k == 'type':
                        assert v == 'AppUser', v
                        continue
                    setattr(user, k, v)

    def new_user(self, user: User, initialize):
        if any(u.username == user.username for u in self.users):
            raise RuntimeError
        self.users.append(user)

    @classmethod
    def create(cls, game_name):
        return GameState(users=[], game_name=game_name)

    def user_name_exists(self, username: UserName):
        return any(u.username == username for u in self.users)