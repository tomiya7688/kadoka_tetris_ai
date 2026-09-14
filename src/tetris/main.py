"""Application entry point for source and frozen builds."""

import argparse
from pathlib import Path
from typing import Sequence

from tetris.adapters.pygame_app import PygameApp
from tetris.runtime_paths import ensure_user_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="KadokaTetrisAI")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="initialize portable runtime directories and exit",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ensure_user_data(args.data_root)
    if args.smoke_test:
        return 0
    return PygameApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
