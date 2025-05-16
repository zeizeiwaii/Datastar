import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
import traceback

# 导入自定义模块
from algorithm.clustering.enhanced_clustering import EnhancedClustering
from algorithm.routing.multi_route_planner import MultiRoutePlanner

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResponsiveScheduler:
    def __init__(self, 
                 spatial_threshold=1.0,    # 空间距离阈值（公里）
                 time_window=30,          # 时间窗口（分钟）
                 min_samples=2,           # 最小样本数
                 max_cluster_radius=5.0,  # 最大聚类半径（公里）
                 max_points_per_route=8,  # 每条路线最大点数
                 amap_key=None            # 高德地图API密钥
                ):
        """
        响应式公交调度系统
        
        参数:
            spatial_threshold: 空间距离阈值（公里）
            time_window: 时间窗口（分钟）
            min_samples: 最小样本数
            max_cluster_radius: 最大聚类半径（公里）
            max_points_per_route: 每条路线最大点数
            amap_key: 高德地图API密钥
        """
        # 初始化聚类器
        self.clusterer = EnhancedClustering(
            spatial_threshold=spatial_threshold,
            time_window=time_window,
            min_samples=min_samples,
            max_cluster_radius=max_cluster_radius,
            max_points_per_route=max_points_per_route
        )
        
        # 初始化路线规划器
        self.route_planner = MultiRoutePlanner(amap_key=amap_key)
        
        logger.info(f"初始化响应式调度系统: 空间阈值={spatial_threshold}公里, 时间窗口={time_window}分钟")

    def process_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理出行请求并生成调度计划
        
        参数:
            requests: 出行请求列表
        返回:
            处理结果，包含聚类和路线规划信息
        """
        if not requests:
            logger.warning("没有待处理的请求")
            return {
                "success": False,
                "error": "没有待处理的请求",
                "clusters": {},
                "routes": {}
            }
            
        start_time = time.time()
        logger.info("=====================================================")
        logger.info("开始处理出行请求")
        logger.info("=====================================================")
        logger.info(f"收到 {len(requests)} 个出行请求")
        
        # 打印每个请求的基本信息
        for i, request in enumerate(requests):
            logger.info(f"\n请求 {i+1}:")
            logger.info(f"- 请求ID: {request.get('request_id', 'unknown')}")
            logger.info(f"- 出发时间: {request.get('departure_time', 'unknown')}")
            logger.info(f"- 乘客数: {request.get('people_count', 1)}")
            logger.info(f"- 起点: lat={request['origin']['lat']}, lng={request['origin']['lng']}")
            logger.info(f"- 终点: lat={request['destination']['lat']}, lng={request['destination']['lng']}")
        
        try:
            # 步骤1: 对请求进行聚类
            logger.info("\n=====================================================")
            logger.info("第1步: 对请求进行聚类")
            logger.info("=====================================================")
            
            # 验证请求数据的完整性
            for i, request in enumerate(requests):
                if not self._validate_request(request):
                    error_msg = f"请求 {i+1} 数据不完整或格式错误"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "clusters": {},
                        "routes": {}
                    }
            
            clustered_requests = self.clusterer.cluster_trips(requests)
            if not clustered_requests:
                error_msg = "聚类过程未返回任何结果"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "clusters": {},
                    "routes": {}
                }
            
            # 步骤2: 获取聚类统计信息
            logger.info("\n=====================================================")
            logger.info("第2步: 获取聚类统计信息")
            logger.info("=====================================================")
            clusters_data = self.clusterer.get_cluster_statistics(clustered_requests)
            
            if not clusters_data:
                error_msg = "无法获取聚类统计信息"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "clusters": {},
                    "routes": {}
                }
            
            valid_clusters = {k: v for k, v in clusters_data.items() if k != -1}
            noise_points = clusters_data.get(-1, {}).get('size', 0)
            
            if not valid_clusters:
                error_msg = "没有形成有效的聚类"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "clusters": clusters_data,
                    "routes": {}
                }
            
            # 步骤3: 路径规划
            logger.info("\n=====================================================")
            logger.info("第3步: 为每个聚类规划路线")
            logger.info("=====================================================")
            logger.info(f"开始为 {len(valid_clusters)} 个有效聚类规划路线")
            
            routes = self.route_planner.plan_multi_routes(clusters_data)
            
            if not routes:
                error_msg = "路线规划失败，未能生成任何有效路线"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "clusters": clusters_data,
                    "routes": {}
                }
            
            processing_time = time.time() - start_time
            
            logger.info("\n=====================================================")
            logger.info("处理完成")
            logger.info("=====================================================")
            logger.info(f"处理时间: {processing_time:.2f}秒")
            logger.info(f"有效聚类数: {len(valid_clusters)}")
            logger.info(f"噪声点数: {noise_points}")
            logger.info(f"规划路线数: {len(routes)}")
            
            return {
                "success": True,
                "processing_time": processing_time,
                "total_requests": len(requests),
                "valid_clusters": len(valid_clusters),
                "noise_points": noise_points,
                "planned_routes": len(routes),
                "clusters": clusters_data,
                "routes": routes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}")
            logger.error("详细错误信息:")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"处理请求时出错: {str(e)}",
                "clusters": {},
                "routes": {},
                "timestamp": datetime.now().isoformat()
            }
            
    def _validate_request(self, request: Dict[str, Any]) -> bool:
        """
        验证请求数据的完整性和格式
        
        参数:
            request: 请求数据
            
        返回:
            是否有效
        """
        try:
            # 检查必要字段
            required_fields = ['request_id', 'departure_time', 'origin', 'destination']
            for field in required_fields:
                if field not in request:
                    logger.error(f"请求缺少必要字段: {field}")
                    return False
            
            # 检查坐标格式
            for location in [request['origin'], request['destination']]:
                if not isinstance(location, dict) or 'lat' not in location or 'lng' not in location:
                    logger.error("请求的坐标格式错误")
                    return False
                    
                # 检查坐标范围
                lat, lng = location['lat'], location['lng']
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    logger.error(f"坐标超出有效范围: lat={lat}, lng={lng}")
                    return False
            
            # 检查时间格式
            try:
                datetime.fromisoformat(request['departure_time'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.error("出发时间格式错误")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证请求数据时出错: {str(e)}")
            return False

    def save_to_database(self, result: Dict[str, Any], db_connection) -> Dict[str, Any]:
        """
        将处理结果保存到数据库
        
        参数:
            result: 处理结果
            db_connection: 数据库连接
            
        返回:
            保存结果
        """
        if not result.get("success"):
            logger.error("无法保存失败的处理结果")
            return {
                "success": False,
                "error": "无法保存失败的处理结果"
            }
        
        try:
            # 开始事务
            with db_connection.begin():
                saved_plans = []
                
                # 为每个有效路线创建调度计划
                for cluster_id, route_data in result.get("routes", {}).items():
                    cluster_data = result["clusters"][cluster_id]
                    
                    # 准备调度计划数据
                    departure_time = datetime.fromisoformat(route_data["departure_time"].replace('Z', '+00:00'))
                    
                    # 路线数据
                    route_polyline = json.dumps({
                        'pickup_route': route_data['pickup_route']['polyline'],
                        'dropoff_route': route_data['dropoff_route']['polyline']
                    })
                    
                    # 保存调度计划
                    query = """
                        INSERT INTO dispatch_plan
                        (start_time, route_polyline, status, created_at)
                        VALUES (:start_time, :route_polyline, 'planned', CURRENT_TIMESTAMP)
                        RETURNING plan_id
                    """
                    
                    params = {
                        'start_time': departure_time,
                        'route_polyline': route_polyline
                    }
                    
                    # 执行插入
                    plan_result = db_connection.execute(query, params)
                    plan_id = plan_result.scalar()
                    
                    # 关联请求到调度计划
                    for trip in cluster_data['trips']:
                        db_connection.execute(
                            """
                            INSERT INTO request_dispatch_link
                            (request_id, plan_id)
                            VALUES (:request_id, :plan_id)
                            """,
                            {
                                'request_id': trip['request_id'],
                                'plan_id': plan_id
                            }
                        )
                    
                    saved_plans.append({
                        'plan_id': plan_id,
                        'cluster_id': cluster_id,
                        'trip_count': len(cluster_data['trips']),
                        'passenger_count': route_data['passenger_count'],
                        'departure_time': departure_time.isoformat()
                    })
                
                logger.info(f"成功保存 {len(saved_plans)} 个调度计划")
                
                return {
                    "success": True,
                    "saved_plans": saved_plans
                }
                
        except Exception as e:
            logger.error(f"保存到数据库时出错: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": f"保存到数据库时出错: {str(e)}"
            }

    def visualize_clusters(self, result: Dict[str, Any], output_file=None) -> Dict[str, Any]:
        """
        可视化聚类和路线规划结果
        
        参数:
            result: 处理结果
            output_file: 输出文件路径，如果为None则返回数据而不保存
            
        返回:
            可视化数据
        """
        if not result.get("success"):
            logger.error("无法可视化失败的处理结果")
            return {
                "success": False,
                "error": "无法可视化失败的处理结果"
            }
        
        try:
            visualization_data = {
                "clusters": [],
                "routes": [],
                "noise_points": []
            }
            
            # 处理每个聚类
            for cluster_id, cluster_data in result.get("clusters", {}).items():
                if cluster_id == -1:  # 噪声点
                    for trip in cluster_data.get('trips', []):
                        visualization_data["noise_points"].append({
                            "origin": trip['origin'],
                            "destination": trip['destination'],
                            "request_id": trip.get('request_id', '')
                        })
                else:  # 有效聚类
                    cluster_viz = {
                        "cluster_id": cluster_id,
                        "size": cluster_data['size'],
                        "center_origin": cluster_data.get('center_origin', {}),
                        "center_destination": cluster_data.get('center_destination', {}),
                        "time_range": cluster_data.get('time_range', {}),
                        "trips": []
                    }
                    
                    for trip in cluster_data.get('trips', []):
                        cluster_viz["trips"].append({
                            "origin": trip['origin'],
                            "destination": trip['destination'],
                            "request_id": trip.get('request_id', '')
                        })
                    
                    visualization_data["clusters"].append(cluster_viz)
            
            # 处理每条路线
            for cluster_id, route_data in result.get("routes", {}).items():
                route_viz = {
                    "cluster_id": cluster_id,
                    "pickup_polyline": route_data['pickup_route']['polyline'],
                    "dropoff_polyline": route_data['dropoff_route']['polyline'],
                    "total_distance": route_data['total_distance'],
                    "total_duration": route_data['total_duration'],
                    "passenger_count": route_data['passenger_count']
                }
                
                visualization_data["routes"].append(route_viz)
            
            # 如果指定了输出文件，保存可视化数据
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(visualization_data, f, ensure_ascii=False, indent=2)
                logger.info(f"可视化数据已保存到 {output_file}")
            
            return {
                "success": True,
                "visualization_data": visualization_data
            }
            
        except Exception as e:
            logger.error(f"生成可视化数据时出错: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": f"生成可视化数据时出错: {str(e)}"
            } 