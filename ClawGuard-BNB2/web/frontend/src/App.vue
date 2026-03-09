<template>
  <el-container class="app-container">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>ClawGuard</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/trading">
          <el-icon><ShoppingCart /></el-icon>
          <span>交易</span>
        </el-menu-item>
        <el-menu-item index="/strategy">
          <el-icon><Operation /></el-icon>
          <span>策略</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>分析</span>
        </el-menu-item>
        <el-menu-item index="/risk">
          <el-icon><Warning /></el-icon>
          <span>风控</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h3>{{ pageTitle }}</h3>
        </div>
        <div class="header-right">
          <el-tag :type="modeType">{{ tradingMode }}</el-tag>
          <el-tag :type="statusType" style="margin-left: 10px">
            {{ apiStatus }}
          </el-tag>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/api/client'

const route = useRoute()
const tradingMode = ref('paper')
const apiStatus = ref('连接中...')

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/trading': '交易管理',
    '/strategy': '策略管理',
    '/analysis': '市场分析',
    '/risk': '风险管理',
    '/settings': '系统设置'
  }
  return titles[route.path] || 'ClawGuard-BNB'
})

const modeType = computed(() => {
  const types = {
    'paper': 'info',
    'testnet': 'warning',
    'live': 'danger'
  }
  return types[tradingMode.value] || 'info'
})

const statusType = computed(() => {
  return apiStatus.value === '已连接' ? 'success' : 'danger'
})

const loadSystemStatus = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/system-status')
    if (res.data.success) {
      tradingMode.value = res.data.data.trading_mode
      apiStatus.value = res.data.data.api_connected ? '已连接' : '未连接'
    }
  } catch (error) {
    console.error('加载系统状态失败:', error)
    apiStatus.value = '未连接'
  }
}

onMounted(() => {
  loadSystemStatus()
  // 每30秒刷新一次状态
  setInterval(loadSystemStatus, 30000)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background-color: #2b3a4a;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
