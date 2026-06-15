#!/usr/bin/env bash
set -euo pipefail

SLAM_ROOT="${SLAM_ROOT:-/mnt/d/Code/slam}"
ORB_ROOT="${ORB_SLAM3_ROOT:-$SLAM_ROOT/external/ORB_SLAM3}"
DATASET="${1:-$SLAM_ROOT/data/rgbd_dataset_freiburg1_xyz}"
OUT_DIR="${2:-$SLAM_ROOT/results/baseline_orb_local/freiburg1_xyz}"
ASSOCIATIONS="${3:-Examples/RGB-D/associations/fr1_xyz.txt}"
CONFIG="${4:-Examples/RGB-D/TUM1_orb_local.yaml}"

mkdir -p "$OUT_DIR"

cd "$ORB_ROOT"

set +e
./Examples/RGB-D/rgbd_tum \
  Vocabulary/ORBvoc.txt \
  "$CONFIG" \
  "$DATASET" \
  "$ASSOCIATIONS" \
  2>&1 | tee "$OUT_DIR/log.txt"
run_status=${PIPESTATUS[0]}
set -e

if [[ ! -f CameraTrajectory.txt || ! -f KeyFrameTrajectory.txt ]]; then
  echo "ORB-SLAM3 exited with status $run_status and did not produce trajectory files." >&2
  exit "$run_status"
fi

mv -f CameraTrajectory.txt "$OUT_DIR/CameraTrajectory.txt"
mv -f KeyFrameTrajectory.txt "$OUT_DIR/KeyFrameTrajectory.txt"

cat > "$OUT_DIR/run_cmd.txt" <<EOF
source $SLAM_ROOT/scripts/slam_env.sh
$SLAM_ROOT/scripts/run_orb_local_tum.sh "$DATASET" "$OUT_DIR" "$ASSOCIATIONS" "$CONFIG"
EOF

echo "Saved ORB-local baseline outputs to $OUT_DIR"
if [[ "$run_status" -ne 0 ]]; then
  echo "Note: ORB-SLAM3 exited with status $run_status after producing trajectories."
fi
