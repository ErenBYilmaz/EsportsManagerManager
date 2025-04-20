from data.clan_tag import CLAN_TAG_FORMATS
from data.user import User


class AppUser(User):
    def clan_tag(self):
        for fmt in CLAN_TAG_FORMATS:
            if fmt.usable(self.username):
                return fmt.clan_tag_from_username(self.username)
        return None
