1.特征提取
TrackRGBD-GrabImageRGBD-Frame-ExtractORB-
monoLeft = (*mpORBextractorLeft)(im,cv::Mat(),mvKeys,mDescriptors,vLapping);
--ORBextractor::operator() 特征提取
-构建金字塔-ComputePyramid
-每层找角点-ComputeKeyPointsOctTree-FAST
-控制特征分布均匀-ComputeKeyPointsOctTree-DistributeOctTree
-给每个点算方向-ComputeKeyPointsOctTree-computeOrientation
-输出关键点和描述子-computeDescriptors
2.特征匹配
TrackRGBD-GrabImageRGBD-
Track()-MonocularInitialization-SearchForInitialization--初始化匹配
        -TrackWithMotionModel-SearchByProjection
先猜第二帧里大概在哪
去那个小窗口里找候选点
用 ORB 描述子比谁最像
保留最稳的一对一匹配
给后续两视图重建提供点对应
3.位姿
TrackRGBD-GrabImageRGBD-
Track()-TrackWithMotionModel-PoseOptimization（只优化相机）
4.重建3D
CreateNewMapPoints
5.优化3D点和相机
LocalBundleAdjustment

一个 vertex 被加入 optimizer 后，如果它不是 fixed，并且有 edge 连接它，它就会参与优化。
比如：
g2o::VertexSBAPointXYZ* vPoint = new g2o::VertexSBAPointXYZ();
vPoint->setEstimate(pMP->GetWorldPos().cast<double>());
vPoint->setId(id);
vPoint->setMarginalized(true);
optimizer.addVertex(vPoint);
这里没有：
vPoint->setFixed(true);
所以它默认是可优化的。
但前提是它要被 edge 约束。
后面有：
e->setVertex(0, optimizer.vertex(id));
这条边连接了这个 MapPoint vertex。
于是优化器会根据重投影误差调整它的位置

