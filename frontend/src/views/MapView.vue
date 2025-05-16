<template>
  <div class="map-container">
    <div id="map" class="map"></div>

    <div class="control-panel">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>地图控制</span>
          </div>
        </template>
        <el-form label-position="top">
          <el-form-item label="显示内容">
            <el-checkbox-group v-model="displayOptions">
              <el-checkbox value="routes">路线</el-checkbox>
              <el-checkbox value="vehicles">车辆</el-checkbox>
              <el-checkbox value="stops">站点</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="timeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
            />
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import { ElMessage } from "element-plus";

const displayOptions = ref(["routes", "vehicles", "stops"]);
const timeRange = ref([]);
let map: any = null;

// 初始化地图
const initMap = async () => {
  try {
    // 确保地图容器存在且有尺寸
    const mapContainer = document.getElementById("map");
    if (!mapContainer) {
      throw new Error("地图容器不存在");
    }

    // 设置地图容器的尺寸
    mapContainer.style.width = "100%";
    mapContainer.style.height = "100%";

    const AMap = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_KEY,
      version: "2.0",
      plugins: [
        "AMap.ToolBar",
        "AMap.Scale",
        "AMap.HawkEye",
        "AMap.MapType",
        "AMap.Geolocation", // 添加定位插件
      ],
      securityJsCode: import.meta.env.VITE_AMAP_SECURITY_JS_CODE,
    });

    // 创建地图实例
    map = new AMap.Map("map", {
      zoom: 13, // 调整默认缩放级别
      viewMode: "3D",
      resizeEnable: true,
    });

    // 等待地图加载完成后再添加控件
    map.on("complete", () => {
      console.log("地图加载完成");
      // 添加控件
      map.addControl(new AMap.ToolBar());
      map.addControl(new AMap.Scale());
      map.addControl(new AMap.HawkEye({ isOpen: true }));
      map.addControl(new AMap.MapType());

      // 添加定位控件
      const geolocation = new AMap.Geolocation({
        enableHighAccuracy: true, // 是否使用高精度定位，默认:true
        timeout: 10000, // 超过10秒后停止定位，默认：无穷大
        zoomToAccuracy: true, // 定位成功后调整地图视野范围使定位位置及精度范围视野内可见，默认：false
        position: "RB", // 定位按钮停靠位置，默认：'LB'，左下角
      });

      map.addControl(geolocation);

      // 定位成功后触发
      geolocation.getCurrentPosition((status: string, result: any) => {
        if (status === "complete") {
          console.log("定位成功", result);
          // 定位成功，将地图中心设置为当前位置
          map.setCenter([result.position.lng, result.position.lat]);

          // 添加定位标记
          const marker = new AMap.Marker({
            position: [result.position.lng, result.position.lat],
            title: "我的位置",
            icon: new AMap.Icon({
              size: new AMap.Size(25, 34),
              image: "https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png",
              imageSize: new AMap.Size(25, 34),
            }),
          });
          marker.setMap(map);
        } else {
          console.error("定位失败", result);
          ElMessage.error("定位失败，请检查定位权限或刷新页面重试");
        }
      });

      // 添加示例路线
      const path = [
        [116.397428, 39.90923],
        [116.397428, 39.91923],
        [116.407428, 39.91923],
        [116.407428, 39.90923],
      ];

      const polyline = new AMap.Polyline({
        path: path,
        strokeColor: "#3366FF",
        strokeWeight: 6,
        strokeOpacity: 0.8,
      });

      polyline.setMap(map);
    });
  } catch (error) {
    console.error("地图加载失败:", error);
    ElMessage.error("地图加载失败，请刷新页面重试");
  }
};

onMounted(() => {
  initMap();
});

onUnmounted(() => {
  if (map) {
    map.destroy();
  }
});
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 60px); /* 减去顶部导航栏的高度 */
  overflow: hidden;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 500px; /* 设置最小高度 */
}

.control-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 300px;
  z-index: 100;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 