from collections import deque
from enum import Enum
from .typing import c_uint16, CPUInterface


class Phase(Enum):
    FETCH_INSTRUCTION = 1
    DECODE_INSTRUCTION = 2
    EXECUTE_INSTRUCTION = 3


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
        self._halt = False
        self._phase = Phase.FETCH_INSTRUCTION
        self._tick = {
            Phase.DECODE_INSTRUCTION: self._decode_instruction,
            Phase.EXECUTE_INSTRUCTION: self._execute_instruction,
            Phase.FETCH_INSTRUCTION: self._fetch_instruction,
        }

    def _fetch_pc(self):
        val = self._bus.read(self.ip)
        self.ip.value += 1
        return val.value

    def _fetch_instruction(self):
        if len(self.pipeline) == 0:
            self.pipeline.appendleft(self._fetch_pc())
        elif len(self.pipeline) == 1:
            self.pipeline.appendleft(self._fetch_pc())
            self._phase = Phase.DECODE_INSTRUCTION
        else:
            raise RuntimeError("Um, pipline overflow?")
        return self._fetch_instruction

    def _decode_instruction(self):

        instruction = self.pipeline.pop()
        self.instruction.value = instruction

        # HLT instruction is special case
        if instruction == 0:
            self._halt = True

        self._phase = Phase.EXECUTE_INSTRUCTION

    def _execute_instruction(self):
        self._phase = Phase.FETCH_INSTRUCTION

    def tick(self):
        if self._halt:
            return False
        self._tick[self._phase]()
        return not self._halt
