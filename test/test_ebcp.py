import unittest

from lib.util import EBCP


class TestEBCP(unittest.TestCase):
    class C(EBCP):
        x: float
        y: float
        name: str

    def test_converting_to_json(self):
        result = self.C(x=3, y=4, name='c').to_json()
        self.assertEqual(result['x'], 3)
        self.assertEqual(result['y'], 4)
        self.assertEqual(result['name'], 'c')
        self.assertEqual(result['type'], 'C')
        print(result)

    def test_converting_to_object(self):
        result = self.C.from_json({'x': 3, 'y': 4, 'name': 'c', 'type': 'C'})
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 4)
        self.assertEqual(result.name, 'c')
        self.assertEqual(type(result),  self.C)

    def test_model_dump(self):
        result = self.C(x=3, y=4, name='c').model_dump()
        self.assertEqual(result['x'], 3)
        self.assertEqual(result['y'], 4)
        self.assertEqual(result['name'], 'c')
        assert 'SUBCLASSES_BY_NAME' not in result
        print(result)