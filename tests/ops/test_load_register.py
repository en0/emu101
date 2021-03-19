import unittest
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
            0b0000000000000000, # hlt
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.dp.value, 0xabcd)
        
    def test_hlt(self):
        self.load_rom([
            0b0000000000000000, #hlt
        ])
        self.emu.run()

    def test_loads_pipeline(self):
        self.load_rom([
            0b0000000000000000, #hlt
        ])
        self.emu.run()
        self.assertEqual(len(self.emu.cpu.pipeline), 1)
