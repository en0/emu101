import unittest
from emu101.ram import RAM
from emu101.typing import c_uint16, c_uint8


class RamTest(unittest.TestCase):
    def setUp(self):
        self.m = RAM(10)

    def test_write(self):
        expected = []
        for i, addr in enumerate(map(lambda x: c_uint16(x), range(10))):
            self.m.write(addr, i)
            expected.append(i)
        self.assertListEqual(self.m._data, expected)

    def test_read(self):
        self.m._data = [c_uint16(x) for x in range(10)]
        for expected, addr in zip(self.m._data, map(lambda x: c_uint16(x), range(10))):
            self.assertEqual(self.m.read(addr), expected)


    

