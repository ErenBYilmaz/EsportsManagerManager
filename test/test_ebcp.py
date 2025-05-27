import unittest
from typing import List

from lib.util import EBCP


class C(EBCP):
    x: float
    y: float
    name: str


class D(C):
    cs: List[C]


class TestEBCP(unittest.TestCase):
    def test_converting_to_json(self):
        result = C(x=3, y=4, name='c').to_json()
        self.assertEqual(result['x'], 3)
        self.assertEqual(result['y'], 4)
        self.assertEqual(result['name'], 'c')
        self.assertEqual(result['type'], 'C')
        print(result)

    def test_converting_to_object(self):
        result = C.from_json({'x': 3, 'y': 4, 'name': 'c', 'type': 'C'})
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 4)
        self.assertEqual(result.name, 'c')
        self.assertEqual(type(result), C)

    def test_model_dump(self):
        result = C(x=3, y=4, name='c').model_dump()
        self.assertEqual(result['x'], 3)
        self.assertEqual(result['y'], 4)
        self.assertEqual(result['name'], 'c')
        assert 'SUBCLASSES_BY_NAME' not in result
        print(result)

    def test_recursive_model(self):
        result = D(x=3, y=4, name='d', cs=[D(x=1, y=2, cs=[], name='d2'), C(x=5, y=6, name='c2')])
        json_result = result.to_json()
        print(json_result)
        self.assertEqual(json_result['x'], 3)
        self.assertEqual(json_result['y'], 4)
        self.assertEqual(json_result['name'], 'd')
        self.assertEqual(len(json_result['cs']), 2)
        self.assertEqual(json_result['type'], 'D')
        self.assertEqual(json_result['cs'][0]['type'], 'D')
        self.assertEqual(json_result['cs'][1]['type'], 'C')
        self.assertEqual(json_result['cs'][0]['name'], 'd2')
        self.assertEqual(json_result['cs'][1]['name'], 'c2')
        self.assertEqual(json_result['cs'][0]['cs'], [])
