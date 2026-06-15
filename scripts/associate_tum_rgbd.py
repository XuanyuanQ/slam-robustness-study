#!/usr/bin/env python3
"""Create TUM RGB-D associations from rgb.txt and depth.txt."""

from __future__ import annotations

import argparse
from pathlib import Path


def read_file_list(path: Path) -> dict[float, str]:
    entries: dict[float, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        entries[float(parts[0])] = parts[1]
    return entries


def associate(
    first: dict[float, str],
    second: dict[float, str],
    offset: float = 0.0,
    max_difference: float = 0.02,
) -> list[tuple[float, float]]:
    potential_matches = [
        (abs(a - (b + offset)), a, b)
        for a in first
        for b in second
        if abs(a - (b + offset)) < max_difference
    ]
    potential_matches.sort()

    matches: list[tuple[float, float]] = []
    first_keys = set(first.keys())
    second_keys = set(second.keys())
    for _, a, b in potential_matches:
        if a in first_keys and b in second_keys:
            first_keys.remove(a)
            second_keys.remove(b)
            matches.append((a, b))

    matches.sort()
    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rgb_txt", type=Path)
    parser.add_argument("depth_txt", type=Path)
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--max-difference", type=float, default=0.02)
    args = parser.parse_args()

    rgb = read_file_list(args.rgb_txt)
    depth = read_file_list(args.depth_txt)
    matches = associate(rgb, depth, args.offset, args.max_difference)

    for rgb_time, depth_time in matches:
        print(f"{rgb_time:.6f} {rgb[rgb_time]} {depth_time:.6f} {depth[depth_time]}")


if __name__ == "__main__":
    main()
