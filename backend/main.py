from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.routes import user_routes, trip_routes, route_routes, vehicle_routes, request_routes, dispatch_routes
from api.route_planning import planning_routes

# 加载环境变量
load_dotenv()

# 设置高德地图API密钥
os.environ["AMAP_KEY"] = "ed5c583e14dfd33f75a6323b5d87491f"

# 初始化数据库
print("正在检查数据库表结构...")
try:
    from init_db import init_db
    init_db()
    print("数据库表初始化完成")
except Exception as e:
    print(f"数据库初始化出错: {e}")
    print("请检查数据库连接和权限配置")

# 创建FastAPI应用
app = FastAPI(
    title="响应式公交系统API",
    description="响应式公交系统的后端API服务",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 注册路由
app.include_router(user_routes)
app.include_router(trip_routes)
app.include_router(route_routes)
app.include_router(vehicle_routes)
app.include_router(request_routes)
app.include_router(dispatch_routes)
app.include_router(planning_routes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 