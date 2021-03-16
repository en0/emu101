from ctypes import c_uint16, c_uint8, c_bool
from abc import ABC, abstractmethod


class CPUInterface(ABC):
    ...


class BusInterface(ABC):
    @abstractmethod
    def read(self, addr: c_uint16) -> c_uint8:
        ...

    @abstractmethod
    def write(self, addr: c_uint16, value: c_uint8) -> None:
        ...
