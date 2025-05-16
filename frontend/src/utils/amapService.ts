/**
 * 高德地图服务工具
 * 提供统一的API请求方法，自动选择正确的Key
 */
import amapConfig from './amapConfig';

/**
 * 发送高德地图API请求
 * @param apiConfig API配置对象
 * @param params 请求参数（不包含key）
 * @returns Promise<any> API响应结果
 */
export const requestAmapAPI = async <T = any>(
    apiConfig: any,
    params: Record<string, any> = {}
): Promise<T> => {
    try {
        // 确定使用哪个Key
        const key = amapConfig.getApiKeyForService(apiConfig);

        // 构建请求URL和参数
        const requestParams = new URLSearchParams({
            key,
            ...apiConfig.DEFAULT_PARAMS,
            ...params
        });

        const url = `${apiConfig.URL}?${requestParams.toString()}`;

        // 发送请求
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }

        const data = await response.json();

        // 记录请求日志
        amapConfig.logApiRequest(
            apiConfig.URL.split('/').pop() || 'amapAPI',
            requestParams.toString(),
            data
        );

        // 检查API响应状态
        if (data.status === '0') {
            throw new Error(`API错误: ${data.info || '未知错误'} (错误码: ${data.infocode})`);
        }

        return data as T;
    } catch (error: any) {
        console.error('高德地图API请求错误:', error);
        throw error;
    }
};

// 周边搜索服务
export const aroundSearch = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.AROUND_SEARCH, params);
};

// 驾车路径规划服务
export const drivingDirection = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.DIRECTION.DRIVING, params);
};

// 步行路径规划服务
export const walkingDirection = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.DIRECTION.WALKING, params);
};

// 公交路径规划服务
export const transitDirection = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.DIRECTION.TRANSIT, params);
};

// 天气查询服务
export const weatherQuery = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.WEATHER, params);
};

// POI搜索服务
export const poiSearch = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.POI_SEARCH, params);
};

// 地理编码服务
export const geocode = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.GEOCODE, params);
};

// 逆地理编码服务
export const regeocode = (params: Record<string, any>) => {
    return requestAmapAPI(amapConfig.API_CONFIG.REGEOCODE, params);
};

export default {
    requestAmapAPI,
    aroundSearch,
    drivingDirection,
    walkingDirection,
    transitDirection,
    weatherQuery,
    poiSearch,
    geocode,
    regeocode
}; 