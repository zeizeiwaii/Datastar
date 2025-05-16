import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime, timedelta
import math
from geopy.distance import geodesic
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedClustering:
    def __init__(self, 
                 spatial_threshold=1.0,    # 空间距离阈值（公里）
                 time_window=30,          # 时间窗口（分钟）
                 min_samples=2,           # 最小样本数
                 max_cluster_radius=5.0,  # 最大聚类半径（公里）
                 max_points_per_route=8   # 每条路线最大点数
                ):
        """
        增强版聚类算法
        
        参数:
            spatial_threshold: 空间距离阈值（公里）
            time_window: 时间窗口（分钟）
            min_samples: 最小样本数
            max_cluster_radius: 最大聚类半径（公里）
            max_points_per_route: 每条路线最大点数
        """
        self.spatial_threshold = spatial_threshold
        self.time_window = time_window
        self.min_samples = min_samples
        self.max_cluster_radius = max_cluster_radius
        self.max_points_per_route = max_points_per_route
        
        # 初始化DBSCAN聚类器
        # 空间阈值转换为度 (1公里约等于0.009度)
        # 空间聚类参数
        self.spatial_eps = spatial_threshold * 0.009
        self.spatial_clusterer = DBSCAN(
            eps=self.spatial_eps,
            min_samples=min_samples,
            metric='haversine'
        )
        
        logger.info(f"初始化增强版聚类算法: 空间阈值={spatial_threshold}公里, 时间窗口={time_window}分钟")

    def _filter_expired_requests(self, trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤掉过期的请求
        
        参数:
            trips: 出行请求列表
            
        返回:
            过滤后的请求列表
        """
        # 找到最早的出发时间作为基准时间
        earliest_time = None
        for trip in trips:
            try:
                departure_time = datetime.fromisoformat(trip['departure_time'].replace('Z', '+00:00'))
                if earliest_time is None or departure_time < earliest_time:
                    earliest_time = departure_time
            except Exception as e:
                logger.error(f"处理请求时间时出错: {str(e)}, 请求ID: {trip.get('request_id', 'unknown')}")
                continue
        
        if earliest_time is None:
            logger.error("无法确定基准时间")
            return []
            
        logger.info(f"使用最早出发时间作为基准: {earliest_time}")
        
        valid_trips = []
        expired_trips = []
        
        for trip in trips:
            try:
                departure_time = datetime.fromisoformat(trip['departure_time'].replace('Z', '+00:00'))
                # 如果出发时间与基准时间相差超过24小时，则视为过期
                time_diff = abs((departure_time - earliest_time).total_seconds() / 3600)
                if time_diff > 24:
                    expired_trips.append(trip)
                    logger.info(f"请求 {trip.get('request_id', 'unknown')} 已过期，出发时间: {departure_time}，与基准时间相差 {time_diff:.1f} 小时")
                else:
                    valid_trips.append(trip)
                    logger.info(f"请求 {trip.get('request_id', 'unknown')} 有效，出发时间: {departure_time}，与基准时间相差 {time_diff:.1f} 小时")
            except Exception as e:
                logger.error(f"处理请求时间时出错: {str(e)}, 请求ID: {trip.get('request_id', 'unknown')}")
                # 如果时间解析出错，暂时保留该请求
                valid_trips.append(trip)
        
        logger.info(f"过滤过期请求: 总请求数={len(trips)}, 有效请求={len(valid_trips)}, 过期请求={len(expired_trips)}")
        
        # 按时间排序
        valid_trips.sort(key=lambda x: x['departure_time'])
        
        # 显示有效请求的时间分布
        if valid_trips:
            logger.info("\n有效请求时间分布:")
            for trip in valid_trips:
                departure_time = datetime.fromisoformat(trip['departure_time'].replace('Z', '+00:00'))
                time_diff = (departure_time - earliest_time).total_seconds() / 3600
                logger.info(f"请求 {trip.get('request_id', 'unknown')}: {departure_time}, 与基准时间相差 {time_diff:.1f} 小时")
        
        return valid_trips

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        计算两点间的Haversine距离（公里）
        """
        # 将经纬度转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # 地球半径（公里）
        return c * r

    def _time_difference_minutes(self, time1_str, time2_str):
        """
        计算两个ISO格式时间字符串之间的分钟差
        """
        time1 = datetime.fromisoformat(time1_str.replace('Z', '+00:00'))
        time2 = datetime.fromisoformat(time2_str.replace('Z', '+00:00'))
        diff = abs((time1 - time2).total_seconds() / 60)
        return diff

    def _prepare_spatial_features(self, trips):
        """
        准备空间聚类特征
        """
        # 提取起点坐标
        origins = np.array([[trip['origin']['lat'], trip['origin']['lng']] for trip in trips])
        return origins

    def _prepare_destination_features(self, trips):
        """
        准备终点空间聚类特征
        """
        # 提取终点坐标
        destinations = np.array([[trip['destination']['lat'], trip['destination']['lng']] for trip in trips])
        return destinations
        
    def _group_by_time_window(self, trips):
        """
        按照时间窗口对出行请求进行分组
        """
        if not trips:
            return []
            
        logger.info("\n开始按时间窗口分组:")
        logger.info(f"时间窗口大小: {self.time_window}分钟")
        logger.info(f"总请求数: {len(trips)}")
            
        # 按出发时间排序
        sorted_trips = sorted(trips, key=lambda x: x['departure_time'])
        logger.info(f"最早出发时间: {sorted_trips[0]['departure_time']}")
        logger.info(f"最晚出发时间: {sorted_trips[-1]['departure_time']}")
        
        time_groups = []
        current_group = [sorted_trips[0]]
        start_time = datetime.fromisoformat(sorted_trips[0]['departure_time'].replace('Z', '+00:00'))
        
        for trip in sorted_trips[1:]:
            trip_time = datetime.fromisoformat(trip['departure_time'].replace('Z', '+00:00'))
            time_diff = (trip_time - start_time).total_seconds() / 60
            
            logger.info(f"\n检查请求 {trip.get('request_id', 'unknown')}:")
            logger.info(f"- 出发时间: {trip['departure_time']}")
            logger.info(f"- 与组起始时间差: {time_diff:.1f}分钟")
            logger.info(f"- 当前组大小: {len(current_group)}")
            
            if time_diff <= self.time_window:
                logger.info("=> 加入当前组")
                current_group.append(trip)
            else:
                logger.info("=> 创建新组")
                time_groups.append(current_group)
                current_group = [trip]
                start_time = trip_time
        
        # 添加最后一组
        if current_group:
            time_groups.append(current_group)
            
        logger.info(f"\n时间分组结果:")
        logger.info(f"总共分成 {len(time_groups)} 个时间组")
        for i, group in enumerate(time_groups):
            logger.info(f"\n时间组 {i+1}:")
            logger.info(f"- 请求数量: {len(group)}")
            logger.info(f"- 时间范围: {group[0]['departure_time']} - {group[-1]['departure_time']}")
            logger.info("- 请求ID: " + ", ".join([str(t.get('request_id', 'unknown')) for t in group]))
            
            # 计算组内最大时间差
            group_start = datetime.fromisoformat(group[0]['departure_time'].replace('Z', '+00:00'))
            group_end = datetime.fromisoformat(group[-1]['departure_time'].replace('Z', '+00:00'))
            max_diff = (group_end - group_start).total_seconds() / 60
            logger.info(f"- 组内最大时间差: {max_diff:.1f}分钟")
            
            # 检查组内请求的空间分布
            if len(group) >= 2:
                max_dist = 0
                for i, t1 in enumerate(group):
                    for j, t2 in enumerate(group[i+1:], i+1):
                        dist = self._haversine_distance(
                            t1['origin']['lat'], t1['origin']['lng'],
                            t2['origin']['lat'], t2['origin']['lng']
                        )
                        max_dist = max(max_dist, dist)
                logger.info(f"- 组内最大空间距离: {max_dist:.2f}公里")
        
        return time_groups

    def _cluster_spatial_data(self, trips):
        """
        对出行请求进行空间聚类
        """
        if not trips:
            logger.warning("没有请求可供聚类")
            return []
            
        try:
            logger.info("\n开始空间聚类:")
            logger.info(f"空间阈值: {self.spatial_threshold}公里")
            logger.info(f"最小样本数: {self.min_samples}")
            logger.info(f"请求数量: {len(trips)}")
            
            # 提取空间特征并转换为弧度
            origin_features = []
            for trip in trips:
                lat = math.radians(trip['origin']['lat'])
                lng = math.radians(trip['origin']['lng'])
                origin_features.append([lat, lng])
            
            origin_features = np.array(origin_features)
            
            # 如果请求数量小于最小样本数，但大于1，将所有请求归为一个聚类
            if 1 < len(origin_features) < self.min_samples:
                logger.info(f"请求数量 ({len(origin_features)}) 小于最小样本数 ({self.min_samples})，但大于1，将所有请求归为一个聚类")
                clustered_trips = []
                for trip in trips:
                    trip_copy = trip.copy()
                    trip_copy['origin_cluster'] = 0
                    clustered_trips.append(trip_copy)
                return clustered_trips
            elif len(origin_features) <= 1:
                logger.info("请求数量不足，无法形成聚类")
                clustered_trips = []
                for trip in trips:
                    trip_copy = trip.copy()
                    trip_copy['origin_cluster'] = -1
                    clustered_trips.append(trip_copy)
                return clustered_trips
            
            # 计算请求间的距离矩阵
            distance_matrix = np.zeros((len(trips), len(trips)))
            for i, trip1 in enumerate(trips):
                for j, trip2 in enumerate(trips):
                    if i != j:
                        distance = self._haversine_distance(
                            trip1['origin']['lat'],
                            trip1['origin']['lng'],
                            trip2['origin']['lat'],
                            trip2['origin']['lng']
                        )
                        distance_matrix[i][j] = distance
            
            logger.info("\n请求间距离矩阵:")
            for i, row in enumerate(distance_matrix):
                logger.info(f"请求 {trips[i].get('request_id', 'unknown')}: " + 
                          ", ".join([f"{d:.2f}km" for d in row]))
            
            # 执行起点聚类
            labels = self.spatial_clusterer.fit_predict(origin_features)
            
            # 将聚类标签添加到原始数据中
            clustered_trips = []
            for trip, label in zip(trips, labels):
                trip_copy = trip.copy()
                trip_copy['origin_cluster'] = int(label)
                clustered_trips.append(trip_copy)
            
            # 获取聚类数量（排除噪声点-1）
            cluster_ids = set([t['origin_cluster'] for t in clustered_trips if t['origin_cluster'] != -1])
            noise_points = len([t for t in clustered_trips if t['origin_cluster'] == -1])
            
            logger.info(f"\n空间聚类结果:")
            logger.info(f"- 有效聚类数: {len(cluster_ids)}")
            logger.info(f"- 噪声点数: {noise_points}")
            
            # 记录每个聚类的详细信息
            for cluster_id in cluster_ids:
                cluster_trips = [t for t in clustered_trips if t['origin_cluster'] == cluster_id]
                logger.info(f"\n聚类 {cluster_id} 详细信息:")
                logger.info(f"- 请求数量: {len(cluster_trips)}")
                logger.info("- 请求ID: " + ", ".join([str(t.get('request_id', 'unknown')) for t in cluster_trips]))
                
                # 计算聚类中心点
                center_lat = sum(t['origin']['lat'] for t in cluster_trips) / len(cluster_trips)
                center_lng = sum(t['origin']['lng'] for t in cluster_trips) / len(cluster_trips)
                logger.info(f"- 中心点: lat={center_lat:.6f}, lng={center_lng:.6f}")
                
                # 计算到中心点的最大距离
                max_distance = 0
                for trip in cluster_trips:
                    distance = self._haversine_distance(
                        trip['origin']['lat'],
                        trip['origin']['lng'],
                        center_lat,
                        center_lng
                    )
                    max_distance = max(max_distance, distance)
                logger.info(f"- 到中心点最大距离: {max_distance:.2f}公里")
                
                # 计算组内最大距离
                max_internal_distance = 0
                for i, t1 in enumerate(cluster_trips):
                    for j, t2 in enumerate(cluster_trips[i+1:], i+1):
                        distance = self._haversine_distance(
                            t1['origin']['lat'],
                            t1['origin']['lng'],
                            t2['origin']['lat'],
                            t2['origin']['lng']
                        )
                        max_internal_distance = max(max_internal_distance, distance)
                logger.info(f"- 组内最大距离: {max_internal_distance:.2f}公里")
            
            if noise_points > 0:
                logger.info("\n噪声点详细信息:")
                noise_trips = [t for t in clustered_trips if t['origin_cluster'] == -1]
                for trip in noise_trips:
                    logger.info(f"- 请求 {trip.get('request_id', 'unknown')}:")
                    logger.info(f"  起点: lat={trip['origin']['lat']}, lng={trip['origin']['lng']}")
                    
                    # 计算到最近聚类中心的距离
                    min_center_distance = float('inf')
                    nearest_cluster = None
                    for cluster_id in cluster_ids:
                        cluster_trips = [t for t in clustered_trips if t['origin_cluster'] == cluster_id]
                        center_lat = sum(t['origin']['lat'] for t in cluster_trips) / len(cluster_trips)
                        center_lng = sum(t['origin']['lng'] for t in cluster_trips) / len(cluster_trips)
                        distance = self._haversine_distance(
                            trip['origin']['lat'],
                            trip['origin']['lng'],
                            center_lat,
                            center_lng
                        )
                        if distance < min_center_distance:
                            min_center_distance = distance
                            nearest_cluster = cluster_id
                    
                    if nearest_cluster is not None:
                        logger.info(f"  到最近聚类 {nearest_cluster} 的距离: {min_center_distance:.2f}公里")
            
            return clustered_trips
            
        except Exception as e:
            logger.error(f"空间聚类过程出错: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def _further_cluster_by_destination(self, origin_clustered_trips):
        """
        对已经按起点聚类的请求进行终点聚类
        """
        if not origin_clustered_trips:
            return []
            
        logger.info("\n开始终点聚类:")
        logger.info(f"总请求数: {len(origin_clustered_trips)}")
            
        # 按起点聚类分组
        origin_clusters = {}
        for trip in origin_clustered_trips:
            origin_cluster_id = trip['origin_cluster']
            if origin_cluster_id not in origin_clusters:
                origin_clusters[origin_cluster_id] = []
            origin_clusters[origin_cluster_id].append(trip)
        
        logger.info(f"起点聚类组数: {len(origin_clusters)}")
        for cluster_id, trips in origin_clusters.items():
            logger.info(f"\n起点聚类 {cluster_id}:")
            logger.info(f"- 请求数: {len(trips)}")
            logger.info("- 请求ID: " + ", ".join([str(t.get('request_id', 'unknown')) for t in trips]))
        
        # 对每个起点聚类内部再按终点聚类
        final_clustered_trips = []
        
        # 聚类计数器
        global_cluster_id = 0
        
        for origin_id, cluster_trips in origin_clusters.items():
            logger.info(f"\n处理起点聚类 {origin_id} 的终点聚类:")
            logger.info(f"请求数: {len(cluster_trips)}")
            
            # 跳过噪声点
            if origin_id == -1:
                logger.info("跳过噪声点组")
                # 将噪声点保留，但设置final_cluster_id为-1
                for trip in cluster_trips:
                    trip_copy = trip.copy()
                    trip_copy['final_cluster_id'] = -1
                    final_clustered_trips.append(trip_copy)
                continue
                
            # 提取终点特征
            destination_features = []
            for trip in cluster_trips:
                lat = math.radians(trip['destination']['lat'])
                lng = math.radians(trip['destination']['lng'])
                destination_features.append([lat, lng])
            
            destination_features = np.array(destination_features)
            
            # 计算终点间的距离矩阵
            distance_matrix = np.zeros((len(cluster_trips), len(cluster_trips)))
            for i, trip1 in enumerate(cluster_trips):
                for j, trip2 in enumerate(cluster_trips):
                    if i != j:
                        distance = self._haversine_distance(
                            trip1['destination']['lat'],
                            trip1['destination']['lng'],
                            trip2['destination']['lat'],
                            trip2['destination']['lng']
                        )
                        distance_matrix[i][j] = distance
            
            logger.info("\n终点间距离矩阵:")
            for i, row in enumerate(distance_matrix):
                logger.info(f"请求 {cluster_trips[i].get('request_id', 'unknown')}: " + 
                          ", ".join([f"{d:.2f}km" for d in row]))
            
            # 如果该起点聚类中的请求数大于最小样本数，执行终点聚类
            if len(cluster_trips) >= self.min_samples:
                logger.info(f"请求数 ({len(cluster_trips)}) >= 最小样本数 ({self.min_samples})，执行终点聚类")
                dest_clusterer = DBSCAN(
                    eps=self.spatial_eps,
                    min_samples=self.min_samples,
                    metric='haversine'
                )
                dest_labels = dest_clusterer.fit_predict(destination_features)
                
                # 将终点聚类结果合并到最终聚类ID中
                for trip, dest_label in zip(cluster_trips, dest_labels):
                    trip_copy = trip.copy()
                    
                    # 对于有效的终点聚类，分配全局聚类ID
                    if dest_label != -1:
                        trip_copy['destination_cluster'] = int(dest_label)
                        trip_copy['final_cluster_id'] = global_cluster_id
                        global_cluster_id += 1
                    else:
                        trip_copy['destination_cluster'] = -1
                        trip_copy['final_cluster_id'] = -1
                        
                    final_clustered_trips.append(trip_copy)
                    
                logger.info(f"终点聚类结果:")
                for label in set(dest_labels):
                    if label != -1:
                        label_trips = [t for t, l in zip(cluster_trips, dest_labels) if l == label]
                        logger.info(f"\n终点聚类 {label}:")
                        logger.info(f"- 请求数: {len(label_trips)}")
                        logger.info("- 请求ID: " + ", ".join([str(t.get('request_id', 'unknown')) for t in label_trips]))
            else:
                # 如果请求数不足以进行终点聚类，但大于1，保留为一个聚类
                if len(cluster_trips) > 1:
                    logger.info(f"请求数 ({len(cluster_trips)}) < 最小样本数 ({self.min_samples})，但大于1，保持为一个聚类")
                    # 检查终点是否足够接近
                    max_dest_distance = 0
                    for i, trip1 in enumerate(cluster_trips):
                        for j, trip2 in enumerate(cluster_trips[i+1:], i+1):
                            distance = self._haversine_distance(
                                trip1['destination']['lat'],
                                trip1['destination']['lng'],
                                trip2['destination']['lat'],
                                trip2['destination']['lng']
                            )
                            max_dest_distance = max(max_dest_distance, distance)
                    
                    logger.info(f"终点最大间距: {max_dest_distance:.2f}公里")
                    
                    # 如果终点足够接近，保持为一个聚类
                    if max_dest_distance <= self.spatial_threshold * 2:
                        logger.info("终点距离在阈值范围内，保持为一个聚类")
                        for trip in cluster_trips:
                            trip_copy = trip.copy()
                            trip_copy['destination_cluster'] = 0
                            trip_copy['final_cluster_id'] = global_cluster_id
                            final_clustered_trips.append(trip_copy)
                        global_cluster_id += 1
                    else:
                        logger.info("终点距离超出阈值，标记为噪声点")
                        for trip in cluster_trips:
                            trip_copy = trip.copy()
                            trip_copy['destination_cluster'] = -1
                            trip_copy['final_cluster_id'] = -1
                            final_clustered_trips.append(trip_copy)
                else:
                    logger.info("单个请求，标记为噪声点")
                    for trip in cluster_trips:
                        trip_copy = trip.copy()
                        trip_copy['destination_cluster'] = -1
                        trip_copy['final_cluster_id'] = -1
                        final_clustered_trips.append(trip_copy)
        
        # 记录终点聚类结果
        final_clusters = {}
        for trip in final_clustered_trips:
            cluster_id = trip['final_cluster_id']
            if cluster_id not in final_clusters:
                final_clusters[cluster_id] = []
            final_clusters[cluster_id].append(trip)
        
        logger.info(f"\n终点聚类最终结果:")
        logger.info(f"- 有效聚类数: {len([k for k in final_clusters.keys() if k != -1])}")
        logger.info(f"- 噪声点数: {len(final_clusters.get(-1, []))}")
        
        for cluster_id, trips in final_clusters.items():
            if cluster_id != -1:  # 排除噪声点
                logger.info(f"\n最终聚类 {cluster_id}:")
                logger.info(f"- 请求数: {len(trips)}")
                logger.info("- 请求ID: " + ", ".join([str(t.get('request_id', 'unknown')) for t in trips]))
                
                # 计算起点中心
                center_origin_lat = sum(t['origin']['lat'] for t in trips) / len(trips)
                center_origin_lng = sum(t['origin']['lng'] for t in trips) / len(trips)
                logger.info(f"- 起点中心: lat={center_origin_lat:.6f}, lng={center_origin_lng:.6f}")
                
                # 计算终点中心
                center_dest_lat = sum(t['destination']['lat'] for t in trips) / len(trips)
                center_dest_lng = sum(t['destination']['lng'] for t in trips) / len(trips)
                logger.info(f"- 终点中心: lat={center_dest_lat:.6f}, lng={center_dest_lng:.6f}")
                
                # 计算起点和终点的最大间距
                max_origin_distance = 0
                max_dest_distance = 0
                for i, t1 in enumerate(trips):
                    for j, t2 in enumerate(trips[i+1:], i+1):
                        origin_dist = self._haversine_distance(
                            t1['origin']['lat'],
                            t1['origin']['lng'],
                            t2['origin']['lat'],
                            t2['origin']['lng']
                        )
                        dest_dist = self._haversine_distance(
                            t1['destination']['lat'],
                            t1['destination']['lng'],
                            t2['destination']['lat'],
                            t2['destination']['lng']
                        )
                        max_origin_distance = max(max_origin_distance, origin_dist)
                        max_dest_distance = max(max_dest_distance, dest_dist)
                
                logger.info(f"- 起点最大间距: {max_origin_distance:.2f}公里")
                logger.info(f"- 终点最大间距: {max_dest_distance:.2f}公里")
        
        return final_clustered_trips

    def _split_large_clusters(self, clustered_trips):
        """
        将大型聚类拆分为满足每条线路最大点数限制的多个小聚类
        """
        # 按最终聚类ID分组
        final_clusters = {}
        for trip in clustered_trips:
            cluster_id = trip['final_cluster_id']
            if cluster_id == -1:  # 跳过噪声点
                continue
                
            if cluster_id not in final_clusters:
                final_clusters[cluster_id] = []
            final_clusters[cluster_id].append(trip)
        
        # 拆分大型聚类
        split_clustered_trips = []
        max_cluster_id = max(final_clusters.keys()) if final_clusters else 0
        next_cluster_id = max_cluster_id + 1
        
        for cluster_id, cluster_trips in final_clusters.items():
            # 如果聚类中的请求数大于每条线路最大点数，拆分为多个小聚类
            if len(cluster_trips) > self.max_points_per_route:
                # 使用KMeans将这个大聚类拆分为多个小聚类
                n_sub_clusters = math.ceil(len(cluster_trips) / self.max_points_per_route)
                
                # 结合起点和终点坐标
                combined_features = []
                for trip in cluster_trips:
                    combined_features.append([
                        trip['origin']['lat'],
                        trip['origin']['lng'],
                        trip['destination']['lat'],
                        trip['destination']['lng']
                    ])
                
                combined_features = np.array(combined_features)
                
                # 执行KMeans聚类
                kmeans = KMeans(n_clusters=n_sub_clusters, random_state=42)
                sub_labels = kmeans.fit_predict(combined_features)
                
                # 将拆分结果合并到最终结果中
                for trip, sub_label in zip(cluster_trips, sub_labels):
                    trip_copy = trip.copy()
                    trip_copy['final_cluster_id'] = next_cluster_id + sub_label
                    split_clustered_trips.append(trip_copy)
                
                logger.info(f"聚类 {cluster_id} 被拆分为 {n_sub_clusters} 个子聚类")
                next_cluster_id += n_sub_clusters
            else:
                # 如果聚类中的请求数不大于每条线路最大点数，保持不变
                for trip in cluster_trips:
                    split_clustered_trips.append(trip)
        
        # 添加噪声点
        for trip in clustered_trips:
            if trip['final_cluster_id'] == -1:
                split_clustered_trips.append(trip)
        
        return split_clustered_trips

    def _check_cluster_distance_constraint(self, clustered_trips):
        """
        检查聚类内的距离约束，确保每个聚类内所有点距离都小于最大聚类半径
        如果不满足条件，尝试拆分或重新分配点
        """
        # 按最终聚类ID分组
        final_clusters = {}
        for trip in clustered_trips:
            cluster_id = trip['final_cluster_id']
            if cluster_id == -1:  # 跳过噪声点
                continue
                
            if cluster_id not in final_clusters:
                final_clusters[cluster_id] = []
            final_clusters[cluster_id].append(trip)
        
        # 检查并调整每个聚类
        adjusted_trips = []
        next_cluster_id = max(final_clusters.keys()) + 1 if final_clusters else 0
        
        for cluster_id, cluster_trips in final_clusters.items():
            if len(cluster_trips) <= 1:
                # 单点聚类，直接添加
                adjusted_trips.extend(cluster_trips)
                continue
            
            # 计算聚类中心点
            origin_lats = [t['origin']['lat'] for t in cluster_trips]
            origin_lngs = [t['origin']['lng'] for t in cluster_trips]
            dest_lats = [t['destination']['lat'] for t in cluster_trips]
            dest_lngs = [t['destination']['lng'] for t in cluster_trips]
            
            origin_center = (sum(origin_lats) / len(origin_lats), sum(origin_lngs) / len(origin_lngs))
            dest_center = (sum(dest_lats) / len(dest_lats), sum(dest_lngs) / len(dest_lngs))
            
            # 检查每个点到中心的距离
            valid_cluster = True
            for trip in cluster_trips:
                origin_distance = self._haversine_distance(
                    trip['origin']['lat'], trip['origin']['lng'],
                    origin_center[0], origin_center[1]
                )
                dest_distance = self._haversine_distance(
                    trip['destination']['lat'], trip['destination']['lng'],
                    dest_center[0], dest_center[1]
                )
                
                if origin_distance > self.max_cluster_radius or dest_distance > self.max_cluster_radius:
                    valid_cluster = False
                    logger.info(f"聚类 {cluster_id} 超出距离约束: 起点距离={origin_distance:.2f}km, 终点距离={dest_distance:.2f}km")
                    break
            
            if valid_cluster:
                # 聚类有效，保持不变
                adjusted_trips.extend(cluster_trips)
                logger.info(f"聚类 {cluster_id} 满足距离约束")
            else:
                # 聚类无效，尝试拆分
                if len(cluster_trips) > 2:
                    # 使用KMeans拆分为2个子聚类
                    combined_features = []
                    for trip in cluster_trips:
                        combined_features.append([
                            trip['origin']['lat'],
                            trip['origin']['lng'],
                            trip['destination']['lat'],
                            trip['destination']['lng']
                        ])
                    
                    kmeans = KMeans(n_clusters=2, random_state=42)
                    sub_labels = kmeans.fit_predict(np.array(combined_features))
                    
                    # 更新聚类ID
                    for trip, sub_label in zip(cluster_trips, sub_labels):
                        trip_copy = trip.copy()
                        trip_copy['final_cluster_id'] = next_cluster_id + sub_label
                        adjusted_trips.append(trip_copy)
                    
                    logger.info(f"聚类 {cluster_id} 被拆分为2个子聚类")
                    next_cluster_id += 2
                else:
                    # 对于只有2个点的聚类，标记为噪声点
                    for trip in cluster_trips:
                        trip_copy = trip.copy()
                        trip_copy['final_cluster_id'] = -1
                        adjusted_trips.append(trip_copy)
                    logger.info(f"聚类 {cluster_id} 被标记为噪声点")
        
        # 添加原来的噪声点
        for trip in clustered_trips:
            if trip['final_cluster_id'] == -1:
                if trip not in adjusted_trips:
                    adjusted_trips.append(trip)
        
        return adjusted_trips

    def cluster_trips(self, trips):
        """
        对出行请求进行增强聚类
        
        参数:
            trips: 出行请求列表
            
        返回:
            聚类后的出行请求列表
        """
        if not trips:
            logger.warning("没有请求可供聚类")
            return []
        
        logger.info("=====================================================")
        logger.info(f"开始聚类处理: 收到 {len(trips)} 个出行请求")
        logger.info("=====================================================")
        
        try:
            # 步骤1: 按时间窗口分组
            time_groups = []
            current_group = [trips[0]]
            start_time = datetime.fromisoformat(trips[0]['departure_time'].replace('Z', '+00:00'))
            
            for trip in trips[1:]:
                trip_time = datetime.fromisoformat(trip['departure_time'].replace('Z', '+00:00'))
                time_diff = (trip_time - start_time).total_seconds() / 60
                
                if time_diff <= self.time_window:
                    current_group.append(trip)
                else:
                    if len(current_group) >= self.min_samples:
                        time_groups.append(current_group)
                    current_group = [trip]
                    start_time = trip_time
            
            # 添加最后一组
            if len(current_group) >= self.min_samples:
                time_groups.append(current_group)
            
            logger.info(f"\n时间分组结果: {len(time_groups)} 个时间组")
            for i, group in enumerate(time_groups):
                logger.info(f"时间组 {i+1}: {len(group)} 个请求")
            
            # 如果没有有效的时间组，返回空结果
            if not time_groups:
                logger.warning("没有找到满足最小样本数的时间组")
                return []
            
            # 步骤2: 对每个时间组进行空间聚类
            all_clusters = []
            cluster_id = 0
            
            for time_group in time_groups:
                logger.info(f"\n处理时间组: {len(time_group)} 个请求")
                
                # 计算组内请求之间的距离矩阵
                n = len(time_group)
                distance_matrix = np.zeros((n, n))
                
                for i in range(n):
                    for j in range(i+1, n):
                        # 计算起点和终点的距离
                        origin_dist = self._haversine_distance(
                            time_group[i]['origin']['lat'],
                            time_group[i]['origin']['lng'],
                            time_group[j]['origin']['lat'],
                            time_group[j]['origin']['lng']
                        )
                        dest_dist = self._haversine_distance(
                            time_group[i]['destination']['lat'],
                            time_group[i]['destination']['lng'],
                            time_group[j]['destination']['lat'],
                            time_group[j]['destination']['lng']
                        )
                        # 使用起点和终点距离的加权平均
                        distance = (origin_dist + dest_dist) / 2
                        distance_matrix[i][j] = distance
                        distance_matrix[j][i] = distance
                
                # 找出距离在阈值内的请求对
                clusters = []
                used = set()
                
                for i in range(n):
                    if i in used:
                        continue
                        
                    cluster = [i]
                    for j in range(i+1, n):
                        if j in used:
                            continue
                        
                        # 检查j是否与当前簇中的所有点都满足距离条件
                        can_add = True
                        for k in cluster:
                            if distance_matrix[j][k] > self.spatial_threshold:
                                can_add = False
                                break
                        
                        if can_add:
                            cluster.append(j)
                    
                    if len(cluster) >= self.min_samples:
                        used.update(cluster)
                        clusters.append(cluster)
                
                # 将索引转换为实际的请求
                for cluster_indices in clusters:
                    cluster_trips = []
                    for idx in cluster_indices:
                        trip = time_group[idx].copy()
                        trip['cluster_id'] = cluster_id
                        cluster_trips.append(trip)
                    
                    logger.info(f"聚类 {cluster_id}: {len(cluster_trips)} 个请求")
                    all_clusters.extend(cluster_trips)
                    cluster_id += 1
                
                # 处理未分配的请求（噪声点）
                for i in range(n):
                    if i not in used:
                        trip = time_group[i].copy()
                        trip['cluster_id'] = -1
                        all_clusters.append(trip)
            
            # 统计最终结果
            valid_clusters = {t['cluster_id'] for t in all_clusters if t['cluster_id'] != -1}
            noise_points = sum(1 for t in all_clusters if t['cluster_id'] == -1)
            
            logger.info("\n=====================================================")
            logger.info("聚类处理完成:")
            logger.info(f"- 总请求数: {len(all_clusters)}")
            logger.info(f"- 有效聚类数: {len(valid_clusters)}")
            logger.info(f"- 噪声点数: {noise_points}")
            logger.info("=====================================================")
            
            if not valid_clusters:
                logger.warning("没有形成有效的聚类")
                return []
            
            return all_clusters
            
        except Exception as e:
            logger.error(f"聚类过程出错: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def get_cluster_statistics(self, clustered_trips):
        """
        获取聚类统计信息
        
        参数:
            clustered_trips: 聚类后的出行请求列表
            
        返回:
            聚类统计信息字典
        """
        if not clustered_trips:
            logger.warning("没有聚类结果可供统计")
            return {}
        
        logger.info("\n=====================================================")
        logger.info("开始统计聚类结果")
        logger.info("=====================================================")
        logger.info(f"总请求数: {len(clustered_trips)}")
        
        # 按最终聚类ID分组
        clusters = {}
        for trip in clustered_trips:
            # 使用cluster_id作为主键
            cluster_id = trip.get('cluster_id', -1)
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'cluster_id': cluster_id,
                    'trips': [],
                    'size': 0,
                    'origins': [],
                    'destinations': [],
                    'departure_times': [],
                    'time_group': trip.get('time_group', 0)
                }
            
            stats = clusters[cluster_id]
            stats['size'] += 1
            stats['trips'].append(trip)
            stats['origins'].append(trip['origin'])
            stats['destinations'].append(trip['destination'])
            stats['departure_times'].append(trip['departure_time'])
        
        logger.info(f"\n找到 {len(clusters)} 个聚类组")
        logger.info(f"其中噪声点组: {1 if -1 in clusters else 0}")
        logger.info(f"有效聚类组: {len(clusters) - (1 if -1 in clusters else 0)}")
        
        # 计算每个聚类的中心点和时间范围
        for cluster_id, stats in clusters.items():
            logger.info(f"\n=====================================================")
            if cluster_id == -1:
                logger.info(f"噪声点组统计信息:")
            else:
                logger.info(f"聚类 {cluster_id} 统计信息:")
            logger.info("=====================================================")
            
            logger.info(f"基本信息:")
            logger.info(f"- 请求数: {stats['size']}")
            logger.info(f"- 时间组: {stats['time_group']}")
            
            if cluster_id != -1:  # 排除噪声点
                # 计算中心点
                origin_lats = [o['lat'] for o in stats['origins']]
                origin_lngs = [o['lng'] for o in stats['origins']]
                dest_lats = [d['lat'] for d in stats['destinations']]
                dest_lngs = [d['lng'] for d in stats['destinations']]
                
                stats['center_origin'] = {
                    'lat': sum(origin_lats) / len(origin_lats),
                    'lng': sum(origin_lngs) / len(origin_lngs)
                }
                stats['center_destination'] = {
                    'lat': sum(dest_lats) / len(dest_lats),
                    'lng': sum(dest_lngs) / len(dest_lngs)
                }
                
                # 将中心点信息添加到每个trip中
                for trip in stats['trips']:
                    trip['center_origin'] = stats['center_origin']
                    trip['center_destination'] = stats['center_destination']
                
                logger.info(f"\n空间信息:")
                logger.info(f"- 起点中心: ({stats['center_origin']['lat']:.6f}, {stats['center_origin']['lng']:.6f})")
                logger.info(f"- 终点中心: ({stats['center_destination']['lat']:.6f}, {stats['center_destination']['lng']:.6f})")
                
                # 计算时间范围
                times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in stats['departure_times']]
                stats['time_range'] = {
                    'start': min(times).isoformat(),
                    'end': max(times).isoformat()
                }
                
                logger.info(f"\n时间信息:")
                logger.info(f"- 最早出发: {stats['time_range']['start']}")
                logger.info(f"- 最晚出发: {stats['time_range']['end']}")
                
                # 计算请求总人数
                stats['total_passengers'] = sum([t.get('people_count', 1) for t in stats['trips']])
                logger.info(f"\n乘客信息:")
                logger.info(f"- 总乘客数: {stats['total_passengers']}")
                logger.info(f"- 平均每个请求乘客数: {stats['total_passengers']/stats['size']:.1f}")
                
                # 计算起始点最大间距
                max_origin_distance = 0
                for i, o1 in enumerate(stats['origins']):
                    for j, o2 in enumerate(stats['origins']):
                        if i != j:
                            dist = self._haversine_distance(o1['lat'], o1['lng'], o2['lat'], o2['lng'])
                            max_origin_distance = max(max_origin_distance, dist)
                
                stats['max_origin_distance'] = max_origin_distance
                
                # 计算终点最大间距
                max_dest_distance = 0
                for i, d1 in enumerate(stats['destinations']):
                    for j, d2 in enumerate(stats['destinations']):
                        if i != j:
                            dist = self._haversine_distance(d1['lat'], d1['lng'], d2['lat'], d2['lng'])
                            max_dest_distance = max(max_dest_distance, dist)
                
                stats['max_dest_distance'] = max_dest_distance
                
                logger.info(f"\n距离信息:")
                logger.info(f"- 起点最大间距: {stats['max_origin_distance']:.2f}公里")
                logger.info(f"- 终点最大间距: {stats['max_dest_distance']:.2f}公里")
                
                # 打印每个请求的详细信息
                logger.info(f"\n请求详细信息:")
                for i, trip in enumerate(stats['trips']):
                    logger.info(f"\n  请求 {i+1}:")
                    logger.info(f"  - 请求ID: {trip.get('request_id', 'unknown')}")
                    logger.info(f"  - 乘客数: {trip.get('people_count', 1)}")
                    logger.info(f"  - 出发时间: {trip['departure_time']}")
                    
                    # 计算到聚类中心的距离
                    origin_dist = self._haversine_distance(
                        trip['origin']['lat'], 
                        trip['origin']['lng'],
                        stats['center_origin']['lat'],
                        stats['center_origin']['lng']
                    )
                    dest_dist = self._haversine_distance(
                        trip['destination']['lat'],
                        trip['destination']['lng'],
                        stats['center_destination']['lat'],
                        stats['center_destination']['lng']
                    )
                    logger.info(f"  - 到聚类中心距离: 起点={origin_dist:.2f}公里, 终点={dest_dist:.2f}公里")
            
            else:  # 噪声点组的统计
                logger.info("\n噪声点详细信息:")
                for i, trip in enumerate(stats['trips']):
                    logger.info(f"\n  噪声点 {i+1}:")
                    logger.info(f"  - 请求ID: {trip.get('request_id', 'unknown')}")
                    logger.info(f"  - 乘客数: {trip.get('people_count', 1)}")
                    logger.info(f"  - 出发时间: {trip['departure_time']}")
                    logger.info(f"  - 起点: lat={trip['origin']['lat']}, lng={trip['origin']['lng']}")
                    logger.info(f"  - 终点: lat={trip['destination']['lat']}, lng={trip['destination']['lng']}")
        
        logger.info("\n=====================================================")
        logger.info("聚类统计完成")
        logger.info("=====================================================")
        
        return clusters 