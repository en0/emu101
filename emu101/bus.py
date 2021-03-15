from typing import Dict, Tuple, List
from .typing import BusInterface, c_uint16, c_uint8


class Bus(BusInterface):
    def __init__(self, memory_map: Dict[Tuple[int, int], BusInterface]):
        self._map: List[BusInterface] = [None for _ in range(0x10000)]
        self._comp_offsets = dict()
        for (start, length), comp in memory_map.items():
            self._comp_offsets[comp] = start
            for addr in range(start, start + length):
                self._map[c_uint16(addr).value] = comp

    def read(self, addr: c_uint16) -> c_uint8:
        comp: BusInterface = self._map[addr.value]
        if comp is None:
            return c_uint16(0)
        offset = self._comp_offsets[comp]
        ref_addr = c_uint16(addr.value - offset)
        return comp.read(ref_addr)

    def write(self, addr: c_uint16, value: c_uint8) -> None:
        comp: BusInterface = self._map[addr.value]
        if comp is None:
            return
        offset = self._comp_offsets[comp]
        ref_addr = c_uint16(addr.value - offset)
        comp.write(ref_addr, value)
