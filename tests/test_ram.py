import unittest
from emu101.ram import RAM
from emu101.typing import c_uint16


class RamTest(unittest.TestCase):
    def setUp(self):
        self._size = 10
        self.m = RAM(self._size)

    def test_read_write(self):
        addr = c_uint16(3)
        data = c_uint16(65274)
        self.m.write(addr, data)
        self.assertEqual(self.m.read(addr).value, 65274)

    def test_write_on_writes_where_it_should(self):
        addr = c_uint16(3)
        data = c_uint16(65274)
        self.m.write(addr, data)
        for i in range(self._size):
            if i == 3:
                continue
            _addr = c_uint16(i)
            self.assertEqual(self.m.read(_addr).value, 0)
    

