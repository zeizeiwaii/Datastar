下面是一份**响应式公交系统软件**的**ER 图（实体-关系模型）文本版本**，由一名专业数据库设计人员的视角整理而成。文本 ER 图主要包括实体（Entity）、属性（Attributes）、主键（PK）、外键（FK）及它们之间的关系说明。

---

# 🧩 文本版 ER 图：响应式公交系统软件

---

## 1️⃣ 实体：UserRequest（用户出行请求）

| 字段名                   | 类型                      | 描述         | 约束            |
| --------------------- | ----------------------- | ---------- | ------------- |
| request\_id           | UUID / SERIAL           | cd请求唯一标识     | PK            |
| origin\_name          | TEXT                    | 起点名称（地名）   | NOT NULL      |
| origin\_location      | GEOGRAPHY(Point) / JSON | 起点经纬度      | NOT NULL      |
| destination\_name     | TEXT                    | 终点名称       | NOT NULL      |
| destination\_location | GEOGRAPHY(Point) / JSON | 终点经纬度      | NOT NULL      |
| people\_count         | INT                     | 预计人数       | NOT NULL      |
| departure\_time       | TIMESTAMP               | 用户期望出发时间   | NOT NULL      |
| submit\_time          | TIMESTAMP               | 提交时间（自动生成） | DEFAULT now() |

---

## 2️⃣ 实体：DispatchPlan（调度计划）

| 字段名             | 类型                                        | 描述                  | 约束                |
| --------------- | ----------------------------------------- | ------------------- | ----------------- |
| plan\_id        | UUID / SERIAL                             | 计划唯一标识              | PK                |
| vehicle\_id     | TEXT                                      | 拟派车辆编号（可为空）         | 可 NULL            |
| start\_time     | TIMESTAMP                                 | 发车时间                | NOT NULL          |
| route\_polyline | TEXT / JSON                               | 路线折线（高德返回的polyline） | NOT NULL          |
| status          | ENUM('planned', 'confirmed', 'cancelled') | 计划状态                | DEFAULT 'planned' |
| created\_at     | TIMESTAMP                                 | 创建时间                | DEFAULT now()     |

---

## 3️⃣ 实体：RequestDispatchLink（请求-调度计划关联表）

> 多个请求可以关联到一个发车计划，一对多关系的实现中间表。

| 字段名         | 类型                           | 描述      | 约束       |
| ----------- | ---------------------------- | ------- | -------- |
| id          | SERIAL                       | 自增主键    | PK       |
| request\_id | FK → UserRequest.request\_id | 外键：用户请求 | NOT NULL |
| plan\_id    | FK → DispatchPlan.plan\_id   | 外键：调度计划 | NOT NULL |

---


---

## ✅ 修正版 `TrafficEvaluation` 表设计（历史拥堵延迟指数表）

| 字段名              | 类型     | 描述               | 约束       |
| ---------------- | ------ | ---------------- | -------- |
| nds\_id          | BIGINT | 路段唯一编码（NDS标准）    | PK       |
| time\_slot       | BIGINT | 时间戳（10分钟粒度）      | NOT NULL |
| link\_name\_chn  | TEXT   | 道路名称（中文）         |          |
| link\_length\_m  | INT    | 道路长度（米）          |          |
| road\_class      | INT    | 道路等级（1\~7）       | 可用于权重    |
| real\_speed\_kph | FLOAT  | 实际速度（km/h）       |          |
| delay\_index     | FLOAT  | 延迟指数（>1 表示拥堵）    |          |
| free\_speed\_kph | FLOAT  | 自由流速度（km/h）      |          |
| link\_type       | INT    | 道路类型（功能性区分）      |          |
| xy\_coordinates  | TEXT   | 起终点坐标（GCJ-02 格式） | 可转为点/线   |
| direction        | INT    | 路段方向（0\~3）       |          |
| adcode           | TEXT   | 所属行政区划代码         | 可做区域过滤   |

---

## 📌 存储建议（PostgreSQL + PostGIS）

* 将 `xy_coordinates` 转换为 **LINESTRING** 类型，便于与用户路径做空间对比。
* 使用 `time_slot` 进行 **时间窗匹配**，提取和用户需求提交时间最近的一条记录。
* 可以为 `nds_id + time_slot` 建立联合唯一索引，避免重复导入。
* 加入 GIN/GiST 空间索引（PostGIS），支持空间聚类、路径重建等功能。

---

## 🧠 在项目中能做什么？

> 你的这份交通数据非常有实际意义！以下是它在你的项目中的关键用途：

### 🔧 路线优化（与高德路线结果进行对比）

* **目标**：当高德返回多条路线（可通过 API 设置策略），你可以：

  * 提取其经过的路段坐标；
  * 比对这些路段的 `delay_index`；
  * 选择总体 **拥堵延迟最小** 的路线作为推荐线路；
  * 若都高于阈值，则提示：“当前交通拥堵，建议延后出发”。

### 🧠 路段打分函数举例：

```sql
SELECT AVG(delay_index)
FROM traffic_evaluation
WHERE ST_Intersects(route_geom, xy_line_geom)
  AND time_slot = '202505091030'
```

### 📊 预测性聚类或热力区域分析

* 可对 `adcode` + `delay_index` 做热力聚合，找出 **高发拥堵区域**；
* 未来还能作为路线**动态避让训练数据**（结合机器学习预测路径）。

---

是否需要我将这些字段字段转为 PostgreSQL 建表语句？或者帮你设计一段样本数据的插入示例？

---

## 🔗 实体关系说明：

* 一个 **UserRequest** 可以归入一个或多个 **DispatchPlan**（通过聚类路线分配），但初期设计为 **多对一关系**。
* 一个 **DispatchPlan** 可以包含多个 **UserRequest**（实现拼车式公交聚合调度）。
* **TrafficEvaluation** 用于提供某一时刻路段的通行效率数据，用于**优化路线推荐算法**，不与其他表直接关联，而是**算法层面引用**。

---

## 🧠 附加说明（设计哲学）

* 所有坐标字段建议使用 PostgreSQL 的 **PostGIS 插件**，支持空间查询（如半径聚类、OD距离计算）。
* 路线可暂时保存为高德 polyline（字符串），后期如要轨迹重构可再做坐标展开。
* 系统后期若支持登录/历史记录/车辆轨迹，可扩展：

  * `User` 实体（绑定乘客或管理员）
  * `Vehicle` 实体（管理公交车信息）
  * `TripHistory` 实体（记录真实运行轨迹）

---

是否需要我用这个结构帮你生成 PostgreSQL 的建表 SQL？
