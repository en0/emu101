from argparse import ArgumentParser, FileType


def get_opts():
    ap = ArgumentParser()
    ap.add_argument("SRC", type=FileType('r'), help="Path to source code.")
    return ap.parse_args()


def main():
    opts = get_opts()
    print(opts)


if __name__ == "__main__":
    main()
