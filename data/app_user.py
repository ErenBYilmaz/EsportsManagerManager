from data.user import User


class AppUser(User):
    def clan_tag(self):
        return self.clan_tag_from_name()

