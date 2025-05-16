<template>
  <div class="admin-dashboard">
    <h2>公交调度管理</h2>

    <!-- 需求统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>今日需求总数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.totalRequests }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>待确认调度</span>
            </div>
          </template>
          <div class="card-value">{{ stats.pendingPlans }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>已发车数量</span>
            </div>
          </template>
          <div class="card-value">{{ stats.confirmedPlans }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 地图展示区域 -->
    <div class="map-container">
      <div id="adminMap" class="map"></div>
    </div>

    <!-- 调度计划列表 -->
    <div class="plan-list">
      <div class="list-header">
        <h3>调度计划列表</h3>
        <el-button type="primary" @click="refreshData">刷新数据</el-button>
      </div>
      <el-table :data="dispatchPlans" style="width: 100%" v-loading="loading">
        <el-table-column prop="plan_id" label="计划ID" width="100" />
        <el-table-column prop="start_time" label="发车时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="request_count" label="需求数量" width="100" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'planned'"
              type="primary"
              size="small"
              @click="confirmDispatch(scope.row)"
              :loading="confirmLoading"
            >
              确认发车
            </el-button>
            <el-button
              v-if="scope.row.status === 'planned'"
              type="danger"
              size="small"
              @click="cancelDispatch(scope.row)"
              :loading="cancelLoading"
            >
              取消计划
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="showPlanDetails(scope.row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 计划详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="调度计划详情"
      width="70%"
      destroy-on-close
    >
      <div v-if="selectedPlan" class="plan-detail">
        <div class="plan-info">
          <h4>基本信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="计划ID">{{
              selectedPlan.plan_id
            }}</el-descriptions-item>
            <el-descriptions-item label="发车时间">{{
              formatTime(selectedPlan.start_time)
            }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(selectedPlan.status)">
                {{ getStatusText(selectedPlan.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="需求数量">{{
              selectedPlan.requests?.length || 0
            }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="route-info">
          <h4>推荐路线</h4>
          <div id="detailMap" class="detail-map"></div>
          <div class="route-stats" v-if="routeStats">
            <p>
              <strong>总距离：</strong
              >{{ (routeStats.distance / 1000).toFixed(1) }} 公里
            </p>
            <p>
              <strong>预计时间：</strong
              >{{ (routeStats.duration / 60).toFixed(0) }} 分钟
            </p>
          </div>
        </div>

        <div class="request-list">
          <h4>包含的出行需求</h4>
          <el-table :data="selectedPlan.requests" style="width: 100%">
            <el-table-column prop="origin_name" label="起点" />
            <el-table-column prop="destination_name" label="终点" />
            <el-table-column prop="people_count" label="人数" width="80" />
            <el-table-column
              prop="departure_time"
              label="期望出发时间"
              width="180"
            >
              <template #default="scope">
                {{ formatTime(scope.row.departure_time) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="action-btns" v-if="selectedPlan.status === 'planned'">
          <el-button
            type="primary"
            @click="confirmCurrentPlan"
            :loading="confirmLoading"
            >确认发车</el-button
          >
          <el-button
            type="danger"
            @click="cancelCurrentPlan"
            :loading="cancelLoading"
            >取消计划</el-button
          >
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  confirmDispatch as apiConfirmDispatch,
  cancelDispatch as apiCancelDispatch,
  getDispatchPlanDetail,
  getDispatchPlans,
  getDashboardStats,
} from "../api/request";

// 统计数据
const stats = reactive({
  totalRequests: 0,
  pendingPlans: 0,
  confirmedPlans: 0,
});

// 调度计划列表
const dispatchPlans = ref([]);
const selectedPlan = ref(null);
const dialogVisible = ref(false);
const loading = ref(false);
const confirmLoading = ref(false);
const cancelLoading = ref(false);
const routeStats = ref(null);

// 地图对象
let map = null;
let detailMap = null;

// 初始化页面
onMounted(async () => {
  await loadData();
  initAMap();
});

// 清理资源
onUnmounted(() => {
  if (map) {
    map.destroy();
  }
  if (detailMap) {
    detailMap.destroy();
  }
});

// 初始化高德地图
const initAMap = async () => {
  try {
    // 使用高德地图JS API
    if (window.AMap) {
      return;
    }

    const script = document.createElement("script");
    script.type = "text/javascript";
    script.async = true;
    script.src =
      "https://webapi.amap.com/maps?v=2.0&key=f3e49391bb7e88bfb311ecfaeefa1f8b&plugin=AMap.Polyline,AMap.DrivingRoute";
    document.head.appendChild(script);

    return new Promise((resolve) => {
      script.onload = () => {
        resolve();
      };
    });
  } catch (error) {
    console.error("加载高德地图失败:", error);
    ElMessage.error("加载地图失败，请刷新页面重试");
  }
};

// 加载所有数据
const loadData = async () => {
  loading.value = true;
  try {
    await Promise.all([loadDashboardStats(), loadDispatchPlansList()]);
  } catch (error) {
    console.error("加载数据失败:", error);
    ElMessage.error("加载数据失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

// 刷新数据
const refreshData = () => {
  loadData();
  ElMessage.success("数据已刷新");
};

// 加载统计数据
const loadDashboardStats = async () => {
  try {
    const data = await getDashboardStats();
    Object.assign(stats, data);
  } catch (error) {
    console.error("加载统计数据失败:", error);
  }
};

// 加载调度计划列表
const loadDispatchPlansList = async () => {
  try {
    dispatchPlans.value = await getDispatchPlans();
  } catch (error) {
    console.error("加载调度计划失败:", error);
  }
};

// 获取状态类型
const getStatusType = (status) => {
  switch (status) {
    case "planned":
      return "warning";
    case "confirmed":
      return "success";
    case "cancelled":
      return "danger";
    default:
      return "info";
  }
};

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case "planned":
      return "待确认";
    case "confirmed":
      return "已发车";
    case "cancelled":
      return "已取消";
    default:
      return "未知";
  }
};

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return "";
  const date = new Date(timeStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 确认发车
const confirmDispatch = async (plan) => {
  try {
    await ElMessageBox.confirm(`确认为计划 ${plan.plan_id} 发车?`, "确认发车", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning",
    });

    confirmLoading.value = true;
    await apiConfirmDispatch(plan.plan_id);
    ElMessage.success("已确认发车");

    // 更新数据
    await loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("确认发车失败:", error);
      ElMessage.error("确认发车失败，请重试");
    }
  } finally {
    confirmLoading.value = false;
  }
};

// 取消计划
const cancelDispatch = async (plan) => {
  try {
    await ElMessageBox.confirm(`确认取消计划 ${plan.plan_id}?`, "取消计划", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning",
    });

    cancelLoading.value = true;
    await apiCancelDispatch(plan.plan_id);
    ElMessage.success("已取消计划");

    // 更新数据
    await loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("取消计划失败:", error);
      ElMessage.error("取消计划失败，请重试");
    }
  } finally {
    cancelLoading.value = false;
  }
};

// 确认当前查看的计划
const confirmCurrentPlan = async () => {
  if (selectedPlan.value) {
    await confirmDispatch(selectedPlan.value);
    if (dialogVisible.value) {
      // 重新加载计划详情
      showPlanDetails(selectedPlan.value);
    }
  }
};

// 取消当前查看的计划
const cancelCurrentPlan = async () => {
  if (selectedPlan.value) {
    await cancelDispatch(selectedPlan.value);
    dialogVisible.value = false;
  }
};

// 显示计划详情
const showPlanDetails = async (plan) => {
  try {
    // 显示对话框
    dialogVisible.value = true;

    // 加载计划详情
    const planDetail = await getDispatchPlanDetail(plan.plan_id);
    selectedPlan.value = planDetail;

    // 等待DOM更新后初始化地图
    setTimeout(() => {
      initDetailMap(planDetail);
    }, 100);
  } catch (error) {
    console.error("获取计划详情失败:", error);
    ElMessage.error("获取计划详情失败");
  }
};

// 初始化详情地图
const initDetailMap = (plan) => {
  try {
    if (!window.AMap) {
      console.error("高德地图API未加载");
      return;
    }

    // 创建地图实例
    detailMap = new window.AMap.Map("detailMap", {
      zoom: 12,
      resizeEnable: true,
    });

    // 解析路线数据
    if (plan && plan.route_polyline) {
      try {
        const routeData =
          typeof plan.route_polyline === "string"
            ? JSON.parse(plan.route_polyline)
            : plan.route_polyline;

        // 保存路线统计数据
        routeStats.value = {
          distance: routeData.distance || 0,
          duration: routeData.duration || 0,
        };

        // 显示起点和终点标记
        if (plan.requests && plan.requests.length > 0) {
          const firstRequest = plan.requests[0];
          const lastRequest = plan.requests[plan.requests.length - 1];

          // 添加起点标记
          new window.AMap.Marker({
            position: [
              firstRequest.origin_location.lng,
              firstRequest.origin_location.lat,
            ],
            map: detailMap,
            icon: "https://webapi.amap.com/theme/v1.3/markers/n/start.png",
          });

          // 添加终点标记
          new window.AMap.Marker({
            position: [
              lastRequest.destination_location.lng,
              lastRequest.destination_location.lat,
            ],
            map: detailMap,
            icon: "https://webapi.amap.com/theme/v1.3/markers/n/end.png",
          });

          // 自动调整地图视野
          detailMap.setFitView();
        }

        // 绘制路线
        if (routeData.steps && routeData.steps.length > 0) {
          const path = [];

          // 解析路径点
          routeData.steps.forEach((step) => {
            if (step.polyline) {
              const points = step.polyline.split(";");
              points.forEach((point) => {
                const [lng, lat] = point.split(",");
                path.push([parseFloat(lng), parseFloat(lat)]);
              });
            }
          });

          // 创建折线
          const polyline = new window.AMap.Polyline({
            path: path,
            strokeColor: "#3366FF",
            strokeWeight: 6,
            strokeOpacity: 0.8,
          });

          // 添加到地图
          detailMap.add(polyline);
          detailMap.setFitView();
        }
      } catch (e) {
        console.error("解析路线数据失败:", e);
      }
    }
  } catch (e) {
    console.error("初始化详情地图失败:", e);
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
  color: #303133;
}

.stat-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  padding: 20px 0;
  color: #409eff;
}

.map-container {
  height: 400px;
  margin-bottom: 20px;
}

.map {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}

.plan-list {
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.detail-map {
  height: 400px;
  margin: 15px 0;
  border-radius: 4px;
}

.plan-detail h4 {
  margin: 20px 0 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.route-stats {
  display: flex;
  gap: 20px;
  background: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.action-btns {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 