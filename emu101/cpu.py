from .typing import c_uint16


class CPU:
    def __init__(self):
        # Address Registers
        self.ip = c_uint16(0xf000)
        self.sp = c_uint16(0x01ff)
        self.dr = c_uint16(0x0200)

        # Data Registers
        self.d0 = c_uint16(0)
        self.d1 = c_uint16(0)
        self.d2 = c_uint16(0)
