import re
from typing import List, Type


class ClanTagExtractor:
    def usable_if(self) -> str:
        raise NotImplementedError('Abstract method')

    def usable(self, username: str) -> bool:
        raise NotImplementedError('Abstract method')

    def clan_tag_from_username(self, username: str) -> str:
        raise NotImplementedError('Abstract method')


class ClanTagFromShortName(ClanTagExtractor):
    def usable_if(self) -> str:
        return 'consist of 2-4 characters not counting any `[` and `]`'

    def usable(self, username: str) -> bool:
        username = re.sub(r'[\[\]]', '', username)
        return 2 <= len(username) <= 4

    def clan_tag_from_username(self, username: str) -> str:
        username = re.sub(r'[\[\]]', '', username)
        return username


class ClanTagFromWordBeginnings(ClanTagExtractor):
    def usable_if(self) -> str:
        return 'contain 2-4 words'

    def beginnings(self, username):
        return re.findall(r'(?:\b|(?<=\d))[^\d\W]', username)

    def usable(self, username: str) -> bool:
        word_beginnings = self.beginnings(username)
        return 2 <= len(word_beginnings) <= 4

    def clan_tag_from_username(self, username: str) -> str:
        word_beginnings = self.beginnings(username)
        return ''.join(word_beginnings)


class ClanTagFromConsonantsIncludingNameBeginning(ClanTagExtractor):
    def usable_if(self) -> str:
        return 'begin with a consonant and consist of 4 consonants'

    def consonants(self, username):
        return re.findall(r'(?![aeiouäöü])[^\d\W]', username)

    def usable(self, username: str) -> bool:
        consonants = self.consonants(username)
        return len(consonants) == 4 and consonants[0] == username[0]

    def clan_tag_from_username(self, username: str) -> str:
        consonants = self.consonants(username)
        return ''.join(consonants)


class ClanTagFrom3Consonants(ClanTagExtractor):
    def usable_if(self) -> str:
        return 'consist of 3 consonants'

    def consonants(self, username):
        return re.findall(r'(?![aeiouäöü])[^\d\W]', username)

    def usable(self, username: str) -> bool:
        consonants = self.consonants(username)
        return len(consonants) == 3

    def clan_tag_from_username(self, username: str) -> str:
        consonants = self.consonants(username)
        if consonants[0] == username[0]:
            return ''.join(consonants)
        return username[0] + ''.join(consonants)


class ClanTagFromSingleWordBeginning(ClanTagExtractor):
    def usable_if(self) -> str:
        return 'consist of at least 3 letters followed by 0-4 digits'

    def usable(self, username: str) -> bool:
        return bool(re.fullmatch(r'[^\d\W]{3,}\d{0,4}', username))

    def clan_tag_from_username(self, username: str) -> str:
        return username[:3]


CLAN_TAG_FORMATS: List[ClanTagExtractor] = [
    ClanTagFromShortName(),
    ClanTagFromWordBeginnings(),
    ClanTagFromConsonantsIncludingNameBeginning(),
    ClanTagFrom3Consonants(),
    ClanTagFromSingleWordBeginning(),
]


def clan_tag_valid(username) -> bool:
    for fmt in CLAN_TAG_FORMATS:
        if fmt.usable(username):
            return True
    return False


def clan_tag_from_name(username):
    for fmt in CLAN_TAG_FORMATS:
        if fmt.usable(username):
            return fmt.clan_tag_from_username(username)
    return None
