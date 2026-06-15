"""Run XFeat matching over adjacent image pairs in a TUM RGB-D sequence."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
XFEAT_ROOT = REPO_ROOT / "external" / "accelerated_features"
DEFAULT_SEQUENCE = REPO_ROOT / "data" / "rgbd_dataset_freiburg1_xyz"
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "learned" / "xfeat_tum_freiburg1_xyz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--rgb-file", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--top-k", type=int, default=4096)
    parser.add_argument("--min-cossim", type=float, default=0.82)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--num-pairs", type=int, default=50)
    parser.add_argument("--pair-stride", type=int, default=1)
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument("--save-vis-every", type=int, default=10)
    parser.add_argument("--max-draw", type=int, default=300)
    parser.add_argument("--use-gpu", action="store_true")
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


def image_to_tensor_bgr(image_bgr: np.ndarray) -> torch.Tensor:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(image_rgb).permute(2, 0, 1).float()[None] / 255.0


def draw_matches(
    image0: np.ndarray,
    image1: np.ndarray,
    keypoints0: np.ndarray,
    keypoints1: np.ndarray,
    matches: np.ndarray,
    max_draw: int,
) -> np.ndarray:
    matches_to_draw = matches[:max_draw]
    cv_kpts0 = [cv2.KeyPoint(float(x), float(y), 3) for x, y in keypoints0]
    cv_kpts1 = [cv2.KeyPoint(float(x), float(y), 3) for x, y in keypoints1]
    cv_matches = [
        cv2.DMatch(_queryIdx=int(i0), _trainIdx=int(i1), _distance=0.0)
        for i0, i1 in matches_to_draw
    ]
    return cv2.drawMatches(
        image0,
        cv_kpts0,
        image1,
        cv_kpts1,
        cv_matches,
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )


def main() -> None:
    args = parse_args()
    if not args.use_gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    sys.path.insert(0, str(XFEAT_ROOT))
    from modules.xfeat import XFeat  # pylint: disable=import-error,import-outside-toplevel

    frames = read_tum_rgb(args.sequence_dir, args.rgb_file)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    vis_dir = args.out_dir / "matches_vis"
    vis_dir.mkdir(parents=True, exist_ok=True)

    xfeat = XFeat(top_k=args.top_k)
    rows: list[dict[str, object]] = []

    pair_count = 0
    pair_idx = 0
    i = args.start
    while i + args.pair_stride < len(frames):
        if args.num_pairs > 0 and pair_count >= args.num_pairs:
            break

        timestamp0, image0_path = frames[i]
        timestamp1, image1_path = frames[i + args.pair_stride]

        image0 = load_image(image0_path)
        image1 = load_image(image1_path)
        tensor0 = image_to_tensor_bgr(image0).to(xfeat.dev)
        tensor1 = image_to_tensor_bgr(image1).to(xfeat.dev)

        with torch.inference_mode():
            feats0 = xfeat.detectAndCompute(tensor0, top_k=args.top_k)[0]
            feats1 = xfeat.detectAndCompute(tensor1, top_k=args.top_k)[0]
            idx0, idx1 = xfeat.match(
                feats0["descriptors"],
                feats1["descriptors"],
                min_cossim=args.min_cossim,
            )

        keypoints0 = feats0["keypoints"].cpu().numpy()
        keypoints1 = feats1["keypoints"].cpu().numpy()
        matches = torch.stack([idx0, idx1], dim=1).cpu().numpy()

        row = {
            "pair_index": pair_idx,
            "frame_index0": i,
            "frame_index1": i + args.pair_stride,
            "timestamp0": f"{timestamp0:.6f}",
            "timestamp1": f"{timestamp1:.6f}",
            "image0": str(image0_path),
            "image1": str(image1_path),
            "num_features0": len(keypoints0),
            "num_features1": len(keypoints1),
            "num_matches": len(matches),
            "min_cossim": args.min_cossim,
            "top_k": args.top_k,
        }
        rows.append(row)

        if args.save_vis_every > 0 and pair_count % args.save_vis_every == 0:
            vis = draw_matches(image0, image1, keypoints0, keypoints1, matches, args.max_draw)
            cv2.imwrite(str(vis_dir / f"pair_{pair_idx:04d}_matches.png"), vis)

        print(
            f"pair {pair_idx:04d}: "
            f"features=({len(keypoints0)}, {len(keypoints1)}) matches={len(matches)}"
        )

        pair_count += 1
        pair_idx += 1
        i += args.frame_step

    summary_path = args.out_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    matches_counts = np.array([int(row["num_matches"]) for row in rows], dtype=np.int32)
    if len(matches_counts):
        np.savez_compressed(
            args.out_dir / "summary_stats.npz",
            num_matches=matches_counts,
            mean_matches=float(matches_counts.mean()),
            median_matches=float(np.median(matches_counts)),
            min_matches=int(matches_counts.min()),
            max_matches=int(matches_counts.max()),
        )
        print(
            "summary: "
            f"pairs={len(rows)} "
            f"mean_matches={matches_counts.mean():.1f} "
            f"median_matches={np.median(matches_counts):.1f} "
            f"min={matches_counts.min()} "
            f"max={matches_counts.max()}"
        )
    else:
        print("summary: no pairs processed")

    print(f"saved: {args.out_dir}")


if __name__ == "__main__":
    main()
