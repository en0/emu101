from argparse import ArgumentParser, FileType
from .emu import EMU


def get_opts():
    ap = ArgumentParser()
    ap.add_argument("PROG", type=FileType('rb'), help="Path to program.")
    return ap.parse_args()


def main():
    opts = get_opts()
    emu = EMU()
    emu.rom.load(opts.PROG)
    emu.run()


if __name__ == "__main__":
    main()
