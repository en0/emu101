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

    def load_ram(self, words, addr = 0):
        self.emu.ram.load(BytesIO(b''.join([
            int.to_bytes(w, 2, "big")
            for w in words
        ])), c_uint16(addr))

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
            0b0000000011000111, 0xbeef, # LD0 0xbeef
            0b1000001100111111,         # WD0
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.bus.read(c_uint16(0xabcd)).value, 0xbeef)

    def test_read_memory_at_dp(self):
        self.emu.bus.write(c_uint16(0xabcd), c_uint16(0xbeef))
        self.load_rom([
            0b0000000011110111, 0xabcd, # LDP 0xabcd
            0b0000000010000111,         # RD0
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.d0.value, 0xbeef)

    def test_jmp_to_immediate(self):
        # Put a hlt instruction at memory 0
        self.emu.bus.write(c_uint16(0x0000), c_uint16(0xFFFF))
        self.load_rom([
            0b0000000011100111, 0x0000, # jmp 0x0000
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        # It should be 2 because the pipeline was cleared on jump
        self.assertEqual(self.emu.cpu.ip.value, 2)

    def test_jmp_to_d0(self):
        # Put a hlt instruction at memory 0
        self.emu.bus.write(c_uint16(0x0000), c_uint16(0xFFFF))
        self.load_rom([
            0b0000000011000111, 0x0000, # LD0 0x0000
            0b0000001101100111,         # JMP
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        # It should be 2 because the pipeline was cleared on jump
        self.assertEqual(self.emu.cpu.ip.value, 2)

    def test_instruction_after_jmp(self):
        self.load_ram([
            0b0000000011000111, 0xbeef, # LD0 0xbeef
            0b1111111111111111,         # HLT
        ])
        self.load_rom([
            0b0000000011000111, 0x0000, # LD0 0x0000
            0b0000001101100111,         # JMP
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.d0.value, 0xbeef)

    def test_instruction_after_jmp_to_immediate(self):
        self.load_ram([
            0b0000000011000111, 0xbeef, # LD0 0xbeef
            0b1111111111111111,         # HLT
        ])
        self.load_rom([
            0b0000000011100111, 0x0000, # jmp 0x0000
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.d0.value, 0xbeef)

    def test_jsr_and_ret(self):
        self.load_ram([
            0b0000000011000111, 0xbeef, # LD0 0xbeef
            0b0010000010100111,         # RET
            0b1111111111111111,         # HLT
        ])
        self.load_rom([
            # WAACCCCCSSDDDJJJ 
            0b1011001111100111, 0x0000, # JSR 0x0000
            0b0000000011000111, 0xbeaf, # LD0 0xbeaf
            0b1111111111111111,         # HLT
        ])
        self.emu.run()
        self.assertEqual(self.emu.cpu.d0.value, 0xbeaf)
        self.assertEqual(self.emu.cpu.ip.value, 0xf006)

    def test_push(self):
        self.load_rom([
            # WAACCCCCSSDDDJJJ 
            0b0000000011000111, 0xbeef, # LD0 0xbeef
            0b1010001101111111,         # push d0
            0b1111111111111111,         # hlt
        ])
        self.emu.run()
        self.assertEqual(self.emu.bus.read(c_uint16(0x01ff - 1)).value, 0xbeef)
        
    def test_hlt(self):
        self.load_rom([
            0b1111111111111111, #hlt
        ])
        self.emu.run()

    def test_loads_pipeline(self):
        self.emu.cpu.tick()
        self.emu.cpu.tick()
        self.assertEqual(len(self.emu.cpu.pipeline), 2)
