# ORB-SLAM3 Study Notes

这份笔记整理最近阅读 ORB-SLAM3 源码时反复问到的核心概念。目标不是替代书本推导，而是帮助把《视觉 SLAM 十四讲》里的概念和 ORB-SLAM3 代码变量对上。

## 1. 总体流程

ORB-SLAM3 每来一帧图像，主要从 `Tracking::Track()` 进入。

核心流程可以概括为：

```text
输入 RGB-D / Stereo / Mono 图像
-> 构造 Frame，提取 ORB 特征
-> 如果未初始化，创建初始 KeyFrame 和 MapPoint
-> 如果已初始化，匹配当前帧特征和已有 MapPoint
-> PoseOptimization 优化当前帧位姿
-> TrackLocalMap 搜索更多局部地图点并再次优化
-> NeedNewKeyFrame 判断是否插入关键帧
-> LocalMapping 创建新 MapPoint、做局部 BA
```

对应源码重点：

- `src/Tracking.cc`: 每帧跟踪主流程
- `src/Frame.cc`: 当前帧数据结构和特征提取
- `src/ORBextractor.cc`: ORB 特征提取
- `src/ORBmatcher.cc`: 特征匹配
- `src/Optimizer.cc`: 位姿优化和 BA
- `src/LocalMapping.cc`: 建图和新 MapPoint 创建

## 2. Frame 和 KeyFrame

`Frame` 是每一张进来的普通图像帧，主要用于实时跟踪。它通常生命周期较短。

`KeyFrame` 是从普通 `Frame` 中挑出来的重要帧，会长期进入地图，用于建图、局部 BA、回环、重定位。

常见关系：

```text
每张图像 -> Frame
部分重要 Frame -> KeyFrame
KeyFrame + MapPoint -> Map
```

常见变量：

- `mCurrentFrame`: 当前正在处理的帧
- `mLastFrame`: 上一帧
- `mpReferenceKF`: 当前参考关键帧
- `mpLastKeyFrame`: 上一个关键帧

## 3. KeyPoint、MapPoint 和描述子

`mvKeysUn[i]` 表示当前帧第 `i` 个去畸变后的 2D 特征点。

`mvpMapPoints[i]` 表示第 `i` 个 2D 特征点对应的 3D 地图点指针。

真正的 3D 世界坐标要通过：

```cpp
pMP->GetWorldPos()
```

所以一组 2D-3D 对应是：

```text
mvKeysUn[i] <-> mvpMapPoints[i]->GetWorldPos()
```

`MapPoint` 也有描述子，但它不是 3D 几何描述子，而是从多个关键帧观测到的 2D ORB 描述子里选出来的代表描述子。

`MapPoint::ComputeDistinctiveDescriptors()` 的原则：

```text
收集所有观测描述子
-> 计算两两 Hamming 距离
-> 对每个候选描述子计算到其他描述子的中位距离
-> 选择中位距离最小的描述子作为代表描述子
```

这样后续可以比较：

```text
当前帧 2D descriptor vs MapPoint representative descriptor
```

## 4. ORB 特征提取

ORB 的核心包括：

- FAST 角点检测
- 图像金字塔
- OctTree 均匀化分布
- 灰度质心法计算方向
- BRIEF 二进制描述子

`ORBextractor::operator()` 大致流程：

```text
ComputePyramid()
-> ComputeKeyPointsOctTree()
-> computeOrientation()
-> GaussianBlur()
-> computeDescriptors()
```

`computeOrientation()` 使用灰度质心法：

```text
在关键点周围 patch 中，把灰度当权重
-> 计算 m10, m01
-> theta = atan2(m01, m10)
-> 存入 KeyPoint::angle
```

`IC_Angle()` 里的 `m_10` 表示左右灰度偏心，`m_01` 表示上下灰度偏心。

`bit_pattern_31_` 是 ORB 描述子预定义的采样点对。每个 bit 来自一对像素强度比较。

## 5. 位姿、SO(3)、SE(3)、Lie Algebra

相机位姿通常表示为：

```text
Tcw = world -> camera
Twc = camera -> world
```

`SO(3)` 表示三维旋转，`SE(3)` 表示三维刚体位姿，也就是旋转和平移。

位姿不能直接普通加减，因为旋转矩阵有正交约束。优化时一般在李代数 `se(3)` 里求一个小扰动：

```text
delta_xi = [小平移, 小旋转]
```

然后通过指数映射更新位姿：

```text
T <- exp(delta_xi) * T
```

源码关键词：

- `Sophus::SE3<float>`
- `g2o::SE3Quat`
- `g2o::VertexSE3Expmap`
- `unit_quaternion()`
- `GetPose()`
- `SetPose()`

## 6. 非线性优化、GN 和 LM

SLAM 优化通常写成最小二乘：

```text
min sum ||e_i(x)||^2
```

视觉 SLAM 常见误差是重投影误差：

```text
e = u_obs - project(Tcw * Xw)
```

因为投影和旋转是非线性的，所以不能一步直接求解。优化器会反复做：

```text
当前估计
-> 计算误差 e
-> 计算雅可比 J
-> 解线性方程得到 delta_xi
-> 更新位姿
-> 重新计算误差
```

高斯牛顿解：

```text
J^T J * dx = -J^T e
```

Levenberg-Marquardt 在高斯牛顿上加阻尼：

```text
(J^T J + lambda I) * dx = -J^T e
```

LM 的作用是在快和稳之间调节：误差下降就更大胆，误差没下降就更保守。

## 7. PoseOptimization

`Optimizer::PoseOptimization(Frame *pFrame)` 只优化当前帧相机位姿，不优化 3D 点。

它的图优化结构是：

```text
Vertex:
  当前帧 Tcw

Edges:
  每个 2D keypoint - 3D MapPoint 对应形成一条重投影边
```

单目边：

```cpp
EdgeSE3ProjectXYZOnlyPose
```

含义：

```text
已知 Xw 和 2D 观测 obs，只优化 pose
```

双目/RGB-D 边：

```cpp
EdgeStereoSE3ProjectXYZOnlyPose
```

观测量是：

```text
obs = [uL, vL, uR]
```

其中 `uR` 是右目横坐标。RGB-D 会把深度转换成虚拟右目坐标。

优化后，`optimizer.optimize(...)` 会更新 g2o 内部的 `vSE3`，最后通过：

```cpp
pFrame->SetPose(pose);
```

写回 `Frame`。

## 8. Huber Kernel 和 Outlier

Huber kernel 是鲁棒损失函数。

普通平方误差对大误差非常敏感，错匹配会把位姿拉偏。Huber 的原则是：

```text
小误差：按平方误差处理
大误差：增长变慢，相当于降低权重
```

`PoseOptimization()` 外层做 4 轮优化，每轮 10 次迭代：

```text
优化 pose
-> 计算每条边 chi2
-> chi2 太大则标记 outlier
-> outlier 下一轮不参与优化
```

`e->setLevel(1)` 表示这条边下一轮不参与 `initializeOptimization(0)`。

## 9. RGB-D / Stereo 反投影

`Frame::UnprojectStereo()` 用 2D 点和深度恢复 3D 点。

标量形式等价于：

```text
Xc = z * K^-1 * [u, v, 1]^T
```

源码写成：

```cpp
x = (u - cx) * z * invfx;
y = (v - cy) * z * invfy;
z = mvDepth[i];
```

然后从相机坐标变到世界坐标：

```cpp
x3D = mRwc * x3Dc + mOw;
```

## 10. LocalMapping 和 CreateNewMapPoints

`LocalMapping::CreateNewMapPoints()` 负责在当前关键帧和邻居关键帧之间创建新的 3D 地图点。

主流程：

```text
找共视邻居 KeyFrame
-> 检查 baseline 是否足够
-> SearchForTriangulation 找匹配点
-> 反投影得到两条观测射线
-> 判断视差是否足够
-> 三角化或用 stereo/RGB-D 深度反投影
-> 检查点是否在两个相机前方
-> 检查重投影误差
-> 检查尺度一致性
-> 创建 MapPoint
-> AddObservation / AddMapPoint
-> ComputeDistinctiveDescriptors
-> UpdateNormalAndDepth
-> AddMapPoint 到 Atlas
```

## 11. 基线、场景深度和视差

`baseline` 是两个关键帧相机中心的距离。

基线太短时，两条射线几乎平行，三角化非常不稳定。

场景深度是关键帧看到的地图点离相机的大致距离，代码里常用中位深度：

```cpp
ComputeSceneMedianDepth()
```

单目情况下会检查：

```text
baseline / scene_depth
```

比例太小表示视差太小，不适合三角化。

## 12. unprojectEig、ray 和极线约束

`unprojectEig()` 把 2D 像素点变成相机坐标系下的 3D 射线方向。

Pinhole 模型：

```text
[(u-cx)/fx, (v-cy)/fy, 1]
```

`ray1`、`ray2` 是把两个相机里的射线方向变到世界坐标系后得到的观测射线。

`cosParallaxRays` 是两条射线夹角的 cos 值：

```text
cos 越小 -> 夹角越大 -> 视差越大 -> 三角化越稳定
```

极线约束表示：

```text
如果两个 2D 点来自同一个 3D 点，那么第二个点应该落在第一个点对应的极线附近
```

用于减少错误匹配。

## 13. mvKeys、mvKeysUn、NLeft、uR

`mvKeys` 是原始 keypoints。

`mvKeysUn` 是去畸变后的 keypoints。

普通 pinhole/RGB-D 流程常用 `mvKeysUn` 做几何计算。

`NLeft` 用于多相机/左右相机特征分开存的情况：

```text
NLeft == -1: 普通模式，不分左右 keypoint 数组
idx < NLeft: 左相机 keypoint
idx >= NLeft: 右相机 keypoint
```

`uR` 是右目横坐标。双目中：

```text
disparity = uL - uR
Z = bf / disparity
```

RGB-D 中也会用深度构造虚拟 `uR`，便于复用 stereo 逻辑。

## 14. UpdateNormalAndDepth

`MapPoint::UpdateNormalAndDepth()` 更新：

- `mNormalVector`: 平均观测方向
- `mfMinDistance`: 最小可靠可见距离
- `mfMaxDistance`: 最大可靠可见距离

用途：

```text
判断当前相机是否可能看到该 MapPoint
判断观察角度是否合理
判断距离是否合理
预测应该在哪个 ORB 金字塔层搜索
```

这些信息主要服务于后续投影匹配，不是直接作为优化误差项。

## 15. mvScaleFactors

`mvScaleFactors[level]` 是 ORB 金字塔每一层的尺度因子。

如果：

```text
scaleFactor = 1.2
```

那么：

```text
level 0: 1.0
level 1: 1.2
level 2: 1.44
```

在 `CreateNewMapPoints()` 里会检查：

```text
两个相机到 3D 点的距离比例
是否和两个 keypoint 的 octave 尺度比例一致
```

如果距离变化和尺度变化严重不一致，说明匹配或三角化结果可疑，会跳过。

## 16. 当前阶段最重要的理解

目前看源码要抓住三条链：

```text
ORB 特征链:
图像 -> KeyPoint -> Descriptor
```

```text
跟踪链:
当前帧 2D 特征 -> 匹配已有 MapPoint -> PoseOptimization -> 更新 Tcw
```

```text
建图链:
KeyFrame 间匹配 -> 三角化/反投影 -> 创建 MapPoint -> Local BA 优化
```

一句话总结：

```text
Tracking 负责快速估计当前相机位姿；
LocalMapping 负责创建和优化地图点；
Optimizer 用图优化把 pose 和 MapPoint 调到更一致。
```
