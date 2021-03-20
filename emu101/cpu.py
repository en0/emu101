from collections import deque
from enum import Enum, IntFlag
from .typing import c_uint16, CPUInterface


class InstructionPhase(Enum):
    FETCH_INSTRUCTION = 1
    DECODE_INSTRUCTION = 2
    EXECUTE_INSTRUCTION = 3


class IOSelect(Enum):
    READ = 0b0000000000000000
    WRITE = 0b1000000000000000


class AddressSelect(Enum):
    DP   = 0b000000000000000
    SP   = 0b010000000000000
    DPD0 = 0b100000000000000
    SPD0 = 0b110000000000000


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


class ConditionFlags(IntFlag):
    LT    = 0b001
    EQ    = 0b010
    GT    = 0b100


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

        self.data_in = c_uint16(0)
        self.alu_out = c_uint16(0)
        self.flags = c_uint16(0)

        # Other Things
        self._bus = bus
        self._halt = False
        self._debug = False
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

    def _decode_instruction(self):

        instruction = self.pipeline.pop()
        self.instruction.value = instruction

        if instruction == 0xffff:
            # HLT instruction is special case
            self._halt = True
            self._io_select = IOSelect.READ
            self._address_select = AddressSelect.DP
            self._comp_select = ComputeSelect.MINUS_D0D0
            self._source_select = SourceSelect.ZERO
            self._dest_select = DestSelect.D0
            self._cond_select = ConditionSelect.FALSE
        elif instruction == 0b0101010101010101:
            self._debug = True
            self._io_select = IOSelect.READ
            self._address_select = AddressSelect.DP
            self._comp_select = ComputeSelect.MINUS_D0D0
            self._source_select = SourceSelect.ZERO
            self._dest_select = DestSelect.D0
            self._cond_select = ConditionSelect.FALSE
        else:
            self._io_select = IOSelect(instruction & 0b1000000000000000)
            self._address_select = AddressSelect(instruction & 0b0110000000000000)
            self._comp_select = ComputeSelect(instruction & 0b0001111100000000)
            self._source_select = SourceSelect(instruction & 0b0000000011000000)
            self._dest_select = DestSelect(instruction & 0b0000000000111000)
            self._cond_select = ConditionSelect(instruction & 0b0000000000000111)

        self._phase = InstructionPhase.EXECUTE_INSTRUCTION

    def _execute_instruction(self):
        self._execute_alu()
        self._execute_io()
        self._execute_store()
        self._phase = InstructionPhase.FETCH_INSTRUCTION

    def _execute_store(self):
        val = {
            SourceSelect.ALU: (lambda: self.alu_out),
            SourceSelect.DATA: (lambda: self.data_in),
            SourceSelect.IMMEDIATE: (lambda: c_uint16(self.pipeline.pop())),
            SourceSelect.ZERO: (lambda: c_uint16(0))
        }[self._source_select]()

        if bool(self.flags.value & self._cond_select.value):
            {
                DestSelect.D0: self.d0,
                DestSelect.D1: self.d1,
                DestSelect.D2: self.d2,
                DestSelect.N1: c_uint16(0),
                DestSelect.IP: self.ip,
                DestSelect.SP: self.sp,
                DestSelect.DP: self.dp,
                DestSelect.N2: c_uint16(0),
            }[self._dest_select].value = val.value

            # if dest is IP, the pipeline needs to be cleared
            if self._dest_select == DestSelect.IP:
                self.pipeline.clear()

    def _execute_alu(self):
        result = {
            ComputeSelect.MINUS_D0D0: (lambda: self.d0.value - self.d0.value),
            ComputeSelect.MINUS_D0D1: (lambda: self.d0.value - self.d1.value),
            ComputeSelect.MINUS_D0D2: (lambda: self.d0.value - self.d2.value),
            ComputeSelect.OUT_D0: (lambda: self.d0.value),
            ComputeSelect.ADD_D0D0: (lambda: self.d0.value + self.d0.value),
            ComputeSelect.ADD_D0D1: (lambda: self.d0.value + self.d1.value),
            ComputeSelect.ADD_D0D2: (lambda: self.d0.value + self.d2.value),
            ComputeSelect.OUT_D1: (lambda: self.d1.value),
            ComputeSelect.AND_D0D0: (lambda: self.d0.value & self.d0.value),
            ComputeSelect.AND_D0D1: (lambda: self.d0.value & self.d1.value),
            ComputeSelect.AND_D0D2: (lambda: self.d0.value & self.d2.value),
            ComputeSelect.OUT_D2: (lambda: self.d2.value),
            ComputeSelect.OR_D0D0: (lambda: self.d0.value | self.d0.value),
            ComputeSelect.OR_D0D1: (lambda: self.d0.value | self.d1.value),
            ComputeSelect.OR_D0D2: (lambda: self.d0.value | self.d2.value),
            ComputeSelect.ROLL_D0: (lambda: self.d0.value << 1),
            ComputeSelect.XOR_D0D0: (lambda: self.d0.value ^ self.d0.value),
            ComputeSelect.XOR_D0D1: (lambda: self.d0.value ^ self.d1.value),
            ComputeSelect.XOR_D0D2: (lambda: self.d0.value ^ self.d2.value),
            ComputeSelect.OUT_IP: (lambda: self.ip.value),
            ComputeSelect.INC_D0: (lambda: self.d0.value + 1),
            ComputeSelect.INC_D1: (lambda: self.d1.value + 1),
            ComputeSelect.INC_D2: (lambda: self.d2.value + 1),
            ComputeSelect.OUT_SP: (lambda: self.sp.value),
            ComputeSelect.DEC_D0: (lambda: self.d0.value - 1),
            ComputeSelect.DEC_D1: (lambda: self.d1.value - 1),
            ComputeSelect.DEC_D2: (lambda: self.d2.value - 1),
            ComputeSelect.OUT_DP: (lambda: self.dp.value),
            ComputeSelect.NOT_D0: (lambda: ~self.d0.value),
            ComputeSelect.NOT_D1: (lambda: ~self.d1.value),
            ComputeSelect.NOT_D2: (lambda: ~self.d2.value),
            ComputeSelect.ROLR_D0: (lambda: self.d0.value >> 1),
        }[self._comp_select]()

        self.flags.value = (
            ConditionFlags.GT if result > 0 else 0 |
            ConditionFlags.LT if result < 0 else 0 |
            ConditionFlags.EQ if result == 0 else 0
        )

        self.alu_out.value = result

    def _execute_io(self):
        if self._io_select == IOSelect.READ:
            self._execute_read()
        elif (
            self._io_select == IOSelect.WRITE and
            bool(self.flags.value & self._cond_select.value)
        ):
            self._execute_write()
            
    def _execute_read(self):
        if self._address_select == AddressSelect.DP:
            self.data_in = self._bus.read(self.dp)

        elif self._address_select == AddressSelect.SP:
            self.data_in = self._bus.read(self.sp)
            self.sp.value += 1

        elif self._address_select == AddressSelect.DPD0:
            addr = c_uint16(self.dp.value + self.d0.value)
            self.data_in = self._bus.read(addr)

        elif self._address_select == AddressSelect.SPD0:
            addr = c_uint16(self.sp.value + self.d0.value)
            self.data_in = self._bus.read(addr)

    def _execute_write(self):
        if self._address_select == AddressSelect.DP:
            self._bus.write(self.dp, self.alu_out)

        elif self._address_select == AddressSelect.SP:
            self.sp.value -= 1
            self._bus.write(self.sp, self.alu_out)

        elif self._address_select == AddressSelect.DPD0:
            addr = c_uint16(self.dp.value + self.d0.value)
            self._bus.write(addr, self.alu_out)

        elif self._address_select == AddressSelect.SPD0:
            addr = c_uint16(self.sp.value + self.d0.value)
            self._bus.write(addr, self.alu_out)

    def tick(self):
        if self._halt:
            return False
        self._tick[self._phase]()
        if self._debug:
            self.core_dump()
            import pdb; pdb.set_trace()
        return not self._halt

    def core_dump(self):
        print("")
        print("EMU101 Core Dump -------------------")
        print("Panic in phase", self._phase)
        print("")
        print("ip: {:04x} ({:016b})".format(self.ip.value, self.ip.value))
        print("sp: {:04x} ({:016b})".format(self.sp.value, self.sp.value))
        print("dp: {:04x} ({:016b})".format(self.dp.value, self.dp.value))
        print("d0: {:04x} ({:016b})".format(self.d0.value, self.d0.value))
        print("d1: {:04x} ({:016b})".format(self.d1.value, self.d1.value))
        print("d2: {:04x} ({:016b})".format(self.d2.value, self.d2.value))
        print("")
        print("instruction: {:016b}".format(self.instruction.value))
        print("immediate:   {:04x}".format(self.immediate.value))
        print("pipeline:   [{}]".format(", ".join(["{:04x}".format(v) for v in self.pipeline])))
        print("")
        print("data_in: {:04x}".format(self.data_in.value))
        print("alu_out: {:04x}".format(self.alu_out.value))
        print("flags:   {:016b}".format(self.flags.value))
        print("")
