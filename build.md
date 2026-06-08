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
cd /mnt/d/Code/slam/external/ORB_SLAM3/Examples/RGB-D$ 
./rgbd_tum ../../Vocabulary/ORBvoc.txt TUM1.yaml /mnt/d/Code/slam/data/rgbd_dataset_freiburg1_xyz associations/fr1_xyz.txt