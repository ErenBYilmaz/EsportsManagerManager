from typing import List

from data.craftingpattern import CraftingPattern
from data.local_gamestate import LocalGameState


class AppLocalGameState(LocalGameState):
    def my_crafting_machines(self):
        return [self.game_state.crafting_machine_by_name(n) for n in self.main_user().crafting_machines]

    def patterns(self, only_craftable_by_me: bool) -> List[CraftingPattern]:
        return [p
                for creator in self.game_state.patterns
                for p in self.game_state.patterns[creator].values()
                if not only_craftable_by_me or self.main_user().crafting_machines_available(p.crafting_machines_needed())]
