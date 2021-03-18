import unittest
from unittest.mock import MagicMock, Mock
from emu101.bus import Bus
from emu101.typing import c_uint16, BusInterface


class BusTest(unittest.TestCase):

    def setUp(self):
        m1 = MagicMock(spec=BusInterface)()
        m2 = MagicMock(spec=BusInterface)()
        self.bus = Bus({
            (0, 5): m1,
            (5, 5): m2,
        })

        self.m1: BusInterface = m1
        self.m2: BusInterface = m2

        self.m1.read = Mock()
        self.m2.read = Mock()

        self.m1.write = Mock()
        self.m2.write = Mock()

    def test_create(self):
        for i in range(0, 5):
            self.assertEqual(self.bus._map[i], self.m1)
        for i in range(5, 10):
            self.assertEqual(self.bus._map[i], self.m2)
        for i in range(10, 0x10000):
            self.assertIsNone(self.bus._map[i])

    def test_read_map_offset_at_zero(self):
        for i in range(0, 5):
            addr = c_uint16(i)
            self.bus.read(addr)
            actual, = self.m1.read.call_args[0]
            self.assertEqual(actual.value, addr.value)

    def test_read_map_offset_at_non_zero(self):
        for i in range(5, 10):
            addr = c_uint16(i)
            expected = c_uint16(i-5)
            self.bus.read(addr)
            actual, = self.m2.read.call_args[0]
            self.assertEqual(actual.value, expected.value)

    def test_read_returns_zero_if_no_mapping(self):
        val = self.bus.read(c_uint16(11))
        self.assertEqual(val.value, 0)
        self.m1.read.assert_not_called()
        self.m2.read.assert_not_called()

    def test_write_map_offset_at_zero(self):
        for val, i in enumerate(range(0, 5)):
            val = c_uint16(val)
            addr = c_uint16(i)
            self.bus.write(addr, val)
            actual_addr, actual_val = self.m1.write.call_args[0]
            self.assertEqual(actual_addr.value, addr.value)
            self.assertEqual(actual_val.value, val.value)

    def test_write_map_offset_at_none_zero(self):
        for val, i in enumerate(range(5, 10)):
            val = c_uint16(val)
            addr = c_uint16(i)
            self.bus.write(addr, val)
            actual_addr, actual_val = self.m2.write.call_args[0]
            expected_addr = c_uint16(i-5)
            self.assertEqual(actual_addr.value, expected_addr.value)
            self.assertEqual(actual_val.value, val.value)

    def test_write_does_nothing_if_no_mapping(self):
        self.bus.write(c_uint16(11), c_uint16(1))
        self.m1.write.assert_not_called()
        self.m2.write.assert_not_called()
