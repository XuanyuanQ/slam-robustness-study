from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class TUMRGBDFrame:
    timestamp: float
    rgb_path: Path
    depth_path: Path | None = None


@dataclass(frozen=True)
class TUMRGBDSequence:
    name: str
    root: Path
    frames: list[TUMRGBDFrame]


def discover_tum_sequences(dataset_root: Path) -> list[Path]:
    if not dataset_root.exists():
        return []

    candidates: list[Path] = []
    for child in sorted(dataset_root.iterdir()):
        if child.is_dir() and (child / "rgb.txt").exists():
            candidates.append(child)

    if (dataset_root / "rgb.txt").exists():
        candidates.insert(0, dataset_root)

    return candidates


def load_tum_sequence(dataset_root: Path, sequence: str | None = None) -> TUMRGBDSequence:
    sequence_root = _resolve_sequence_root(dataset_root, sequence)
    rgb_entries = _read_association_file(sequence_root / "rgb.txt")
    depth_entries = _read_association_file(sequence_root / "depth.txt")

    depth_lookup = {timestamp: path for timestamp, path in depth_entries}
    frames: list[TUMRGBDFrame] = []
    for timestamp, rgb_path in rgb_entries:
        frames.append(
            TUMRGBDFrame(
                timestamp=timestamp,
                rgb_path=rgb_path,
                depth_path=depth_lookup.get(timestamp),
            )
        )

    return TUMRGBDSequence(
        name=sequence_root.name,
        root=sequence_root,
        frames=frames,
    )


def _resolve_sequence_root(dataset_root: Path, sequence: str | None) -> Path:
    if sequence:
        candidate = dataset_root / sequence
        if candidate.exists():
            return candidate
        if dataset_root.exists() and dataset_root.name == sequence and (
            dataset_root / "rgb.txt"
        ).exists():
            return dataset_root
        raise FileNotFoundError(
            f"Could not find TUM RGB-D sequence '{sequence}' under {dataset_root}"
        )

    if (dataset_root / "rgb.txt").exists():
        return dataset_root

    discovered = discover_tum_sequences(dataset_root)
    if not discovered:
        raise FileNotFoundError(
            f"No TUM RGB-D sequence found under {dataset_root}. "
            "Expected a folder containing rgb.txt."
        )

    return discovered[0]


def _read_association_file(path: Path) -> list[tuple[float, Path]]:
    if not path.exists():
        return []

    entries: list[tuple[float, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        timestamp = float(parts[0])
        rel_path = Path(parts[1])
        entries.append((timestamp, _resolve_data_path(path.parent, rel_path)))
    return entries


def _resolve_data_path(base_dir: Path, rel_path: Path) -> Path:
    if rel_path.is_absolute():
        return rel_path
    return (base_dir / rel_path).resolve()

