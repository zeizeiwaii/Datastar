<template>
  <div class="proxy-test">
    <h2>高德地图API代理测试</h2>

    <div class="test-section">
      <h3>1. API Key配置</h3>
      <div class="info-box">
        <p>
          <strong>代理状态:</strong> {{ proxyEnabled ? "已启用" : "已禁用" }}
        </p>
        <p><strong>普通API Key:</strong> {{ apiKey }}</p>
        <p><strong>新Web服务Key:</strong> {{ newWebServiceKey }}</p>
        <p><strong>API请求地址:</strong> {{ apiUrl }}</p>
        <el-button type="primary" @click="toggleProxy">
          {{ proxyEnabled ? "禁用代理" : "启用代理" }}
        </el-button>
      </div>
    </div>

    <div class="test-section">
      <h3>2. POI搜索测试 (使用普通Key)</h3>
      <div class="search-box">
        <el-input
          v-model="keyword"
          placeholder="请输入地点关键词"
          style="width: 300px"
        ></el-input>
        <el-button type="primary" @click="searchPOI">搜索</el-button>
      </div>

      <div v-if="loading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon> 正在加载...
      </div>

      <div v-if="error" class="error">
        <el-alert
          :title="error"
          type="error"
          show-icon
          :closable="false"
        ></el-alert>
      </div>

      <div v-if="results.length > 0" class="results">
        <h4>搜索结果:</h4>
        <el-table :data="results" style="width: 100%">
          <el-table-column prop="name" label="名称"></el-table-column>
          <el-table-column prop="address" label="地址"></el-table-column>
          <el-table-column prop="typeName" label="类型"></el-table-column>
          <el-table-column prop="location" label="位置"></el-table-column>
        </el-table>
      </div>
    </div>

    <div class="test-section">
      <h3>3. 周边搜索测试 (使用新Web服务Key)</h3>
      <div class="search-box">
        <el-input
          v-model="location"
          placeholder="请输入位置坐标，如：121.473701,31.230416"
          style="width: 300px"
        ></el-input>
        <el-input
          v-model="radius"
          placeholder="搜索半径(米)"
          style="width: 150px"
        ></el-input>
        <el-button type="primary" @click="searchAround">搜索周边</el-button>
      </div>

      <div v-if="aroundLoading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon> 正在加载...
      </div>

      <div v-if="aroundError" class="error">
        <el-alert
          :title="aroundError"
          type="error"
          show-icon
          :closable="false"
        ></el-alert>
      </div>

      <div v-if="aroundResults.length > 0" class="results">
        <h4>周边搜索结果:</h4>
        <el-table :data="aroundResults" style="width: 100%">
          <el-table-column prop="name" label="名称"></el-table-column>
          <el-table-column prop="address" label="地址"></el-table-column>
          <el-table-column prop="typeName" label="类型"></el-table-column>
          <el-table-column prop="distance" label="距离(米)"></el-table-column>
        </el-table>
      </div>
    </div>

    <div class="test-section">
      <h3>4. 调试日志</h3>
      <pre class="log-box">{{ log }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import amapConfig from "../utils/amapConfig";
import amapService from "../utils/amapService";

// 搜索相关 - POI搜索
const keyword = ref("上海市");
const results = ref<any[]>([]);
const loading = ref(false);
const error = ref("");

// 搜索相关 - 周边搜索
const location = ref("121.473701,31.230416");
const radius = ref("1000");
const aroundResults = ref<any[]>([]);
const aroundLoading = ref(false);
const aroundError = ref("");

// 日志
const log = ref("");

// 代理状态
const proxyEnabled = ref(amapConfig.USE_PROXY);
const apiKey = computed(() =>
  proxyEnabled.value
    ? amapConfig.SERVER_API_KEY
    : amapConfig.WEB_SERVICE_API_KEY
);
const newWebServiceKey = computed(() => amapConfig.WEB_SERVICE_API_KEY);
const apiUrl = computed(() => {
  const baseUrl = amapConfig.API_CONFIG.POI_SEARCH.URL;
  return baseUrl;
});

// 切换代理
const toggleProxy = () => {
  // 这里只是在当前组件修改，并不会实际修改amapConfig文件
  proxyEnabled.value = !proxyEnabled.value;
  ElMessage.success(`已${proxyEnabled.value ? "启用" : "禁用"}代理模式`);
  addLog(`代理模式已${proxyEnabled.value ? "启用" : "禁用"}`);
};

// 搜索POI (使用普通Key)
const searchPOI = async () => {
  if (!keyword.value) {
    ElMessage.warning("请输入搜索关键词");
    return;
  }

  loading.value = true;
  error.value = "";
  results.value = [];

  try {
    // 使用服务进行搜索
    addLog(`发起POI搜索请求，关键词: ${keyword.value}`);

    const data = await amapService.poiSearch({
      keywords: keyword.value,
    });

    addLog(`接收POI搜索响应: 找到 ${data.count || 0} 条结果`);

    if (data.pois && data.pois.length > 0) {
      results.value = data.pois.map((poi: any) => ({
        name: poi.name,
        address: poi.address || "暂无地址",
        typeName: poi.type,
        location: poi.location,
      }));
    } else {
      error.value = "未找到任何结果";
    }
  } catch (err: any) {
    error.value = `请求出错: ${err.message}`;
    addLog(`POI搜索错误: ${err.message}`);
  } finally {
    loading.value = false;
  }
};

// 周边搜索 (使用新Web服务Key)
const searchAround = async () => {
  if (!location.value || !radius.value) {
    ElMessage.warning("请输入完整的位置和半径信息");
    return;
  }

  aroundLoading.value = true;
  aroundError.value = "";
  aroundResults.value = [];

  try {
    // 使用服务进行周边搜索
    addLog(
      `发起周边搜索请求，位置: ${location.value}, 半径: ${radius.value}米`
    );

    const data = await amapService.aroundSearch({
      location: location.value,
      radius: radius.value,
    });

    addLog(`接收周边搜索响应: 找到 ${data.count || 0} 条结果`);

    if (data.pois && data.pois.length > 0) {
      aroundResults.value = data.pois.map((poi: any) => ({
        name: poi.name,
        address: poi.address || "暂无地址",
        typeName: poi.type,
        distance: poi.distance || "未知",
      }));
    } else {
      aroundError.value = "未找到任何结果";
    }
  } catch (err: any) {
    aroundError.value = `请求出错: ${err.message}`;
    addLog(`周边搜索错误: ${err.message}`);
  } finally {
    aroundLoading.value = false;
  }
};

// 添加日志
const addLog = (message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  log.value = `[${timestamp}] ${message}\n${log.value}`;
};

// 初始化
addLog("组件已加载");
addLog(`当前代理状态: ${proxyEnabled.value ? "已启用" : "已禁用"}`);
addLog(`普通API Key: ${apiKey.value}`);
addLog(`新Web服务Key: ${newWebServiceKey.value}`);
addLog(`API URL: ${apiUrl.value}`);
</script>

<style scoped>
.proxy-test {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.test-section {
  margin-bottom: 30px;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 20px;
}

.info-box {
  background-color: #f8f8f8;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
}

.search-box {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 15px 0;
}

.results {
  margin-top: 20px;
}

.log-box {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  height: 200px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
  font-size: 12px;
}
</style> 