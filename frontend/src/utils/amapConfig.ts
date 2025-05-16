/**
 * 高德地图配置文件
 * 用于统一管理高德地图API的相关配置
 */

// JS API相关配置 (用于地图组件、室内地图、地铁图等)
export const JS_API_KEY = "f3e49391bb7e88bfb311ecfaeefa1f8b";
export const SECURITY_JSCODE = "12987db7c703bb181705363cf67bfdbf"; // 更新的安全密钥

// Web服务API相关配置 (用于HTTP REST API请求)
export const WEB_SERVICE_API_KEY = "ed5c583e14dfd33f75a6323b5d87491f"; // 用于周边搜索、路径规划等服务

// 服务器端Key，用于通过Vite代理调用REST API
export const SERVER_API_KEY = WEB_SERVICE_API_KEY; // 与Web服务API Key保持一致

// 是否使用代理
export const USE_PROXY = true;

// API配置
export const API_CONFIG = {
    // POI搜索配置 - 使用Web服务API Key
    POI_SEARCH: {
        URL: USE_PROXY ? "/amap-api/v5/place/text" : "https://restapi.amap.com/v5/place/text",
        DEFAULT_PARAMS: {
            output: "json",
            page_size: "10",
            page_num: "1",
            show_fields: "business,children",
            region: "上海市"
        },
        USE_WEB_SERVICE_KEY: true,
        RETRY_TIMES: 3,
        RETRY_DELAY: 1000
    },

    // 地理编码配置 - 使用Web服务API Key
    GEOCODE: {
        URL: USE_PROXY ? "/amap-api/v3/geocode/geo" : "https://restapi.amap.com/v3/geocode/geo",
        DEFAULT_PARAMS: {
            output: "json",
            batch: "false"
        },
        USE_WEB_SERVICE_KEY: true,
        RETRY_TIMES: 3,
        RETRY_DELAY: 1000
    },

    // 逆地理编码配置 - 使用Web服务API Key
    REGEOCODE: {
        URL: USE_PROXY ? "/amap-api/v3/geocode/regeo" : "https://restapi.amap.com/v3/geocode/regeo",
        DEFAULT_PARAMS: {
            output: "json",
            extensions: "base"
        },
        USE_WEB_SERVICE_KEY: true,
        RETRY_TIMES: 3,
        RETRY_DELAY: 1000
    },

    // 周边搜索配置 - 使用Web服务API Key
    AROUND_SEARCH: {
        URL: USE_PROXY ? "/amap-api/v5/place/around" : "https://restapi.amap.com/v5/place/around",
        DEFAULT_PARAMS: {
            output: "json",
            page_size: "10",
            page_num: "1",
            show_fields: "business,children"
        },
        USE_WEB_SERVICE_KEY: true,
        RETRY_TIMES: 3,
        RETRY_DELAY: 1000
    },

    // 路径规划配置 - 使用Web服务API Key
    DIRECTION: {
        DRIVING: {
            URL: USE_PROXY ? "/amap-api/v5/direction/driving" : "https://restapi.amap.com/v5/direction/driving",
            DEFAULT_PARAMS: {
                output: "json",
                extensions: "base"
            },
            USE_WEB_SERVICE_KEY: true,
            RETRY_TIMES: 3,
            RETRY_DELAY: 1000
        },
        WALKING: {
            URL: USE_PROXY ? "/amap-api/v5/direction/walking" : "https://restapi.amap.com/v5/direction/walking",
            DEFAULT_PARAMS: {
                output: "json"
            },
            USE_WEB_SERVICE_KEY: true,
            RETRY_TIMES: 3,
            RETRY_DELAY: 1000
        },
        TRANSIT: {
            URL: USE_PROXY ? "/amap-api/v5/direction/transit/integrated" : "https://restapi.amap.com/v5/direction/transit/integrated",
            DEFAULT_PARAMS: {
                output: "json",
                city: "上海",
                nightflag: "0"
            },
            USE_WEB_SERVICE_KEY: true,
            RETRY_TIMES: 3,
            RETRY_DELAY: 1000
        }
    },

    // 天气查询配置 - 使用Web服务API Key
    WEATHER: {
        URL: USE_PROXY ? "/amap-api/v3/weather/weatherInfo" : "https://restapi.amap.com/v3/weather/weatherInfo",
        DEFAULT_PARAMS: {
            output: "json",
            city: "310000", // 上海市
            extensions: "all"
        },
        USE_WEB_SERVICE_KEY: true,
        RETRY_TIMES: 3,
        RETRY_DELAY: 1000
    }
};

// JS API加载配置
export const JS_API_CONFIG = {
    VERSION: "2.0",
    PLUGINS: [
        "AMap.Scale",
        "AMap.ToolBar",
        "AMap.Driving",
        "AMap.Geocoder",
        "AMap.Marker",
        "AMap.Polyline",
        "AMap.InfoWindow",
        "AMap.CircleEditor",
        "AMap.MarkerClusterer"  // 添加点聚合插件
    ],
    // 安全配置
    SECURITY_CONFIG: {
        securityJsCode: SECURITY_JSCODE
    },
    // 重试配置
    RETRY: {
        MAX_TIMES: 3,
        DELAY: 1000
    },
    // 地图样式
    MAP_STYLE: {
        DEFAULT: "amap://styles/normal",
        DARK: "amap://styles/dark",
        LIGHT: "amap://styles/light",
        FRESH: "amap://styles/fresh"
    }
};

// 默认地图中心点坐标（上海市中心）
export const DEFAULT_CENTER = {
    lng: 121.473701,
    lat: 31.230416,
    zoom: 12
};

// 错误代码映射
export const ERROR_CODES = {
    USERKEY_PLAT_NOMATCH: "您的API密钥与平台类型不匹配，请确保使用Web服务类型的Key且已绑定正确域名",
    INVALID_USER_KEY: "无效的用户Key",
    SERVICE_NOT_AVAILABLE: "服务不可用",
    DAILY_QUERY_OVER_LIMIT: "请求超出日限额",
    ACCESS_TOO_FREQUENT: "请求过于频繁",
    INVALID_PARAMS: "无效的请求参数",
    INVALID_SECURITY_CODE: "安全密钥无效或未配置",
    NETWORK_ERROR: "网络连接错误，请检查网络设置",
    SCRIPT_LOAD_ERROR: "地图脚本加载失败",
    MAP_INIT_ERROR: "地图初始化失败",
    PLUGIN_LOAD_ERROR: "插件加载失败",
    UNKNOWN_ERROR: "未知错误"
};

/**
 * 获取API Key
 * 根据是否使用代理返回对应的Key
 */
export const getApiKey = (): string => {
    return USE_PROXY ? SERVER_API_KEY : WEB_SERVICE_API_KEY;
};

/**
 * 获取指定API的Key
 * 根据API配置决定使用哪个Key
 * @param apiConfig API配置
 */
export const getApiKeyForService = (apiConfig: any): string => {
    if (apiConfig && apiConfig.USE_WEB_SERVICE_KEY) {
        return USE_PROXY ? SERVER_API_KEY : WEB_SERVICE_API_KEY;
    }
    return JS_API_KEY;
};

/**
 * 获取错误信息
 * @param infocode 错误代码
 * @returns 错误描述
 */
export const getErrorMessage = (infocode: string): string => {
    const knownErrors: { [key: string]: string } = {
        '10001': ERROR_CODES.INVALID_USER_KEY,
        '10002': ERROR_CODES.SERVICE_NOT_AVAILABLE,
        '10003': ERROR_CODES.DAILY_QUERY_OVER_LIMIT,
        '10004': ERROR_CODES.ACCESS_TOO_FREQUENT,
        '10000': "请求成功",
        '20000': ERROR_CODES.INVALID_PARAMS,
        '20800': ERROR_CODES.USERKEY_PLAT_NOMATCH,
        '30001': ERROR_CODES.INVALID_SECURITY_CODE,
        '10009': ERROR_CODES.USERKEY_PLAT_NOMATCH,
        'NETWORK_ERROR': ERROR_CODES.NETWORK_ERROR,
        'SCRIPT_LOAD_ERROR': ERROR_CODES.SCRIPT_LOAD_ERROR,
        'MAP_INIT_ERROR': ERROR_CODES.MAP_INIT_ERROR,
        'PLUGIN_LOAD_ERROR': ERROR_CODES.PLUGIN_LOAD_ERROR
    };

    return knownErrors[infocode] || ERROR_CODES.UNKNOWN_ERROR;
};

/**
 * 记录API请求日志
 * @param apiName API名称
 * @param params 请求参数
 * @param response 响应结果
 */
export const logApiRequest = (apiName: string, params: any, response: any): void => {
    const timestamp = new Date().toISOString();
    console.group(`[高德地图API] ${apiName} - ${timestamp}`);
    console.log('请求参数:', params);
    console.log('响应结果:', response);
    if (response && response.status !== '1') {
        console.warn('请求失败:', getErrorMessage(response.infocode));
    }
    console.groupEnd();
};

/**
 * 验证API配置
 * @returns 验证结果
 */
export const validateApiConfig = (): { valid: boolean; message: string } => {
    if (!JS_API_KEY) {
        return { valid: false, message: "未配置JavaScript API密钥" };
    }
    if (!SECURITY_JSCODE) {
        return { valid: false, message: "未配置安全密钥" };
    }
    if (!WEB_SERVICE_API_KEY) {
        return { valid: false, message: "未配置Web服务API密钥" };
    }
    return { valid: true, message: "配置验证通过" };
};

export default {
    JS_API_KEY,
    SECURITY_JSCODE,
    WEB_SERVICE_API_KEY,
    SERVER_API_KEY,
    USE_PROXY,
    API_CONFIG,
    JS_API_CONFIG,
    DEFAULT_CENTER,
    ERROR_CODES,
    getApiKey,
    getApiKeyForService,
    getErrorMessage,
    logApiRequest,
    validateApiConfig
};