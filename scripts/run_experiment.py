from __future__ import annotations

import argparse
from pathlib import Path

from _common import ensure_project_on_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch a SLAM experiment from the scripts directory."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data") / "TUM_RGBD",
        help="Path to the dataset root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Where to write experiment outputs.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "learned", "compare"],
        default="baseline",
        help="Which experiment mode to run.",
    )
    parser.add_argument(
        "--sequence",
        type=str,
        default="",
        help="Optional sequence name or id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved command and configuration.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ensure_project_on_path()

    from src.main import main as project_main

    import sys

    argv = [
        "--dataset-root",
        str(args.dataset_root),
        "--output-dir",
        str(args.output_dir),
        "--mode",
        args.mode,
    ]
    if args.sequence:
        argv.extend(["--sequence", args.sequence])
    if args.dry_run:
        argv.append("--dry-run")

    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *argv]
        return project_main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())
