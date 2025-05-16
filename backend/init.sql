-- 启用PostGIS扩展
CREATE EXTENSION IF NOT EXISTS postgis;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 创建车辆表
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    plate_number TEXT UNIQUE NOT NULL,
    vehicle_type TEXT,
    capacity INTEGER,
    current_location JSONB,
    status TEXT DEFAULT 'available',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 创建用户出行请求表
CREATE TABLE IF NOT EXISTS user_request (
    request_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    origin_name TEXT NOT NULL,
    origin_location GEOGRAPHY(Point) NOT NULL,
    destination_name TEXT NOT NULL,
    destination_location GEOGRAPHY(Point) NOT NULL,
    people_count INTEGER NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    cluster_id INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 创建调度计划表
CREATE TABLE IF NOT EXISTS dispatch_plan (
    plan_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    name TEXT,
    route_polyline TEXT NOT NULL,
    status TEXT DEFAULT 'planned' CHECK (status IN ('planned', 'confirmed', 'cancelled')),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 创建请求-调度计划关联表
CREATE TABLE IF NOT EXISTS request_dispatch_link (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES user_request(request_id),
    plan_id INTEGER REFERENCES dispatch_plan(plan_id),
    UNIQUE(request_id, plan_id)
);

-- 创建交通评价数据表
CREATE TABLE traffic_evaluation (
    nds_id BIGINT PRIMARY KEY,
    time_slot BIGINT NOT NULL,
    link_name_chn TEXT,
    link_length_m INTEGER,
    road_class INTEGER,
    real_speed_kph FLOAT,
    delay_index FLOAT,
    free_speed_kph FLOAT,
    link_type INTEGER,
    xy_coordinates TEXT,
    direction INTEGER,
    adcode TEXT,
    UNIQUE(nds_id, time_slot)
);

-- 创建空间索引
CREATE INDEX idx_user_request_origin ON user_request USING GIST(origin_location);
CREATE INDEX idx_user_request_destination ON user_request USING GIST(destination_location);

-- 创建时间索引
CREATE INDEX idx_user_request_departure_time ON user_request(departure_time);
CREATE INDEX idx_dispatch_plan_start_time ON dispatch_plan(start_time);
CREATE INDEX idx_traffic_evaluation_time_slot ON traffic_evaluation(time_slot);

-- 创建用户相关索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_request_user_id ON user_request(user_id);

-- 创建车辆相关索引
CREATE INDEX idx_vehicles_plate_number ON vehicles(plate_number);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_dispatch_plan_vehicle_id ON dispatch_plan(vehicle_id);

-- 创建状态索引
CREATE INDEX idx_user_request_status ON user_request(status);
CREATE INDEX idx_dispatch_plan_status ON dispatch_plan(status);

-- 创建关联表索引
CREATE INDEX idx_request_dispatch_link_request_id ON request_dispatch_link(request_id);
CREATE INDEX idx_request_dispatch_link_plan_id ON request_dispatch_link(plan_id); 