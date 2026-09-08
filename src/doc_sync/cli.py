"""Command-line interface for doc-sync."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .application import run
from .config import build_configuration
from .diagnostics import write_diagnostics
from .exit_codes import OPERATIONAL_ERROR, USAGE_ERROR


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc-sync", description="Synchronize generated Python API documentation.")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("check", "sync"):
        command = subparsers.add_parser(mode, help=f"{mode} generated API documentation")
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--docs", type=Path, default=Path("API_DOCS.md"))
        command.add_argument("--exclude", action="append", default=[])
        command.add_argument("--verbose", action="store_true")
        command.add_argument("--max-file-bytes", type=int, default=5_000_000, help=argparse.SUPPRESS)
        command.add_argument("--max-files", type=int, default=100_000, help=argparse.SUPPRESS)
        command.add_argument("--max-depth", type=int, default=100, help=argparse.SUPPRESS)
        command.add_argument("--max-output-bytes", type=int, default=10_000_000, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        config = build_configuration(
            args.root,
            args.docs,
            tuple(args.exclude),
            verbose=args.verbose,
            max_file_bytes=args.max_file_bytes,
            max_files=args.max_files,
            max_depth=args.max_depth,
            max_output_bytes=args.max_output_bytes,
        )
        result = run(config, args.mode)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return USAGE_ERROR
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return OPERATIONAL_ERROR

    print(result.message, file=sys.stdout)
    write_diagnostics(result.diagnostics)
    return result.exit_code
