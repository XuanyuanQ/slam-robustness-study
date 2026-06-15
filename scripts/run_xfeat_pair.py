"""Run XFeat on a pair of images and save features plus match visualization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
XFEAT_ROOT = REPO_ROOT / "external" / "accelerated_features"
DEFAULT_TUM_RGB = REPO_ROOT / "data" / "rgbd_dataset_freiburg1_xyz" / "rgb"
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "learned" / "xfeat_smoke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image0", type=Path, default=None, help="First image path.")
    parser.add_argument("--image1", type=Path, default=None, help="Second image path.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory.")
    parser.add_argument("--top-k", type=int, default=4096, help="Maximum number of XFeat keypoints.")
    parser.add_argument(
        "--min-cossim",
        type=float,
        default=0.82,
        help="Minimum cosine similarity for mutual nearest-neighbor matching.",
    )
    parser.add_argument(
        "--max-draw",
        type=int,
        default=300,
        help="Maximum number of matches to draw in the visualization.",
    )
    parser.add_argument("--use-gpu", action="store_true", help="Allow CUDA if available.")
    return parser.parse_args()


def default_pair() -> tuple[Path, Path]:
    images = sorted(DEFAULT_TUM_RGB.glob("*.png"))
    if len(images) < 2:
        raise FileNotFoundError(
            f"Need at least two PNG images in {DEFAULT_TUM_RGB}. "
            "Pass --image0 and --image1 explicitly if your dataset is elsewhere."
        )
    return images[0], images[1]


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def image_to_tensor_bgr(image_bgr: np.ndarray) -> torch.Tensor:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float()[None] / 255.0
    return tensor


def draw_matches(
    image0: np.ndarray,
    image1: np.ndarray,
    keypoints0: np.ndarray,
    keypoints1: np.ndarray,
    matches: np.ndarray,
    max_draw: int,
) -> np.ndarray:
    draw_matches = matches[:max_draw]
    cv_kpts0 = [cv2.KeyPoint(float(x), float(y), 3) for x, y in keypoints0]
    cv_kpts1 = [cv2.KeyPoint(float(x), float(y), 3) for x, y in keypoints1]
    cv_matches = [
        cv2.DMatch(_queryIdx=int(i0), _trainIdx=int(i1), _distance=0.0)
        for i0, i1 in draw_matches
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
        # XFeat selects CUDA automatically when available; this keeps the smoke test CPU-stable.
        import os

        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    sys.path.insert(0, str(XFEAT_ROOT))
    from modules.xfeat import XFeat  # pylint: disable=import-error,import-outside-toplevel

    image0_path, image1_path = (
        (args.image0, args.image1) if args.image0 and args.image1 else default_pair()
    )
    image0 = load_image(image0_path)
    image1 = load_image(image1_path)

    xfeat = XFeat(top_k=args.top_k)
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
    descriptors0 = feats0["descriptors"].cpu().numpy()
    descriptors1 = feats1["descriptors"].cpu().numpy()
    scores0 = feats0["scores"].cpu().numpy()
    scores1 = feats1["scores"].cpu().numpy()
    matches = torch.stack([idx0, idx1], dim=1).cpu().numpy()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out_dir / "features_0.npz",
        image=str(image0_path),
        keypoints=keypoints0,
        descriptors=descriptors0,
        scores=scores0,
    )
    np.savez_compressed(
        args.out_dir / "features_1.npz",
        image=str(image1_path),
        keypoints=keypoints1,
        descriptors=descriptors1,
        scores=scores1,
    )
    np.savez_compressed(
        args.out_dir / "matches.npz",
        image0=str(image0_path),
        image1=str(image1_path),
        matches=matches,
        matched_keypoints0=keypoints0[matches[:, 0]] if len(matches) else np.empty((0, 2)),
        matched_keypoints1=keypoints1[matches[:, 1]] if len(matches) else np.empty((0, 2)),
    )

    match_vis = draw_matches(image0, image1, keypoints0, keypoints1, matches, args.max_draw)
    cv2.imwrite(str(args.out_dir / "matches.png"), match_vis)

    print(f"image0: {image0_path}")
    print(f"image1: {image1_path}")
    print(f"features0: {len(keypoints0)}")
    print(f"features1: {len(keypoints1)}")
    print(f"matches: {len(matches)}")
    print(f"saved: {args.out_dir}")


if __name__ == "__main__":
    main()
