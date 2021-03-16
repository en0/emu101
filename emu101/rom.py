from typing import IO
from .typing import BusInterface, c_uint16, c_uint8

class ROM(BusInterface):
    def __init__(self, size: int) -> None:
        self._data = [c_uint8(0) for _ in range(size)]

    def read(self, addr: c_uint16) -> c_uint8:
        return self._data[addr.value]

    def write(self, addr: c_uint16, value: c_uint8) -> None:
        ...

    def load(self, fp: IO, at: c_uint16 = None) -> None:
        addr = at.value if at else 0
        byte = fp.read(1)
        while byte:
            self._data[c_uint16(addr).value] = c_uint8(ord(byte))
            byte = fp.read(1)
            addr += 1
