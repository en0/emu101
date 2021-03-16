import unittest
from ctypes import c_uint16, c_uint8
from io import BytesIO
from emu101.rom import ROM


class ROMTest(unittest.TestCase):
    def setUp(self):
        self.rom = ROM(10)

    def test_load_file(self):
        byte_arr = []
        for val in range(10, 20):
            byte_arr.append(val.to_bytes(1, "little"))
        fd = BytesIO(b''.join(byte_arr))
        self.rom.load(fd)
        for i, val in enumerate(range(10, 20)):
            addr = c_uint16(i)
            self.assertEqual(self.rom.read(addr).value, val)

