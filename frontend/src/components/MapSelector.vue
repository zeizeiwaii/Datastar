<template>
  <div class="map-selector">
    <div class="map-container" ref="mapContainer"></div>
    <div class="search-controls">
      <!-- 起点搜索框 -->
      <div class="search-box">
        <div class="search-header">
          <div class="icon-wrapper origin">
            <span class="marker-icon">A</span>
          </div>
          <el-input
            v-model="originKeyword"
            placeholder="请输入起点"
            @input="handleSearchInput('origin')"
            @focus="searchMode = 'origin'"
            clearable
          >
            <template #prefix>
              <el-icon><LocationFilled /></el-icon>
            </template>
          </el-input>
        </div>
        <!-- 起点搜索结果 -->
        <div
          v-if="searchMode === 'origin' && searchResults.length > 0"
          class="search-results"
        >
          <div
            v-for="item in searchResults"
            :key="item.id"
            class="result-item"
            @click="selectPlace(item, 'origin')"
          >
            <div class="item-name">{{ item.name }}</div>
            <div class="item-address">{{ item.address }}</div>
          </div>
        </div>
      </div>

      <!-- 终点搜索框 -->
      <div class="search-box">
        <div class="search-header">
          <div class="icon-wrapper destination">
            <span class="marker-icon">B</span>
          </div>
          <el-input
            v-model="destinationKeyword"
            placeholder="请输入终点"
            @input="handleSearchInput('destination')"
            @focus="searchMode = 'destination'"
            clearable
          >
            <template #prefix>
              <el-icon><LocationFilled /></el-icon>
            </template>
          </el-input>
        </div>
        <!-- 终点搜索结果 -->
        <div
          v-if="searchMode === 'destination' && searchResults.length > 0"
          class="search-results"
        >
          <div
            v-for="item in searchResults"
            :key="item.id"
            class="result-item"
            @click="selectPlace(item, 'destination')"
          >
            <div class="item-name">{{ item.name }}</div>
            <div class="item-address">{{ item.address }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  onMounted,
  onUnmounted,
  watch,
  defineEmits,
  defineProps,
  defineComponent,
} from "vue";
import { LocationFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { Location } from "../types/request";
import amapConfig from "../utils/amapConfig";

interface LocationValue {
  name: string;
  location: Location;
}

interface Props {
  modelValue: {
    origin: LocationValue;
    destination: LocationValue;
  };
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (
    e: "update:modelValue",
    value: { origin: LocationValue; destination: LocationValue }
  ): void;
}>();

// 地图相关
const mapContainer = ref<HTMLElement | null>(null);
let map: any = null;
let originMarker: any = null;
let destinationMarker: any = null;
let drivingInstance: any = null;

// 搜索相关
const originKeyword = ref("");
const destinationKeyword = ref("");
const searchResults = ref<any[]>([]);
const searchMode = ref<"origin" | "destination">("origin");
let placeSearch: any = null;

// 初始化地图
onMounted(async () => {
  await loadAMapScript();
  initMap();

  // 监听点击事件，用于直接在地图上选点
  map.on("click", handleMapClick);

  // 初始化面板展示已有的起终点数据
  console.log("初始化地图组件，传入的modelValue:", props.modelValue);

  if (props.modelValue) {
    // 显示起点
    if (
      props.modelValue.origin &&
      props.modelValue.origin.location &&
      props.modelValue.origin.location.lng
    ) {
      console.log("初始化起点:", props.modelValue.origin);
      originKeyword.value = props.modelValue.origin.name;
      setMarker("origin", props.modelValue.origin.location);
    }

    // 显示终点
    if (
      props.modelValue.destination &&
      props.modelValue.destination.location &&
      props.modelValue.destination.location.lng
    ) {
      console.log("初始化终点:", props.modelValue.destination);
      destinationKeyword.value = props.modelValue.destination.name;
      setMarker("destination", props.modelValue.destination.location);
    }

    // 如果有起点和终点，则规划路线
    if (
      props.modelValue.origin &&
      props.modelValue.origin.location &&
      props.modelValue.origin.location.lng &&
      props.modelValue.destination &&
      props.modelValue.destination.location &&
      props.modelValue.destination.location.lng
    ) {
      planRoute();
    }
  }
});

// 加载高德地图脚本
const loadAMapScript = () => {
  return new Promise<void>((resolve, reject) => {
    // 如果已经加载过，直接返回
    if ((window as any).AMap) {
      console.log("高德地图已加载，跳过加载过程");
      resolve();
      return;
    }

    // 先验证API配置
    const configValidation = amapConfig.validateApiConfig();
    if (!configValidation.valid) {
      console.error("高德地图配置无效:", configValidation.message);
      reject(new Error(configValidation.message));
      return;
    }

    console.log("开始加载高德地图...");

    // 先加载JSAPI Loader
    const loaderScript = document.createElement("script");
    loaderScript.type = "text/javascript";
    loaderScript.async = true;
    loaderScript.src = "https://webapi.amap.com/loader.js";

    loaderScript.onload = () => {
      console.log("高德地图Loader加载成功，准备加载地图...");
      // 使用类型断言解决TypeScript错误
      const AMapLoader = (window as any).AMapLoader;
      AMapLoader.load({
        key: amapConfig.JS_API_KEY,
        version: amapConfig.JS_API_CONFIG.VERSION,
        plugins: amapConfig.JS_API_CONFIG.PLUGINS,
        // 确保安全密钥正确配置
        securityJsCode: amapConfig.SECURITY_JSCODE,
      })
        .then(() => {
          console.log("高德地图加载成功，版本:", (window as any).AMap.version);
          // 设置全局安全密钥配置
          try {
            if ((window as any).AMap.SecurityConfig) {
              (window as any).AMap.SecurityConfig.securityJsCode =
                amapConfig.SECURITY_JSCODE;
              console.log("已全局注册安全密钥");
            }
          } catch (e) {
            console.warn("设置全局安全密钥失败:", e);
          }
          resolve();
        })
        .catch((e: any) => {
          console.error("高德地图API加载失败:", e);
          // 尝试使用备选方式加载
          const fallbackScript = document.createElement("script");
          fallbackScript.type = "text/javascript";
          fallbackScript.async = true;
          fallbackScript.src = `https://webapi.amap.com/maps?v=${
            amapConfig.JS_API_CONFIG.VERSION
          }&key=${
            amapConfig.JS_API_KEY
          }&plugin=${amapConfig.JS_API_CONFIG.PLUGINS.join(",")}&security=${
            amapConfig.SECURITY_JSCODE
          }`;

          fallbackScript.onload = () => {
            console.log("使用备选方式加载高德地图成功");
            try {
              if ((window as any).AMap.SecurityConfig) {
                (window as any).AMap.SecurityConfig.securityJsCode =
                  amapConfig.SECURITY_JSCODE;
                console.log("已全局注册安全密钥(备选方式)");
              }
            } catch (e) {
              console.warn("设置全局安全密钥失败(备选方式):", e);
            }
            resolve();
          };

          fallbackScript.onerror = (error) => {
            console.error("高德地图备选加载失败:", error);
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
      console.error("高德地图loader加载失败:", error);
      reject(new Error("高德地图加载器加载失败"));
    };

    document.head.appendChild(loaderScript);
  });
};

// 初始化地图
const initMap = () => {
  if (!mapContainer.value || !(window as any).AMap) return;

  try {
    // 使用类型断言解决TypeScript错误
    const AMap = (window as any).AMap;

    // 创建地图实例
    map = new AMap.Map(mapContainer.value, {
      zoom: 12,
      center: [amapConfig.DEFAULT_CENTER.lng, amapConfig.DEFAULT_CENTER.lat],
      viewMode: "2D",
      securityJsCode: amapConfig.SECURITY_JSCODE,
    });

    // 创建驾车规划实例
    drivingInstance = new AMap.Driving({
      policy: 0, // 0表示最快捷模式，不使用字符串常量
      map: map,
      securityJsCode: amapConfig.SECURITY_JSCODE,
    });

    // 创建起点和终点的标记
    originMarker = new AMap.Marker({
      map: map,
      visible: false,
      draggable: true,
      content: '<div class="custom-marker origin-marker">A</div>',
    });

    destinationMarker = new AMap.Marker({
      map: map,
      visible: false,
      draggable: true,
      content: '<div class="custom-marker destination-marker">B</div>',
    });

    // 标记拖拽结束事件
    originMarker.on("dragend", (e: any) => {
      const position = e.target.getPosition();
      updateLocationFromMarker(position, "origin");
    });

    destinationMarker.on("dragend", (e: any) => {
      const position = e.target.getPosition();
      updateLocationFromMarker(position, "destination");
    });

    console.log("地图初始化成功", AMap.version);
  } catch (error) {
    console.error("地图初始化错误:", error);
    ElMessage.error("地图初始化失败，请刷新页面重试");
  }
};

// 清理地图资源
onUnmounted(() => {
  if (map) {
    map.destroy();
  }
});

// 处理地图点击事件
const handleMapClick = (e: any) => {
  const position = e.lnglat;
  // 根据当前搜索模式确定是设置起点还是终点
  if (searchMode.value === "origin") {
    setMarker("origin", { lng: position.lng, lat: position.lat });
    updateLocationFromMarker(position, "origin");
  } else {
    setMarker("destination", { lng: position.lng, lat: position.lat });
    updateLocationFromMarker(position, "destination");
  }
};

// 设置标记点
const setMarker = (type: "origin" | "destination", location: Location) => {
  const marker = type === "origin" ? originMarker : destinationMarker;
  marker.setPosition([location.lng, location.lat]);
  marker.show();

  // 调整地图视野以包含所有标记
  adjustMapView();
};

// 调整地图视野以包含所有可见的标记
const adjustMapView = () => {
  const markers = [];
  if (originMarker && originMarker.getVisible()) {
    markers.push(originMarker);
  }
  if (destinationMarker && destinationMarker.getVisible()) {
    markers.push(destinationMarker);
  }

  if (markers.length > 0) {
    map.setFitView(markers);
  }
};

// 处理搜索输入
const handleSearchInput = (type: "origin" | "destination") => {
  const keyword =
    type === "origin" ? originKeyword.value : destinationKeyword.value;

  if (!keyword) {
    searchResults.value = [];
    return;
  }

  try {
    // 构建高德地图V5版本POI搜索API参数
    const params = new URLSearchParams({
      key: amapConfig.getApiKey(), // 使用getApiKey()获取正确的Key
      keywords: keyword,
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
        amapConfig.logApiRequest("POI搜索", params.toString(), result);

        if (result.status === "1" && result.pois && result.pois.length > 0) {
          searchResults.value = result.pois.map((poi: any) => ({
            id: poi.id,
            name: poi.name,
            address: poi.address || "暂无详细地址",
            location: {
              lng: parseFloat(poi.location.split(",")[0]),
              lat: parseFloat(poi.location.split(",")[1]),
            },
            // 保存原始POI对象，以便获取更多信息
            original: poi,
          }));
        } else {
          searchResults.value = [];
          if (result.status === "0") {
            // 详细记录API错误
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
          }
        }
      })
      .catch((error) => {
        console.error("POI搜索错误:", error);
        searchResults.value = [];
        ElMessage.error({
          message: "地点搜索服务异常，请重试: " + error.message,
          duration: 5000,
        });
      });
  } catch (error) {
    console.error("POI搜索参数构建错误:", error);
    ElMessage.error({
      message: "搜索参数错误，请联系管理员",
      duration: 5000,
    });
  }
};

// 更新模型值
const updateModelValue = (
  type: "origin" | "destination",
  value: LocationValue
) => {
  console.log(`更新${type}位置:`, value);

  const newValue = { ...props.modelValue };
  if (type === "origin") {
    newValue.origin = {
      ...value,
      // 确保location对象为深拷贝
      location: { ...value.location },
    };
  } else {
    newValue.destination = {
      ...value,
      // 确保location对象为深拷贝
      location: { ...value.location },
    };
  }

  console.log("发送新值到父组件:", newValue);
  emit("update:modelValue", newValue);
};

// 选择地点
const selectPlace = (place: any, type: "origin" | "destination") => {
  console.log(`选择${type}地点:`, place);

  // 确保place对象完整且有效
  if (!place || !place.location || !place.name) {
    console.error("选择的地点数据不完整", place);
    ElMessage.warning("地点数据不完整，请重新选择");
    return;
  }

  // 设置搜索框显示文本
  if (type === "origin") {
    originKeyword.value = place.name;
  } else {
    destinationKeyword.value = place.name;
  }

  // 设置标记
  setMarker(type, place.location);

  // 更新位置信息
  const locationInfo = {
    name: place.name,
    location: { ...place.location }, // 深拷贝确保引用独立
    // 保存POI ID，可用于后续查询
    id: place.id || "",
    // 如果有地址，也保存下来
    address: place.address || "",
    original: place.original || null,
  };

  // 打印调试信息
  console.log(`准备更新${type}信息:`, locationInfo);

  updateModelValue(type, locationInfo);

  // 清空搜索结果
  searchResults.value = [];

  // 如果起点和终点都已设置，则规划路线
  const currentValue = props.modelValue;
  if (
    currentValue.origin &&
    currentValue.origin.location.lng &&
    currentValue.destination &&
    currentValue.destination.location.lng
  ) {
    planRoute();
  }
};

// 从标记更新位置信息（通过地理编码获取地点名称）
const updateLocationFromMarker = (
  position: any,
  type: "origin" | "destination"
) => {
  console.log(`从标记更新${type}位置:`, position);

  try {
    // 改用REST API进行逆地理编码，避免安全密钥问题
    const params = new URLSearchParams({
      key: amapConfig.getApiKeyForService(amapConfig.API_CONFIG.REGEOCODE),
      location: `${position.lng},${position.lat}`,
      ...amapConfig.API_CONFIG.REGEOCODE.DEFAULT_PARAMS,
    });

    const url = `${amapConfig.API_CONFIG.REGEOCODE.URL}?${params.toString()}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP错误 ${response.status}`);
        }
        return response.json();
      })
      .then((result) => {
        // 记录API请求和响应
        amapConfig.logApiRequest("逆地理编码", params.toString(), result);

        if (result.status === "1" && result.regeocode) {
          const name = result.regeocode.formatted_address || "未知地点";
          const location = { lng: position.lng, lat: position.lat };

          console.log(`获取到${type}地点信息:`, name, location);

          // 更新搜索框文本
          if (type === "origin") {
            originKeyword.value = name;
          } else {
            destinationKeyword.value = name;
          }

          // 更新模型值
          const locationInfo = {
            name,
            location: { ...location }, // 深拷贝确保引用独立
            id: "", // 通过点击获取的位置没有POI ID
            address: result.regeocode.formatted_address || "",
            original: result.regeocode, // 保存原始结果
          };

          console.log(`准备从标记更新${type}信息:`, locationInfo);
          updateModelValue(type, locationInfo);

          // 如果起点和终点都已设置，则规划路线
          const currentValue = props.modelValue;
          if (
            currentValue.origin &&
            currentValue.origin.location.lng &&
            currentValue.destination &&
            currentValue.destination.location.lng
          ) {
            planRoute();
          }
        } else {
          console.error("逆地理编码失败:", result.info, result);
          let errorMsg = "无法获取该位置的地址信息";
          if (result && result.info) {
            errorMsg = `地址解析失败: ${amapConfig.getErrorMessage(
              result.infocode
            )}`;
          }
          ElMessage.warning(errorMsg);
        }
      })
      .catch((error) => {
        console.error("逆地理编码请求错误:", error);
        ElMessage.error("地址解析失败，请重试: " + error.message);
      });
  } catch (error) {
    console.error("位置标记处理错误:", error);
    ElMessage.error("地址解析失败，请重试");
  }
};

// 路线规划
const planRoute = () => {
  const { origin, destination } = props.modelValue;

  if (
    !origin ||
    !destination ||
    !origin.location.lng ||
    !destination.location.lng
  ) {
    return;
  }

  const originPos = [origin.location.lng, origin.location.lat];
  const destPos = [destination.location.lng, destination.location.lat];

  // 使用带安全密钥的驾车规划实例
  if (!drivingInstance._opts || !drivingInstance._opts.securityJsCode) {
    // 如果之前的实例未配置安全密钥，重新创建一个
    const AMap = (window as any).AMap;
    drivingInstance = new AMap.Driving({
      policy: 0,
      map: map,
      securityJsCode: amapConfig.SECURITY_JSCODE,
    });
  }

  drivingInstance.search(originPos, destPos, (status: string, result: any) => {
    if (status === "complete") {
      console.log("路径规划成功");
      // 路径规划成功，结果已自动显示在地图上
    } else {
      console.error("路径规划失败:", status, result);
      let errorMsg = "路径规划失败";
      if (result && result.info) {
        errorMsg = `路径规划失败: ${amapConfig.getErrorMessage(
          result.infocode
        )}`;
      }
      ElMessage.warning(errorMsg);
    }
  });
};

// 监听输入变化
watch(
  () => props.modelValue,
  (newValue) => {
    // 如果是外部更新了值，则更新标记和搜索框
    if (newValue.origin && newValue.origin.name) {
      originKeyword.value = newValue.origin.name;
      if (newValue.origin.location.lng) {
        setMarker("origin", newValue.origin.location);
      }
    }

    if (newValue.destination && newValue.destination.name) {
      destinationKeyword.value = newValue.destination.name;
      if (newValue.destination.location.lng) {
        setMarker("destination", newValue.destination.location);
      }
    }

    // 如果起点和终点都有值，尝试规划路线
    if (
      newValue.origin &&
      newValue.origin.location.lng &&
      newValue.destination &&
      newValue.destination.location.lng
    ) {
      planRoute();
    }
  },
  { deep: true }
);
</script>

<style scoped>
.map-selector {
  position: relative;
  width: 100%;
  height: 500px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.map-container {
  width: 100%;
  height: 100%;
}

.search-controls {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 320px;
  z-index: 100;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 10px;
}

.search-box {
  position: relative;
  margin-bottom: 10px;
}

.search-header {
  display: flex;
  align-items: center;
}

.icon-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  margin-right: 10px;
  color: white;
  font-weight: bold;
}

.icon-wrapper.origin {
  background-color: #67c23a;
}

.icon-wrapper.destination {
  background-color: #f56c6c;
}

.marker-icon {
  font-size: 12px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.result-item {
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.result-item:hover {
  background-color: #f9f9f9;
}

.item-name {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 4px;
}

.item-address {
  font-size: 12px;
  color: #999;
}

/* 自定义地图标记样式 */
:deep(.custom-marker) {
  width: 25px;
  height: 25px;
  border-radius: 50%;
  color: #fff;
  font-weight: bold;
  text-align: center;
  line-height: 25px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
}

:deep(.origin-marker) {
  background-color: #67c23a;
}

:deep(.destination-marker) {
  background-color: #f56c6c;
}
</style> 