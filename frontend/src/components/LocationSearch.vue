<template>
  <div class="location-search">
    <div class="search-input">
      <el-input
        v-model="searchKeyword"
        placeholder="请输入地点"
        @input="handleSearch"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 搜索结果列表 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div
        v-for="poi in searchResults"
        :key="poi.id"
        class="result-item"
        @click="selectLocation(poi)"
      >
        <div class="poi-name">{{ poi.name }}</div>
        <div class="poi-address">{{ poi.address }}</div>
      </div>
    </div>

    <!-- 地图容器 -->
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { Location } from "../types/request";
import amapConfig from "../utils/amapConfig";

interface LocationValue {
  name: string;
  location: Location;
}

// 简化的POI接口定义
interface POI {
  id: string;
  name: string;
  address: string;
  location: string;
}

const props = defineProps<{
  modelValue?: LocationValue;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: LocationValue): void;
}>();

// 搜索相关
const searchKeyword = ref("");
const searchResults = ref<POI[]>([]);

// 地图相关
const mapContainer = ref<HTMLElement | null>(null);
const map = ref<any>(null);
const marker = ref<any>(null);

// 初始化地图
onMounted(async () => {
  try {
    await loadAMapScript();
    initMap();
  } catch (error) {
    console.error("地图初始化失败:", error);
    ElMessage.error("地图加载失败，请刷新页面重试");
  }
});

// 加载高德地图脚本
const loadAMapScript = () => {
  return new Promise<void>((resolve, reject) => {
    // 如果已经加载过，直接返回
    if ((window as any).AMap) {
      resolve();
      return;
    }

    // 先验证API配置
    const configValidation = amapConfig.validateApiConfig();
    if (!configValidation.valid) {
      console.error(
        "LocationSearch: 高德地图配置无效:",
        configValidation.message
      );
      reject(new Error(configValidation.message));
      return;
    }

    // 先加载JSAPI Loader
    const loaderScript = document.createElement("script");
    loaderScript.type = "text/javascript";
    loaderScript.async = true;
    loaderScript.src = "https://webapi.amap.com/loader.js";

    loaderScript.onload = () => {
      // 使用类型断言解决TypeScript错误
      const AMapLoader = (window as any).AMapLoader;
      AMapLoader.load({
        key: amapConfig.JS_API_KEY,
        version: amapConfig.JS_API_CONFIG.VERSION,
        plugins: ["AMap.Geocoder"],
        securityJsCode: amapConfig.SECURITY_JSCODE,
      })
        .then(() => {
          console.log("LocationSearch: 高德地图加载成功");
          resolve();
        })
        .catch((e: any) => {
          console.error("LocationSearch: 高德地图API加载失败:", e);
          // 尝试使用备选方式加载
          const fallbackScript = document.createElement("script");
          fallbackScript.type = "text/javascript";
          fallbackScript.async = true;
          fallbackScript.src = `https://webapi.amap.com/maps?v=${amapConfig.JS_API_CONFIG.VERSION}&key=${amapConfig.JS_API_KEY}&plugin=AMap.Geocoder&security=${amapConfig.SECURITY_JSCODE}`;

          fallbackScript.onload = () => {
            console.log("LocationSearch: 使用备选方式加载高德地图成功");
            resolve();
          };

          fallbackScript.onerror = (error) => {
            console.error("LocationSearch: 高德地图备选加载失败:", error);
            ElMessage.error({
              message: "地图加载失败：" + amapConfig.getErrorMessage("20800"),
              duration: 5000,
            });
            reject(new Error("高德地图加载失败，请检查API Key或网络连接"));
          };

          document.head.appendChild(fallbackScript);
        });
    };

    loaderScript.onerror = (error) => {
      console.error("LocationSearch: 高德地图loader加载失败:", error);
      reject(new Error("高德地图加载器加载失败"));
    };

    document.head.appendChild(loaderScript);
  });
};

// 初始化地图
const initMap = () => {
  if (!mapContainer.value) return;

  const AMap = (window as any).AMap;

  // 创建地图实例
  map.value = new AMap.Map(mapContainer.value, {
    zoom: 11,
    center: [116.397428, 39.90923],
  });

  // 创建标记点
  marker.value = new AMap.Marker({
    draggable: true,
  });

  // 添加到地图
  map.value.add(marker.value);

  // 监听标记点拖动结束事件
  marker.value.on("dragend", (e: any) => {
    const position = e.target.getPosition();
    // 逆地理编码获取地址
    const geocoder = new AMap.Geocoder();
    geocoder.getAddress(
      [position.lng, position.lat],
      (status: string, result: any) => {
        if (status === "complete" && result.regeocode) {
          emit("update:modelValue", {
            name: result.regeocode.formattedAddress,
            location: {
              lng: position.lng,
              lat: position.lat,
            },
          });
        }
      }
    );
  });

  // 如果有初始值，设置标记
  if (props.modelValue?.location) {
    marker.value.setPosition([
      props.modelValue.location.lng,
      props.modelValue.location.lat,
    ]);
    map.value.setCenter([
      props.modelValue.location.lng,
      props.modelValue.location.lat,
    ]);
  }
};

// 处理搜索
const handleSearch = () => {
  if (!searchKeyword.value) {
    searchResults.value = [];
    return;
  }

  try {
    // 使用高德地图V5版本POI搜索API
    // 构建查询参数
    const params = new URLSearchParams({
      key: amapConfig.getApiKey(),
      keywords: searchKeyword.value,
      ...amapConfig.API_CONFIG.POI_SEARCH.DEFAULT_PARAMS,
    });

    const url = `${amapConfig.API_CONFIG.POI_SEARCH.URL}?${params.toString()}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP错误 ${response.status}`);
        }
        return response.json();
      })
      .then((result) => {
        // 记录API请求和响应
        amapConfig.logApiRequest(
          "LocationSearch POI搜索",
          params.toString(),
          result
        );

        if (result.status === "1" && result.pois && result.pois.length > 0) {
          searchResults.value = result.pois.map((poi: any) => ({
            id: poi.id,
            name: poi.name,
            address: poi.address || "暂无详细地址",
            location: poi.location,
          }));
        } else {
          searchResults.value = [];
          if (result.status === "0") {
            console.error(
              `搜索失败: ${result.info}(代码:${result.infocode})`,
              result
            );
            ElMessage.warning({
              message: `地点搜索失败: ${amapConfig.getErrorMessage(
                result.infocode
              )}`,
              duration: 5000,
            });
          } else {
            ElMessage.warning("未找到相关地点");
          }
        }
      })
      .catch((error) => {
        console.error("LocationSearch POI搜索错误:", error);
        searchResults.value = [];
        ElMessage.error({
          message: "搜索服务异常，请稍后重试: " + error.message,
          duration: 5000,
        });
      });
  } catch (error) {
    console.error("LocationSearch 参数构建错误:", error);
    ElMessage.error({
      message: "搜索参数错误，请联系管理员",
      duration: 5000,
    });
  }
};

// 选择地点
const selectLocation = (poi: POI) => {
  // 解析经纬度（V5 API返回的location格式为"lng,lat"）
  const [lng, lat] = poi.location.split(",").map(Number);
  const AMap = (window as any).AMap;

  // 更新标记点位置
  if (marker.value && map.value) {
    marker.value.setPosition([lng, lat]);
    map.value.setCenter([lng, lat]);
  }

  // 清除搜索结果
  searchResults.value = [];
  searchKeyword.value = poi.name;

  // 触发更新事件
  emit("update:modelValue", {
    name: poi.name,
    location: {
      lng,
      lat,
    },
  });
};

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue?.location && marker.value && map.value) {
      marker.value.setPosition([newValue.location.lng, newValue.location.lat]);
      map.value.setCenter([newValue.location.lng, newValue.location.lat]);
    }
  },
  { deep: true }
);
</script>

<style scoped>
.location-search {
  position: relative;
  width: 100%;
}

.search-input {
  margin-bottom: 10px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.result-item {
  padding: 10px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}

.result-item:hover {
  background-color: #f5f7fa;
}

.poi-name {
  font-weight: bold;
  margin-bottom: 4px;
}

.poi-address {
  font-size: 12px;
  color: #666;
}

.map-container {
  height: 300px;
  margin-top: 10px;
  border-radius: 4px;
  overflow: hidden;
}
</style> 