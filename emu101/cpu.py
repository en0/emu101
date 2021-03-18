from collections import deque
from .typing import c_uint16, CPUInterface


class CPU(CPUInterface):
    def __init__(self, bus):

        # Address Registers
        self.ip = c_uint16(0xf000)
        self.sp = c_uint16(0x01ff)
        self.dp = c_uint16(0x0200)

        # Data Registers
        self.d0 = c_uint16(0)
        self.d1 = c_uint16(0)
        self.d2 = c_uint16(0)

        # internal registers
        self.instruction = c_uint16(0)
        self.immediate = c_uint16(0)
        self.pipeline = deque()

        # Other Things
        self._bus = bus
        self._tick = self._fetch_instruction

    def _fetch_pc(self):
        val = self._bus.read(self.ip)
        self.ip.value += 1
        return val.value

    def _fetch_instruction(self):
        if len(self.pipeline) == 2:
            ...
        elif len(self.pipeline) == 1:
            self.pipeline.appendleft(self._fetch_pc())
        elif len(self.pipeline) == 0:
            self.pipeline.appendleft(self._fetch_pc())
        else:
            raise RuntimeError("Um, pipline overflow?")
        return self._fetch_instruction

    def tick(self):
        self._tick = self._tick()
