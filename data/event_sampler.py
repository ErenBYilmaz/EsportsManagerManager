from typing import List

from data.action_event_sampler import ActionSampler, HireCoachSampler, OptimizeNutritionPlanSampler, PlayRankedMatchesSampler, PlayUnrankedMatchesSampler, PlayBotMatchesSampler, AnalyzeMatches, \
    FreeTimeSampler, MotivationalSpeechSampler, StreamingSampler, AnalyzeMetaSampler, NewStrategySampler, SabotageSampler, DopingSampler, ReplacePlayerSampler
from data.esports_game import ESportsGame
from data.esports_player import ESportsPlayer
from data.game_event_base import GameEvent
from lib.util import EBCP


class EventSampler(EBCP):
    def samplers(self) -> List[ActionSampler]:
        return [
            HireCoachSampler(),
            OptimizeNutritionPlanSampler(),
            PlayRankedMatchesSampler(),
            PlayUnrankedMatchesSampler(),
            FreeTimeSampler(),
            MotivationalSpeechSampler(),
            AnalyzeMatches(),
            PlayBotMatchesSampler(),
            StreamingSampler(),
            AnalyzeMetaSampler(),
            NewStrategySampler(),
            SabotageSampler(),
            DopingSampler(),
            ReplacePlayerSampler(),
        ]

    def get_events_for_action(self, game: ESportsGame, player: ESportsPlayer, action_name: str) -> List[GameEvent]:
        for s in self.samplers():
            if s.action_name == action_name:
                return s.get_events_for_action(game, player, action_name)
        raise ValueError(f"Unknown action name '{action_name}'")
