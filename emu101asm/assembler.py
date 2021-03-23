import re
from itertools import count
from io import FileIO


_re_label = re.compile(r"^(\w+):(.*)")
_re_op = re.compile(r"^(?:(?P<dst>[a-z0-9]+)(?:,(?P<dst_b>[a-z09]+))?)=(?P<src>[a-z0-9+@! ]+)(?:\?(?:(?P<cond>[a-z]+)(?:,(?P<cond_src>[a-z0-9]+))?))?")


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
