from typing import List

from data.custom_trueskill import CustomTrueSkill
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event_base import GameEvent


class ComposedEvent(GameEvent):
    events: List[GameEvent]
    description: str = ''

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        for event in self.events:
            event.apply(game, player)

    def short_notation(self):
        return '\n'.join(event.short_notation() for event in self.events)

    def text_description(self):
        if self.description == '':
            return self.short_notation()
        elif len(self.short_notation()) == 0:
            return self.description
        else:
            return self.description + '\n\n' + self.short_notation()


class SkillChange(GameEvent):
    hidden_elo_change: float

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        player.hidden_elo += self.hidden_elo_change

    def short_notation(self):
        ts = CustomTrueSkill()
        return f"{self.hidden_elo_change:+.1f} skill ({ts.one_on_one_score_ratio(self.hidden_elo_change) - 1:+.1%})"


class EventAffectingOtherPlayer(GameEvent):
    player_name: str
    event: GameEvent

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        self.event.apply(game, game.players[self.player_name])

    def short_notation(self):
        return f"{self.event.short_notation()} for {self.player_name}"


class HiddenSkillChange(SkillChange):
    order: int

    def short_notation(self):
        return f"+-??? skill (probably around +-{self.order})"


class MoneyChange(GameEvent):
    money_change: float

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        player.money += self.money_change

    def short_notation(self):
        return f"{self.money_change:+.2f} €"


class HealthChange(GameEvent):
    health_change: float

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        player.health += self.health_change

    def short_notation(self):
        ts = CustomTrueSkill()
        return f"{self.health_change:+.1f} health ({ts.one_on_one_score_ratio(self.health_change) - 1:+.1%})"


class MotivationChange(GameEvent):
    motivation_change: float

    def apply(self, game: ESportsGame, player: ESportsPlayer):
        player.motivation += self.motivation_change

    def short_notation(self):
        ts = CustomTrueSkill()
        return f"{self.motivation_change:+.1f} motivation ({ts.one_on_one_score_ratio(self.motivation_change) - 1:+.1%})"
