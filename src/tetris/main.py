"""Application entry point for source and frozen builds."""

import argparse
from pathlib import Path
from typing import Sequence

from tetris.adapters.pygame_app import PygameApp
from tetris.input_config import load_keyboard_bindings
from tetris.runtime_paths import ensure_user_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="KadokaTetrisAI")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="initialize portable runtime directories and config, then exit",
    )
    parser.add_argument(
        "--player",
        type=int,
        choices=(0, 1),
        default=0,
        help="keyboard binding profile to use (0 or 1)",
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
    user_data = ensure_user_data(args.data_root)
    bindings = load_keyboard_bindings(user_data / "Config")
    if args.smoke_test:
        return 0
    return PygameApp(bindings=bindings, player=args.player).run()


if __name__ == "__main__":
    raise SystemExit(main())
