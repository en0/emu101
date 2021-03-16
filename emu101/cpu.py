from .typing import c_uint16, c_uint8, c_bool


class CPU:
    def __init__(self):
        # Address Register
        self.a = c_uint8(0)

        # Data Registers
        self.r1 = c_uint8(0)
        self.r2 = c_uint8(0)

        # Control registers
        self.pc = c_uint16(0xfffc)
        self.sp = c_uint16(0x1000)

        # Flags
        self.if = c_bool(False) # Interrupt Flag
        self.cf = c_bool(False) # Carry Flag
        self.zf = c_bool(False) # Zero Flag
        self.of = c_bool(False) # overflow Flag
        self.sf = c_bool(False) # Sign Flag
        self.hf = c_bool(False) # Halt Flag
