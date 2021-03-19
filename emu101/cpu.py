from collections import deque
from enum import Enum
from .typing import c_uint16, CPUInterface


class InstructionPhase(Enum):
    FETCH_INSTRUCTION = 1
    DECODE_INSTRUCTION = 2
    EXECUTE_INSTRUCTION = 3


class IOSelect(Enum):
    READ = 0b0000000000000000
    WRITE = 0b1000000000000000


class AddressSelect(Enum):
    DP_D0 = 0b000000000000000
    DP    = 0b010000000000000
    DSP   = 0b100000000000000
    ISP   = 0b110000000000000


class ComputeSelect(Enum):
    MINUS_D0D0 = 0b0000000000000
    MINUS_D0D1 = 0b0000100000000
    MINUS_D0D2 = 0b0001000000000
    OUT_D0     = 0b0001100000000
    ADD_D0D0   = 0b0010000000000
    ADD_D0D1   = 0b0010100000000
    ADD_D0D2   = 0b0011000000000
    OUT_D1     = 0b0011100000000
    AND_D0D0   = 0b0100000000000
    AND_D0D1   = 0b0100100000000
    AND_D0D2   = 0b0101000000000
    OUT_D2     = 0b0101100000000
    OR_D0D0    = 0b0110000000000
    OR_D0D1    = 0b0110100000000
    OR_D0D2    = 0b0111000000000
    ROLL_D0    = 0b0111100000000
    XOR_D0D0   = 0b1000000000000
    XOR_D0D1   = 0b1000100000000
    XOR_D0D2   = 0b1001000000000
    OUT_IP     = 0b1001100000000
    INC_D0     = 0b1010000000000
    INC_D1     = 0b1010100000000
    INC_D2     = 0b1011000000000
    OUT_SP     = 0b1011100000000
    DEC_D0     = 0b1100000000000
    DEC_D1     = 0b1100100000000
    DEC_D2     = 0b1101000000000
    OUT_DP     = 0b1101100000000
    NOT_D0     = 0b1110000000000
    NOT_D1     = 0b1110100000000
    NOT_D2     = 0b1111000000000
    ROLR_D0    = 0b1111100000000


class SourceSelect(Enum):
    ZERO = 0b00000000
    ALU = 0b01000000
    DATA = 0b10000000
    IMMEDIATE = 0b11000000


class DestSelect(Enum):
    D0 = 0b000000
    D1 = 0b001000
    D2 = 0b010000
    N1 = 0b011000
    IP = 0b100000
    SP = 0b101000
    DP = 0b110000
    N2 = 0b111000


class ConditionSelect(Enum):
    FALSE = 0b000
    LT    = 0b001
    EQ    = 0b010
    LE    = 0b011
    GT    = 0b100
    NE    = 0b101
    GE    = 0b110
    TRUE  = 0b111


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

        self.data = c_uint16(0)

        # Other Things
        self._bus = bus
        self._halt = False
        self._io_select = IOSelect.READ
        self._address_select = AddressSelect.DP
        self._source_select = SourceSelect.ZERO
        self._comp_select = ComputeSelect.MINUS_D0D0
        self._dest_select = DestSelect.N1
        self._cond_select = ConditionSelect.FALSE
        self._phase = InstructionPhase.FETCH_INSTRUCTION
        self._tick = {
            InstructionPhase.DECODE_INSTRUCTION: self._decode_instruction,
            InstructionPhase.EXECUTE_INSTRUCTION: self._execute_instruction,
            InstructionPhase.FETCH_INSTRUCTION: self._fetch_instruction,
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
            self._phase = InstructionPhase.DECODE_INSTRUCTION
        else:
            raise RuntimeError("Um, pipline overflow?")
        return self._fetch_instruction

    def _decode_instruction(self):

        instruction = self.pipeline.pop()
        self.instruction.value = instruction

        # HLT instruction is special case
        if instruction == 0:
            self._halt = True

        # Write to ram
        self._io_select = IOSelect(instruction & 0b1000000000000000)
        # Ram address source
        self._address_select = AddressSelect(instruction & 0b0110000000000000)
        # ALU (and input) operation
        self._comp_select = ComputeSelect(instruction & 0b0001111100000000)
        # Register Write Source Select
        self._source_select = SourceSelect(instruction & 0b0000000011000000)
        # Register Write Destination  Select
        self._dest_select = DestSelect(instruction & 0b0000000000111000)
        # Conditional
        self._cond_select = ConditionSelect(instruction & 0b0000000000000111)
        print(self._io_select, self._address_select, self._comp_select, self._source_select, self._dest_select, self._cond_select)
        self._phase = InstructionPhase.EXECUTE_INSTRUCTION

    def _execute_instruction(self):
        #self._execute_alu()
        self._execute_io()
        #self._execute_store()
        self._phase = InstructionPhase.FETCH_INSTRUCTION

    def _execute_io(self):
        if self._io_select == IOSelect.READ:
            self.data = self._execute_read()
        elif self._io_select == IOSelect.WRITE:
            self._execute_write()
            
    def _execute_read(self):
        if self._address_select == AddressSelect.DP:
            return self._bus.read(self.dp)
        if self._address_select == AddressSelect.DP_D0:
            return self._bus.read(c_uint16(self.dp.value + self.d0.value))
        if self._address_select == AddressSelect.DSP:
            self.sp.value -= 1
            return self._bus.read(self.sp)
        if self._address_select == AddressSelect.ISP:
            return self._bus.read(self.sp)
            self.sp.value += 1

    def _execute_write(self):
        if self._address_select == AddressSelect.DP:
            return self._bus.write(self.dp, self.data)
        if self._address_select == AddressSelect.DP_D0:
            addr = c_uint16(self.dp.value + self.d0.value)
            return self._bus.write(addr, self.data)
        if self._address_select == AddressSelect.DSP:
            self.sp.value -= 1
            return self._bus.write(self.sp, self.data)
        if self._address_select == AddressSelect.ISP:
            return self._bus.write(self.sp, self.data)
            self.sp.value += 1

    def tick(self):
        if self._halt:
            return False
        self._tick[self._phase]()
        return not self._halt
