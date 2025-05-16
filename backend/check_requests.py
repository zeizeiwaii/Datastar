from models.database import engine
from sqlalchemy import text
import json

def check_user_requests():
    print("正在查询user_request表中的数据...")
    try:
        with engine.connect() as connection:
            # 查询user_request表中的所有记录
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
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("没有找到任何用户请求记录。")
                return
            
            print(f"找到 {len(rows)} 条用户请求记录：")
            print("-" * 100)
            
            # 打印表头
            print(f"{'ID':<5} | {'起点':<15} | {'终点':<15} | {'人数':<5} | {'出发时间':<20} | {'提交时间':<20} | {'起点坐标':<25} | {'终点坐标':<25}")
            print("-" * 100)
            
            # 打印数据行
            for row in rows:
                print(f"{row.request_id:<5} | {row.origin_name[:13]:<15} | {row.destination_name[:13]:<15} | {row.people_count:<5} | {str(row.departure_time):<20} | {str(row.submit_time):<20} | {row.origin_location_text:<25} | {row.destination_location_text:<25}")
            
            print("-" * 100)
            
            # 详细打印第一条记录（格式化显示）
            if rows:
                first_row = rows[0]
                print("\n最新记录详情:")
                print(f"请求ID: {first_row.request_id}")
                print(f"起点名称: {first_row.origin_name}")
                print(f"起点坐标: {first_row.origin_location_text}")
                print(f"终点名称: {first_row.destination_name}")
                print(f"终点坐标: {first_row.destination_location_text}")
                print(f"人数: {first_row.people_count}")
                print(f"出发时间: {first_row.departure_time}")
                print(f"提交时间: {first_row.submit_time}")
    
    except Exception as e:
        print(f"查询出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_requests() 