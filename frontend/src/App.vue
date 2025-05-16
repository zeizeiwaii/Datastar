<template>
  <el-container class="app-container">
    <el-header>
      <nav>
        <router-link to="/">首页</router-link> |
        <router-link to="/map">地图</router-link> |
        <router-link to="/trips">出行需求</router-link> |
        <router-link to="/routes">路线管理</router-link> |
        <router-link to="/route-planning">响应式路线规划</router-link>
      </nav>
    </el-header>

    <el-main>
      <router-view />
    </el-main>

    <el-footer>
      <p>响应式公交系统 V2.0</p>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
// 组件逻辑
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  line-height: 60px;
  text-align: center;
}

.el-header nav {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.el-header a {
  color: white;
  text-decoration: none;
}

.el-header a.router-link-active {
  font-weight: bold;
}

.el-main {
  padding: 20px;
}

.el-footer {
  background-color: #f5f7fa;
  color: #909399;
  text-align: center;
  line-height: 60px;
}
</style> 