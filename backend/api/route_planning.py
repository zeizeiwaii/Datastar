from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models import Route, Trip, RequestDispatchLink  # 修改导入语句，移除不存在的 Vehicle 和 RouteTrip
from sqlalchemy import text
import json
import sys
import os
import logging
import traceback
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 在启动时记录路由注册信息
logger.info("=====================================")
logger.info("正在初始化路由规划API模块...")

# 导入算法相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from algorithm.responsive_scheduler import ResponsiveScheduler
    logger.info("成功导入ResponsiveScheduler")
    
    # 检查geopy是否安装
    try:
        import geopy
        logger.info("成功导入geopy")
    except ImportError:
        logger.error("缺少依赖包: geopy, 请运行 'pip install geopy'")
except Exception as e:
    logger.error(f"导入ResponsiveScheduler失败: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# 创建路由实例
planning_routes = APIRouter(prefix="/api/routes", tags=["routes"])
logger.info(f"创建APIRouter: prefix=/api/routes, tags=['routes']")

# 数据模型
class PlanningRequest(BaseModel):
    timeWindow: int
    spatialThreshold: float
    maxPointsPerRoute: int
    minSamples: int

class DispatchRequest(BaseModel):
    routeId: str
    clusterId: str
    planningResult: Dict[str, Any]

# 获取待处理的请求
@planning_routes.get("/pending")
async def get_pending_requests(db: Session = Depends(get_db)):
    logger.info("API调用: GET /routes/pending")
    try:
        # 移除时间窗口限制，查询所有未被分配到调度计划的请求
        query = text("""
            SELECT ur.request_id, ur.origin_name, ur.destination_name, 
                   ur.departure_time, ur.people_count,
                   ST_AsGeoJSON(ur.origin_location) as origin_location,
                   ST_AsGeoJSON(ur.destination_location) as destination_location,
                   ur.submit_time
            FROM user_request ur
            LEFT JOIN request_dispatch_link rdl ON ur.request_id = rdl.request_id
            WHERE rdl.id IS NULL
            ORDER BY ur.departure_time
        """)
        
        logger.info(f"执行SQL查询: {query}")
        result = db.execute(query)
        
        requests = []
        for row in result:
            try:
                # 解析地理位置JSON
                try:
                    origin_json = json.loads(row.origin_location)
                    dest_json = json.loads(row.destination_location)
                except json.JSONDecodeError as json_error:
                    logger.error(f"解析地理位置JSON失败，请求ID: {row.request_id}")
                    logger.error(f"origin_location: {row.origin_location}")
                    logger.error(f"destination_location: {row.destination_location}")
                    continue
                
                # 验证经纬度数据
                try:
                    origin_lat = float(origin_json['coordinates'][1])
                    origin_lng = float(origin_json['coordinates'][0])
                    dest_lat = float(dest_json['coordinates'][1])
                    dest_lng = float(dest_json['coordinates'][0])
                    
                    # 检查经纬度范围
                    if not (-90 <= origin_lat <= 90 and -180 <= origin_lng <= 180 and
                           -90 <= dest_lat <= 90 and -180 <= dest_lng <= 180):
                        logger.error(f"经纬度超出有效范围，请求ID: {row.request_id}")
                        logger.error(f"origin: ({origin_lat}, {origin_lng})")
                        logger.error(f"destination: ({dest_lat}, {dest_lng})")
                        continue
                except (IndexError, ValueError) as coord_error:
                    logger.error(f"提取经纬度失败，请求ID: {row.request_id}")
                    logger.error(str(coord_error))
                    continue
                
                # 构建请求数据
                request_data = {
                    'request_id': row.request_id,
                    'origin_name': row.origin_name,
                    'destination_name': row.destination_name,
                    'departure_time': row.departure_time.isoformat(),
                    'people_count': row.people_count,
                    'origin': {
                        'lat': origin_lat,
                        'lng': origin_lng
                    },
                    'destination': {
                        'lat': dest_lat,
                        'lng': dest_lng
                    },
                    'submit_time': row.submit_time.isoformat()
                }
                requests.append(request_data)
                
            except Exception as row_error:
                logger.error(f"处理查询结果行时出错，请求ID: {row.request_id}")
                logger.error(str(row_error))
                logger.error(traceback.format_exc())
                continue
        
        # 记录所有请求及其状态，帮助诊断
        try:
            status_query = text("""
                SELECT 
                    ur.request_id, 
                    ur.departure_time,
                    CASE WHEN rdl.id IS NULL THEN '未分配' ELSE '已分配' END as status,
                    dp.plan_id,
                    dp.status as plan_status
                FROM 
                    user_request ur
                LEFT JOIN 
                    request_dispatch_link rdl ON ur.request_id = rdl.request_id
                LEFT JOIN 
                    dispatch_plan dp ON rdl.plan_id = dp.plan_id
                ORDER BY 
                    ur.departure_time
            """)
            
            status_result = db.execute(status_query)
            logger.info("所有请求的状态:")
            
            for row in status_result:
                logger.info(f"请求ID: {row.request_id}, 出发时间: {row.departure_time}, 状态: {row.status}, 计划ID: {row.plan_id}, 计划状态: {row.plan_status}")
        except Exception as status_error:
            logger.error(f"获取请求状态时出错: {str(status_error)}")
        
        logger.info(f"查询结果: 找到 {len(requests)} 个待处理请求")
        return {"success": True, "data": requests, "count": len(requests)}
        
    except Exception as e:
        logger.error(f"获取待处理请求失败: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": f"获取待处理请求失败: {str(e)}", "data": [], "count": 0}

# 路线规划
@planning_routes.post("/plan")
async def plan_routes(request: PlanningRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"收到路线规划请求: {request}")
        
        # 获取待处理的出行请求
        pending_trips = db.query(Trip).filter(Trip.status == 'pending').all()
        if not pending_trips:
            return {"success": False, "message": "没有待处理的出行请求"}
            
        # 转换数据格式
        formatted_requests = []
        for trip in pending_trips:
            try:
                # 从地理位置字段中提取经纬度
                origin_location = db.scalar(text("SELECT ST_AsGeoJSON(origin_location) FROM user_request WHERE request_id = :id"), {'id': trip.id})
                destination_location = db.scalar(text("SELECT ST_AsGeoJSON(destination_location) FROM user_request WHERE request_id = :id"), {'id': trip.id})
                
                # 解析地理位置JSON
                origin_json = json.loads(origin_location)
                dest_json = json.loads(destination_location)
                
                # 提取经纬度
                origin_lat = float(origin_json['coordinates'][1])
                origin_lng = float(origin_json['coordinates'][0])
                dest_lat = float(dest_json['coordinates'][1])
                dest_lng = float(dest_json['coordinates'][0])
                
                formatted_requests.append({
                    'request_id': trip.id,
                    'origin_name': trip.origin_name,
                    'destination_name': trip.destination_name,
                    'departure_time': trip.departure_time.isoformat(),
                    'people_count': trip.passenger_count,
                    'origin': {
                        'lat': origin_lat,
                        'lng': origin_lng,
                        'name': trip.origin_name
                    },
                    'destination': {
                        'lat': dest_lat,
                        'lng': dest_lng,
                        'name': trip.destination_name
                    },
                    'submit_time': trip.created_at.isoformat() if trip.created_at else datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"处理请求 {trip.id} 时出错: {str(e)}")
                continue
            
        # 初始化调度器
        scheduler = ResponsiveScheduler(
            spatial_threshold=request.spatialThreshold,
            time_window=request.timeWindow,
            min_samples=request.minSamples,
            max_points_per_route=request.maxPointsPerRoute,
            max_cluster_radius=request.spatialThreshold * 2,  # 设置为空间阈值的2倍
            amap_key=os.getenv("AMAP_KEY")  # 从环境变量获取高德地图API密钥
        )
        
        # 执行路线规划
        planning_result = scheduler.process_requests(formatted_requests)
        
        if not planning_result or not planning_result.get('routes'):
            return {"success": False, "message": "路线规划失败"}
            
        # 保存规划结果到数据库
        saved_routes = []
        for route_id, route_data in planning_result['routes'].items():
            try:
                # 确保路线数据包含必要的字段
                pickup_route = route_data.get('pickup_route', {})
                dropoff_route = route_data.get('dropoff_route', {})
                
                # 创建新的路线记录
                route = Route(
                    path=json.dumps({
                        'pickup_route': {
                            'polyline': pickup_route.get('polyline', []),
                            'path': pickup_route.get('path', []),
                            'stops': pickup_route.get('stops', []),
                            'distance': pickup_route.get('distance', 0),
                            'duration': pickup_route.get('duration', 0),
                            'steps': pickup_route.get('steps', [])
                        },
                        'dropoff_route': {
                            'polyline': dropoff_route.get('polyline', []),
                            'path': dropoff_route.get('path', []),
                            'stops': dropoff_route.get('stops', []),
                            'distance': dropoff_route.get('distance', 0),
                            'duration': dropoff_route.get('duration', 0),
                            'steps': dropoff_route.get('steps', [])
                        }
                    }),
                    status='planned',
                    start_time=datetime.now()  # 设置一个默认的开始时间
                )
                db.add(route)
                
                # 更新相关出行请求的状态
                cluster = planning_result['clusters'].get(route_id)
                if cluster and cluster.get('trips'):
                    for trip_data in cluster['trips']:
                        trip = db.query(Trip).filter(Trip.id == trip_data['request_id']).first()
                        if trip:
                            trip.status = 'clustered'
                            trip.cluster_id = int(route_id)
                            route.trips.append(trip)
                
                saved_routes.append(route)
                
                # 记录路线信息
                logger.info(f"保存路线 {route_id}:")
                logger.info(f"- 接乘客路线: {len(pickup_route.get('polyline', []))} 个坐标点")
                logger.info(f"- 送乘客路线: {len(dropoff_route.get('polyline', []))} 个坐标点")
                
            except Exception as e:
                logger.error(f"保存路线 {route_id} 时出错: {str(e)}")
                continue
        
        try:
            db.commit()
            logger.info(f"成功保存 {len(saved_routes)} 条路线到数据库")
        except Exception as e:
            db.rollback()
            logger.error(f"提交数据库事务时出错: {str(e)}")
            return {"success": False, "message": "保存路线数据失败"}
        
        # 返回规划结果
        return {
            "success": True,
            "message": "路线规划成功",
            "data": planning_result
        }
        
    except Exception as e:
        logger.error(f"路线规划出错: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"路线规划失败: {str(e)}"}

logger.info("路由规划API模块初始化完成")
logger.info("=====================================")

# 确认调度计划
@planning_routes.post("/dispatch")
async def dispatch_route(dispatch_request: DispatchRequest, db: Session = Depends(get_db)):
    try:
        route_id = dispatch_request.routeId
        cluster_id = dispatch_request.clusterId
        planning_result = dispatch_request.planningResult
        
        logger.info(f"确认发车: 路线ID={route_id}, 聚类ID={cluster_id}")
        
        # 获取聚类和路线数据
        if (not planning_result or 
            not planning_result.get("clusters") or 
            not planning_result.get("routes")):
            return {"success": False, "message": "规划结果数据不完整"}
        
        cluster_data = planning_result["clusters"].get(cluster_id)
        route_data = planning_result["routes"].get(route_id)
        
        if not cluster_data or not route_data:
            return {"success": False, "message": "找不到对应的聚类或路线数据"}
        
        # 准备路线折线数据（用于地图显示）
        route_polyline = json.dumps({
            'pickup_route': route_data['pickup_route']['polyline'],
            'dropoff_route': route_data['dropoff_route']['polyline']
        })
        
        # 获取出发时间
        departure_time = datetime.fromisoformat(route_data["departure_time"].replace('Z', '+00:00'))
        
        # 开始事务
        try:
            # 保存调度计划
            plan_query = text("""
                INSERT INTO dispatch_plan
                (route_polyline, status, start_time, created_at)
                VALUES (:route_polyline, 'planned', :start_time, CURRENT_TIMESTAMP)
                RETURNING plan_id
            """)
            
            params = {
                'route_polyline': route_polyline,
                'start_time': departure_time if departure_time else datetime.now()
            }
            
            # 执行插入
            plan_result = db.execute(plan_query, params)
            plan_id = plan_result.scalar()
            
            # 关联请求到调度计划
            for trip in cluster_data['trips']:
                link_query = text("""
                    INSERT INTO request_dispatch_link
                    (request_id, plan_id)
                    VALUES (:request_id, :plan_id)
                """)
                
                db.execute(link_query, {
                    'request_id': trip['request_id'],
                    'plan_id': plan_id
                })
            
            db.commit()
            
            logger.info(f"调度计划已创建，ID={plan_id}, 包含{len(cluster_data['trips'])}个请求")
            
            return {
                "success": True, 
                "message": "已成功创建调度计划", 
                "plan_id": plan_id,
                "trip_count": len(cluster_data['trips'])
            }
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"保存调度计划失败: {str(db_error)}")
            logger.error(traceback.format_exc())
            return {"success": False, "message": f"保存调度计划失败: {str(db_error)}"}
        
    except Exception as e:
        logger.error(f"提交调度计划失败: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"提交调度计划失败: {str(e)}"} 