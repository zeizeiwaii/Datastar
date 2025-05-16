<template>
  <div class="trips">
    <el-row :gutter="20">
      <el-col :span="24">
        <h2>出行需求管理</h2>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>需求列表</span>
              <el-button type="primary" @click="showAddDialog"
                >添加需求</el-button
              >
            </div>
          </template>

          <el-table :data="trips" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="user.username" label="用户" width="120" />
            <el-table-column label="起点" width="200">
              <template #default="{ row }">
                {{ formatLocation(row.origin) }}
              </template>
            </el-table-column>
            <el-table-column label="终点" width="200">
              <template #default="{ row }">
                {{ formatLocation(row.destination) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="departure_time"
              label="出发时间"
              width="180"
            />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cluster_id" label="聚类ID" width="100" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="viewTrip(row)"
                    >查看</el-button
                  >
                  <el-button size="small" type="primary" @click="editTrip(row)"
                    >编辑</el-button
                  >
                  <el-button size="small" type="danger" @click="deleteTrip(row)"
                    >删除</el-button
                  >
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
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
      :title="dialogType === 'add' ? '添加出行需求' : '编辑出行需求'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="起点" prop="origin">
          <el-input v-model="form.origin" placeholder="请输入起点地址" />
        </el-form-item>
        <el-form-item label="终点" prop="destination">
          <el-input v-model="form.destination" placeholder="请输入终点地址" />
        </el-form-item>
        <el-form-item label="出发时间" prop="departure_time">
          <el-date-picker
            v-model="form.departure_time"
            type="datetime"
            placeholder="选择出发时间"
          />
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
    <el-dialog v-model="detailVisible" title="出行需求详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{
          currentTrip.id
        }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{
          currentTrip.user?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="起点">{{
          formatLocation(currentTrip.origin)
        }}</el-descriptions-item>
        <el-descriptions-item label="终点">{{
          formatLocation(currentTrip.destination)
        }}</el-descriptions-item>
        <el-descriptions-item label="出发时间">{{
          currentTrip.departure_time
        }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTrip.status)">
            {{ getStatusText(currentTrip.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="聚类ID">{{
          currentTrip.cluster_id
        }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{
          currentTrip.created_at
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

// 定义类型
interface Location {
  lat: number;
  lng: number;
}

interface User {
  username: string;
}

interface Trip {
  id: number;
  user?: User;
  origin: Location;
  destination: Location;
  departure_time: string;
  status: "pending" | "clustered" | "assigned" | "completed";
  cluster_id?: number;
  created_at?: string;
}

// 数据列表
const trips = ref<Trip[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 对话框控制
const dialogVisible = ref(false);
const dialogType = ref<"add" | "edit">("add");
const detailVisible = ref(false);
const currentTrip = ref<Trip>({} as Trip);

// 表单
const formRef = ref<FormInstance>();
const form = ref<Partial<Trip>>({
  origin: { lat: 0, lng: 0 },
  destination: { lat: 0, lng: 0 },
  departure_time: "",
});

// 表单验证规则
const rules = ref<FormRules>({
  origin: [{ required: true, message: "请输入起点地址", trigger: "blur" }],
  destination: [{ required: true, message: "请输入终点地址", trigger: "blur" }],
  departure_time: [
    { required: true, message: "请选择出发时间", trigger: "change" },
  ],
});

// 获取数据
const fetchTrips = async () => {
  try {
    const response = await fetch(
      `/api/trips?page=${currentPage.value}&size=${pageSize.value}`
    );
    const data = await response.json();
    trips.value = data.items;
    total.value = data.total;
  } catch (error) {
    ElMessage.error("获取数据失败");
  }
};

// 格式化位置信息
const formatLocation = (location: any) => {
  if (!location) return "";
  return `${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`;
};

// 获取状态类型
const getStatusType = (
  status: string
): "success" | "info" | "warning" | "primary" | "danger" => {
  const types: Record<
    string,
    "success" | "info" | "warning" | "primary" | "danger"
  > = {
    pending: "info",
    clustered: "warning",
    assigned: "success",
    completed: "primary",
  };
  return types[status] || "info";
};

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: "待处理",
    clustered: "已聚类",
    assigned: "已分配",
    completed: "已完成",
  };
  return texts[status] || status;
};

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = "add";
  form.value = {
    origin: { lat: 0, lng: 0 },
    destination: { lat: 0, lng: 0 },
    departure_time: "",
  };
  dialogVisible.value = true;
};

// 编辑出行需求
const editTrip = (row: any) => {
  dialogType.value = "edit";
  form.value = { ...row };
  dialogVisible.value = true;
};

// 查看出行需求
const viewTrip = (row: any) => {
  currentTrip.value = row;
  detailVisible.value = true;
};

// 删除出行需求
const deleteTrip = async (row: any) => {
  try {
    await ElMessageBox.confirm("确定要删除这条出行需求吗？", "提示", {
      type: "warning",
    });
    await fetch(`/api/trips/${row.id}`, { method: "DELETE" });
    ElMessage.success("删除成功");
    fetchTrips();
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
            ? "/api/trips"
            : `/api/trips/${form.value.id}`;

        await fetch(url, {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form.value),
        });

        ElMessage.success(dialogType.value === "add" ? "添加成功" : "更新成功");
        dialogVisible.value = false;
        fetchTrips();
      } catch (error) {
        ElMessage.error(dialogType.value === "add" ? "添加失败" : "更新失败");
      }
    }
  });
};

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchTrips();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchTrips();
};

// 初始化
onMounted(() => {
  fetchTrips();
});
</script>

<style scoped>
.trips {
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
</style> 