<template>
  <div class="user-request">
    <h2>提交出行需求</h2>

    <!-- 地图选择器 -->
    <div class="map-wrapper">
      <map-selector
        v-model="locations"
        @update:model-value="handleLocationUpdate"
      />
    </div>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="出发时间" prop="departureTime">
          <el-date-picker
            v-model="form.departureTime"
            type="datetime"
            placeholder="选择出发时间"
            :min-date="new Date()"
          />
        </el-form-item>

        <el-form-item label="人数" prop="peopleCount">
          <el-input-number v-model="form.peopleCount" :min="1" :max="10" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="submitting"
            >提交需求</el-button
          >
        </el-form-item>
      </el-form>
    </div>

    <!-- 当前选择的起终点信息 -->
    <div
      class="selected-locations"
      v-if="isOriginSelected || isDestinationSelected"
    >
      <div v-if="isOriginSelected" class="location-info">
        <strong>已选起点:</strong> {{ locations.origin.name }}
      </div>
      <div v-if="isDestinationSelected" class="location-info">
        <strong>已选终点:</strong> {{ locations.destination.name }}
      </div>
    </div>

    <!-- 提交成功弹窗 -->
    <el-dialog v-model="showSuccessDialog" title="提交成功" width="30%" center>
      <div class="success-dialog">
        <el-icon class="success-icon" color="#67C23A"
          ><SuccessFilled
        /></el-icon>
        <p>已收到您的请求，请稍后查看发车信息</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="resetForm">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import { SuccessFilled } from "@element-plus/icons-vue";
import { submitRequest } from "../api/request";
import type { FormInstance } from "element-plus";
import type { Location } from "../types/request";
import { MapSelector } from "../components";

interface LocationValue {
  name: string;
  location: Location;
  id?: string;
  address?: string;
  original?: any;
}

interface LocationsState {
  origin: LocationValue;
  destination: LocationValue;
}

interface FormState {
  departureTime: string;
  peopleCount: number;
}

const formRef = ref<FormInstance>();
const submitting = ref(false);
const showSuccessDialog = ref(false);

// 地点选择数据
const locations = reactive<LocationsState>({
  origin: {
    name: "",
    location: { lng: 0, lat: 0 },
    id: "",
    address: "",
    original: null,
  },
  destination: {
    name: "",
    location: { lng: 0, lat: 0 },
    id: "",
    address: "",
    original: null,
  },
});

// 表单数据
const form = reactive<FormState>({
  departureTime: "",
  peopleCount: 1,
});

// 表单验证规则
const rules = {
  departureTime: [
    { required: true, message: "请选择出发时间", trigger: "change" },
  ],
  peopleCount: [{ required: true, message: "请输入人数", trigger: "change" }],
};

// 监测地点是否已选择
const isOriginSelected = computed(() => {
  return locations.origin.name && locations.origin.location.lng !== 0;
});

const isDestinationSelected = computed(() => {
  return locations.destination.name && locations.destination.location.lng !== 0;
});

// 处理地图组件更新的位置信息
const handleLocationUpdate = (newLocations: LocationsState) => {
  console.log("位置已更新:", newLocations);

  // 确保深度复制对象而不是仅引用
  if (newLocations.origin) {
    locations.origin = {
      name: newLocations.origin.name,
      location: { ...newLocations.origin.location },
      id: newLocations.origin.id || "",
      address: newLocations.origin.address || "",
      original: newLocations.origin.original || null,
    };
  }

  if (newLocations.destination) {
    locations.destination = {
      name: newLocations.destination.name,
      location: { ...newLocations.destination.location },
      id: newLocations.destination.id || "",
      address: newLocations.destination.address || "",
      original: newLocations.destination.original || null,
    };
  }
};

// 监视locations变化，方便调试
watch(
  locations,
  (newVal) => {
    console.log("locations变化:", newVal);
  },
  { deep: true }
);

// 提交表单
const submitForm = async () => {
  console.log("提交表单，当前locations:", locations);

  // 验证地点选择
  if (!isOriginSelected.value) {
    ElMessage.warning("请选择起点");
    return;
  }

  if (!isDestinationSelected.value) {
    ElMessage.warning("请选择终点");
    return;
  }

  if (!formRef.value) return;

  try {
    await formRef.value.validate();

    submitting.value = true;

    const requestData = {
      origin: locations.origin.name,
      destination: locations.destination.name,
      departureTime: form.departureTime,
      peopleCount: form.peopleCount,
      originLocation: locations.origin.location,
      destinationLocation: locations.destination.location,
      originPOI: {
        id: locations.origin.id || "",
        name: locations.origin.name,
        address: locations.origin.address || "",
        location: locations.origin.location,
        ...(locations.origin.original || {}),
      },
      destinationPOI: {
        id: locations.destination.id || "",
        name: locations.destination.name,
        address: locations.destination.address || "",
        location: locations.destination.location,
        ...(locations.destination.original || {}),
      },
    };

    console.log("发送请求数据:", requestData);
    const result = await submitRequest(requestData);

    if (result.success) {
      showSuccessDialog.value = true;
    } else {
      ElMessage.error("提交失败，请重试");
    }
  } catch (error) {
    console.error("提交失败:", error);
    ElMessage.error("提交失败，请重试");
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();

    // 重置地点选择
    locations.origin = {
      name: "",
      location: { lng: 0, lat: 0 },
      id: "",
      address: "",
      original: null,
    };
    locations.destination = {
      name: "",
      location: { lng: 0, lat: 0 },
      id: "",
      address: "",
      original: null,
    };

    showSuccessDialog.value = false;
  }
};
</script>

<style scoped>
.user-request {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
  color: #303133;
}

.map-wrapper {
  margin-bottom: 20px;
}

.form-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.success-dialog {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.success-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.selected-locations {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.location-info {
  margin: 5px 0;
  font-size: 14px;
}
</style> 