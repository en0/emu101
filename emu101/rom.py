from typing import IO
from .typing import BusInterface, c_uint16

class ROM(BusInterface):
    def __init__(self, size: int) -> None:
        self._data = [c_uint16(0) for _ in range(size)]

    def read(self, addr: c_uint16) -> c_uint16:
        return self._data[addr.value]

    def write(self, addr: c_uint16, value: c_uint16) -> None:
        ...

    def load(self, fp: IO, at: c_uint16 = None) -> None:
        addr = at.value if at else 0
        word = fp.read(2)
        while word:
            self._data[c_uint16(addr).value] = c_uint16(int.from_bytes(word, 'big'))
            word = fp.read(2)
            addr += 1
