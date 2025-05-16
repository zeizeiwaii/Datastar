<template>
  <div class="routes">
    <el-row :gutter="20">
      <el-col :span="24">
        <h2>路线规划管理</h2>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>路线列表</span>
              <el-button type="primary" @click="showAddDialog"
                >添加路线</el-button
              >
            </div>
          </template>

          <el-table :data="routes" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="路线名称" width="150" />
            <el-table-column
              prop="vehicle.plate_number"
              label="车辆"
              width="120"
            />
            <el-table-column label="站点数" width="100">
              <template #default="{ row }">
                {{ row.stops?.length || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="距离" width="120">
              <template #default="{ row }">
                {{ formatDistance(row.route?.distance) }}
              </template>
            </el-table-column>
            <el-table-column label="预计时间" width="120">
              <template #default="{ row }">
                {{ formatDuration(row.route?.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="viewRoute(row)"
                    >查看</el-button
                  >
                  <el-button size="small" type="primary" @click="editRoute(row)"
                    >编辑</el-button
                  >
                  <el-button
                    size="small"
                    type="success"
                    @click="startRoute(row)"
                    >发车</el-button
                  >
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteRoute(row)"
                    >删除</el-button
                  >
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              :current-page="currentPage"
              :page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加路线' : '编辑路线'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="路线名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入路线名称" />
        </el-form-item>
        <el-form-item label="车辆" prop="vehicle_id">
          <el-select v-model="form.vehicle_id" placeholder="请选择车辆">
            <el-option
              v-for="vehicle in vehicles"
              :key="vehicle.id"
              :label="vehicle.plate_number"
              :value="vehicle.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="站点" prop="stops">
          <el-table :data="form.stops" style="width: 100%">
            <el-table-column label="站点名称" width="200">
              <template #default="{ row }">
                <el-input v-model="row.name" placeholder="站点名称" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" @click="removeStop($index)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <div class="add-stop">
            <el-button type="primary" @click="addStop">添加站点</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailVisible" title="路线详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{
          currentRoute.id
        }}</el-descriptions-item>
        <el-descriptions-item label="路线名称">{{
          currentRoute.name
        }}</el-descriptions-item>
        <el-descriptions-item label="车辆">{{
          currentRoute.vehicle?.plate_number
        }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRoute.status)">
            {{ getStatusText(currentRoute.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="距离">{{
          formatDistance(currentRoute.route?.distance)
        }}</el-descriptions-item>
        <el-descriptions-item label="预计时间">{{
          formatDuration(currentRoute.route?.duration)
        }}</el-descriptions-item>
      </el-descriptions>

      <div class="route-stops">
        <h3>站点列表</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(stop, index) in currentRoute.stops"
            :key="index"
            :timestamp="formatTime(stop.arrival_time)"
          >
            {{ stop.name }}
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

interface Route {
  id: number;
  name: string;
  vehicle: {
    plate_number: string;
  };
  stops: Array<{
    name: string;
    location: {
      lat: number;
      lng: number;
    };
    arrival_time?: string;
  }>;
  route?: {
    distance: number;
    duration: number;
  };
  status: string;
}

interface Vehicle {
  id: number;
  plate_number: string;
}

// 数据列表
const routes = ref<Route[]>([]);
const vehicles = ref<Vehicle[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 对话框控制
const dialogVisible = ref(false);
const dialogType = ref<"add" | "edit">("add");
const detailVisible = ref(false);
const currentRoute = ref<Route | null>(null);

// 表单
const formRef = ref<FormInstance>();
const form = ref({
  id: 0,
  name: "",
  vehicle_id: "",
  stops: [] as Array<{
    name: string;
    location: {
      lat: number;
      lng: number;
    };
  }>,
});

// 表单验证规则
const rules = ref<FormRules>({
  name: [{ required: true, message: "请输入路线名称", trigger: "blur" }],
  vehicle_id: [{ required: true, message: "请选择车辆", trigger: "change" }],
  stops: [{ required: true, message: "请添加站点", trigger: "change" }],
});

// 获取数据
const fetchRoutes = async () => {
  try {
    const response = await fetch(
      `/api/routes?page=${currentPage.value}&size=${pageSize.value}`
    );
    const data = await response.json();
    routes.value = data.items;
    total.value = data.total;
  } catch (error) {
    ElMessage.error("获取数据失败");
  }
};

const fetchVehicles = async () => {
  try {
    const response = await fetch("/api/vehicles");
    const data = await response.json();
    vehicles.value = data;
  } catch (error) {
    ElMessage.error("获取车辆数据失败");
  }
};

// 格式化距离
const formatDistance = (distance: number) => {
  if (!distance) return "0 km";
  return `${(distance / 1000).toFixed(1)} km`;
};

// 格式化时间
const formatDuration = (duration: number) => {
  if (!duration) return "0分钟";
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  }
  return `${minutes}分钟`;
};

// 格式化时间戳
const formatTime = (time: string) => {
  if (!time) return "";
  return new Date(time).toLocaleTimeString();
};

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    active: "success",
    completed: "info",
    cancelled: "danger",
  };
  return types[status] || "info";
};

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: "运行中",
    completed: "已完成",
    cancelled: "已取消",
  };
  return texts[status] || status;
};

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = "add";
  form.value = {
    id: 0,
    name: "",
    vehicle_id: "",
    stops: [],
  };
  dialogVisible.value = true;
};

// 添加站点
const addStop = () => {
  form.value.stops.push({
    name: "",
    location: { lat: 0, lng: 0 },
  });
};

// 删除站点
const removeStop = (index: number) => {
  form.value.stops.splice(index, 1);
};

// 编辑路线
const editRoute = (row: any) => {
  dialogType.value = "edit";
  form.value = { ...row };
  dialogVisible.value = true;
};

// 查看路线
const viewRoute = (row: any) => {
  currentRoute.value = row;
  detailVisible.value = true;
};

// 发车
const startRoute = async (row: any) => {
  try {
    await ElMessageBox.confirm("确定要发车吗？", "提示", {
      type: "warning",
    });
    await fetch(`/api/routes/${row.id}/start`, { method: "POST" });
    ElMessage.success("发车成功");
    fetchRoutes();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("发车失败");
    }
  }
};

// 删除路线
const deleteRoute = async (row: any) => {
  try {
    await ElMessageBox.confirm("确定要删除这条路线吗？", "提示", {
      type: "warning",
    });
    await fetch(`/api/routes/${row.id}`, { method: "DELETE" });
    ElMessage.success("删除成功");
    fetchRoutes();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const method = dialogType.value === "add" ? "POST" : "PUT";
        const url =
          dialogType.value === "add"
            ? "/api/routes"
            : `/api/routes/${form.value.id}`;

        await fetch(url, {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form.value),
        });

        ElMessage.success(dialogType.value === "add" ? "添加成功" : "更新成功");
        dialogVisible.value = false;
        fetchRoutes();
      } catch (error) {
        ElMessage.error(dialogType.value === "add" ? "添加失败" : "更新失败");
      }
    }
  });
};

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchRoutes();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchRoutes();
};

// 初始化
onMounted(() => {
  fetchRoutes();
  fetchVehicles();
});
</script>

<style scoped>
.routes {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.add-stop {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

.route-stops {
  margin-top: 20px;
}

.route-stops h3 {
  margin-bottom: 15px;
}
</style> 