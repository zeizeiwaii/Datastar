import time
import schedule
import threading
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import json
import logging

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入响应式调度系统
from algorithm.responsive_scheduler import ResponsiveScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/datastar")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建响应式调度系统实例
scheduler = ResponsiveScheduler(
    spatial_threshold=1.0,  # 1公里空间阈值
    time_window=30,         # 30分钟时间窗口
    min_samples=2,          # 最小2个样本形成聚类
    max_cluster_radius=5.0, # 最大聚类半径5公里
    max_points_per_route=8, # 每条路线最多8个点
    amap_key=os.getenv("AMAP_KEY")
)

def get_pending_requests():
    """获取未处理的出行请求"""
    db = SessionLocal()
    try:
        # 查询未被分配到调度计划的请求，移除时间窗口限制
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
        
        result = db.execute(query)
        
        requests = []
        for row in result:
            origin_json = json.loads(row.origin_location)
            dest_json = json.loads(row.destination_location)
            
            requests.append({
                'request_id': row.request_id,
                'origin_name': row.origin_name,
                'destination_name': row.destination_name,
                'departure_time': row.departure_time.isoformat(),
                'people_count': row.people_count,
                'origin': {
                    'lat': origin_json['coordinates'][1],
                    'lng': origin_json['coordinates'][0]
                },
                'destination': {
                    'lat': dest_json['coordinates'][1],
                    'lng': dest_json['coordinates'][0]
                },
                'submit_time': row.submit_time.isoformat()
            })
        
        return requests
    except Exception as e:
        logger.error(f"获取待处理请求失败: {str(e)}")
        return []
    finally:
        db.close()

def process_trips():
    """处理出行请求，生成调度计划"""
    logger.info("开始处理出行请求")
    
    # 获取未处理的请求
    requests = get_pending_requests()
    
    if not requests:
        logger.info("没有待处理的请求")
        return
    
    logger.info(f"找到 {len(requests)} 个待处理请求")
    
    try:
        # 使用响应式调度系统处理请求
        result = scheduler.process_requests(requests)
        
        if not result.get("success"):
            logger.error(f"处理请求失败: {result.get('error', '未知错误')}")
            return
        
        # 将处理结果保存到数据库
        db = SessionLocal()
        try:
            save_result = scheduler.save_to_database(result, db)
            
            if save_result.get("success"):
                saved_plans = save_result.get("saved_plans", [])
                logger.info(f"成功保存 {len(saved_plans)} 个调度计划")
                
                # 输出每个计划的详情
                for plan in saved_plans:
                    logger.info(f"调度计划 {plan['plan_id']}: {plan['trip_count']} 个请求, {plan['passenger_count']} 位乘客, 出发时间 {plan['departure_time']}")
            else:
                logger.error(f"保存调度计划失败: {save_result.get('error', '未知错误')}")
        finally:
            db.close()
        
        # 保存可视化数据（可选）
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualization_data")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(output_dir, f"viz_data_{timestamp}.json")
            
            viz_result = scheduler.visualize_clusters(result, output_file)
            
            if viz_result.get("success"):
                logger.info(f"可视化数据已保存到 {output_file}")
            else:
                logger.error(f"生成可视化数据失败: {viz_result.get('error', '未知错误')}")
        except Exception as e:
            logger.error(f"保存可视化数据时出错: {str(e)}")
            
    except Exception as e:
        logger.error(f"处理出行请求时出错: {str(e)}", exc_info=True)

def run_scheduler():
    """运行调度器"""
    logger.info("启动响应式公交调度系统")
    
    # 设置定时任务
    schedule.every(30).minutes.do(process_trips)  # 每30分钟运行一次
    
    # 立即运行一次
    process_trips()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 在单独的线程中运行调度器
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    logger.info("调度器已在后台启动")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，调度器正在退出...")
        # 清理操作
        schedule.clear()
        logger.info("调度器已退出") 