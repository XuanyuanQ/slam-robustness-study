from __future__ import annotations

import argparse

from _common import ensure_project_on_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the baseline vs learned comparison.")
    parser.add_argument("--dataset-root", default="data/TUM_RGBD")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--sequence", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_project_on_path()
    from run_experiment import main as run_main

    argv = [
        "--mode",
        "compare",
        "--dataset-root",
        str(args.dataset_root),
        "--output-dir",
        str(args.output_dir),
    ]
    if args.sequence:
        argv.extend(["--sequence", args.sequence])
    if args.dry_run:
        argv.append("--dry-run")
    return run_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
