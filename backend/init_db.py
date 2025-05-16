from models.database import engine, Base, SessionLocal
from models.user import User
from models.trip import Trip
from models.route import Route
from models.vehicle import Vehicle
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import json
import os

def init_db():
    print("开始初始化数据库...")
    
    try:
        # 第一步：创建ORM模型对应的表
        print("创建ORM模型对应的表...")
        Base.metadata.create_all(bind=engine)
        print("ORM模型表创建完成")
        
        # 第二步：执行init.sql创建其他表和索引
        print("执行init.sql创建其他表和索引...")
        
        # 获取init.sql文件的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(current_dir, "init.sql")
        
        if not os.path.exists(sql_file_path):
            print(f"警告：SQL文件不存在: {sql_file_path}")
            return
        
        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # 连接到数据库并执行SQL
        with engine.connect() as connection:
            # 分割SQL语句并逐一执行
            statements = sql_script.split(';')
            for statement in statements:
                # 跳过空语句
                if statement.strip():
                    try:
                        print(f"执行SQL语句: {statement.strip()[:50]}...")
                        # 开启独立事务执行每条语句
                        with connection.begin():
                            connection.execute(text(statement))
                        print("SQL语句执行成功")
                    except Exception as e:
                        if "already exists" in str(e) or "已经存在" in str(e):
                            print(f"提示：表或索引已存在，继续执行...")
                        else:
                            print(f"SQL执行错误: {e}")
        
        print("SQL脚本执行完成")
        
        # 第三步：创建测试数据
        print("创建测试数据...")
        db = SessionLocal()
        try:
            # 检查是否已存在测试用户
            test_user = db.query(User).filter(User.username == "test_user").first()
            if not test_user:
                # 创建测试用户
                test_user = User(
                    username="test_user",
                    email="test@example.com",
                    hashed_password="test_password_hash",
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                print("测试用户创建成功")
            else:
                print("测试用户已存在")

            # 检查是否已存在测试车辆
            test_vehicle = db.query(Vehicle).filter(Vehicle.plate_number == "沪A12345").first()
            if not test_vehicle:
                # 创建测试车辆
                test_vehicle = Vehicle(
                    plate_number="沪A12345",
                    vehicle_type="bus",
                    capacity=30,
                    current_location={"lat": 31.2304, "lng": 121.4737},
                    status="available",
                    is_active=True
                )
                db.add(test_vehicle)
                db.commit()
                db.refresh(test_vehicle)
                print("测试车辆创建成功")
            else:
                print("测试车辆已存在")

            # 检查是否已存在测试行程
            test_trip = db.query(Trip).filter(
                Trip.user_id == test_user.id,
                Trip.origin_name == "上海火车站"
            ).first()
            
            if not test_trip:
                # 创建测试行程
                test_trip = Trip(
                    user_id=test_user.id,
                    origin_name="上海火车站",
                    destination_name="浦东国际机场",
                    origin_location="POINT(121.4737 31.2304)",
                    destination_location="POINT(121.8083 31.1443)",
                    passenger_count=2,
                    departure_time=datetime.now(),
                    status="pending"
                )
                db.add(test_trip)
                db.commit()
                print("测试行程创建成功")
            else:
                print("测试行程已存在")

        except Exception as e:
            print(f"创建测试数据出错: {e}")
            db.rollback()
        finally:
            db.close()
        
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化过程出错: {e}")

if __name__ == "__main__":
    print("直接执行init_db.py脚本...")
    init_db()
    print("数据库初始化完成。") 