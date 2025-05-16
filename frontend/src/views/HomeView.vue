<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>响应式公交系统</h1>
        <p class="subtitle">
          基于高德API + 用户出行聚类 + 路线整合 + 发车判断的智能公交调度系统
        </p>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="feature-cards">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实时监控</span>
            </div>
          </template>
          <div class="card-content">
            <el-statistic :value="statistics.activeTrips" title="当前出行需求">
              <template #suffix>
                <span>个</span>
              </template>
            </el-statistic>
            <el-statistic :value="statistics.activeClusters" title="活跃聚类">
              <template #suffix>
                <span>个</span>
              </template>
            </el-statistic>
            <el-statistic :value="statistics.activeRoutes" title="运行路线">
              <template #suffix>
                <span>条</span>
              </template>
            </el-statistic>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>
          <div class="card-content">
            <el-alert
              v-for="(status, index) in systemStatus"
              :key="index"
              :title="status.title"
              :type="status.type"
              :description="status.description"
              show-icon
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="card-content">
            <el-button type="primary" @click="$router.push('/map')">
              查看地图
            </el-button>
            <el-button type="success" @click="$router.push('/trips')">
              管理出行需求
            </el-button>
            <el-button type="warning" @click="$router.push('/routes')">
              查看路线规划
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="system-info">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <div class="card-content">
            <el-descriptions :column="3" border>
              <el-descriptions-item label="系统版本"
                >2.0.0</el-descriptions-item
              >
              <el-descriptions-item label="最后更新"
                >2024-01-20</el-descriptions-item
              >
              <el-descriptions-item label="运行状态">正常</el-descriptions-item>
              <el-descriptions-item label="数据库状态"
                >正常</el-descriptions-item
              >
              <el-descriptions-item label="API状态">正常</el-descriptions-item>
              <el-descriptions-item label="地图服务">正常</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

// 统计数据
const statistics = ref({
  activeTrips: 156,
  activeClusters: 12,
  activeRoutes: 8,
});

// 系统状态
const systemStatus = ref([
  {
    title: "系统运行正常",
    type: "success",
    description: "所有服务正常运行中",
  },
  {
    title: "数据库连接正常",
    type: "success",
    description: "PostgreSQL数据库连接正常",
  },
  {
    title: "高德API服务正常",
    type: "success",
    description: "地图服务API调用正常",
  },
]);
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #409eff;
  margin-bottom: 10px;
}

.subtitle {
  text-align: center;
  color: #606266;
  margin-bottom: 40px;
}

.feature-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.system-info {
  margin-top: 20px;
}

.el-button {
  width: 100%;
  margin-bottom: 10px;
}

.el-alert {
  margin-bottom: 10px;
}
</style> 