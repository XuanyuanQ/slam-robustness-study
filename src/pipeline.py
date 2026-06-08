from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .datasets import TUMRGBDSequence, load_tum_sequence


@dataclass
class ExperimentConfig:
    dataset_root: Path
    output_dir: Path
    mode: str
    sequence: str | None = None
    dry_run: bool = False
    dataset: TUMRGBDSequence | None = None


def run_experiment(config: ExperimentConfig) -> None:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.output_dir / "logs").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "figures").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "tables").mkdir(parents=True, exist_ok=True)

    print("=== SLAM Experiment Config ===")
    print(f"dataset_root: {config.dataset_root}")
    print(f"output_dir:   {config.output_dir}")
    print(f"mode:         {config.mode}")
    print(f"sequence:     {config.sequence}")
    print(f"dry_run:      {config.dry_run}")

    if config.dry_run:
        print("Dry run only. No experiment executed.")
        return

    dataset = config.dataset or load_tum_sequence(config.dataset_root, config.sequence)
    print(f"resolved_seq: {dataset.name}")
    print(f"num_frames:   {len(dataset.frames)}")

    if config.mode == "baseline":
        _run_baseline(dataset, config.output_dir)
    elif config.mode == "learned":
        _run_learned(dataset, config.output_dir)
    elif config.mode == "compare":
        _run_compare(dataset, config.output_dir)
    else:
        raise ValueError(f"Unsupported mode: {config.mode}")


def _run_baseline(dataset: TUMRGBDSequence, output_dir: Path) -> None:
    print("[baseline] ORB + frame-to-frame matching + pose estimation")
    print(f"[baseline] sequence: {dataset.name}")
    print(f"[baseline] output:   {output_dir}")
    # TODO: implement ORB feature extraction, matching, and pose estimation.


def _run_learned(dataset: TUMRGBDSequence, output_dir: Path) -> None:
    print("[learned] learned-feature pipeline")
    print(f"[learned] sequence: {dataset.name}")
    print(f"[learned] output:   {output_dir}")
    # TODO: implement learned feature extraction and matching.


def _run_compare(dataset: TUMRGBDSequence, output_dir: Path) -> None:
    print("[compare] running baseline vs learned-feature comparison")
    print(f"[compare] sequence: {dataset.name}")
    print(f"[compare] output:   {output_dir}")
    # TODO: run both pipelines and generate comparison figures/tables.
