# 高德地图API集成指南

## 概述

本项目使用高德地图API提供位置搜索、地图显示、路径规划等功能。高德地图API分为两种类型：

1. **JavaScript API**：用于在前端页面中加载地图组件、室内地图、地铁图等
2. **Web服务API**：用于HTTP请求，如周边搜索、路径规划、天气查询等

## 配置说明

### API Key配置

本项目在`frontend/src/utils/amapConfig.ts`中统一管理所有高德地图相关配置：

```typescript
// JS API相关配置 (用于地图组件、室内地图、地铁图等)
export const JS_API_KEY = "f3e49391bb7e88bfb311ecfaeefa1f8b";
export const SECURITY_JSCODE = "12987db7c703bb181705363cf67bfdbf"; // 安全密钥

// Web服务API相关配置 (用于HTTP REST API请求)
export const WEB_SERVICE_API_KEY = "ed5c583e14dfd33f5a6323b5d87491f";
```

### 代理配置

为避免跨域问题，我们在`vite.config.ts`中配置了代理：

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

使用此配置，可以通过`/amap-api`路径发送请求，会被自动转发到高德地图服务器。

## 使用方法

### 1. 加载地图组件

在Vue组件中加载地图：

```typescript
import amapConfig from "../utils/amapConfig";

// 加载高德地图脚本
const loadAMapScript = () => {
  return new Promise<void>((resolve, reject) => {
    // 如果已经加载过，直接返回
    if ((window as any).AMap) {
      resolve();
      return;
    }

    // 加载JSAPI Loader
    const loaderScript = document.createElement("script");
    loaderScript.src = "https://webapi.amap.com/loader.js";
    loaderScript.onload = () => {
      const AMapLoader = (window as any).AMapLoader;
      AMapLoader.load({
        key: amapConfig.JS_API_KEY,
        version: amapConfig.JS_API_CONFIG.VERSION,
        plugins: amapConfig.JS_API_CONFIG.PLUGINS,
        securityJsCode: amapConfig.SECURITY_JSCODE, // 必需！
      })
        .then(() => resolve())
        .catch((e: any) => reject(e));
    };
    document.head.appendChild(loaderScript);
  });
};

// 在mounted中调用
onMounted(async () => {
  await loadAMapScript();
  // 初始化地图
  map = new (window as any).AMap.Map(mapContainer.value, {
    center: [amapConfig.DEFAULT_CENTER.lng, amapConfig.DEFAULT_CENTER.lat],
    zoom: 14,
  });
});
```

### 2. 使用Web服务API

使用`amapService.ts`提供的统一方法调用API：

```typescript
import amapService from "../utils/amapService";

// POI搜索示例
const searchPOI = async () => {
  try {
    const data = await amapService.poiSearch({
      keywords: "上海市临港",
    });
    console.log("搜索结果:", data.pois);
  } catch (err) {
    console.error("搜索出错:", err);
  }
};

// 周边搜索示例
const searchAround = async () => {
  try {
    const data = await amapService.aroundSearch({
      location: "121.473701,31.230416",
      radius: "1000",
    });
    console.log("周边结果:", data.pois);
  } catch (err) {
    console.error("周边搜索出错:", err);
  }
};

// 驾车路径规划示例
const planRoute = async () => {
  try {
    const data = await amapService.drivingDirection({
      origin: "121.473701,31.230416",
      destination: "121.522782,31.215630",
    });
    console.log("路径规划结果:", data.route);
  } catch (err) {
    console.error("路径规划出错:", err);
  }
};
```

## 常见错误及解决方案

### 1. USERKEY_PLAT_NOMATCH (错误码10009)

**症状**：API返回错误信息"USERKEY_PLAT_NOMATCH"，错误码10009

**原因**：使用了与平台不匹配的Key，例如在Web端使用了服务端的Key或在服务端使用了Web端的Key

**解决方案**：
- 确保使用正确类型的Key：
  - 对于地图组件，使用JS API Key
  - 对于HTTP请求，使用Web服务API Key
- 使用`amapService.ts`中的方法，它会自动选择正确的Key

### 2. INVALID_SECURITY_CODE (错误码30001)

**症状**：地图加载失败，报错"INVALID_SECURITY_CODE"或错误码30001

**原因**：高德地图JS API 2.0版本必须配置安全密钥

**解决方案**：
- 确保加载地图时配置了安全密钥：
  ```typescript
  AMapLoader.load({
    key: amapConfig.JS_API_KEY,
    securityJsCode: amapConfig.SECURITY_JSCODE, // 必须配置
    // 其他配置...
  })
  ```

### 3. 跨域问题

**症状**：浏览器控制台报CORS错误，无法访问高德API

**解决方案**：
- 使用配置好的Vite代理路径：
  ```typescript
  // 不要使用
  const url = "https://restapi.amap.com/v5/place/text";
  
  // 应该使用
  const url = "/amap-api/v5/place/text";
  ```
- 或者在请求中添加适当的CORS头

### 4. 请求超限或无效Key

**症状**：
- 错误码10001：INVALID_USER_KEY - 无效的用户Key
- 错误码10003：DAILY_QUERY_OVER_LIMIT - 请求超出日限额

**解决方案**：
- 检查Key是否正确配置
- 控制请求频率，避免超出限额
- 如果是开发环境，考虑申请更高配额的Key

## 测试与验证

使用`frontend/src/views/ProxyTestView.vue`页面可以测试不同API Key的功能和有效性。
该页面提供了：

1. POI搜索测试（使用Web服务API Key）
2. 周边搜索测试（使用Web服务API Key）
3. 调试日志功能

## 最佳实践

1. **统一使用服务模块**：使用`amapService.ts`中的方法，而不是直接调用API
2. **优先使用代理**：在前端开发中优先使用配置好的Vite代理
3. **错误处理**：对每个API调用添加适当的错误处理逻辑
4. **限制请求频率**：控制API调用频率，避免超出配额
5. **密钥保护**：避免在客户端暴露API Key，尤其是在生产环境 