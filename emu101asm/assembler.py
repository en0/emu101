import re
from itertools import count
from io import FileIO
from enum import IntFlag
from typing import NamedTuple


_re_label = re.compile(r"^(\w+):(.*)")
_re_op = re.compile(r"^(?:(?P<dst>[a-z0-9]+)(?:,(?P<dst_b>[a-z09]+))?)=(?P<src>[a-z0-9+@! ]+)(?:\?(?:(?P<cond>[a-z]+)(?:,(?P<cond_src>[a-z0-9]+))?))?")

io_map = {
    "r": 0b0000000000000000,
    "w": 0b1000000000000000,
}

compute_map = {
    "sub d0": 0b0000000000000,
    "sub d1": 0b0000100000000,
    "sub d2": 0b0001000000000,
    "d0": 0b0001100000000,
    "add d0": 0b0010000000000,
    "add d1": 0b0010100000000,
    "add d2": 0b0011000000000,
    "d1": 0b0011100000000,
    "and d0": 0b0100000000000,
    "and d1": 0b0100100000000,
    "and d2": 0b0101000000000,
    "d2": 0b0101100000000,
    "or d0": 0b0110000000000,
    "or d1": 0b0110100000000,
    "or d2": 0b0111000000000,
    "shl": 0b0111100000000,
    "xor d0": 0b1000000000000,
    "xor d1": 0b1000100000000,
    "xor d2": 0b1001000000000,
    "ip": 0b1001100000000,
    "inc d0": 0b1010000000000,
    "inc d1": 0b1010100000000,
    "inc d2": 0b1011000000000,
    "sp": 0b1011100000000,
    "dec d0": 0b1100000000000,
    "dec d1": 0b1100100000000,
    "dec d2": 0b1101000000000,
    "dp": 0b1101100000000,
    "not d0": 0b1110000000000,
    "not d1": 0b1110100000000,
    "not d2": 0b1111000000000,
    "shr": 0b1111100000000,
}

address_map = {
    "dp": 0b000000000000000,
    "sp": 0b010000000000000,
    "dp+d0": 0b100000000000000,
    "sp+d0": 0b110000000000000,
    "default": 0b000000000000000 ,
}

condition_map = {
    "gt": 0b100,
    "ge": 0b110,
    "eq": 0b010,
    "le": 0b011,
    "lt": 0b001,
    "ne": 0b101,
    "z": 0b010,
    "nz": 0b101,
    "true": 0b111,
    "false": 0b000,
    "default": 0b111,
}

dest_map = {
    "d0": 0b000000,
    "d1": 0b001000,
    "d2": 0b010000,
    "ip": 0b100000,
    "sp": 0b101000,
    "dp": 0b110000,
    "default": 0b111000,
}

source_map = {
    "alu": 0b01000000,
    "data": 0b10000000,
    "!": 0b11000000,
    "@": 0b11000000,
    "default": 0b00000000,
}


class AssemblyBytes(NamedTuple):
    bytecode: bytes
    opcode: str 
    line_no: int
    has_imm: bool


class CompileError(RuntimeError):
    def __init__(self, line_no: int, label: str, symbol: str, info: str):
        self.line_no = line_no
        self.label = label
        self.symbol = symbol
        self.info = info


class DecodingError(RuntimeError):
    def __init__(self, info):
        self.info = info


class Assembler:
    def __init__(self, in_fp: FileIO, out_fp: FileIO, prog_offset=0x0200, ram_offset=0xf000):
        self._ram = count(prog_offset)
        self._prog = ram_offset
        self._offset = ram_offset
        self._fp = in_fp
        self._out = out_fp
        self._refs = {}
        self._assembled_bytes = []
        self._pending_refs = {}

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
            self._add_label(label, next(self._ram))
        return self._refs[label]

    def _add_label(self, label, offset=None):
        if offset is None:
            self._refs[label] = len(self._assembled_bytes)+self._prog
        else:
            self._refs[label] = offset

    def _decode_cond(self, cond, cond_src, **kwargs):
        if cond is None:
            return condition_map["default"]

        if cond in condition_map:
            code = condition_map[cond]
        else:
            raise DecodingError("Unknown Conditional")

        if cond_src is not None and cond_src in compute_map:
            code |= compute_map[cond_src]

        elif cond_src is not None:
            raise DecodingError("Unknown Source or Computation in Conditional")

        return code

    def _decode_src(self, src, **kwargs):
        code, imm = 0 | source_map["default"], None
        if src.startswith("!0x"):
            imm = int(src[3:], 16)
            code = source_map["!"]
        elif src.startswith("!0b"):
            imm = int(src[3:], 2)
            code = source_map["!"]
        elif src.startswith("!"):
            imm = int(src[1:], 10)
            code = source_map["!"]
        elif src.startswith("@"):
            imm = src[1:]
            code = source_map["@"]
        elif src == "data":
            code = source_map["data"]
        elif src in compute_map:
            code = compute_map[src] | source_map["alu"]
        else:
            raise DecodingError("Unknown Source or Computation")

        return code, imm

    def _decode_dst(self, dst, dst_b, **kwargs):

        def get_dest(d):
            try:
                return dest_map[d]
            except KeyError:
                raise DecodingError("Unknown Destination")

        code = dest_map["default"]
        if dst_b is None and dst == 'data':
            code = io_map["w"] | dest_map["default"] | address_map["dp"]
        elif dst_b is None:
            code = get_dest(dst)
        elif dst == dst_b:
            raise DecodingError("Duplicate Destination Error")
        elif dst_b == 'data':
            code = io_map["w"] | get_dest(dst) | address_map["dp"]
        elif dst == 'data':
            code = io_map["w"] | get_dest(dst_b) | address_map["dp"]
        else:
            raise DecodingError("Unknown Destination Error")
        return code

    def _append_bytes(self, code: int, imm, opcode, lineno):
        self._assembled_bytes.append(AssemblyBytes(
            bytecode=code.to_bytes(2, "big"),
            opcode=opcode,
            line_no=lineno,
            has_imm=imm is not None
        ))

        if isinstance(imm, int):
            self._assembled_bytes.append(AssemblyBytes(
                bytecode=imm.to_bytes(2, "big"),
                opcode=opcode,
                line_no=lineno,
                has_imm=False
            ))

        elif isinstance(imm, str):
            self._pending_refs[len(self._assembled_bytes)] = imm
            self._assembled_bytes.append(AssemblyBytes(
                bytecode=None,
                opcode=opcode,
                line_no=lineno,
                has_imm=False
            ))

    def _set_bytes(self, val: int, offset: int):
        ab = self._assembled_bytes[offset]
        self._assembled_bytes[offset] = AssemblyBytes(
            bytecode=val.to_bytes(2, 'big'),
            opcode=ab.opcode,
            line_no=ab.line_no,
            has_imm=ab.has_imm,
        )

    def assemble(self):
        try:
            for line_no, label, op in self._iter():
                try:
                    self._add_label(label)
                    code = 0b0000000000000000
                    imm = None
                    op_match = _re_op.match(op)
                    if op == "hlt":
                        code = 0b1111111111111111
                    elif op == "nop" or op == "noop":
                        code = 0b0000000000000000
                    elif op == "brk":
                        code = 0b0101010101010101
                    elif op_match:
                        c = op_match.groupdict()
                        code |= self._decode_dst(**c)
                        src_code, imm = self._decode_src(**c)
                        code |= src_code
                        code |= self._decode_cond(**c)
                    else:
                        raise CompileError(line_no, label, op, "Syntax Error")
                except DecodingError as ex:
                    raise CompileError(line_no, label, op, ex.info) from ex
                except CompileError as ex:
                    raise
                except Exception as ex:
                    raise CompileError(line_no, label, op, "Unknown Error") from ex
                else:
                    self._append_bytes(code, imm, op, line_no)
        except CompileError as ex:
            print(f"{ex.info}\nLine: {ex.line_no}, Symbol: {ex.symbol}")
            return

        self._fulfill_pending_refs()
        self._write_assembly()

    def _fulfill_pending_refs(self):
        for offset, label in self._pending_refs.items():
            addr = self._get_ref(label)
            self._set_bytes(addr, offset)

    def _write_assembly(self):
        assembly_bytes = enumerate(iter(self._assembled_bytes))
        try:
            while True:
                i, ab = next(assembly_bytes)
                self._out.write(ab.bytecode)
                if ab.has_imm:
                    _, imm = next(assembly_bytes)
                    self._out.write(imm.bytecode)
                    print("{:04x}: {:016b} {:04x} {}".format(
                        i + self._prog,
                        int.from_bytes(ab.bytecode, "big"),
                        int.from_bytes(imm.bytecode, "big"),
                        ab.opcode,
                    ))
                else:
                    print("{:04x}: {:016b} ---- {}".format(
                        i + self._prog,
                        int.from_bytes(ab.bytecode, "big"),
                        ab.opcode,
                    ))
        except StopIteration:
            pass
