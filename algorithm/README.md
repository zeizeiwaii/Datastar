# 响应式公交调度算法

本目录包含响应式公交调度系统的核心算法组件，包括空间时间聚类算法和多路线规划算法。

## 目录结构

```
algorithm/
  ├── clustering/        # 聚类算法
  │   ├── trip_clustering.py      # 基础聚类算法
  │   └── enhanced_clustering.py  # 增强版聚类算法
  ├── routing/           # 路线规划算法
  │   ├── route_planner.py        # 基础路线规划
  │   └── multi_route_planner.py  # 多路线规划器
  ├── decision/          # 决策支持
  └── responsive_scheduler.py    # 响应式调度系统集成
```

## 核心功能

1. **时空聚类**：对用户出行请求按时间窗口和空间距离进行聚类
2. **多路线规划**：根据聚类结果，规划最优接送路线
3. **需求分析**：分析聚类后的需求分布，提供决策支持

## 使用指南

### 响应式调度系统

`ResponsiveScheduler` 类集成了聚类和路线规划功能，是系统的主要入口：

```python
from algorithm.responsive_scheduler import ResponsiveScheduler

# 创建调度器实例
scheduler = ResponsiveScheduler(
    spatial_threshold=1.0,  # 1公里空间阈值
    time_window=30,         # 30分钟时间窗口
    min_samples=2,          # 最小2个样本形成聚类
    max_cluster_radius=5.0, # 最大聚类半径5公里
    max_points_per_route=8, # 每条路线最多8个点
    amap_key="您的高德地图API密钥"  # 可选，也可从环境变量读取
)

# 处理出行请求
requests = [
    {
        'request_id': 1,
        'origin_name': '起点名称',
        'destination_name': '终点名称',
        'departure_time': '2023-11-23T10:00:00',
        'people_count': 1,
        'origin': {
            'lat': 31.230416,
            'lng': 121.473701
        },
        'destination': {
            'lat': 31.219456,
            'lng': 121.456297
        }
    },
    # 更多请求...
]

# 处理请求并获取结果
result = scheduler.process_requests(requests)

# 可视化结果
viz_result = scheduler.visualize_clusters(result, "output_visualization.json")

# 保存结果到数据库
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("数据库连接URL")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

save_result = scheduler.save_to_database(result, db)
```

### 参数说明

#### ResponsiveScheduler 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| spatial_threshold | float | 1.0 | 空间距离阈值（公里），决定了聚类的空间范围 |
| time_window | int | 30 | 时间窗口（分钟），决定了聚类的时间范围 |
| min_samples | int | 2 | 最小样本数，形成有效聚类的最少请求数 |
| max_cluster_radius | float | 5.0 | 最大聚类半径（公里），限制聚类的最大空间范围 |
| max_points_per_route | int | 8 | 每条路线最大点数，超过这个数量的聚类会被拆分 |
| amap_key | str | None | 高德地图API密钥，如果为None则从环境变量AMAP_KEY读取 |

#### 输入请求格式

每个请求必须包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| request_id | int | 请求ID |
| origin_name | str | 起点名称 |
| destination_name | str | 终点名称 |
| departure_time | str | 出发时间，ISO格式，如"2023-11-23T10:00:00" |
| people_count | int | 人数 |
| origin | dict | 起点坐标，包含lat（纬度）和lng（经度） |
| destination | dict | 终点坐标，包含lat（纬度）和lng（经度） |

#### 输出结果格式

处理结果包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 处理是否成功 |
| processing_time | float | 处理耗时（秒） |
| total_requests | int | 总请求数 |
| valid_clusters | int | 有效聚类数 |
| noise_points | int | 噪声点数（未能形成聚类的点） |
| planned_routes | int | 规划的路线数 |
| clusters | dict | 聚类信息 |
| routes | dict | 路线信息 |
| timestamp | str | 处理时间戳 |

## 算法说明

### 增强版聚类算法

增强版聚类算法结合时间和空间两个维度，实现了以下功能：

1. **时间窗口分组**：首先按照时间窗口（默认30分钟）将请求分组
2. **双重空间聚类**：对每个时间组内的请求先按起点聚类，再按终点聚类
3. **大型聚类拆分**：将超过最大点数的聚类拆分为多个小聚类
4. **距离约束检查**：确保每个聚类内所有点距离都小于最大聚类半径

### 多路线规划器

多路线规划器通过调用高德地图API，为每个聚类规划最优的接送路线：

1. **途经点优化**：使用贪心算法优化途经点访问顺序，减少总行程距离
2. **分段规划**：处理超过API限制的大量途经点，通过分段规划并合并结果
3. **双阶段规划**：接送路线分为两个阶段 - 接乘客阶段和送乘客阶段
4. **效率分析**：计算路线效率指标，如平均成本、总距离、总时间等

## 环境依赖

- Python 3.8+
- 核心库依赖:
  - numpy
  - scikit-learn
  - pandas
  - requests
  - geopy

## 高德地图API配置

需要在环境变量或创建调度器时提供高德地图API密钥(AMAP_KEY)。

申请高德地图API密钥的步骤：
1. 注册高德地图开发者账号
2. 创建应用，获取API密钥(Key)
3. 开通路径规划和地点搜索服务权限

## 问题排查

常见问题及解决方案：

1. **无法形成有效聚类**：尝试调整`spatial_threshold`和`time_window`参数
2. **聚类过大**：降低`max_cluster_radius`或`max_points_per_route`参数
3. **路线规划失败**：检查API密钥是否有效，以及网络连接状态
4. **API调用限制**：增加重试间隔`sleep_time`参数 