from math import inf
from typing import IO
from pprint import pprint as pp
from .bus import Bus
from .ram import RAM
from .rom import ROM
from .cpu import CPU


class EMU:
    def __init__(self):
        self.rom = ROM(0xEFFF)
        self.ram = RAM(0x0FFF)
        self.bus = Bus({
            (0x0000, 0xEFFF): self.ram,
            (0xF000, 0x0FFF): self.rom,
        })
        self.cpu = CPU(self.bus)

    def run(self):
        while self.cpu.tick(): ...

