from math import inf
from typing import IO
from pprint import pprint as pp
from ctypes import c_uint16
from .bus import Bus
from .ram import RAM
from .rom import ROM
from .cpu import CPU


class EMU:
    def __init__(self):
        self.ram = RAM(0xEFFF)
        self.rom = ROM(0x0FFF)
        self.bus = Bus({
            (0x0000, 0xEFFF): self.ram,
            (0xF000, 0x0FFF): self.rom,
        })
        self.cpu = CPU(self.bus)

    def core_dump(self):
        self.cpu.core_dump()

    def run(self):
        try:
            while self.cpu.tick(): ...
            self.core_dump()
            print("ans:", self.bus.read(c_uint16(0x0201)).value)
        except:
            self.core_dump()
            raise

