import re
from itertools import count
from io import FileIO
from enum import IntFlag


_re_label = re.compile(r"^(\w+):(.*)")
_re_op = re.compile(r"^(?:(?P<dst>[a-z0-9]+)(?:,(?P<dst_b>[a-z09]+))?)=(?P<src>[a-z0-9+@! ]+)(?:\?(?:(?P<cond>[a-z]+)(?:,(?P<cond_src>[a-z0-9]+))?))?")

class IOSelect(IntFlag):
    READ = 0b0000000000000000
    WRITE = 0b1000000000000000

compute_map = {
        "MINUS_D0D0": 0b0000000000000
        "MINUS_D0D1": 0b0000100000000
        "MINUS_D0D2": 0b0001000000000
        "OUT_D0": 0b0001100000000
        "ADD_D0D0": 0b0010000000000
        "ADD_D0D1": 0b0010100000000
        "ADD_D0D2": 0b0011000000000
        "OUT_D1": 0b0011100000000
        "AND_D0D0": 0b0100000000000
        "AND_D0D1": 0b0100100000000
        "AND_D0D2": 0b0101000000000
        "OUT_D2": 0b0101100000000
        "OR_D0D0": 0b0110000000000
        "OR_D0D1": 0b0110100000000
        "OR_D0D2": 0b0111000000000
        "ROLL_D0": 0b0111100000000
        "XOR_D0D0": 0b1000000000000
        "XOR_D0D1": 0b1000100000000
        "XOR_D0D2": 0b1001000000000
        "OUT_IP": 0b1001100000000
        "INC_D0": 0b1010000000000
        "INC_D1": 0b1010100000000
        "INC_D2": 0b1011000000000
        "OUT_SP": 0b1011100000000
        "DEC_D0": 0b1100000000000
        "DEC_D1": 0b1100100000000
        "DEC_D2": 0b1101000000000
        "OUT_DP": 0b1101100000000
        "NOT_D0": 0b1110000000000
        "NOT_D1": 0b1110100000000
        "NOT_D2": 0b1111000000000
        "ROLR_D0": 0b1111100000000
}

address_map = {
    "dp"    = 0b000000000000000
    "sp"    = 0b010000000000000
    "dp+d0" = 0b100000000000000
    "sp+d0" = 0b110000000000000
    "default" = 0b000000000000000 
}

condition_map = {
    "gt": 0b100
    "ge": 0b110
    "eq": 0b010
    "le": 0b011
    "lt": 0b001
    "ne": 0b101
    "z": 0b010
    "nz": 0b101
    "true": 0b111
    "false": 0b000
    "default": 0b111
}

dest_map = {
    "d0" = 0b000000
    "d1" = 0b001000
    "d2" = 0b010000
    "ip" = 0b100000
    "sp" = 0b101000
    "dp" = 0b110000
    "default" = 0b111000
}

source_map = {
    "alu": 0b01000000
    "data": 0b10000000
    "!": 0b11000000
    "@": 0b11000000
    "default": 0b00000000
}


class Assembler:
    def __init__(self, fp: FileIO, prog_offset=0x0200, ram_offset=0xf000):
        self._ram = count(prog_offset)
        self._prog = ram_offset
        self._fp = fp
        self._refs = {}

    def _iter(self):
        last_label = None
        last_label_i = 0
        for line_no, line in enumerate(self._fp):
            line = line.rstrip("\n").strip(" ")
            if line.startswith("#"):
                continue
            elif line == "":
                continue
            lb_match = _re_label.match(line)
            if lb_match:
                lb, op, *_ = lb_match.groups()
                last_label = lb
                last_label_i = 0
                yield line_no, lb.lower(), op.strip(" ").lower()
            elif last_label:
                last_label_i += 1
                yield line_no, f"{last_label}+{last_label_i}", line.lower()
            else:
                yield line_no, None, line.lower()

    def _get_ref(self, label):
        if label not in self._refs:
            self._add_ref(label, next(self._ram))
        return self._refs[label]

    def _add_ref(self, label, offset):
        self._refs[label] = offset.to_bytes(2, "big")

    def _find_labels(self):
        self._fp.seek(0)
        self._refs = {}
        for i, (_, label, line) in enumerate(self._iter()):
            offset = self._prog + i
            if label is not None:
                self._add_ref(label, offset)

    def _emit(self, val):
        print(val)

    def _assemble(self):
        self._fp.seek(0)
        for line_no, label, op in self._iter():
            print(op)
            op_match = _re_op.match(op)
            if op == "hlt":
                self._emit(0b1111111111111111)
            elif op == "nop" or op == "noop":
                self._emit(0b0000000000000000)
            elif op_match:
                print(op_match.groupdict())
            else:
                raise Exception(f"What you mean? {line_no}, {op}")
                #print(op)

    def assemble(self):
        self._find_labels()
        self._assemble()
        print(self._refs)
