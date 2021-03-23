from argparse import ArgumentParser, FileType
from .assembler import Assembler


def get_opts():
    ap = ArgumentParser()
    ap.add_argument("SRC", type=FileType('r'), help="Path to source code.")
    return ap.parse_args()


def main():
    opts = get_opts()
    a = Assembler(opts.SRC)
    a.assemble()


if __name__ == "__main__":
    main()
