from __future__ import annotations

import argparse


def cmd_hello(_: argparse.Namespace) -> int:
    print("baseline-engine: ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baseline",
        description="baseline-engine: baseline-first behavior modeling and deviation scoring",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    hello = sub.add_parser("hello", help="Sanity check command to confirm install + CLI wiring.")
    hello.set_defaults(func=cmd_hello)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
