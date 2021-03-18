from argparse import ArgumentParser, FileType


def get_opts():
    ap = ArgumentParser()
    ap.add_argument("PROG", type=FileType, help="Path to program.")
    return ap.parse_args()


def main():
    opts = get_opts()
    ...
