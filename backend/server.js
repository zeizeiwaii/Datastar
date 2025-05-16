const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const app = express();

// 数据库连接配置
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'responsive_bus',
    password: 'your_password', // 请修改为你的数据库密码
    port: 5432,
});

// 中间件
app.use(cors());
app.use(express.json());

// 提交出行请求
app.post('/api/submitRequest', async (req, res) => {
    const client = await pool.connect();
    try {
        const { origin, destination, departureTime, peopleCount, originLocation, destinationLocation } = req.body;

        // 开始事务
        await client.query('BEGIN');

        // 插入用户请求
        const result = await client.query(
            `INSERT INTO user_request 
       (origin_name, origin_location, destination_name, destination_location, people_count, departure_time)
       VALUES ($1, ST_SetSRID(ST_MakePoint($2, $3), 4326), $4, ST_SetSRID(ST_MakePoint($5, $6), 4326), $7, $8)
       RETURNING request_id`,
            [
                origin,
                originLocation.lng,
                originLocation.lat,
                destination,
                destinationLocation.lng,
                destinationLocation.lat,
                peopleCount,
                departureTime
            ]
        );

        // 提交事务
        await client.query('COMMIT');

        res.json({
            success: true,
            requestId: result.rows[0].request_id
        });
    } catch (error) {
        // 回滚事务
        await client.query('ROLLBACK');
        console.error('提交请求失败:', error);
        res.status(500).json({
            success: false,
            error: '提交请求失败，请稍后重试'
        });
    } finally {
        client.release();
    }
});

// 获取仪表盘统计数据
app.get('/api/dashboard/stats', async (req, res) => {
    const client = await pool.connect();
    try {
        // 获取今日需求总数
        const totalRequests = await client.query(
            `SELECT COUNT(*) FROM user_request 
       WHERE DATE(submit_time) = CURRENT_DATE`
        );

        // 获取待确认调度数量
        const pendingPlans = await client.query(
            `SELECT COUNT(*) FROM dispatch_plan 
       WHERE status = 'planned'`
        );

        // 获取已发车数量
        const confirmedPlans = await client.query(
            `SELECT COUNT(*) FROM dispatch_plan 
       WHERE status = 'confirmed'`
        );

        res.json({
            totalRequests: parseInt(totalRequests.rows[0].count),
            pendingPlans: parseInt(pendingPlans.rows[0].count),
            confirmedPlans: parseInt(confirmedPlans.rows[0].count)
        });
    } catch (error) {
        console.error('获取统计数据失败:', error);
        res.status(500).json({
            success: false,
            error: '获取统计数据失败'
        });
    } finally {
        client.release();
    }
});

// 获取调度计划列表
app.get('/api/dispatch/plans', async (req, res) => {
    const client = await pool.connect();
    try {
        const result = await client.query(
            `SELECT dp.*, COUNT(rdl.request_id) as request_count
       FROM dispatch_plan dp
       LEFT JOIN request_dispatch_link rdl ON dp.plan_id = rdl.plan_id
       GROUP BY dp.plan_id
       ORDER BY dp.start_time DESC`
        );

        res.json(result.rows);
    } catch (error) {
        console.error('获取调度计划失败:', error);
        res.status(500).json({
            success: false,
            error: '获取调度计划失败'
        });
    } finally {
        client.release();
    }
});

// 获取调度计划详情
app.get('/api/dispatch/plan/:planId', async (req, res) => {
    const client = await pool.connect();
    try {
        const { planId } = req.params;

        // 获取计划基本信息
        const planResult = await client.query(
            `SELECT * FROM dispatch_plan WHERE plan_id = $1`,
            [planId]
        );

        if (planResult.rows.length === 0) {
            return res.status(404).json({
                success: false,
                error: '调度计划不存在'
            });
        }

        // 获取计划包含的需求
        const requestsResult = await client.query(
            `SELECT ur.* 
       FROM user_request ur
       JOIN request_dispatch_link rdl ON ur.request_id = rdl.request_id
       WHERE rdl.plan_id = $1`,
            [planId]
        );

        res.json({
            ...planResult.rows[0],
            requests: requestsResult.rows
        });
    } catch (error) {
        console.error('获取计划详情失败:', error);
        res.status(500).json({
            success: false,
            error: '获取计划详情失败'
        });
    } finally {
        client.release();
    }
});

// 确认发车
app.post('/api/dispatch/confirm/:planId', async (req, res) => {
    const client = await pool.connect();
    try {
        const { planId } = req.params;

        await client.query(
            `UPDATE dispatch_plan 
       SET status = 'confirmed' 
       WHERE plan_id = $1 AND status = 'planned'`,
            [planId]
        );

        res.json({ success: true });
    } catch (error) {
        console.error('确认发车失败:', error);
        res.status(500).json({
            success: false,
            error: '确认发车失败'
        });
    } finally {
        client.release();
    }
});

// 取消计划
app.post('/api/dispatch/cancel/:planId', async (req, res) => {
    const client = await pool.connect();
    try {
        const { planId } = req.params;

        await client.query(
            `UPDATE dispatch_plan 
       SET status = 'cancelled' 
       WHERE plan_id = $1 AND status = 'planned'`,
            [planId]
        );

        res.json({ success: true });
    } catch (error) {
        console.error('取消计划失败:', error);
        res.status(500).json({
            success: false,
            error: '取消计划失败'
        });
    } finally {
        client.release();
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
}); 