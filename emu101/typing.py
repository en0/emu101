from ctypes import c_uint16
from abc import ABC, abstractmethod


class CPUInterface(ABC):
    @abstractmethod
    def tick(self):
        pass


class BusInterface(ABC):
    @abstractmethod
    def read(self, addr: c_uint16) -> c_uint16:
        ...

    @abstractmethod
    def write(self, addr: c_uint16, value: c_uint16) -> None:
        ...
