from data.clan_tag import clan_tag_from_name
from data.user import User


class AppUser(User):
    def clan_tag(self):
        return clan_tag_from_name(self.username)

