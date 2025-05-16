import numpy as np
from sklearn.cluster import DBSCAN
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta

class TripClustering:
    def __init__(self, eps=0.5, min_samples=2, time_window=30):
        """
        初始化聚类器
        :param eps: 空间距离阈值（公里）
        :param min_samples: 最小样本数
        :param time_window: 时间窗口（分钟）
        """
        self.eps = eps
        self.min_samples = min_samples
        self.time_window = time_window
        self.clusterer = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric='euclidean'
        )

    def _prepare_features(self, trips: List[Dict[str, Any]]) -> np.ndarray:
        """
        准备聚类特征
        :param trips: 出行需求列表
        :return: 特征矩阵
        """
        features = []
        for trip in trips:
            # 提取起点和终点坐标
            origin = trip['origin']
            destination = trip['destination']
            # 提取时间特征（转换为分钟数）
            departure_time = pd.to_datetime(trip['departure_time'])
            time_feature = departure_time.hour * 60 + departure_time.minute
            
            features.append([
                origin['lat'],
                origin['lng'],
                destination['lat'],
                destination['lng'],
                time_feature
            ])
        return np.array(features)

    def cluster_trips(self, trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对出行需求进行聚类
        :param trips: 出行需求列表
        :return: 带有聚类标签的出行需求列表
        """
        if not trips:
            return []

        # 准备特征
        features = self._prepare_features(trips)
        
        # 执行聚类
        labels = self.clusterer.fit_predict(features)
        
        # 将聚类结果添加到原始数据中
        clustered_trips = []
        for trip, label in zip(trips, labels):
            trip_copy = trip.copy()
            trip_copy['cluster_id'] = int(label)
            clustered_trips.append(trip_copy)
        
        return clustered_trips

    def get_cluster_statistics(self, clustered_trips: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        获取每个聚类的统计信息
        :param clustered_trips: 聚类后的出行需求列表
        :return: 聚类统计信息
        """
        cluster_stats = {}
        
        for trip in clustered_trips:
            cluster_id = trip['cluster_id']
            if cluster_id not in cluster_stats:
                cluster_stats[cluster_id] = {
                    'size': 0,
                    'origins': [],
                    'destinations': [],
                    'departure_times': []
                }
            
            stats = cluster_stats[cluster_id]
            stats['size'] += 1
            stats['origins'].append(trip['origin'])
            stats['destinations'].append(trip['destination'])
            stats['departure_times'].append(trip['departure_time'])
        
        # 计算每个聚类的中心点和时间范围
        for cluster_id, stats in cluster_stats.items():
            if cluster_id != -1:  # 排除噪声点
                # 计算中心点
                origins = np.array([(o['lat'], o['lng']) for o in stats['origins']])
                destinations = np.array([(d['lat'], d['lng']) for d in stats['destinations']])
                
                stats['center_origin'] = {
                    'lat': float(np.mean(origins[:, 0])),
                    'lng': float(np.mean(origins[:, 1]))
                }
                stats['center_destination'] = {
                    'lat': float(np.mean(destinations[:, 0])),
                    'lng': float(np.mean(destinations[:, 1]))
                }
                
                # 计算时间范围
                times = pd.to_datetime(stats['departure_times'])
                stats['time_range'] = {
                    'start': times.min().isoformat(),
                    'end': times.max().isoformat()
                }
        
        return cluster_stats 