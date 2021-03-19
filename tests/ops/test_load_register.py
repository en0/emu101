import unittest
from ctypes import c_uint16
from io import BytesIO
from emu101.emu import EMU


class LoadRegTest(unittest.TestCase):

    def setUp(self):
        self.emu = EMU()

    def load_rom(self, words):
        self.emu.rom.load(BytesIO(b''.join([
            int.to_bytes(w, 2, "big")
            for w in words
        ])))

    def test_ldp(self):
        self.load_rom([
            0b0000000011110111, 0xabcd, # ldp 0xabcd
            0b1111111111111111, # hlt
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.dp.value, 0xabcd)

    def test_write_memory_at_dp(self):
        self.load_rom([
            0b0000000011110111, 0xabcd, # LDP 0xabcd
            0b1000001100111111,         # WD0
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.ram.read(c_uint16(0xabcd)).value, 0x0000)
        
    def test_hlt(self):
        self.load_rom([
            0b1111111111111111, #hlt
        ])
        self.emu.run()

    def test_loads_pipeline(self):
        self.emu.cpu.tick()
        self.emu.cpu.tick()
        self.assertEqual(len(self.emu.cpu.pipeline), 2)
