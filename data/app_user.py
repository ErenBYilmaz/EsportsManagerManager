import re

from data.user import User


class AppUser(User):
    def clan_tag(self):
        if 3 <= len(self.username) <= 4:
            return self.username
        word_beginnings = re.findall(r'(?:\b|(?<=\d))[^\d\W]', self.username)
        if 3 <= len(word_beginnings) <= 4:
            return ''.join(word_beginnings)
        consonants = re.findall(r'(?![aeiouäöü])[^\d\W]', self.username)
        if len(consonants) == 4 and consonants[0] == self.username[0]:
            return ''.join(consonants)
        if len(consonants) == 3:
            if consonants[0] == self.username[0]:
                return ''.join(consonants)
            else:
                return self.username[0] + ''.join(consonants)
        if re.fullmatch(r'[^\d\W]{3,}', self.username):
            return self.username[:3]