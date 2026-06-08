#!/usr/bin/env bash

# Source this file in a new shell to restore the known-good ORB-SLAM3 build setup.
# Example:
#   source /mnt/d/Code/slam/scripts/slam_env.sh

export SLAM_ROOT="/mnt/d/Code/slam"
export ORB_SLAM3_ROOT="$SLAM_ROOT/external/ORB_SLAM3"
export PANGOLIN_ROOT="$HOME/opt/pangolin-v0.6"
export PANGOLIN_DIR="$PANGOLIN_ROOT/lib/cmake/Pangolin"
export CC="/usr/bin/gcc-12"
export CXX="/usr/bin/g++-12"

alias cslam='cd "$SLAM_ROOT"'
alias corb='cd "$ORB_SLAM3_ROOT"'

echo "[slam_env] SLAM_ROOT=$SLAM_ROOT"
echo "[slam_env] ORB_SLAM3_ROOT=$ORB_SLAM3_ROOT"
echo "[slam_env] PANGOLIN_DIR=$PANGOLIN_DIR"
echo "[slam_env] CC=$CC"
echo "[slam_env] CXX=$CXX"
