import os.path
from typing import List

from data.app_gamestate import AppGameState
from data.esports_game import ESportsGame


def kick_users(save_path: str, usernames: List[str]):
    state = AppGameState.load(save_path)
    state.users = [
        user for user in state.users
        if user.username not in usernames
    ]
    remove_control_from_game(state.game, usernames)
    state.commit()


def remove_control_from_game(game: ESportsGame, usernames: List[str]):
    for player in game.players.values():
        if player.controller in usernames:
            player.controller = None
    if game.ongoing_match is not None:
        remove_control_from_game(game.ongoing_match, usernames)


def main():
    save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_game')
    kick_usernames = [
        # 'Eren',
        'Test',
    ]
    kick_users(save_path, kick_usernames)


if __name__ == '__main__':
    main()
