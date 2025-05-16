<template>
  <div class="route-planning">
    <h2>响应式路线规划</h2>

    <el-card class="planning-card">
      <template #header>
        <div class="card-header">
          <span>规划参数设置</span>
        </div>
      </template>

      <el-form :model="planningForm" label-width="180px">
        <el-form-item label="时间窗口(分钟)">
          <el-slider
            v-model="planningForm.timeWindow"
            :min="10"
            :max="60"
            :step="5"
            :marks="{ 10: '10', 30: '30', 60: '60' }"
            show-input
          >
          </el-slider>
        </el-form-item>

        <el-form-item label="空间距离阈值(公里)">
          <el-slider
            v-model="planningForm.spatialThreshold"
            :min="0.5"
            :max="5"
            :step="0.5"
            :marks="{ 0.5: '0.5', 1: '1', 3: '3', 5: '5' }"
            show-input
          >
          </el-slider>
        </el-form-item>

        <el-form-item label="每条路线最大点数">
          <el-slider
            v-model="planningForm.maxPointsPerRoute"
            :min="4"
            :max="16"
            :step="2"
            :marks="{ 4: '4', 8: '8', 12: '12', 16: '16' }"
            show-input
          >
          </el-slider>
        </el-form-item>

        <el-form-item label="最小聚类样本数">
          <el-slider
            v-model="planningForm.minSamples"
            :min="2"
            :max="6"
            :step="1"
            :marks="{ 2: '2', 4: '4', 6: '6' }"
            show-input
          >
          </el-slider>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="generateRoutes"
            :loading="generating"
            >生成路线</el-button
          >
          <el-button @click="resetForm">重置参数</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="planning-content" v-if="routePlanningResult">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card class="map-card">
            <template #header>
              <div class="card-header">
                <span>路线地图</span>
                <div class="map-controls">
                  <el-radio-group v-model="mapViewMode" size="small">
                    <el-radio-button value="routes">路线视图</el-radio-button>
                    <el-radio-button value="stops">经停点视图</el-radio-button>
                  </el-radio-group>
                  <el-button-group class="map-buttons">
                    <el-button size="small" @click="fitMapView">
                      <el-icon><FullScreen /></el-icon>
                      适应视图
                    </el-button>
                    <el-button size="small" @click="clearMapOverlays">
                      <el-icon><Delete /></el-icon> 清除标记
                    </el-button>
                  </el-button-group>
                </div>
              </div>
            </template>
            <div
              id="map-container"
              ref="mapContainer"
              class="map-container"
            ></div>
          </el-card>
        </el-col>

        <el-col :span="8" v-if="routePlanningResult">
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>规划结果</span>
              </div>
            </template>

            <!-- 聚类统计信息 -->
            <div class="result-summary">
              <el-descriptions title="聚类统计" :column="1" border>
                <el-descriptions-item label="总请求数">{{
                  routePlanningResult.total_requests
                }}</el-descriptions-item>
                <el-descriptions-item label="有效聚类">{{
                  routePlanningResult.valid_clusters
                }}</el-descriptions-item>
                <el-descriptions-item label="计划路线">{{
                  routePlanningResult.planned_routes
                }}</el-descriptions-item>
                <el-descriptions-item label="孤立请求">{{
                  routePlanningResult.noise_points
                }}</el-descriptions-item>
                <el-descriptions-item label="处理时间"
                  >{{
                    (routePlanningResult.processing_time || 0).toFixed(2)
                  }}秒</el-descriptions-item
                >
              </el-descriptions>
            </div>

            <!-- 路线列表 -->
            <div class="route-list">
              <h3>
                规划路线 ({{
                  Object.keys(routePlanningResult.routes).length
                }}条)
              </h3>
              <el-collapse v-model="activeRoutes">
                <el-collapse-item
                  v-for="(route, id) in routePlanningResult.routes"
                  :key="id"
                  :title="`路线 ${id} (${route.trip_count}个请求, ${route.passenger_count}位乘客)`"
                  :name="id"
                >
                  <div class="route-details">
                    <p>
                      <strong>总距离:</strong>
                      {{ (route.total_distance / 1000).toFixed(2) }}公里
                    </p>
                    <p>
                      <strong>预计时间:</strong>
                      {{ Math.floor(route.total_duration / 60) }}分钟
                    </p>
                    <p><strong>接送分段:</strong></p>
                    <el-steps
                      direction="vertical"
                      :active="2"
                      finish-status="success"
                    >
                      <el-step
                        title="接乘客阶段"
                        :description="`${(
                          route.pickup_route.distance / 1000
                        ).toFixed(2)}公里, ${Math.floor(
                          route.pickup_route.duration / 60
                        )}分钟`"
                      ></el-step>
                      <el-step
                        title="送乘客阶段"
                        :description="`${(
                          route.dropoff_route.distance / 1000
                        ).toFixed(2)}公里, ${Math.floor(
                          route.dropoff_route.duration / 60
                        )}分钟`"
                      ></el-step>
                    </el-steps>
                    <el-button
                      type="primary"
                      size="small"
                      @click="viewRouteDetail(route, id)"
                      >查看详情</el-button
                    >
                    <el-button
                      type="success"
                      size="small"
                      @click="confirmRoute(route, id)"
                      >确认发车</el-button
                    >
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 请求数据提示 -->
    <el-empty
      v-if="!routePlanningResult && !generating"
      description="请设置参数并生成路线"
    ></el-empty>

    <!-- 加载中提示 -->
    <div class="loading-container" v-if="generating">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 路线详情对话框 -->
    <el-dialog
      v-model="routeDetailVisible"
      title="路线详情"
      width="80%"
      destroy-on-close
    >
      <div class="route-detail-content">
        <el-tabs>
          <el-tab-pane label="乘客信息">
            <el-table :data="selectedRoutePassengers" stripe>
              <el-table-column
                prop="request_id"
                label="请求ID"
                width="90"
              ></el-table-column>
              <el-table-column
                prop="origin_name"
                label="起点"
                min-width="150"
              ></el-table-column>
              <el-table-column
                prop="destination_name"
                label="终点"
                min-width="150"
              ></el-table-column>
              <el-table-column prop="departure_time" label="出发时间">
                <template #default="scope">
                  {{ formatDateTime(scope.row.departure_time) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="people_count"
                label="人数"
                width="90"
              ></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="接送路线">
            <div class="pickup-route">
              <h4>接乘客路线</h4>
              <ol class="route-steps">
                <li
                  v-for="(step, index) in selectedRoute?.pickup_route?.steps"
                  :key="'pickup-' + index"
                >
                  {{ step.instruction }}
                  <div class="step-details">
                    {{ (step.distance / 1000).toFixed(2) }}公里 |
                    {{ Math.floor(step.duration / 60) }}分钟
                  </div>
                </li>
              </ol>
            </div>
            <div class="dropoff-route">
              <h4>送乘客路线</h4>
              <ol class="route-steps">
                <li
                  v-for="(step, index) in selectedRoute?.dropoff_route?.steps"
                  :key="'dropoff-' + index"
                >
                  {{ step.instruction }}
                  <div class="step-details">
                    {{ (step.distance / 1000).toFixed(2) }}公里 |
                    {{ Math.floor(step.duration / 60) }}分钟
                  </div>
                </li>
              </ol>
            </div>
          </el-tab-pane>
          <el-tab-pane label="统计信息">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总距离"
                >{{
                  ((selectedRoute?.total_distance || 0) / 1000).toFixed(2)
                }}公里</el-descriptions-item
              >
              <el-descriptions-item label="预计时间"
                >{{
                  Math.floor((selectedRoute?.total_duration || 0) / 60)
                }}分钟</el-descriptions-item
              >
              <el-descriptions-item label="乘客数"
                >{{
                  selectedRoute?.passenger_count || 0
                }}人</el-descriptions-item
              >
              <el-descriptions-item label="请求数"
                >{{ selectedRoute?.trip_count || 0 }}个</el-descriptions-item
              >
              <el-descriptions-item label="每位乘客成本"
                >¥{{
                  (selectedRoute?.cost_per_passenger || 0).toFixed(2)
                }}</el-descriptions-item
              >
              <el-descriptions-item label="效率"
                >{{
                  (selectedRoute?.efficiency || 0).toFixed(2)
                }}米/乘客</el-descriptions-item
              >
            </el-descriptions>
          </el-tab-pane>
        </el-tabs>

        <div class="dialog-footer">
          <el-button @click="routeDetailVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleConfirmRoute"
            >确认发车</el-button
          >
        </div>
      </div>
    </el-dialog>

    <!-- 确认发车对话框 -->
    <el-dialog v-model="confirmRouteVisible" title="确认发车" width="400px">
      <p>确定为以下路线安排发车吗？</p>
      <div class="confirm-route-info">
        <p><strong>路线:</strong> {{ selectedRouteId }}</p>
        <p>
          <strong>乘客数:</strong> {{ selectedRoute?.passenger_count || 0 }}人
        </p>
        <p>
          <strong>总距离:</strong>
          {{ ((selectedRoute?.total_distance || 0) / 1000).toFixed(2) }}公里
        </p>
        <p>
          <strong>预计时间:</strong>
          {{ Math.floor((selectedRoute?.total_duration || 0) / 60) }}分钟
        </p>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="confirmRouteVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRouteDispatch"
            >确认发车</el-button
          >
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import amapConfig from "../utils/amapConfig";
import mapInitializer from "../utils/mapInitializer";
import { FullScreen, Delete } from "@element-plus/icons-vue";

// 类型定义
interface Location {
  lat: number;
  lng: number;
}

interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
}

interface RouteSegment {
  distance: number;
  duration: number;
  polyline: Location[];
  steps: RouteStep[];
  start_location: Location;
  end_location: Location;
  waypoints: Location[];
}

interface Route {
  pickup_route: RouteSegment;
  dropoff_route: RouteSegment;
  total_distance: number;
  total_duration: number;
  passenger_count: number;
  trip_count: number;
  cost_per_passenger: number;
  efficiency: number;
  is_fallback?: boolean;
  fallback_reason?: string;
}

interface PlanningResult {
  success: boolean;
  processing_time: number;
  total_requests: number;
  valid_clusters: number;
  noise_points: number;
  planned_routes: number;
  clusters: Record<string, any>;
  routes: Record<string, Route>;
  timestamp: string;
}

// 定义高德地图类型
interface AMapType {
  Bounds: new (sw: [number, number], ne: [number, number]) => any;
  Polyline: new (options: any) => any;
  Marker: new (options: any) => {
    setMap: (map: any) => void;
    getPosition: () => any;
    on: (event: string, handler: Function) => void;
  };
  Pixel: new (x: number, y: number) => any;
  Icon: new (options: any) => any;
  InfoWindow: new (options: any) => {
    open: (map: any, position: any) => void;
    close: () => void;
  };
  Size: new (width: number, height: number) => any;
}

declare global {
  interface Window {
    AMap: AMapType;
  }
}

// 路线颜色配置
const ROUTE_COLORS = {
  PICKUP: "#2ecc71", // 接乘客路线颜色（绿色）
  DROPOFF: "#e74c3c", // 送乘客路线颜色（红色）
  MARKER: "#3498db", // 站点标记颜色（蓝色）
};

// 地图相关状态
const mapInstance = ref<any>(null);
const mapContainer = ref<HTMLElement | null>(null);
const mapMarkers = ref<any[]>([]);
const mapPolylines = ref<any[]>([]);
const mapInfoWindows = ref<any[]>([]);

// 表单数据
const planningForm = reactive({
  timeWindow: 60,
  spatialThreshold: 2.0,
  maxPointsPerRoute: 8,
  minSamples: 2,
});

// 路线规划结果
const routePlanningResult = ref<PlanningResult | null>(null);
const generating = ref(false);
const activeRoutes = ref<string[]>([]);
const mapViewMode = ref<"routes" | "stops">("routes");

// 路线详情弹窗
const routeDetailVisible = ref(false);
const selectedRoute = ref<Route | null>(null);
const selectedRouteId = ref<string | null>(null);
const selectedRoutePassengers = ref<any[]>([]);

// 确认发车弹窗
const confirmRouteVisible = ref(false);

// 地图边界对象
const mapBounds = ref<any>(null);

// 验证坐标点是否有效
const isValidCoordinate = (lng: number, lat: number): boolean => {
  return (
    !isNaN(lng) &&
    !isNaN(lat) &&
    lng >= -180 &&
    lng <= 180 &&
    lat >= -90 &&
    lat <= 90
  );
};

// 初始化
onMounted(async () => {
  console.log("组件挂载，开始初始化地图...");

  try {
    if (!mapContainer.value) {
      console.error("地图容器元素未找到");
      throw new Error("地图容器元素未找到");
    }

    // 检查容器尺寸
    const containerWidth = mapContainer.value.clientWidth;
    const containerHeight = mapContainer.value.clientHeight;

    console.log("地图容器状态:", {
      container: mapContainer.value,
      id: mapContainer.value.id,
      clientWidth: containerWidth,
      clientHeight: containerHeight,
      offsetWidth: mapContainer.value.offsetWidth,
      offsetHeight: mapContainer.value.offsetHeight,
      style: mapContainer.value.style,
    });

    if (containerWidth === 0 || containerHeight === 0) {
      console.error("地图容器尺寸为0");
      throw new Error("地图容器尺寸异常，请检查样式");
    }

    // 等待DOM完全渲染
    await nextTick();

    // 初始化地图
    mapInstance.value = await mapInitializer.initMap({
      container: mapContainer.value,
      zoom: 12,
      center: [amapConfig.DEFAULT_CENTER.lng, amapConfig.DEFAULT_CENTER.lat],
      plugins: ["AMap.Scale", "AMap.ToolBar", "AMap.Driving"],
      viewMode: "2D",
    });

    console.log("地图初始化成功:", mapInstance.value);
  } catch (error) {
    console.error("地图初始化失败:", error);
    ElMessage.error("地图初始化失败，请刷新页面重试");
  }
});

// 清理资源
onUnmounted(() => {
  console.log("组件卸载，清理地图资源...");
  if (mapInstance.value) {
    mapInitializer.clearMapInstance(mapInstance.value);
  }
});

// 监听地图视图模式变化
watch(mapViewMode, (newMode) => {
  if (routePlanningResult.value) {
    if (newMode === "routes") {
      displayRoutesOnMap(routePlanningResult.value);
    } else {
      displayStopsOnMap(routePlanningResult.value);
    }
  }
});

// 初始化地图
const initMap = async () => {
  try {
    if (!mapContainer.value) {
      throw new Error("地图容器未找到");
    }

    // 等待容器渲染完成
    await nextTick();

    // 检查容器尺寸
    const containerWidth = mapContainer.value.clientWidth;
    const containerHeight = mapContainer.value.clientHeight;

    if (containerWidth === 0 || containerHeight === 0) {
      throw new Error("地图容器尺寸异常，请检查样式");
    }

    console.log("开始初始化地图...");
    mapInstance.value = await mapInitializer.initMap({
      container: mapContainer.value,
      zoom: amapConfig.DEFAULT_CENTER.zoom,
      center: [amapConfig.DEFAULT_CENTER.lng, amapConfig.DEFAULT_CENTER.lat],
      viewMode: "2D",
    });

    // 添加地图加载完成事件监听
    mapInstance.value.on("complete", () => {
      console.log("地图加载完成");
    });

    // 添加地图错误事件监听
    mapInstance.value.on("error", (error: any) => {
      console.error("地图加载错误:", error);
      ElMessage.error("地图加载出错，请刷新页面重试");
    });

    console.log("地图初始化成功");
  } catch (error) {
    console.error("地图初始化失败:", error);
    ElMessage.error("地图初始化失败，请刷新页面重试");
    throw error;
  }
};

// 创建标记点
const createMarker = (position: [number, number], options: any = {}): any => {
  if (!isValidCoordinate(position[0], position[1])) {
    throw new Error("无效的坐标点");
  }

  const AMap = (window as any).AMap;
  return new AMap.Marker({
    position,
    offset: new AMap.Pixel(-12, -17),
    ...options,
  });
};

// 创建信息窗口
const createInfoWindow = (
  content: string,
  offset: [number, number] = [0, -30]
): any => {
  const AMap = (window as any).AMap;
  return new AMap.InfoWindow({
    content,
    offset: new AMap.Pixel(offset[0], offset[1]),
    closeWhenClickMap: true,
  });
};

// 显示经停点
const displayStopsOnMap = (result: PlanningResult) => {
  console.log("开始显示经停点，检查参数:", {
    hasMap: !!mapInstance.value,
    hasResult: !!result,
    hasClusters: result?.clusters ? Object.keys(result.clusters).length : 0,
  });

  if (!mapInstance.value) {
    console.error("地图未初始化");
    ElMessage.error("地图未初始化，请刷新页面重试");
    return;
  }

  if (
    !result ||
    !result.clusters ||
    Object.keys(result.clusters).length === 0
  ) {
    console.error("聚类数据为空");
    ElMessage.error("没有找到可显示的聚类数据");
    return;
  }

  try {
    clearMapOverlays();

    const AMap = (window as any).AMap;
    const bounds = new AMap.Bounds([0, 0], [0, 0]);
    let validClusterCount = 0;

    // 处理每个聚类
    for (const [clusterId, cluster] of Object.entries(result.clusters)) {
      if (clusterId === "-1") continue; // 跳过噪声点

      try {
        if (
          !cluster.center_origin ||
          !cluster.center_destination ||
          !isValidCoordinate(
            cluster.center_origin.lng,
            cluster.center_origin.lat
          ) ||
          !isValidCoordinate(
            cluster.center_destination.lng,
            cluster.center_destination.lat
          )
        ) {
          console.warn(`聚类 ${clusterId} 中心点坐标无效，已跳过`);
          continue;
        }

        // 创建起点标记
        const originMarker = createMarker(
          [cluster.center_origin.lng, cluster.center_origin.lat],
          {
            content: `<div class="custom-marker origin-marker">起${clusterId}</div>`,
            offset: new AMap.Pixel(-12, -12),
          }
        );

        // 创建起点信息窗口
        const originInfoWindow = createInfoWindow(`
          <div class="cluster-info">
            <h4>聚类 ${clusterId} - 起点</h4>
            <p>请求数: ${cluster.trips.length}</p>
            <p>总人数: ${cluster.total_passengers}</p>
          </div>
        `);

        // 添加鼠标事件
        originMarker.on("mouseover", () => {
          originInfoWindow.open(mapInstance.value, originMarker.getPosition());
        });

        originMarker.on("mouseout", () => {
          originInfoWindow.close();
        });

        originMarker.setMap(mapInstance.value);
        mapMarkers.value.push(originMarker);
        mapInfoWindows.value.push(originInfoWindow);

        // 创建终点标记
        const destMarker = createMarker(
          [cluster.center_destination.lng, cluster.center_destination.lat],
          {
            content: `<div class="custom-marker dest-marker">终${clusterId}</div>`,
            offset: new AMap.Pixel(-12, -12),
          }
        );

        // 创建终点信息窗口
        const destInfoWindow = createInfoWindow(`
          <div class="cluster-info">
            <h4>聚类 ${clusterId} - 终点</h4>
            <p>请求数: ${cluster.trips.length}</p>
            <p>总人数: ${cluster.total_passengers}</p>
          </div>
        `);

        // 添加鼠标事件
        destMarker.on("mouseover", () => {
          destInfoWindow.open(mapInstance.value, destMarker.getPosition());
        });

        destMarker.on("mouseout", () => {
          destInfoWindow.close();
        });

        destMarker.setMap(mapInstance.value);
        mapMarkers.value.push(destMarker);
        mapInfoWindows.value.push(destInfoWindow);

        // 更新地图边界
        bounds.extend([cluster.center_origin.lng, cluster.center_origin.lat]);
        bounds.extend([
          cluster.center_destination.lng,
          cluster.center_destination.lat,
        ]);

        validClusterCount++;
      } catch (error) {
        console.error(`处理聚类 ${clusterId} 时出错:`, error);
      }
    }

    // 调整地图视野
    if (validClusterCount > 0) {
      try {
        mapInstance.value.setBounds(bounds);
      } catch (error) {
        console.error("设置地图视图范围时出错:", error);
        mapInstance.value.setCenter([
          amapConfig.DEFAULT_CENTER.lng,
          amapConfig.DEFAULT_CENTER.lat,
        ]);
        mapInstance.value.setZoom(amapConfig.DEFAULT_CENTER.zoom);
      }
    } else {
      console.warn("没有找到有效的聚类数据用于显示");
      ElMessage.warning("无法显示经停点，没有有效的聚类数据");
    }
  } catch (error) {
    console.error("显示经停点时出错:", error);
    ElMessage.error("显示经停点时出错，请重试");
  }
};

// 在地图上显示路线
const displayRoutesOnMap = async (result: PlanningResult) => {
  console.log("开始显示路线，检查参数:", {
    hasMap: !!mapInstance.value,
    hasResult: !!result,
    hasRoutes: result?.routes ? Object.keys(result.routes).length : 0,
  });

  if (!mapInstance.value) {
    try {
      await initMap();
    } catch (error: any) {
      console.error("显示路线时初始化地图失败:", error);
      ElMessage.error("地图初始化失败，无法显示路线");
      return;
    }
  }

  if (!result.routes || Object.keys(result.routes).length === 0) {
    console.error("路线数据为空");
    ElMessage.error("没有找到可显示的路线数据");
    return;
  }

  // 清除之前的路线
  clearMapOverlays();

  const AMap = window.AMap;
  const bounds = new AMap.Bounds([0, 0], [0, 0]);
  const routeColors = [
    "#ff4d4f",
    "#40a9ff",
    "#52c41a",
    "#faad14",
    "#722ed1",
    "#eb2f96",
  ];

  try {
    let colorIndex = 0;
    for (const [routeId, route] of Object.entries(result.routes)) {
      const color = routeColors[colorIndex % routeColors.length];
      colorIndex++;

      // 绘制接乘客路线
      if (route.pickup_route?.polyline) {
        const pickupPath = route.pickup_route.polyline.map((point) => [
          point.lng,
          point.lat,
        ]);
        const pickupPolyline = new AMap.Polyline({
          path: pickupPath,
          strokeColor: color,
          strokeWeight: 6,
          strokeOpacity: 0.8,
          strokeStyle: "solid",
          showDir: true,
          zIndex: 100,
        });

        pickupPolyline.setMap(mapInstance.value);
        mapPolylines.value.push(pickupPolyline);

        // 更新地图边界
        pickupPath.forEach((point) => bounds.extend(point));
      }

      // 绘制送乘客路线
      if (route.dropoff_route?.polyline) {
        const dropoffPath = route.dropoff_route.polyline.map((point) => [
          point.lng,
          point.lat,
        ]);
        const dropoffPolyline = new AMap.Polyline({
          path: dropoffPath,
          strokeColor: color,
          strokeWeight: 6,
          strokeOpacity: 0.8,
          strokeStyle: "dashed",
          showDir: true,
          zIndex: 100,
        });

        dropoffPolyline.setMap(mapInstance.value);
        mapPolylines.value.push(dropoffPolyline);

        // 更新地图边界
        dropoffPath.forEach((point) => bounds.extend(point));

        // 添加路线标签
        const midPoint = dropoffPath[Math.floor(dropoffPath.length / 2)];
        const labelMarker = new AMap.Marker({
          position: midPoint,
          content: `<div class="route-label">路线${routeId}</div>`,
          offset: new AMap.Pixel(-30, -15),
          zIndex: 120,
        });

        labelMarker.setMap(mapInstance.value);
        mapMarkers.value.push(labelMarker);
      }
    }

    // 调整地图视野
    if (!bounds.isEmpty()) {
      mapInstance.value.setBounds(bounds);
    }
  } catch (error: any) {
    console.error("在地图上显示路线时出错:", error);
    ElMessage.error("在地图上显示路线时出错");
  }
};

// 生成路线
const generateRoutes = async () => {
  if (generating.value) return;
  generating.value = true;
  console.log("开始生成路线，准备发起API请求");

  try {
    // 发送请求到后端进行路线规划
    const planUrl = "/api/routes/plan";
    console.log("正在请求规划API:", planUrl, "参数:", planningForm);

    const planningResponse = await fetch(planUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        timeWindow: planningForm.timeWindow,
        spatialThreshold: planningForm.spatialThreshold,
        maxPointsPerRoute: planningForm.maxPointsPerRoute,
        minSamples: planningForm.minSamples,
      }),
    });

    if (!planningResponse.ok) {
      throw new Error(`规划API请求失败: ${planningResponse.status}`);
    }

    const result = await planningResponse.json();
    console.log("规划API响应数据:", result);

    if (result.success && result.data) {
      // 保存规划结果
      routePlanningResult.value = result.data;

      // 检查路线数据
      if (!result.data.routes || Object.keys(result.data.routes).length === 0) {
        console.warn("规划结果中没有路线数据");
        ElMessage.warning("规划结果中没有路线数据");
        generating.value = false;
        return;
      }

      // 确保地图已初始化
      if (!mapInstance.value) {
        await initMap();
      }

      // 显示路线
      if (mapViewMode.value === "routes") {
        await displayRoutesOnMap(result.data);
      } else {
        await displayStopsOnMap(result.data);
      }

      ElMessage.success(`成功规划了 ${result.data.planned_routes} 条路线`);
    } else {
      throw new Error(result.message || "路线规划失败");
    }
  } catch (error) {
    console.error("生成路线出错:", error);
    ElMessage.error(error.message || "生成路线时发生错误，请重试");
  } finally {
    generating.value = false;
  }
};

// 清理地图上的所有覆盖物
const clearMapOverlays = () => {
  try {
    // 清除所有标记点
    mapMarkers.value.forEach((marker) => {
      marker.setMap(null);
    });
    mapMarkers.value = [];

    // 清除所有路线
    mapPolylines.value.forEach((polyline) => {
      polyline.setMap(null);
    });
    mapPolylines.value = [];

    // 清除所有信息窗口
    mapInfoWindows.value.forEach((infoWindow) => {
      infoWindow.close();
    });
    mapInfoWindows.value = [];

    console.log("地图覆盖物已清除");
  } catch (error) {
    console.error("清除地图覆盖物时出错:", error);
  }
};

// 查看路线详情
const viewRouteDetail = async (route: any, routeId: string) => {
  try {
    selectedRoute.value = route;
    selectedRouteId.value = routeId;

    // 获取乘客信息
    const cluster = routePlanningResult.value?.clusters[routeId];
    if (cluster && cluster.trips) {
      selectedRoutePassengers.value = cluster.trips;
    }

    // 显示详情对话框
    routeDetailVisible.value = true;
  } catch (error) {
    console.error("查看路线详情时出错:", error);
    ElMessage.error("查看路线详情失败，请重试");
  }
};

// 确认发车
const confirmRoute = (route: Route, routeId: string) => {
  selectedRoute.value = route;
  selectedRouteId.value = routeId;
  confirmRouteVisible.value = true;
};

// 提交发车安排
const submitRouteDispatch = async () => {
  try {
    if (!selectedRoute.value || !selectedRouteId.value) {
      ElMessage.warning("请先选择要发车的路线");
      return;
    }

    // 调用API确认发车
    const response = await fetch("/api/routes/dispatch", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        routeId: selectedRouteId.value,
        clusterId: selectedRouteId.value,
        planningResult: routePlanningResult.value,
      }),
    });

    const result = await response.json();

    if (result.success) {
      ElMessage.success("已成功安排发车");
      confirmRouteVisible.value = false;

      // 更新路线状态
      if (routePlanningResult.value) {
        // 从结果中移除已确认的路线
        const routes = { ...routePlanningResult.value.routes };
        delete routes[selectedRouteId.value];
        routePlanningResult.value.routes = routes;
        routePlanningResult.value.planned_routes -= 1;

        // 更新地图显示
        if (mapViewMode.value === "routes") {
          await displayRoutesOnMap(routePlanningResult.value);
        } else {
          await displayStopsOnMap(routePlanningResult.value);
        }
      }
    } else {
      ElMessage.error(result.message || "发车安排失败");
    }
  } catch (error) {
    console.error("发车安排出错:", error);
    ElMessage.error("发车安排时发生错误，请重试");
  }
};

// 重置表单
const resetForm = () => {
  planningForm.timeWindow = 60;
  planningForm.spatialThreshold = 2.0;
  planningForm.maxPointsPerRoute = 8;
  planningForm.minSamples = 2;
};

// 格式化日期时间
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return "";

  const date = new Date(dateTimeStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 处理确认发车
const handleConfirmRoute = () => {
  if (selectedRoute.value && selectedRouteId.value) {
    confirmRoute(selectedRoute.value, selectedRouteId.value);
  } else {
    ElMessage.warning("无法确认发车：路线数据不完整");
  }
};

// 适应视图函数
const fitMapView = () => {
  if (mapInstance.value && mapBounds.value) {
    try {
      mapInstance.value.setBounds(mapBounds.value);
    } catch (error) {
      console.error("设置地图视图范围时出错:", error);
      // 如果无法设置bounds，使用默认视图
      mapInstance.value.setZoom(12);
      mapInstance.value.setCenter([121.473701, 31.230416]);
    }
  }
};

// 显示路线
const displayRoute = async (route: any, routeId: string) => {
  try {
    if (!mapInstance.value || !route) {
      throw new Error("地图未初始化或路线数据无效");
    }

    clearMapOverlays();

    const AMap = (window as any).AMap;
    if (!AMap) {
      throw new Error("AMap对象未找到");
    }

    console.log(`开始显示路线 ${routeId}...`, route);

    // 创建接乘客路线
    if (route.pickup_route) {
      // 获取路径点（支持path和polyline两种格式）
      const pickupPath = route.pickup_route.path || route.pickup_route.polyline;

      if (!pickupPath) {
        console.error("接乘客路线缺少路径数据");
        return;
      }

      // 过滤无效坐标点
      const validPickupPath = pickupPath
        .filter((point: any) => isValidCoordinate(point.lng, point.lat))
        .map((point: any) => [point.lng, point.lat]);

      if (validPickupPath.length > 0) {
        const pickupLine = new AMap.Polyline({
          path: validPickupPath,
          strokeColor: ROUTE_COLORS.PICKUP,
          strokeWeight: 6,
          strokeOpacity: 0.8,
          showDir: true,
        });

        pickupLine.setMap(mapInstance.value);
        mapPolylines.value.push(pickupLine);

        // 添加接乘客站点标记
        const stops = route.pickup_route.stops || [];
        stops.forEach((stop: any, index: number) => {
          if (!isValidCoordinate(stop.lng, stop.lat)) {
            console.warn(`接乘客站点 ${index + 1} 坐标无效，已跳过`);
            return;
          }

          try {
            const marker = new AMap.Marker({
              position: [stop.lng, stop.lat],
              icon: new AMap.Icon({
                size: new AMap.Size(25, 34),
                imageSize: new AMap.Size(25, 34),
                image:
                  "https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png",
              }),
              offset: new AMap.Pixel(-12, -17),
            });

            const infoWindow = new AMap.InfoWindow({
              content: `<div class="info-window">
                <h4>接乘客站点 ${index + 1}</h4>
                <p>地址: ${stop.address || "未知地址"}</p>
                <p>乘客数: ${stop.passenger_count || 1}人</p>
              </div>`,
              offset: new AMap.Pixel(0, -30),
            });

            marker.on("click", () => {
              infoWindow.open(mapInstance.value, marker.getPosition());
            });

            marker.setMap(mapInstance.value);
            mapMarkers.value.push(marker);
            mapInfoWindows.value.push(infoWindow);
          } catch (error) {
            console.error(`创建接乘客站点 ${index + 1} 标记时出错:`, error);
          }
        });
      } else {
        console.warn("接乘客路线没有有效的坐标点");
      }
    }

    // 创建送乘客路线
    if (route.dropoff_route) {
      // 获取路径点（支持path和polyline两种格式）
      const dropoffPath =
        route.dropoff_route.path || route.dropoff_route.polyline;

      if (!dropoffPath) {
        console.error("送乘客路线缺少路径数据");
        return;
      }

      // 过滤无效坐标点
      const validDropoffPath = dropoffPath
        .filter((point: any) => isValidCoordinate(point.lng, point.lat))
        .map((point: any) => [point.lng, point.lat]);

      if (validDropoffPath.length > 0) {
        const dropoffLine = new AMap.Polyline({
          path: validDropoffPath,
          strokeColor: ROUTE_COLORS.DROPOFF,
          strokeWeight: 6,
          strokeOpacity: 0.8,
          showDir: true,
        });

        dropoffLine.setMap(mapInstance.value);
        mapPolylines.value.push(dropoffLine);

        // 添加送乘客站点标记
        const stops = route.dropoff_route.stops || [];
        stops.forEach((stop: any, index: number) => {
          if (!isValidCoordinate(stop.lng, stop.lat)) {
            console.warn(`送乘客站点 ${index + 1} 坐标无效，已跳过`);
            return;
          }

          try {
            const marker = new AMap.Marker({
              position: [stop.lng, stop.lat],
              icon: new AMap.Icon({
                size: new AMap.Size(25, 34),
                imageSize: new AMap.Size(25, 34),
                image:
                  "https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png",
              }),
              offset: new AMap.Pixel(-12, -17),
            });

            const infoWindow = new AMap.InfoWindow({
              content: `<div class="info-window">
                <h4>送乘客站点 ${index + 1}</h4>
                <p>地址: ${stop.address || "未知地址"}</p>
                <p>下车人数: ${stop.passenger_count || 1}人</p>
              </div>`,
              offset: new AMap.Pixel(0, -30),
            });

            marker.on("click", () => {
              infoWindow.open(mapInstance.value, marker.getPosition());
            });

            marker.setMap(mapInstance.value);
            mapMarkers.value.push(marker);
            mapInfoWindows.value.push(infoWindow);
          } catch (error) {
            console.error(`创建送乘客站点 ${index + 1} 标记时出错:`, error);
          }
        });
      } else {
        console.warn("送乘客路线没有有效的坐标点");
      }
    }

    // 调整地图视野以包含所有覆盖物
    const allOverlays = [...mapPolylines.value, ...mapMarkers.value];
    if (allOverlays.length > 0) {
      try {
        mapInstance.value.setFitView(allOverlays);
      } catch (error) {
        console.error("调整地图视野时出错:", error);
        // 如果调整视野失败，使用默认中心点
        mapInstance.value.setCenter([
          amapConfig.DEFAULT_CENTER.lng,
          amapConfig.DEFAULT_CENTER.lat,
        ]);
        mapInstance.value.setZoom(amapConfig.DEFAULT_CENTER.zoom);
      }
    }

    console.log(`路线 ${routeId} 显示完成`);
  } catch (error) {
    console.error("显示路线时出错:", error);
    ElMessage.error("显示路线时出错，请重试");
  }
};
</script>

<style scoped>
.route-planning {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.planning-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-card {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.map-card :deep(.el-card__body) {
  flex: 1;
  padding: 0;
  position: relative;
  min-height: 400px;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
}

.result-card {
  height: 600px;
  overflow: auto;
}

.result-summary {
  margin-bottom: 20px;
}

.route-list {
  margin-top: 20px;
}

.route-details {
  padding: 10px;
}

.loading-container {
  margin-top: 40px;
  padding: 20px;
}

.route-detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.pickup-route,
.dropoff-route {
  margin-bottom: 30px;
}

.route-steps {
  padding-left: 20px;
}

.route-steps li {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.step-details {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.dialog-footer {
  margin-top: 20px;
  text-align: right;
}

.confirm-route-info {
  margin: 20px 0;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

/* 自定义标记样式 */
:deep(.custom-marker) {
  width: 24px;
  height: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  color: white;
  font-size: 12px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

:deep(.origin-marker) {
  background-color: #ff4d4f;
}

:deep(.dest-marker) {
  background-color: #52c41a;
}

:deep(.pickup-start) {
  background-color: #40a9ff;
}

:deep(.dropoff-end) {
  background-color: #722ed1;
}

:deep(.fallback) {
  opacity: 0.7;
  border: 2px dashed #faad14;
}

:deep(.route-label) {
  padding: 4px 8px;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

:deep(.cluster-info) {
  padding: 10px;
  max-width: 300px;
}

:deep(.cluster-info h4) {
  margin: 0 0 10px 0;
  color: #1890ff;
}

:deep(.cluster-info p) {
  margin: 5px 0;
  font-size: 13px;
}

.map-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.map-buttons {
  margin-left: 16px;
}

.info-window {
  padding: 10px;
}

.info-window h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.info-window p {
  margin: 5px 0;
  color: #666;
}
</style> 