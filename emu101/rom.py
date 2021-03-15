from .typing import BusInterface, c_uint16, c_uint8

class ROM(BusInterface):
    def __init__(self, size: int) -> None:
        self._data = [c_uint8(0) for _ in range(size)]

    def read(self, addr: c_uint16) -> c_uint8:
        return self._data[addr.value]

    def write(self, addr: c_uint16, value: c_uint8) -> None:
        ...
