import requests
from typing import List, Dict, Any
import json
import os
from dotenv import load_dotenv

class RoutePlanner:
    def __init__(self):
        """
        初始化路线规划器
        """
        load_dotenv()
        self.amap_key = os.getenv("AMAP_KEY")
        self.base_url = "https://restapi.amap.com/v3"

    def _call_amap_api(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用高德地图API
        :param endpoint: API端点
        :param params: 请求参数
        :return: API响应
        """
        params['key'] = self.amap_key
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)
        return response.json()

    def plan_route(self, origin: Dict[str, float], destination: Dict[str, float], 
                  waypoints: List[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        规划单条路线
        :param origin: 起点坐标
        :param destination: 终点坐标
        :param waypoints: 途经点列表
        :return: 路线规划结果
        """
        # 构建请求参数
        params = {
            'origin': f"{origin['lng']},{origin['lat']}",
            'destination': f"{destination['lng']},{destination['lat']}",
            'strategy': 10,  # 推荐路线
            'extensions': 'all'
        }

        if waypoints:
            waypoints_str = ';'.join([f"{p['lng']},{p['lat']}" for p in waypoints])
            params['waypoints'] = waypoints_str

        # 调用高德地图API
        result = self._call_amap_api('direction/driving', params)
        
        if result['status'] == '1' and result['route']:
            return {
                'distance': float(result['route']['distance']),
                'duration': int(result['route']['time']),
                'steps': result['route']['paths'][0]['steps'],
                'toll': float(result['route']['toll']),
                'toll_distance': float(result['route']['toll_distance'])
            }
        return None

    def optimize_route(self, cluster: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化聚类后的路线
        :param cluster: 聚类信息
        :return: 优化后的路线
        """
        # 获取聚类中心点
        origin = cluster['center_origin']
        destination = cluster['center_destination']
        
        # 获取所有途经点
        waypoints = []
        for i in range(len(cluster['origins'])):
            if i > 0:  # 跳过第一个点（作为起点）
                waypoints.append(cluster['origins'][i])
        
        # 规划路线
        route = self.plan_route(origin, destination, waypoints)
        
        if route:
            return {
                'route': route,
                'cluster_id': cluster['cluster_id'],
                'passenger_count': cluster['size'],
                'time_range': cluster['time_range']
            }
        return None

    def get_route_details(self, route_id: str) -> Dict[str, Any]:
        """
        获取路线详细信息
        :param route_id: 路线ID
        :return: 路线详细信息
        """
        params = {
            'id': route_id
        }
        
        result = self._call_amap_api('direction/driving', params)
        
        if result['status'] == '1':
            return result['route']
        return None 