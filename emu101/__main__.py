from .bus import Bus
from .ram import RAM
from .rom import ROM

bios = ROM(0x100)
memory = RAM(0x100)
bus = Bus({
    (0xFF00, 0x100): bios,
    (0x0000, 0x100): memory,
})
from pprint import pprint as pp
pp(bus._map)
