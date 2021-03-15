from .typing import BusInterface, c_uint16, c_uint8
from .rom import ROM

class RAM(ROM, BusInterface):
    def write(self, addr: c_uint16, value: c_uint8) -> None:
        self._data[addr.value] = value
