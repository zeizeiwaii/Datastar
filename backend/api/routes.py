from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models.trip import Trip as TripModel
from models.user import User as UserModel
from fastapi.responses import JSONResponse
from sqlalchemy import text

# 创建路由实例
user_routes = APIRouter(prefix="/users", tags=["users"])
trip_routes = APIRouter(prefix="/trips", tags=["trips"])
route_routes = APIRouter(prefix="/routes", tags=["routes"])
vehicle_routes = APIRouter(prefix="/vehicles", tags=["vehicles"])
request_routes = APIRouter(prefix="/request", tags=["request"])
dispatch_routes = APIRouter(prefix="/dispatch", tags=["dispatch"])

# 数据模型
class User(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class Trip(BaseModel):
    id: int
    user: Optional[User] = None
    origin: dict
    destination: dict
    departure_time: datetime
    status: str
    cluster_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Route(BaseModel):
    id: int
    name: str
    vehicle_id: int
    stops: List[str]
    distance: float
    estimated_time: int
    status: str

class Vehicle(BaseModel):
    id: int
    plate_number: str
    capacity: int
    status: str
    current_location: Optional[str] = None

class RequestData(BaseModel):
    origin: str
    destination: str
    departureTime: str
    peopleCount: int
    originLocation: Dict[str, float]
    destinationLocation: Dict[str, float]

# 用户路由
@user_routes.get("/")
async def get_users():
    return {"message": "获取用户列表"}

# 行程路由
@trip_routes.get("/")
async def get_trips(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    try:
        # 计算偏移量
        offset = (page - 1) * size
        
        # 获取总数
        total = db.query(TripModel).count()
        
        # 获取分页数据
        trips = db.query(TripModel).offset(offset).limit(size).all()
        
        return {
            "items": trips,
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 路线路由
@route_routes.get("/")
async def get_routes(page: int = 1, size: int = 10):
    return {"message": "获取路线列表"}

# 车辆路由
@vehicle_routes.get("/")
async def get_vehicles():
    return {"message": "获取车辆列表"}

# 获取所有出行请求
@request_routes.get("/listRequests")
async def list_requests(db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT 
                request_id, 
                origin_name, 
                destination_name, 
                people_count, 
                departure_time,
                submit_time,
                ST_AsText(origin_location) as origin_location_text,
                ST_AsText(destination_location) as destination_location_text
            FROM 
                user_request
            ORDER BY 
                submit_time DESC;
        """)
        
        result = db.execute(query)
        requests = []
        
        for row in result:
            requests.append({
                "request_id": row.request_id,
                "origin_name": row.origin_name,
                "destination_name": row.destination_name,
                "people_count": row.people_count,
                "departure_time": row.departure_time.isoformat() if row.departure_time else None,
                "submit_time": row.submit_time.isoformat() if row.submit_time else None,
                "origin_location": row.origin_location_text,
                "destination_location": row.destination_location_text
            })
        
        return {"success": True, "data": requests, "count": len(requests)}
    
    except Exception as e:
        print(f"获取请求列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取请求列表失败: {str(e)}")

# 提交出行请求
@request_routes.post("/submitRequest")
async def submit_request(request_data: RequestData, db: Session = Depends(get_db)):
    try:
        # 检查user_request表是否存在，如果不存在则创建
        try:
            check_table_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_request'
                );
            """)
            result = db.execute(check_table_query)
            table_exists = result.scalar()
            
            if not table_exists:
                print("user_request表不存在，尝试创建...")
                # 创建表的SQL语句
                create_table_query = text("""
                    -- 启用PostGIS扩展
                    CREATE EXTENSION IF NOT EXISTS postgis;
                    
                    -- 创建用户出行请求表
                    CREATE TABLE IF NOT EXISTS user_request (
                        request_id SERIAL PRIMARY KEY,
                        origin_name TEXT NOT NULL,
                        origin_location GEOGRAPHY(Point) NOT NULL,
                        destination_name TEXT NOT NULL,
                        destination_location GEOGRAPHY(Point) NOT NULL,
                        people_count INTEGER NOT NULL,
                        departure_time TIMESTAMP NOT NULL,
                        submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- 创建空间索引
                    CREATE INDEX IF NOT EXISTS idx_user_request_origin ON user_request USING GIST(origin_location);
                    CREATE INDEX IF NOT EXISTS idx_user_request_destination ON user_request USING GIST(destination_location);
                    
                    -- 创建时间索引
                    CREATE INDEX IF NOT EXISTS idx_user_request_departure_time ON user_request(departure_time);
                    CREATE INDEX IF NOT EXISTS idx_user_request_submit_time ON user_request(submit_time);
                """)
                
                # 执行创建表操作
                db.execute(create_table_query)
                db.commit()
                print("user_request表创建成功")
        except Exception as table_check_error:
            print(f"检查和创建表失败: {table_check_error}")
            # 继续执行，让后续代码返回更具体的错误信息
        
        # 打印接收到的请求数据，方便调试
        print("="*50)
        print(f"接收到的请求数据: {request_data}")
        print("="*50)
        
        # 处理日期时间格式
        departure_time = request_data.departureTime
        try:
            # 尝试解析ISO格式日期时间
            parsed_time = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            departure_time = parsed_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"解析后的日期时间: {departure_time}")
        except Exception as e:
            print(f"日期解析失败，使用原始值: {e}")
            # 保持原始值不变
        
        # 准备地理位置数据
        origin_lng = float(request_data.originLocation["lng"])
        origin_lat = float(request_data.originLocation["lat"])
        dest_lng = float(request_data.destinationLocation["lng"])
        dest_lat = float(request_data.destinationLocation["lat"])
        
        print(f"起点坐标: {origin_lng}, {origin_lat}")
        print(f"终点坐标: {dest_lng}, {dest_lat}")
        
        try:
            # 尝试方法1: 使用参数化查询
            query = text("""
                INSERT INTO user_request 
                (origin_name, origin_location, destination_name, destination_location, people_count, departure_time)
                VALUES (:origin, 
                        ST_SetSRID(ST_MakePoint(:origin_lng, :origin_lat), 4326),
                        :destination, 
                        ST_SetSRID(ST_MakePoint(:dest_lng, :dest_lat), 4326),
                        :people_count, 
                        :departure_time)
                RETURNING request_id
            """)
            
            params = {
                "origin": request_data.origin,
                "origin_lng": origin_lng,
                "origin_lat": origin_lat,
                "destination": request_data.destination,
                "dest_lng": dest_lng,
                "dest_lat": dest_lat,
                "people_count": request_data.peopleCount,
                "departure_time": departure_time
            }
            print("方法1 - 参数化查询:")
            print(f"SQL参数: {params}")
            
            result = db.execute(query, params)
            request_id = result.scalar()
            db.commit()
            
            print(f"请求提交成功，ID: {request_id}")
            return JSONResponse(content={
                "success": True,
                "requestId": request_id,
                "message": "出行请求已成功提交"
            })
            
        except Exception as sql_error:
            db.rollback()
            print(f"方法1失败: {sql_error}")
            import traceback
            traceback.print_exc()
            
            try:
                # 尝试方法2: 使用原始SQL (小心SQL注入)
                print("方法2 - 直接SQL:")
                # 清理输入以减少SQL注入风险
                origin_name = request_data.origin.replace("'", "''")
                destination_name = request_data.destination.replace("'", "''")
                
                direct_query = text(f"""
                    INSERT INTO user_request 
                    (origin_name, origin_location, destination_name, destination_location, people_count, departure_time)
                    VALUES (
                        '{origin_name}', 
                        ST_SetSRID(ST_MakePoint({origin_lng}, {origin_lat}), 4326), 
                        '{destination_name}', 
                        ST_SetSRID(ST_MakePoint({dest_lng}, {dest_lat}), 4326), 
                        {request_data.peopleCount}, 
                        '{departure_time}'
                    )
                    RETURNING request_id
                """)
                print(f"SQL查询: {direct_query}")
                
                result = db.execute(direct_query)
                request_id = result.scalar()
                db.commit()
                
                print(f"请求提交成功(备用方法)，ID: {request_id}")
                return JSONResponse(content={
                    "success": True,
                    "requestId": request_id,
                    "message": "出行请求已成功提交(备用方法)"
                })
                
            except Exception as direct_sql_error:
                db.rollback()
                print(f"方法2失败: {direct_sql_error}")
                traceback.print_exc()
                
                try:
                    # 尝试方法3: 使用最简单的测试插入
                    test_query = text("""
                        INSERT INTO user_request 
                        (origin_name, destination_name, people_count, departure_time,
                         origin_location, destination_location)
                        VALUES (
                            '测试起点', 
                            '测试终点', 
                            1,
                            CURRENT_TIMESTAMP,
                            ST_SetSRID(ST_MakePoint(121.5, 31.2), 4326),
                            ST_SetSRID(ST_MakePoint(121.6, 31.3), 4326)
                        )
                        RETURNING request_id
                    """)
                    print("方法3 - 测试插入:")
                    print(f"SQL查询: {test_query}")
                    
                    result = db.execute(test_query)
                    request_id = result.scalar()
                    db.commit()
                    
                    print(f"测试插入成功，ID: {request_id}")
                    error_msg = "用户数据插入失败，但测试插入成功。可能是数据格式问题。"
                    print(error_msg)
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": error_msg
                        }
                    )
                    
                except Exception as test_error:
                    db.rollback()
                    print(f"方法3失败: {test_error}")
                    traceback.print_exc()
                    
                    # 所有方法都失败了
                    error_msg = f"数据库操作失败: {str(test_error)}"
                    print(error_msg)
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": error_msg
                        }
                    )
                
                error_msg = f"SQL执行失败: {str(direct_sql_error)}"
                print(error_msg)
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": error_msg
                    }
                )
            
            error_msg = f"参数化SQL执行失败: {str(sql_error)}"
            print(error_msg)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": error_msg
                }
            )
        
    except Exception as e:
        db.rollback()
        print(f"整体处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 尝试确定具体错误类型，提供更友好的错误信息
        error_message = str(e)
        if "postgis" in error_message.lower():
            error_message = "PostGIS扩展错误，请确保数据库已正确安装PostGIS扩展"
        elif "syntax error" in error_message.lower():
            error_message = "SQL语法错误，请检查查询语句"
        elif "violates not-null constraint" in error_message.lower():
            error_message = "必填字段为空，请确保所有必填字段都已提供"
        elif "date/time" in error_message.lower() or "timestamp" in error_message.lower():
            error_message = "日期时间格式错误，请使用正确的格式"
        elif "parameter" in error_message.lower() and "bind" in error_message.lower():
            error_message = "SQL参数绑定错误，请检查参数格式"
        elif "f405" in error_message.lower():
            error_message = "SQL参数绑定错误，PostGIS函数参数格式不正确"
            
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"提交请求失败: {error_message}"
            }
        )

# 获取仪表盘统计数据
@dispatch_routes.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        # 获取今日需求总数
        total_requests_query = text("""
            SELECT COUNT(*) FROM user_request 
            WHERE DATE(submit_time) = CURRENT_DATE
        """)
        total_requests = db.execute(total_requests_query).scalar()
        
        # 获取待确认调度数量
        pending_plans_query = text("""
            SELECT COUNT(*) FROM dispatch_plan 
            WHERE status = 'planned'
        """)
        pending_plans = db.execute(pending_plans_query).scalar()
        
        # 获取已发车数量
        confirmed_plans_query = text("""
            SELECT COUNT(*) FROM dispatch_plan 
            WHERE status = 'confirmed'
        """)
        confirmed_plans = db.execute(confirmed_plans_query).scalar()
        
        return {
            "totalRequests": total_requests or 0,
            "pendingPlans": pending_plans or 0,
            "confirmedPlans": confirmed_plans or 0
        }
    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")

# 获取调度计划列表
@dispatch_routes.get("/plans")
async def get_dispatch_plans(db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT dp.plan_id, dp.vehicle_id, dp.start_time, dp.status, dp.created_at,
                   COUNT(rdl.request_id) as request_count
            FROM dispatch_plan dp
            LEFT JOIN request_dispatch_link rdl ON dp.plan_id = rdl.plan_id
            GROUP BY dp.plan_id
            ORDER BY dp.created_at DESC
        """)
        
        result = db.execute(query)
        plans = []
        
        for row in result:
            plans.append({
                "plan_id": row.plan_id,
                "vehicle_id": row.vehicle_id,
                "start_time": row.start_time.isoformat() if row.start_time else None,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "request_count": row.request_count
            })
            
        return plans
    except Exception as e:
        print(f"获取调度计划列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取调度计划列表失败")

# 获取调度计划详情
@dispatch_routes.get("/plan/{plan_id}")
async def get_dispatch_plan_detail(plan_id: int, db: Session = Depends(get_db)):
    try:
        # 获取计划基本信息
        plan_query = text("""
            SELECT dp.* FROM dispatch_plan dp
            WHERE dp.plan_id = :plan_id
        """)
        
        plan_result = db.execute(plan_query, {"plan_id": plan_id}).fetchone()
        
        if not plan_result:
            raise HTTPException(status_code=404, detail="调度计划不存在")
        
        # 获取请求信息
        requests_query = text("""
            SELECT ur.*, 
                   ST_AsGeoJSON(ur.origin_location) as origin_location_json,
                   ST_AsGeoJSON(ur.destination_location) as destination_location_json
            FROM user_request ur
            JOIN request_dispatch_link rdl ON ur.request_id = rdl.request_id
            WHERE rdl.plan_id = :plan_id
        """)
        
        requests_result = db.execute(requests_query, {"plan_id": plan_id})
        
        # 构建响应
        import json
        
        plan_data = {
            "plan_id": plan_result.plan_id,
            "vehicle_id": plan_result.vehicle_id,
            "start_time": plan_result.start_time.isoformat() if plan_result.start_time else None,
            "status": plan_result.status,
            "created_at": plan_result.created_at.isoformat() if plan_result.created_at else None,
            "route_polyline": plan_result.route_polyline
        }
        
        requests = []
        for req in requests_result:
            origin_location = json.loads(req.origin_location_json)
            destination_location = json.loads(req.destination_location_json)
            
            requests.append({
                "request_id": req.request_id,
                "origin_name": req.origin_name,
                "destination_name": req.destination_name,
                "people_count": req.people_count,
                "departure_time": req.departure_time.isoformat() if req.departure_time else None,
                "submit_time": req.submit_time.isoformat() if req.submit_time else None,
                "origin_location": {
                    "lng": origin_location["coordinates"][0],
                    "lat": origin_location["coordinates"][1]
                },
                "destination_location": {
                    "lng": destination_location["coordinates"][0],
                    "lat": destination_location["coordinates"][1]
                }
            })
        
        plan_data["requests"] = requests
        
        return plan_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取调度计划详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取调度计划详情失败")

# 确认发车
@dispatch_routes.post("/confirm/{plan_id}")
async def confirm_dispatch(plan_id: int, db: Session = Depends(get_db)):
    try:
        query = text("""
            UPDATE dispatch_plan
            SET status = 'confirmed'
            WHERE plan_id = :plan_id AND status = 'planned'
            RETURNING plan_id
        """)
        
        result = db.execute(query, {"plan_id": plan_id})
        updated_plan_id = result.scalar()
        
        if not updated_plan_id:
            raise HTTPException(status_code=404, detail="计划不存在或已经被确认")
            
        db.commit()
        
        return {"success": True, "message": "已确认发车"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"确认发车失败: {str(e)}")
        raise HTTPException(status_code=500, detail="确认发车失败")

# 取消计划
@dispatch_routes.post("/cancel/{plan_id}")
async def cancel_dispatch(plan_id: int, db: Session = Depends(get_db)):
    try:
        query = text("""
            UPDATE dispatch_plan
            SET status = 'cancelled'
            WHERE plan_id = :plan_id AND status = 'planned'
            RETURNING plan_id
        """)
        
        result = db.execute(query, {"plan_id": plan_id})
        updated_plan_id = result.scalar()
        
        if not updated_plan_id:
            raise HTTPException(status_code=404, detail="计划不存在或已经被取消")
            
        db.commit()
        
        return {"success": True, "message": "已取消计划"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"取消计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="取消计划失败") 