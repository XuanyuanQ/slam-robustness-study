"""Evaluate OpenCV ORB matching under simple image degradations on a TUM RGB-D sequence."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE = REPO_ROOT / "data" / "rgbd_dataset_freiburg1_xyz"
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "baseline" / "orb_degradation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--rgb-file", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--nfeatures", type=int, default=4096)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--num-pairs", type=int, default=50)
    parser.add_argument("--pair-stride", type=int, default=1)
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument("--save-vis-every", type=int, default=10)
    parser.add_argument("--max-draw", type=int, default=300)
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["clean", "blur", "low_light", "noise"],
        choices=["clean", "blur", "low_light", "noise"],
    )
    parser.add_argument("--blur-ksize", type=int, default=9)
    parser.add_argument("--low-light-alpha", type=float, default=0.35)
    parser.add_argument("--noise-sigma", type=float, default=18.0)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def read_tum_rgb(sequence_dir: Path, rgb_file: Path | None) -> list[tuple[float, Path]]:
    rgb_path = rgb_file or sequence_dir / "rgb.txt"
    if not rgb_path.exists():
        raise FileNotFoundError(f"Missing TUM rgb file: {rgb_path}")

    frames: list[tuple[float, Path]] = []
    with rgb_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            timestamp, rel_path = line.split()[:2]
            frames.append((float(timestamp), sequence_dir / rel_path))
    if len(frames) < 2:
        raise ValueError(f"Need at least two RGB frames in {rgb_path}")
    return frames


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def degrade_image(image: np.ndarray, condition: str, args: argparse.Namespace, rng: np.random.Generator) -> np.ndarray:
    if condition == "clean":
        return image.copy()
    if condition == "blur":
        ksize = args.blur_ksize if args.blur_ksize % 2 == 1 else args.blur_ksize + 1
        return cv2.GaussianBlur(image, (ksize, ksize), 0)
    if condition == "low_light":
        dark = image.astype(np.float32) * args.low_light_alpha
        return np.clip(dark, 0, 255).astype(np.uint8)
    if condition == "noise":
        noise = rng.normal(0.0, args.noise_sigma, image.shape).astype(np.float32)
        noisy = image.astype(np.float32) + noise
        return np.clip(noisy, 0, 255).astype(np.uint8)
    raise ValueError(f"Unknown condition: {condition}")


def detect_and_match(
    orb: cv2.ORB,
    matcher: cv2.BFMatcher,
    image0: np.ndarray,
    image1: np.ndarray,
) -> tuple[list[cv2.KeyPoint], list[cv2.KeyPoint], list[cv2.DMatch]]:
    gray0 = cv2.cvtColor(image0, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    keypoints0, descriptors0 = orb.detectAndCompute(gray0, None)
    keypoints1, descriptors1 = orb.detectAndCompute(gray1, None)

    if descriptors0 is None or descriptors1 is None:
        return keypoints0 or [], keypoints1 or [], []

    matches = matcher.match(descriptors0, descriptors1)
    matches = sorted(matches, key=lambda match: match.distance)
    return keypoints0, keypoints1, matches


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not rows:
            return
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    frames = read_tum_rgb(args.sequence_dir, args.rgb_file)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orb = cv2.ORB_create(nfeatures=args.nfeatures)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    rng = np.random.default_rng(args.seed)
    all_rows: list[dict[str, object]] = []

    for condition in args.conditions:
        condition_dir = args.out_dir / condition
        vis_dir = condition_dir / "matches_vis"
        vis_dir.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, object]] = []

        pair_count = 0
        pair_idx = 0
        frame_idx = args.start
        while frame_idx + args.pair_stride < len(frames):
            if args.num_pairs > 0 and pair_count >= args.num_pairs:
                break

            timestamp0, image0_path = frames[frame_idx]
            timestamp1, image1_path = frames[frame_idx + args.pair_stride]

            image0_raw = load_image(image0_path)
            image1_raw = load_image(image1_path)
            image0 = degrade_image(image0_raw, condition, args, rng)
            image1 = degrade_image(image1_raw, condition, args, rng)

            keypoints0, keypoints1, matches = detect_and_match(orb, matcher, image0, image1)
            distances = np.array([match.distance for match in matches], dtype=np.float32)

            row = {
                "method": "ORB",
                "condition": condition,
                "pair_index": pair_idx,
                "frame_index0": frame_idx,
                "frame_index1": frame_idx + args.pair_stride,
                "timestamp0": f"{timestamp0:.6f}",
                "timestamp1": f"{timestamp1:.6f}",
                "image0": str(image0_path),
                "image1": str(image1_path),
                "num_features0": len(keypoints0),
                "num_features1": len(keypoints1),
                "num_matches": len(matches),
                "mean_match_distance": f"{distances.mean():.3f}" if len(distances) else "",
                "median_match_distance": f"{np.median(distances):.3f}" if len(distances) else "",
                "nfeatures": args.nfeatures,
            }
            rows.append(row)
            all_rows.append(row)

            if args.save_vis_every > 0 and pair_count % args.save_vis_every == 0:
                vis = cv2.drawMatches(
                    image0,
                    keypoints0,
                    image1,
                    keypoints1,
                    matches[: args.max_draw],
                    None,
                    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
                )
                cv2.imwrite(str(vis_dir / f"pair_{pair_idx:04d}_matches.png"), vis)

            print(
                f"{condition} pair {pair_idx:04d}: "
                f"features=({len(keypoints0)}, {len(keypoints1)}) matches={len(matches)}"
            )

            pair_count += 1
            pair_idx += 1
            frame_idx += args.frame_step

        write_csv(condition_dir / "summary.csv", rows)

        counts = np.array([int(row["num_matches"]) for row in rows], dtype=np.int32)
        if len(counts):
            np.savez_compressed(
                condition_dir / "summary_stats.npz",
                num_matches=counts,
                mean_matches=float(counts.mean()),
                median_matches=float(np.median(counts)),
                min_matches=int(counts.min()),
                max_matches=int(counts.max()),
            )
            print(
                f"{condition} summary: pairs={len(rows)} "
                f"mean={counts.mean():.1f} median={np.median(counts):.1f} "
                f"min={counts.min()} max={counts.max()}"
            )

    write_csv(args.out_dir / "summary_all.csv", all_rows)

    aggregate_rows: list[dict[str, object]] = []
    for condition in args.conditions:
        counts = np.array(
            [int(row["num_matches"]) for row in all_rows if row["condition"] == condition],
            dtype=np.int32,
        )
        if len(counts):
            aggregate_rows.append(
                {
                    "method": "ORB",
                    "condition": condition,
                    "pairs": len(counts),
                    "mean_matches": f"{counts.mean():.3f}",
                    "median_matches": f"{np.median(counts):.3f}",
                    "min_matches": int(counts.min()),
                    "max_matches": int(counts.max()),
                }
            )
    write_csv(args.out_dir / "aggregate.csv", aggregate_rows)
    print(f"saved: {args.out_dir}")


if __name__ == "__main__":
    main()
