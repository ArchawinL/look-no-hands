"""Command line entry point: ``python -m look_no_hands <command>``."""

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="look_no_hands", description=__doc__)
    parser.add_subparsers(dest="command", required=True)
    parser.parse_args(argv)
    return 0
