# 响应式公交调度系统

本系统旨在为公交公司提供一种基于用户实时出行需求的"响应式公交调度系统"。用户可通过前端提交出行请求，公交公司依据用户需求、历史交通数据、高德地图API进行聚类分析和线路规划，并手动决定是否派出车辆，以实现临港区域的高效公共出行服务。

## 功能概述

### 用户端功能
- 提交出行需求：用户可以输入起点、终点、出发时间和人数
- 地点选择：基于高德地图POI接口进行模糊地点搜索
- 提交响应反馈：提交成功后给予提示

### 管理端功能
- 用户需求可视化：按时间段汇总展示需求
- 聚类分析：将半小时内的出行请求进行时间和空间聚类
- 路线规划：调用高德路线规划API获取建议线路，并基于历史交通数据进行优化
- 发车管理：查看推荐发车线路，确认或取消发车

## 技术架构

### 前端
- 框架：Vue 3 + Element Plus
- 地图服务：高德地图 JS API

### 后端
- API服务：FastAPI (Python)
- 数据库：PostgreSQL + PostGIS
- 算法服务：基于Python的聚类算法和路线规划
- 定时任务：基于schedule的调度模块

## 项目结构
```
.
├── frontend/                # 前端代码
│   ├── src/                 # 源代码
│   │   ├── api/             # API接口
│   │   ├── assets/          # 静态资源
│   │   ├── components/      # 组件
│   │   ├── router/          # 路由
│   │   ├── stores/          # 状态管理
│   │   ├── types/           # 类型定义
│   │   └── views/           # 页面
│   └── ...
├── backend/                 # 后端代码
│   ├── api/                 # API路由
│   ├── models/              # 数据模型
│   ├── server.js            # Express服务器
│   ├── main.py              # FastAPI应用入口
│   ├── scheduler.py         # 调度任务
│   └── ...
└── algorithm/               # 算法部分
    ├── clustering/          # 聚类算法
    ├── routing/             # 路线规划
    └── ...
```

## 数据库设计

系统使用PostgreSQL数据库，主要包含以下表：
- user_request：存储用户出行请求
- dispatch_plan：存储调度计划
- request_dispatch_link：请求-调度计划关联表
- traffic_evaluation：交通评价数据（延迟指数）

## 使用说明

### 用户端
1. 打开用户请求页面
2. 使用高德地图搜索选择起点和终点
3. 设置出发时间和人数
4. 提交请求
5. 等待公交公司确认发车

### 管理端
1. 查看仪表盘统计数据
2. 查看调度计划列表
3. 查看推荐路线详情
4. 确认发车或取消计划

## 系统流程
1. 用户提交出行请求，保存到数据库
2. 每30分钟触发一次调度计算
3. 系统获取未处理的请求，进行聚类分析
4. 对聚类结果，调用高德API进行路线规划
5. 将规划结果保存为调度计划
6. 管理员在管理界面查看并确认发车或取消

## 环境配置

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 后端
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 调度器
```bash
cd backend
python scheduler.py
```

## 开发注意事项

### 高德地图
- 需要创建高德地图开发者账号
- 申请Web端JS API开发密钥
- 在环境变量中配置AMAP_KEY

### 数据库
- 需要安装PostgreSQL数据库和PostGIS扩展
- 使用init.sql初始化数据库结构
- 设置数据库连接参数(.env文件)

## 未来改进方向
1. 实现用户账号系统和权限管理
2. 添加实时车辆位置跟踪功能
3. 加入机器学习模型预测出行需求
4. 优化路线规划算法，考虑更多约束因素
5. 开发移动端应用，提供更便捷的用户体验

## 聚类与路线规划算法

系统使用了增强版聚类和多路线规划算法，以实现更智能的响应式公交调度：

### 核心特性

1. **时空聚类**：结合时间窗口和空间距离的双重聚类
   - 默认30分钟时间窗口，1平方公里地理范围阈值
   - 支持对起点和终点同时进行聚类分析
   - 自动将超大聚类拆分为多个小聚类

2. **智能路线规划**：
   - 基于高德地图API进行最优路径规划
   - 自动优化途经点顺序，降低总行程距离
   - 支持接送两阶段路线规划模式

3. **配置灵活**：
   - 支持自定义聚类参数（时间窗口、空间阈值等）
   - 支持调整路线规划参数（最大点数、重试策略等）

### 算法流程

1. 获取未处理的出行请求
2. 按时间窗口（30分钟）对请求进行初步分组
3. 对每个时间组内的请求进行空间聚类
   - 首先按起点位置聚类
   - 然后按终点位置进一步聚类
4. 检查每个聚类的地理分布，如有必要进行拆分
5. 为每个有效聚类规划最优接送路线
6. 生成调度计划并保存到数据库

### 调度示例

假设系统处理了10个用户请求，30分钟时间窗口内，系统可能形成如下聚类：
- 聚类1：3个请求（A区域 → B区域）
- 聚类2：4个请求（C区域 → D区域）
- 聚类3：2个请求（E区域 → F区域）
- 噪声点：1个孤立请求（超出聚类范围）

系统将为每个聚类规划一条路线，每条路线包含：
1. 接乘客路线：从虚拟起点出发，依次接所有乘客
2. 送乘客路线：按最优顺序送所有乘客到目的地

更多算法细节请参考 [algorithm/README.md](algorithm/README.md)。

## 项目维护
- 定期备份数据库
- 监控系统运行状态
- 更新高德地图API版本
- 优化聚类参数和算法效率

## 高德地图API配置与错误处理

### USERKEY_PLAT_NOMATCH错误解决方案

如果遇到高德地图API返回"USERKEY_PLAT_NOMATCH"错误（错误码10009），这表明API Key与使用的平台类型不匹配。此错误的主要原因是在Web端使用了服务端的Key或在服务端使用了Web端的Key。

我们实施了以下解决方案：

#### 1. 创建统一配置文件
在`frontend/src/utils/amapConfig.ts`中配置两种不同用途的Key：

```typescript
// JS API相关配置 (用于地图组件、室内地图、地铁图等)
export const JS_API_KEY = "f3e49391bb7e88bfb311ecfaeefa1f8b";
export const SECURITY_JSCODE = "12987db7c703bb181705363cf67bfdbf";

// Web服务API相关配置 (用于HTTP REST API请求)
export const WEB_SERVICE_API_KEY = "ed5c583e14dfd33f5a6323b5d87491f";
```

#### 2. 使用Vite代理配置
在`vite.config.ts`中配置代理，避免跨域问题：

```typescript
server: {
  proxy: {
    '/amap-api': {
      target: 'https://restapi.amap.com',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/amap-api/, ''),
      headers: {
        'Referer': 'http://localhost:3000/'
      }
    }
  }
}
```

#### 3. 创建统一服务模块
在`frontend/src/utils/amapService.ts`中创建服务模块，根据不同API类型自动选择正确的Key：

```typescript
export const requestAmapAPI = async <T = any>(
  apiConfig: any,
  params: Record<string, any> = {}
): Promise<T> => {
  // 确定使用哪个Key
  const key = amapConfig.getApiKeyForService(apiConfig);
  // ... 发送请求逻辑
};
```

#### 4. 标记API类型
在配置中为每个API服务添加标记，指示是否使用Web服务的Key：

```typescript
API_CONFIG: {
  POI_SEARCH: {
    URL: USE_PROXY ? "/amap-api/v5/place/text" : "https://restapi.amap.com/v5/place/text",
    // ... 其他配置
    USE_WEB_SERVICE_KEY: true  // 标记使用Web服务Key
  }
}
```

#### 5. 安全密钥配置
为JavaScript SDK加载添加安全密钥：

```typescript
AMapLoader.load({
  key: amapConfig.JS_API_KEY,
  version: amapConfig.JS_API_CONFIG.VERSION,
  plugins: amapConfig.JS_API_CONFIG.PLUGINS,
  securityJsCode: amapConfig.SECURITY_JSCODE,
})
```

### 关键点说明

1. **两种不同的API Key**:
   - JS API Key: 用于地图组件、室内地图等JavaScript SDK功能
   - Web服务API Key: 用于周边搜索、路径规划等REST API服务

2. **安全密钥**: 高德地图JS API 2.0版本必须配置安全密钥，否则会报错

3. **错误码对照**:
   - 10009: USERKEY_PLAT_NOMATCH - API Key与平台不匹配
   - 10001: INVALID_USER_KEY - 无效的用户Key
   - 10002: SERVICE_NOT_AVAILABLE - 服务不可用
   - 30001: INVALID_SECURITY_CODE - 安全密钥无效或未配置

### 测试验证
使用`frontend/src/views/ProxyTestView.vue`页面可以测试不同API Key的功能和有效性。