import unittest

from data.app_user import AppUser


class TestClanTag(unittest.TestCase):
    def setUp(self):
        self.user = AppUser(username='user1')

    def test_1(self):
        self.user.username = 'Eren Bora Yilmaz'
        self.assertEqual(self.user.clan_tag(), 'EBY')

    def test_2(self):
        self.user.username = 'Eren'
        self.assertEqual(self.user.clan_tag(), 'Eren')

    def test_3(self):
        self.user.username = 'Wizard'
        self.assertEqual(self.user.clan_tag(), 'Wzrd')

    def test_4(self):
        self.user.username = 'Anagram'
        self.assertEqual(self.user.clan_tag(), 'Ana')

    def test_5(self):
        self.user.username = 'timmaylivinalie'
        self.assertEqual(self.user.clan_tag(), 'tim')

    def test_6(self):
        self.user.username = '1rg3ndw3r'
        self.assertEqual(self.user.clan_tag(), 'rnr')

    def test_7(self):
        self.user.username = 'MrX13'
        self.assertEqual(self.user.clan_tag(), 'MrX')

    def test_8(self):
        self.user.username = 'Mortal Combat'
        self.assertEqual(self.user.clan_tag(), 'MC')

    def test_9(self):
        self.user.username = 'koljastrohm-games.com'
        self.assertEqual(self.user.clan_tag(), 'kgc')

    def test_10(self):
        self.user.username = '1rg3ndw13'
        self.assertEqual(self.user.clan_tag(), 'rn')

    def test_11(self):
        self.user.username = 'Greenzone96'
        self.assertEqual(self.user.clan_tag(), 'Gre')

    def test_12(self):
        self.user.username = '[][]'
        self.assertEqual(self.user.clan_tag(), None)

    def test_13(self):
        self.user.username = '[ADE]'
        self.assertEqual(self.user.clan_tag(), 'ADE')

    def test_14(self):
        for username in ['DESKTOP-6BUMF70', 'DESKTOP-C29IE4D', 'DESKTOP-VO4T18A']:
            self.user.username = username
            self.assertNotEqual(self.user.clan_tag(), None)
