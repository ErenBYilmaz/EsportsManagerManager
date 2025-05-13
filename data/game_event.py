from typing import List

from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event_base import GameEventBase


class GameEvent(GameEventBase):
    affected_game: ESportsGame
    affected_player: ESportsPlayer


class ComposedEvent(GameEventBase):
    events: List[GameEventBase]
    description: str = ''

    def apply(self):
        for event in self.events:
            event.apply()

    def short_notation(self):
        return '\n'.join(event.short_notation() for event in self.events)

    def text_description(self):
        if self.description == '':
            return self.short_notation()
        else:
            return self.description + '\n\n' + self.short_notation()


class SkillChange(GameEvent):
    hidden_elo_change: float

    def apply(self):
        self.affected_player.hidden_elo += self.hidden_elo_change

    def short_notation(self):
        return f"{self.hidden_elo_change:+.1f} skill"


class MoneyChange(GameEvent):
    money_change: float

    def apply(self):
        self.affected_player.money += self.money_change

    def short_notation(self):
        return f"{self.money_change:+.1f} €"


class HealthChange(GameEvent):
    health_change: float

    def apply(self):
        self.affected_player.health += self.health_change

    def short_notation(self):
        return f"{self.health_change:+.1f} health"


class MotivationChange(GameEvent):
    motivation_change: float

    def apply(self):
        self.affected_player.motivation += self.motivation_change

    def short_notation(self):
        return f"{self.motivation_change:+.1f} motivation"


class ReplacePlayerWithNewlyGeneratedPlayer(GameEvent):
    def apply(self):
        player = self.affected_player
        game = self.affected_game
        new_player = ESportsPlayer.create()
        new_player.controller = player.controller
        new_player.manager = player.manager
        new_player.hidden_elo = player.hidden_elo
        new_player.visible_elo = player.visible_elo
        new_player.visible_elo_sigma = player.visible_elo_sigma
        new_player.money = player.money
        del game.players[player.name]
        game.players[new_player.name] = new_player

    def short_notation(self):
        return f"Player replacement"

