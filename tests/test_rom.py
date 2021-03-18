import unittest
from ctypes import c_uint16
from io import BytesIO
from emu101.rom import ROM
from random import randint


class ROMTest(unittest.TestCase):

    def test_load_small_file(self):
        data = b'\xfe\xfa'
        fd = BytesIO(data)
        rom = ROM(1)
        rom.load(fd)
        self.assertEqual(rom.read(c_uint16(0)).value, 65274)

    def test_load_less_small_file(self):
        data = b'\x2e\xfa\x01\x02'
        fd = BytesIO(data)
        rom = ROM(2)
        rom.load(fd)
        self.assertEqual(rom.read(c_uint16(0)).value, 12026)
        self.assertEqual(rom.read(c_uint16(1)).value, 258)

    def test_memory_offset(self):
        data = b'\x2e\xfa'
        fd = BytesIO(data)
        rom = ROM(100)
        rom.load(fd, c_uint16(50))
        self.assertEqual(rom.read(c_uint16(50)).value, 12026)

    def test_memory_offset_2(self):
        data = b'\x2e\xfa\x01\x02'
        fd = BytesIO(data)
        rom = ROM(100)
        rom.load(fd, c_uint16(50))
        self.assertEqual(rom.read(c_uint16(50)).value, 12026)
        self.assertEqual(rom.read(c_uint16(51)).value, 258)
