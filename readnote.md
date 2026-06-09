1.入口
TrackRGBD-GrabImageRGBD-Frame-ExtractORB-
monoLeft = (*mpORBextractorLeft)(im,cv::Mat(),mvKeys,mDescriptors,vLapping);
--ORBextractor::operator() 特征提取
-构建金字塔-ComputePyramid
-每层找角点-ComputeKeyPointsOctTree-FAST
-控制特征分布均匀-ComputeKeyPointsOctTree-DistributeOctTree
-给每个点算方向-ComputeKeyPointsOctTree-computeOrientation
-输出关键点和描述子-computeDescriptors
