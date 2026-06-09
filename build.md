python .\scripts\run_experiment.py --dry-run



sudo apt update
sudo apt install -y libboost-all-dev libboost-serialization-dev

整编
cd /mnt/d/Code/slam/external/ORB_SLAM3
rm -rf build
rm -rf Thirdparty/DBoW2/build
rm -rf Thirdparty/g2o/build
rm -rf Thirdparty/Sophus/build
export CC=/usr/bin/gcc-12
export CXX=/usr/bin/g++-12
export Pangolin_DIR=/home/xuanyuan/opt/pangolin-v0.6/lib/cmake/Pangolin

./build.sh
只编译example
cd /mnt/d/Code/slam/external/ORB_SLAM3/build
make -j4 rgbd_tum

运行 example
cd /mnt/d/Code/slam/external/ORB_SLAM3/Examples/RGB-D
./rgbd_tum ../../Vocabulary/ORBvoc.txt TUM1.yaml /mnt/d/Code/slam/data/rgbd_dataset_freiburg1_xyz associations/fr1_xyz.txt

评估命令 
如果可视化失败：
pip install evo评估工具
python3 - <<'PY'
import json
from pathlib import Path

p = Path.home() / ".evo" / "settings.json"
data = json.loads(p.read_text())
data["plot_backend"] = "Agg"
p.write_text(json.dumps(data, indent=2))
print("updated:", p)
PY

ATE
evo_ape tum /mnt/d/Code/slam/data/rgbd_dataset_freiburg1_xyz/groundtruth.txt /mnt/d/Code/slam/results/baseline/CameraTrajectory.txt -a --save_plot /mnt/d/Code/slam/results/baseline/eval/ate.png --save_results /mnt/d/Code/slam/results/baseline/eval/ate.zip

RPE 
evo_rpe tum /mnt/d/Code/slam/data/rgbd_dataset_freiburg1_xyz/groundtruth.txt /mnt/d/Code/slam/results/baseline/CameraTrajectory.txt -a --save_plot /mnt/d/Code/slam/results/baseline/eval/rpe.png --save_results /mnt/d/Code/slam/results/baseline/eval/rpe.zip

 轨迹图
evo_traj tum /mnt/d/Code/slam/data/rgbd_dataset_freiburg1_xyz/groundtruth.txt /mnt/d/Code/slam/results/baseline/CameraTrajectory.txt -a --plot_mode xy --save_plot /mnt/d/Code/slam/results/baseline/eval/traj_xy.png