from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import ExperimentConfig, run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the SLAM front-end robustness experiment."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data") / "TUM_RGBD",
        help="Path to the local dataset root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory where figures and outputs will be written.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "learned", "compare"],
        default="baseline",
        help="Experiment mode to run.",
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
        help="Print the resolved configuration without running the experiment.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = ExperimentConfig(
        dataset_root=args.dataset_root,
        output_dir=args.output_dir,
        mode=args.mode,
        sequence=args.sequence or None,
        dry_run=args.dry_run,
    )
    run_experiment(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

