import requests
import json
import os
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from datetime import datetime
import time
from geopy.distance import geodesic
import heapq
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiRoutePlanner:
    def __init__(self, 
                 amap_key=None, 
                 timeout=15,      # API请求超时时间（秒）
                 retry_limit=3,   # API请求重试次数
                 sleep_time=1     # 请求间隔时间（秒）
                ):
        """
        多路线规划器
        
        参数:
            amap_key: 高德地图API密钥，如果为None则从环境变量读取
            timeout: API请求超时时间（秒）
            retry_limit: API请求重试次数
            sleep_time: 请求间隔时间（秒）
        """
        # 加载环境变量
        load_dotenv()
        
        # 获取高德地图API密钥
        self.amap_key = amap_key or os.getenv("AMAP_KEY")
        if not self.amap_key:
            logger.warning("未设置高德地图API密钥，将无法进行路线规划")
        
        # API配置
        self.base_url = "https://restapi.amap.com/v3"
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.sleep_time = sleep_time
        
        logger.info("初始化多路线规划器")

    def _call_amap_api(self, endpoint: str, params: Dict[str, Any], retries=0) -> Dict[str, Any]:
        """
        调用高德地图API
        
        参数:
            endpoint: API端点
            params: 请求参数
            retries: 当前重试次数
            
        返回:
            API响应
        """
        if not self.amap_key:
            raise ValueError("未设置高德地图API密钥")
        
        # 添加API密钥
        params['key'] = self.amap_key
        
        # 构建完整URL
        url = f"{self.base_url}/{endpoint}"
        
        # 记录请求日志
        logger.info(f"高德地图API请求: {url}")
        logger.info(f"请求参数: {params}")
        
        try:
            # 发送请求
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()  # 抛出HTTP错误
            
            result = response.json()
            logger.info(f"高德地图API响应: {result}")
            
            # 检查API响应状态
            if result.get('status') != '1':
                error_msg = f"高德地图API错误: {result.get('info')} (代码: {result.get('infocode')})"
                logger.error(error_msg)
                
                # 提供更详细的错误信息
                infocode = result.get('infocode')
                if infocode == '10001':
                    logger.error("API密钥无效，请检查密钥配置")
                elif infocode == '10003':
                    logger.error("API请求超过配额限制")
                elif infocode == '10009' or infocode == '20800':
                    logger.error("API密钥与平台类型不匹配，请确保使用Web服务密钥")
                
                # 如果API限流，尝试重试
                if result.get('infocode') in ['10004', '10008', '10020'] and retries < self.retry_limit:
                    sleep_time = self.sleep_time * (retries + 1)  # 指数退避
                    logger.info(f"API请求受限，{sleep_time}秒后重试 ({retries+1}/{self.retry_limit})")
                    time.sleep(sleep_time)
                    return self._call_amap_api(endpoint, params, retries + 1)
                
                raise Exception(error_msg)
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            
            # 如果请求失败，尝试重试
            if retries < self.retry_limit:
                sleep_time = self.sleep_time * (retries + 1)  # 指数退避
                logger.info(f"API请求失败，{sleep_time}秒后重试 ({retries+1}/{self.retry_limit})")
                time.sleep(sleep_time)
                return self._call_amap_api(endpoint, params, retries + 1)
            
            raise

    def _format_location(self, location: Dict[str, float]) -> str:
        """
        格式化位置坐标
        
        参数:
            location: 位置坐标，包含lat和lng
            
        返回:
            格式化的坐标字符串 "lng,lat"
        """
        return f"{location['lng']},{location['lat']}"

    def _tsp_optimize_route(self, locations: List[Dict[str, float]]) -> List[int]:
        """
        使用贪心算法解决TSP问题，优化点位的访问顺序
        
        参数:
            locations: 位置坐标列表
            
        返回:
            优化后的点位访问顺序索引
        """
        n = len(locations)
        if n <= 2:
            return list(range(n))  # 如果只有1或2个点，直接返回原始顺序
        
        # 计算所有点对之间的距离
        distance_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    loc1 = (locations[i]['lat'], locations[i]['lng'])
                    loc2 = (locations[j]['lat'], locations[j]['lng'])
                    distance_matrix[i][j] = geodesic(loc1, loc2).kilometers
        
        # 贪心算法: 从第一个点开始，每次选择最近的未访问点
        visited = [False] * n
        current = 0  # 起点
        route = [current]
        visited[current] = True
        
        for _ in range(n - 1):
            next_point = -1
            min_distance = float('inf')
            
            for j in range(n):
                if not visited[j] and distance_matrix[current][j] < min_distance:
                    min_distance = distance_matrix[current][j]
                    next_point = j
            
            route.append(next_point)
            visited[next_point] = True
            current = next_point
        
        return route

    def _find_optimal_waypoints_order(self, 
                                     origin: Dict[str, float], 
                                     destination: Dict[str, float], 
                                     waypoints: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        找到最优的途经点顺序
        
        参数:
            origin: 起点坐标
            destination: 终点坐标
            waypoints: 途经点坐标列表
            
        返回:
            优化排序后的途经点列表
        """
        if not waypoints:
            return []
        
        # 合并所有点位（起点、途经点）
        all_points = [origin] + waypoints
        
        # 优化点位访问顺序
        optimized_indices = self._tsp_optimize_route(all_points)
        
        # 从优化后的顺序中移除起点，并保持终点单独处理
        # 注意：我们需要找到起点在优化路径中的位置
        try:
            origin_index = optimized_indices.index(0)  # 起点在合并列表中的索引为0
            
            # 重新排序，使起点作为第一个点
            optimized_indices = optimized_indices[origin_index:] + optimized_indices[:origin_index]
            
            # 移除起点
            optimized_indices.pop(0)
            
            # 获取优化后的途经点
            optimized_waypoints = [all_points[i] for i in optimized_indices]
            
            return optimized_waypoints
        except ValueError:
            logger.error("无法在优化路径中找到起点")
            return waypoints

    def plan_single_route(self, 
                         origin: Dict[str, float], 
                         destination: Dict[str, float], 
                         waypoints: List[Dict[str, float]] = None,
                         optimize_order: bool = True) -> Dict[str, Any]:
        """
        规划单条路线
        
        参数:
            origin: 起点坐标
            destination: 终点坐标
            waypoints: 途经点坐标列表
            optimize_order: 是否优化途经点顺序
            
        返回:
            路线规划结果
        """
        if not waypoints:
            waypoints = []
            
        logger.info(f"规划路线: 起点={origin}, 终点={destination}, 途经点数量={len(waypoints)}")
        
        # 高德API限制一次请求最多支持16个途经点，如果超过需要分段请求
        max_waypoints = 16
        
        if optimize_order and waypoints:
            logger.info("优化途经点顺序")
            waypoints = self._find_optimal_waypoints_order(origin, destination, waypoints)
        
        # 构建请求参数
        params = {
            'origin': self._format_location(origin),
            'destination': self._format_location(destination),
            'strategy': 10,  # 综合最优路线
            'extensions': 'all'  # 返回详细信息
        }
        
        if waypoints:
            # 如果途经点数量超过限制，需要分段规划
            if len(waypoints) > max_waypoints:
                logger.info(f"途经点数量 {len(waypoints)} 超过API限制 {max_waypoints}，将分段规划")
                return self._plan_route_with_multiple_segments(origin, destination, waypoints)
            else:
                # 格式化途经点
                waypoints_str = ';'.join([self._format_location(p) for p in waypoints])
                params['waypoints'] = waypoints_str
        
        try:
            # 记录详细的请求参数
            logger.info(f"高德地图API请求参数: {json.dumps(params)}")
            
            # 调用高德地图API
            result = self._call_amap_api('direction/driving', params)
            
            if not result:
                logger.error("高德地图API返回空结果")
                return self._create_fallback_route(origin, destination, waypoints, "API返回空结果")
                
            if not result.get('route'):
                logger.error(f"路线规划失败: {result}")
                return self._create_fallback_route(origin, destination, waypoints, f"API返回结果缺少route字段: {result}")
            
            route_data = result['route']
            
            if not route_data.get('paths') or len(route_data['paths']) == 0:
                logger.error("路线规划失败: 返回结果中没有路径数据")
                logger.error(f"API完整响应: {json.dumps(result)}")
                return self._create_fallback_route(origin, destination, waypoints, "API返回结果中没有路径数据")
                
            # 提取路线信息
            path = route_data['paths'][0]
            
            # 验证路线步骤
            if not path.get('steps'):
                logger.error("路线规划失败: 返回结果中没有步骤数据")
                logger.error(f"API路径数据: {json.dumps(path)}")
                return self._create_fallback_route(origin, destination, waypoints, "API返回结果中没有步骤数据")
                
            # 提取路线折线（处理可能的空值）
            polyline = self._extract_polyline(path['steps'])
            
            # 验证折线数据的有效性
            if not polyline or len(polyline) < 2:
                logger.warning("路线规划未返回有效的折线数据，创建备用直线路线")
                return self._create_fallback_route(origin, destination, waypoints, "无效的折线数据")
            
            # 验证折线点的有效性
            valid_polyline = True
            for point in polyline:
                if not isinstance(point, dict) or 'lng' not in point or 'lat' not in point:
                    valid_polyline = False
                    logger.warning(f"发现无效的折线点: {point}")
                    break
                if not (-180 <= point['lng'] <= 180 and -90 <= point['lat'] <= 90):
                    valid_polyline = False
                    logger.warning(f"发现超出范围的经纬度: lng={point['lng']}, lat={point['lat']}")
                    break
            
            if not valid_polyline:
                logger.warning("折线数据包含无效点，创建备用直线路线")
                return self._create_fallback_route(origin, destination, waypoints, "折线数据包含无效点")
            
            # 提取路线详情
            route_info = {
                'distance': float(path['distance']),  # 路线总长度（米）
                'duration': int(path['duration']),    # 预计行驶时间（秒）
                'toll_distance': float(route_data.get('toll_distance', 0)),  # 收费路段长度（米）
                'toll': float(route_data.get('toll', 0)),                  # 预计路费（元）
                'steps': path['steps'],              # 路线详情步骤
                'polyline': polyline,  # 路线折线
                'start_location': origin,
                'end_location': destination,
                'waypoints': waypoints
            }
            
            # 检查polyline结果
            if len(polyline) < 10:
                logger.warning(f"折线点数量较少({len(polyline)}个点)，可能不够精确")
                # 记录所有折线点便于调试
                logger.debug(f"折线点: {polyline}")
            else:
                logger.info(f"规划路线成功，生成了{len(polyline)}个折线点")
            
            # 计算额外统计信息
            route_info['avg_speed'] = (route_info['distance'] / 1000) / (route_info['duration'] / 3600)  # 平均速度（公里/小时）
            route_info['waypoints_count'] = len(waypoints)
            
            return route_info
        except Exception as e:
            logger.error(f"路线规划出错: {str(e)}")
            logger.exception("详细错误信息:")
            return self._create_fallback_route(origin, destination, waypoints, f"API调用异常: {str(e)}")

    def _create_fallback_polyline(self, origin: Dict[str, float], destination: Dict[str, float], waypoints: List[Dict[str, float]] = None) -> List[Dict[str, float]]:
        """
        创建备用折线，当高德API返回无效数据时使用
        
        参数:
            origin: 起点坐标
            destination: 终点坐标
            waypoints: 途经点坐标列表
            
        返回:
            备用折线点列表
        """
        logger.info("创建备用折线")
        polyline = [{'lng': origin['lng'], 'lat': origin['lat']}]
        
        # 如果有途经点，添加途经点
        if waypoints:
            for point in waypoints:
                polyline.append({'lng': point['lng'], 'lat': point['lat']})
        
        # 添加终点
        polyline.append({'lng': destination['lng'], 'lat': destination['lat']})
        
        logger.info(f"创建了包含 {len(polyline)} 个点的备用折线")
        return polyline

    def _create_fallback_route(self, origin: Dict[str, float], destination: Dict[str, float], waypoints: List[Dict[str, float]], reason: str) -> Dict[str, Any]:
        """
        创建备用路线，当高德API调用失败时使用
        
        参数:
            origin: 起点坐标
            destination: 终点坐标
            waypoints: 途经点坐标列表
            reason: 创建备用路线的原因
            
        返回:
            备用路线信息
        """
        logger.info(f"创建备用路线，原因: {reason}")
        
        # 创建备用折线
        polyline = self._create_fallback_polyline(origin, destination, waypoints)
        
        # 计算路线总距离（直线距离）
        total_distance = 0
        for i in range(len(polyline) - 1):
            p1 = (polyline[i]['lat'], polyline[i]['lng'])
            p2 = (polyline[i+1]['lat'], polyline[i+1]['lng'])
            total_distance += geodesic(p1, p2).meters
        
        # 估算行驶时间（假设平均时速50km/h）
        est_duration = (total_distance / 1000) / 50 * 3600  # 秒
        
        # 创建备用步骤
        steps = []
        for i in range(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i+1]
            
            step_polyline = f"{p1['lng']},{p1['lat']};{p2['lng']},{p2['lat']}"
            p1_name = "起点" if i == 0 else f"途经点{i}"
            p2_name = "终点" if i == len(polyline) - 2 else f"途经点{i+1}"
            
            step_distance = geodesic((p1['lat'], p1['lng']), (p2['lat'], p2['lng'])).meters
            step_duration = (step_distance / 1000) / 50 * 3600  # 秒
            
            steps.append({
                'instruction': f"从{p1_name}行驶至{p2_name}",
                'distance': str(round(step_distance)),
                'duration': str(round(step_duration)),
                'polyline': step_polyline,
                'action': "直行",
                'assistant_action': ""
            })
        
        # 创建备用路线信息
        route_info = {
            'distance': total_distance,
            'duration': int(est_duration),
            'toll_distance': 0,
            'toll': 0,
            'steps': steps,
            'polyline': polyline,
            'start_location': origin,
            'end_location': destination,
            'waypoints': waypoints or [],
            'is_fallback': True,  # 标记为备用路线
            'fallback_reason': reason
        }
        
        # 计算额外统计信息
        route_info['avg_speed'] = 50  # 固定平均速度50km/h
        route_info['waypoints_count'] = len(waypoints) if waypoints else 0
        
        logger.info(f"创建了备用路线，总距离: {(total_distance/1000):.2f}km, 预计时间: {(est_duration/60):.2f}分钟")
        return route_info

    def _extract_polyline(self, steps):
        """
        从路线步骤中提取折线
        
        参数:
            steps: 路线步骤
            
        返回:
            路线折线
        """
        polyline = []
        try:
            if not steps:
                logger.error("路线步骤为空")
                return []
                
            logger.info(f"开始从{len(steps)}个路线步骤中提取折线")
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    logger.warning(f"步骤{i+1}不是字典类型: {type(step)}")
                    continue
                    
                if 'polyline' not in step:
                    logger.warning(f"步骤{i+1}中缺少polyline字段")
                    continue
                    
                polyline_str = step.get('polyline')
                if not polyline_str:
                    logger.warning(f"步骤{i+1}的polyline为空")
                    continue
                    
                if not isinstance(polyline_str, str):
                    logger.warning(f"步骤{i+1}的polyline不是字符串类型: {type(polyline_str)}")
                    continue
                    
                if ';' not in polyline_str:
                    logger.warning(f"步骤{i+1}的polyline格式不正确: {polyline_str[:30]}...")
                    continue
                    
                points = polyline_str.split(';')
                for point in points:
                    if not point or not point.strip():
                        continue
                        
                    try:
                        if ',' not in point:
                            logger.warning(f"坐标点格式不正确: {point}")
                            continue
                            
                        lng, lat = point.strip().split(',')
                        try:
                            lng_float = float(lng)
                            lat_float = float(lat)
                            
                            # 验证经纬度范围
                            if not (-180 <= lng_float <= 180 and -90 <= lat_float <= 90):
                                logger.warning(f"经纬度超出有效范围: lng={lng_float}, lat={lat_float}")
                                continue
                                
                            polyline.append({'lng': lng_float, 'lat': lat_float})
                        except ValueError as e:
                            logger.warning(f"无法将坐标转换为浮点数: {point}, 错误: {str(e)}")
                            continue
                    except Exception as e:
                        logger.warning(f"处理坐标点时出错: {point}, 错误: {str(e)}")
                        continue
                        
            if not polyline:
                logger.error("没有从路线步骤中提取到任何有效的折线点")
                
        except Exception as e:
            logger.error(f"提取折线点时发生异常: {str(e)}")
            logger.exception("详细异常信息:")
            polyline = []
            
        return polyline

    def _plan_route_with_multiple_segments(self, 
                                          origin: Dict[str, float], 
                                          destination: Dict[str, float], 
                                          waypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        通过分段规划处理大量途经点
        
        参数:
            origin: 起点坐标
            destination: 终点坐标
            waypoints: 途经点坐标列表
            
        返回:
            合并后的路线规划结果
        """
        max_waypoints = 16
        
        # 将途经点分组
        waypoint_groups = []
        for i in range(0, len(waypoints), max_waypoints):
            waypoint_groups.append(waypoints[i:i+max_waypoints])
        
        logger.info(f"将 {len(waypoints)} 个途经点分为 {len(waypoint_groups)} 组进行规划")
        
        # 规划第一段路线，从起点到第一组途经点的最后一点
        current_origin = origin
        combined_route = {
            'distance': 0,
            'duration': 0,
            'toll_distance': 0,
            'toll': 0,
            'steps': [],
            'polyline': [],
            'start_location': origin,
            'end_location': destination,
            'waypoints': waypoints,
            'waypoints_count': len(waypoints),
            'avg_speed': 0
        }
        
        # 循环处理每组途经点
        for i, group in enumerate(waypoint_groups):
            # 如果是最后一组，终点为最终目的地
            if i == len(waypoint_groups) - 1:
                current_destination = destination
            else:
                # 否则，终点为下一组的第一个点
                current_destination = waypoint_groups[i+1][0]
            
            # 规划当前段路线
            segment_route = self.plan_single_route(
                current_origin, 
                current_destination, 
                group[:-1] if i == len(waypoint_groups) - 1 else group,
                optimize_order=False  # 已经优化过顺序，不再优化
            )
            
            if not segment_route:
                logger.error(f"分段 {i+1}/{len(waypoint_groups)} 规划失败")
                return None
            
            # 合并路线信息
            combined_route['distance'] += segment_route['distance']
            combined_route['duration'] += segment_route['duration']
            combined_route['toll_distance'] += segment_route['toll_distance']
            combined_route['toll'] += segment_route['toll']
            combined_route['steps'].extend(segment_route['steps'])
            combined_route['polyline'].extend(segment_route['polyline'])
            
            # 更新起点为当前终点
            current_origin = current_destination
        
        # 计算平均速度
        combined_route['avg_speed'] = (combined_route['distance'] / 1000) / (combined_route['duration'] / 3600)
        
        return combined_route

    def plan_cluster_route(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据聚类数据规划路线
        
        参数:
            cluster_data: 聚类数据
            
        返回:
            规划的路线信息
        """
        try:
            # 提取请求数据
            trips = cluster_data.get('trips', [])
            if not trips:
                logger.error("聚类数据中没有请求")
                return None
            
            # 提取聚类中心（从第一个trip中获取，因为所有trip都有相同的中心点）
            if not trips[0].get('center_origin'):
                logger.error("聚类数据缺少起点中心信息")
                return None
            
            # 使用起点中心作为虚拟起点
            center = trips[0]['center_origin']
            logger.info(f"聚类起点中心: lat={center['lat']}, lng={center['lng']}")
            
            # 获取聚类中的所有起点和终点
            origins = [trip['origin'] for trip in trips]
            destinations = [trip['destination'] for trip in trips]
            
            # 输出详细的聚类点信息
            logger.info("=== 聚类详细信息 ===")
            logger.info(f"聚类ID: {cluster_data.get('cluster_id', 0)}")
            logger.info(f"请求数量: {len(trips)}")
            logger.info(f"总乘客数: {sum([trip.get('people_count', 1) for trip in trips])}")
            
            # 输出每个请求的详细信息
            for i, trip in enumerate(trips):
                logger.info(f"\n请求 {i+1}:")
                logger.info(f"  - 请求ID: {trip.get('request_id', 'unknown')}")
                logger.info(f"  - 乘客数: {trip.get('people_count', 1)}")
                logger.info(f"  - 出发地: lat={trip['origin']['lat']}, lng={trip['origin']['lng']}")
                logger.info(f"  - 目的地: lat={trip['destination']['lat']}, lng={trip['destination']['lng']}")
                
                # 计算与聚类中心的距离
                origin_distance = geodesic(
                    (trip['origin']['lat'], trip['origin']['lng']),
                    (center['lat'], center['lng'])
                ).kilometers
                dest_distance = geodesic(
                    (trip['destination']['lat'], trip['destination']['lng']),
                    (center['lat'], center['lng'])
                ).kilometers
                logger.info(f"  - 到聚类中心的距离: 起点={origin_distance:.2f}km, 终点={dest_distance:.2f}km")
            
            logger.info("\n=== 路线规划信息 ===")
            # 设置虚拟起点（中心点）
            virtual_origin = center
            
            # 提取出发时间
            try:
                departure_time_str = trips[0]['departure_time']
                departure_time = departure_time_str
                logger.info(f"计划出发时间: {departure_time}")
            except (KeyError, IndexError) as e:
                logger.error(f"无法提取出发时间: {str(e)}")
                departure_time = datetime.now().isoformat()
                logger.info(f"使用当前时间作为出发时间: {departure_time}")
            
            # 规划接乘客路线（从虚拟起点出发，依次接所有乘客）
            logger.info(f"\n开始规划接乘客路线:")
            logger.info(f"- 起点(聚类中心): lat={virtual_origin['lat']}, lng={virtual_origin['lng']}")
            logger.info(f"- 终点(最后一个接的乘客): lat={origins[-1]['lat']}, lng={origins[-1]['lng']}")
            logger.info(f"- 途经点数量: {len(origins)-1}")
            
            pickup_route = self.plan_single_route(
                virtual_origin,
                origins[-1],  # 最后一个接的乘客的位置作为终点
                origins[:-1],  # 其余乘客位置作为途经点
                optimize_order=True  # 优化接车顺序
            )
            
            if not pickup_route:
                logger.error("接乘客路线规划失败")
                # 尝试不优化顺序再试一次
                logger.info("尝试不优化顺序再规划一次接乘客路线")
                pickup_route = self.plan_single_route(
                    virtual_origin,
                    origins[-1],
                    origins[:-1],
                    optimize_order=False
                )
                
                if not pickup_route:
                    logger.error("接乘客路线规划再次失败，无法生成路线计划")
                    return None
            else:
                logger.info(f"接乘客路线规划成功:")
                logger.info(f"- 总距离: {pickup_route['distance']/1000:.2f}km")
                logger.info(f"- 预计时间: {pickup_route['duration']/60:.0f}分钟")
                logger.info(f"- 平均速度: {pickup_route['avg_speed']:.1f}km/h")
            
            # 规划送乘客路线（从最后一个接的乘客位置出发，依次送所有乘客到目的地）
            logger.info(f"\n开始规划送乘客路线:")
            logger.info(f"- 起点(最后接的乘客): lat={origins[-1]['lat']}, lng={origins[-1]['lng']}")
            logger.info(f"- 终点(最后一个目的地): lat={destinations[-1]['lat']}, lng={destinations[-1]['lng']}")
            logger.info(f"- 途经点数量: {len(destinations)-1}")
            
            dropoff_route = self.plan_single_route(
                origins[-1],  # 从最后接的乘客位置出发
                destinations[-1],  # 最后送到的乘客的目的地作为终点
                destinations[:-1],  # 其余乘客目的地作为途经点
                optimize_order=True  # 优化送车顺序
            )
            
            if not dropoff_route:
                logger.error("送乘客路线规划失败")
                # 尝试不优化顺序再试一次
                logger.info("尝试不优化顺序再规划一次送乘客路线")
                dropoff_route = self.plan_single_route(
                    origins[-1],
                    destinations[-1],
                    destinations[:-1],
                    optimize_order=False
                )
                
                if not dropoff_route:
                    logger.error("送乘客路线规划再次失败，无法生成完整路线计划")
                    # 只返回接乘客路线
                    logger.warning("将只返回接乘客路线")
                    result = {
                        'cluster_id': cluster_data.get('cluster_id', 0),
                        'total_distance': pickup_route['distance'],
                        'total_duration': pickup_route['duration'],
                        'departure_time': departure_time,
                        'pickup_route': pickup_route,
                        'dropoff_route': None,  # 没有送乘客路线
                        'passenger_count': sum([trip.get('people_count', 1) for trip in trips]),
                        'trips': trips
                    }
                    logger.info("\n=== 路线规划结果（仅接乘客路线）===")
                    logger.info(f"总距离: {result['total_distance']/1000:.2f}km")
                    logger.info(f"总时间: {result['total_duration']/60:.0f}分钟")
                    return result
            else:
                logger.info(f"送乘客路线规划成功:")
                logger.info(f"- 总距离: {dropoff_route['distance']/1000:.2f}km")
                logger.info(f"- 预计时间: {dropoff_route['duration']/60:.0f}分钟")
                logger.info(f"- 平均速度: {dropoff_route['avg_speed']:.1f}km/h")
            
            # 返回完整的路线信息
            result = {
                'cluster_id': cluster_data.get('cluster_id', 0),
                'total_distance': pickup_route['distance'] + dropoff_route['distance'],
                'total_duration': pickup_route['duration'] + dropoff_route['duration'],
                'departure_time': departure_time,
                'pickup_route': pickup_route,
                'dropoff_route': dropoff_route,
                'passenger_count': sum([trip.get('people_count', 1) for trip in trips]),
                'trips': trips
            }
            
            logger.info("\n=== 路线规划最终结果 ===")
            logger.info(f"总距离: {result['total_distance']/1000:.2f}km")
            logger.info(f"总时间: {result['total_duration']/60:.0f}分钟")
            logger.info(f"平均速度: {(result['total_distance']/1000)/(result['total_duration']/3600):.1f}km/h")
            logger.info(f"总乘客数: {result['passenger_count']}")
            logger.info("=====================================")
            
            return result
            
        except Exception as e:
            logger.error(f"规划聚类路线时出错: {str(e)}", exc_info=True)
            return None

    def plan_multi_routes(self, clusters_data: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        规划多条路线，每个聚类一条路线
        
        参数:
            clusters_data: 聚类数据字典，键为聚类ID，值为聚类数据
            
        返回:
            路线规划结果字典，键为聚类ID，值为路线数据
        """
        routes = {}
        
        logger.info(f"开始为 {len(clusters_data)} 个聚类规划路线")
        
        for cluster_id, cluster_data in clusters_data.items():
            # 跳过噪声点
            if cluster_id == -1:
                continue
            
            logger.info(f"规划聚类 {cluster_id} 的路线，包含 {len(cluster_data['trips'])} 个请求")
            
            route = self.plan_cluster_route(cluster_data)
            if route:
                routes[cluster_id] = route
            else:
                logger.warning(f"聚类 {cluster_id} 的路线规划失败")
        
        logger.info(f"多路线规划完成，成功规划 {len(routes)} 条路线")
        
        return routes 