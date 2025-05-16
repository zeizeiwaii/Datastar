import axios from 'axios';
import type { Location, POI } from '../types/request';

// 根据运行环境自动选择API地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : '');

// 创建axios实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000, // 10秒超时
    headers: {
        'Content-Type': 'application/json'
    }
});

// 添加请求拦截器进行错误处理
apiClient.interceptors.response.use(
    response => response,
    error => {
        console.error('API请求错误:', error);
        if (error.response) {
            // 服务器返回错误状态码
            console.error('状态码:', error.response.status);
            console.error('响应数据:', error.response.data);
        } else if (error.request) {
            // 请求发出但没有收到响应
            console.error('未收到响应:', error.request);
        } else {
            // 请求配置出错
            console.error('请求配置错误:', error.message);
        }
        return Promise.reject(error);
    }
);

export interface RequestData {
    origin: string;
    destination: string;
    departureTime: string;
    peopleCount: number;
    originLocation: Location;
    destinationLocation: Location;
    originPOI?: POI;
    destinationPOI?: POI;
}

export const submitRequest = async (data: RequestData) => {
    try {
        console.log("发送请求数据:", data);
        const response = await apiClient.post('/request/submitRequest', data);
        console.log("请求成功，响应:", response.data);
        return response.data;
    } catch (error: any) {
        console.error('提交请求失败:', error);

        // 提取更详细的错误信息
        let errorMessage = '提交失败';
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }

        throw new Error(errorMessage);
    }
};

export const getDashboardStats = async () => {
    try {
        const response = await apiClient.get('/dispatch/dashboard/stats');
        return response.data;
    } catch (error) {
        console.error('获取统计数据失败:', error);
        throw new Error('获取统计数据失败');
    }
};

export const getDispatchPlans = async () => {
    try {
        const response = await apiClient.get('/dispatch/plans');
        return response.data;
    } catch (error) {
        console.error('获取调度计划失败:', error);
        throw new Error('获取调度计划失败');
    }
};

export const getDispatchPlanDetail = async (planId: number) => {
    try {
        const response = await apiClient.get(`/dispatch/plan/${planId}`);
        return response.data;
    } catch (error) {
        console.error('获取计划详情失败:', error);
        throw new Error('获取计划详情失败');
    }
};

export const confirmDispatch = async (planId: number) => {
    try {
        const response = await apiClient.post(`/dispatch/confirm/${planId}`);
        return response.data;
    } catch (error) {
        console.error('确认发车失败:', error);
        throw new Error('确认发车失败');
    }
};

export const cancelDispatch = async (planId: number) => {
    try {
        const response = await apiClient.post(`/dispatch/cancel/${planId}`);
        return response.data;
    } catch (error) {
        console.error('取消计划失败:', error);
        throw new Error('取消计划失败');
    }
}; 