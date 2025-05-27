from typing import Optional, List

from data.event_sampler import EventSampler
from data.game_event import ComposedEvent
from data.game_event_base import GameEvent


class TakeActionEvent(GameEvent):
    action_name: str
    description: str = ''
    sampled_events: Optional[List[GameEvent]] = None

    def apply(self, game, player):
        self.setup_if_needed(game, player)
        for e in self.sampled_events:
            e.apply(game, player)

    def setup_if_needed(self, game, player):
        if self.sampled_events is None:
            self.sampled_events = EventSampler().get_events_for_action(game, player, self.action_name)

    def text_description(self):
        base_description = self.description if self.description != '' else ("Action taken: " + self.action_name)
        if self.sampled_events is None:
            return base_description
        elif len(self.sampled_events) == 1:
            return self.sampled_events[0].text_description()
        else:
            return base_description + '\n\n' + self.short_notation()

    def short_notation(self):
        if self.sampled_events is None:
            return f"Action taken: {self.action_name}"
        elif len(self.sampled_events) == 1:
            return self.sampled_events[0].short_notation()
        else:
            return ComposedEvent(
                events=self.sampled_events,
                description="Action taken: " + self.action_name
            ).short_notation()
