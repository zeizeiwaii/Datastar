from typing import Dict, Any, List
import numpy as np
from datetime import datetime, timedelta

class DepartureDecision:
    def __init__(self, 
                 min_passengers: int = 5,
                 max_wait_time: int = 30,
                 min_occupancy_rate: float = 0.6):
        """
        初始化发车决策器
        :param min_passengers: 最小乘客数
        :param max_wait_time: 最大等待时间（分钟）
        :param min_occupancy_rate: 最小载客率
        """
        self.min_passengers = min_passengers
        self.max_wait_time = max_wait_time
        self.min_occupancy_rate = min_occupancy_rate

    def _calculate_occupancy_rate(self, passenger_count: int, vehicle_capacity: int) -> float:
        """
        计算载客率
        :param passenger_count: 乘客数量
        :param vehicle_capacity: 车辆容量
        :return: 载客率
        """
        return passenger_count / vehicle_capacity

    def _calculate_wait_time(self, first_request_time: datetime) -> int:
        """
        计算等待时间
        :param first_request_time: 第一个请求的时间
        :return: 等待时间（分钟）
        """
        now = datetime.now()
        wait_time = (now - first_request_time).total_seconds() / 60
        return int(wait_time)

    def _evaluate_route_profitability(self, route: Dict[str, Any]) -> float:
        """
        评估路线盈利能力
        :param route: 路线信息
        :return: 盈利能力得分
        """
        # 基础参数
        distance = route['route']['distance']  # 米
        duration = route['route']['duration']  # 秒
        passenger_count = route['passenger_count']
        
        # 计算每公里收入（假设每人每公里收费1元）
        revenue_per_km = passenger_count * 1.0
        
        # 计算运营成本（假设每公里成本0.5元）
        cost_per_km = 0.5
        
        # 计算利润率
        profit_margin = (revenue_per_km - cost_per_km) / revenue_per_km
        
        # 考虑时间因素（高峰时段加权）
        hour = datetime.now().hour
        time_factor = 1.0
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # 高峰时段
            time_factor = 1.5
        
        return profit_margin * time_factor

    def make_decision(self, 
                     cluster: Dict[str, Any],
                     vehicle: Dict[str, Any],
                     route: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出发车决策
        :param cluster: 聚类信息
        :param vehicle: 车辆信息
        :param route: 路线信息
        :return: 决策结果
        """
        # 计算关键指标
        passenger_count = cluster['size']
        occupancy_rate = self._calculate_occupancy_rate(passenger_count, vehicle['capacity'])
        first_request_time = datetime.fromisoformat(cluster['time_range']['start'])
        wait_time = self._calculate_wait_time(first_request_time)
        profitability = self._evaluate_route_profitability(route)
        
        # 决策逻辑
        should_depart = False
        reason = ""
        
        if passenger_count >= self.min_passengers:
            if occupancy_rate >= self.min_occupancy_rate:
                should_depart = True
                reason = "满足最小乘客数和载客率要求"
            elif wait_time >= self.max_wait_time:
                should_depart = True
                reason = "等待时间超过阈值"
            elif profitability > 0.8:  # 高盈利能力
                should_depart = True
                reason = "路线盈利能力高"
        
        return {
            'should_depart': should_depart,
            'reason': reason,
            'metrics': {
                'passenger_count': passenger_count,
                'occupancy_rate': occupancy_rate,
                'wait_time': wait_time,
                'profitability': profitability
            },
            'thresholds': {
                'min_passengers': self.min_passengers,
                'min_occupancy_rate': self.min_occupancy_rate,
                'max_wait_time': self.max_wait_time
            }
        }

    def get_decision_explanation(self, decision: Dict[str, Any]) -> str:
        """
        获取决策解释
        :param decision: 决策结果
        :return: 决策解释文本
        """
        metrics = decision['metrics']
        thresholds = decision['thresholds']
        
        explanation = f"决策结果：{'建议发车' if decision['should_depart'] else '建议等待'}\n"
        explanation += f"原因：{decision['reason']}\n\n"
        explanation += "详细指标：\n"
        explanation += f"- 当前乘客数：{metrics['passenger_count']}人（阈值：{thresholds['min_passengers']}人）\n"
        explanation += f"- 载客率：{metrics['occupancy_rate']:.2%}（阈值：{thresholds['min_occupancy_rate']:.2%}）\n"
        explanation += f"- 等待时间：{metrics['wait_time']}分钟（阈值：{thresholds['max_wait_time']}分钟）\n"
        explanation += f"- 路线盈利能力：{metrics['profitability']:.2f}"
        
        return explanation 