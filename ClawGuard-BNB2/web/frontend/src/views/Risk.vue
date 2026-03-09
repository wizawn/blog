<template>
  <div class="risk">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>风控配置</span>
          </template>
          <el-form :model="riskConfig" label-width="180px">
            <el-form-item label="单笔订单最大金额">
              <el-input-number v-model="riskConfig.max_order_value" :min="0" />
              <span style="margin-left: 10px">USDT</span>
            </el-form-item>
            <el-form-item label="每日最大亏损">
              <el-input-number v-model="riskConfig.max_daily_loss" :min="0" />
              <span style="margin-left: 10px">USDT</span>
            </el-form-item>
            <el-form-item label="最大持仓比例">
              <el-input-number v-model="riskConfig.max_position_size" :min="0" :max="1" :step="0.1" />
            </el-form-item>
            <el-form-item label="启用止损">
              <el-switch v-model="riskConfig.enable_stop_loss" />
            </el-form-item>
            <el-form-item label="默认止损比例">
              <el-input-number v-model="riskConfig.default_stop_loss_percent" :min="0" :max="1" :step="0.01" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveRiskConfig">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>风控统计</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="总订单数">
              {{ stats.total_orders || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="被拒绝订单">
              {{ stats.rejected_orders || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="拒绝率">
              {{ stats.rejection_rate?.toFixed(2) || 0 }}%
            </el-descriptions-item>
            <el-descriptions-item label="总交易金额">
              {{ stats.total_value?.toFixed(2) || 0 }} USDT
            </el-descriptions-item>
            <el-descriptions-item label="今日亏损">
              <span :class="stats.daily_loss < 0 ? 'loss' : 'profit'">
                {{ stats.daily_loss?.toFixed(2) || 0 }} USDT
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="getRiskLevelType(stats.risk_level)">
                {{ getRiskLevelText(stats.risk_level) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <span>风控告警</span>
      </template>
      <el-table :data="alerts" style="width: 100%">
        <el-table-column label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getAlertType(scope.row.level)" size="small">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="150" />
        <el-table-column prop="message" label="消息" />
        <el-table-column prop="symbol" label="交易对" width="120" />
        <el-table-column prop="time" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage } from 'element-plus'

const riskConfig = ref({
  max_order_value: 10000,
  max_daily_loss: 1000,
  max_position_size: 0.1,
  enable_stop_loss: true,
  default_stop_loss_percent: 0.05
})

const stats = ref({})
const alerts = ref([])

const getRiskLevelType = (level) => {
  const types = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger'
  }
  return types[level] || 'info'
}

const getRiskLevelText = (level) => {
  const texts = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
  }
  return texts[level] || '未知'
}

const getAlertType = (level) => {
  const types = {
    'info': 'info',
    'warning': 'warning',
    'error': 'danger'
  }
  return types[level] || 'info'
}

const loadRiskConfig = async () => {
  try {
    const res = await apiClient.get('/api/risk/config')
    if (res.data.success) {
      riskConfig.value = res.data.data
    }
  } catch (error) {
    console.error('加载风控配置失败:', error)
  }
}

const saveRiskConfig = async () => {
  try {
    const res = await apiClient.post('/api/risk/config', riskConfig.value)
    if (res.data.success) {
      ElMessage.success('风控配置已保存')
    }
  } catch (error) {
    console.error('保存风控配置失败:', error)
  }
}

const loadStats = async () => {
  try {
    const res = await apiClient.get('/api/risk/stats')
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (error) {
    console.error('加载风控统计失败:', error)
  }
}

const loadAlerts = async () => {
  try {
    const res = await apiClient.get('/api/risk/alerts')
    if (res.data.success) {
      alerts.value = res.data.data
    }
  } catch (error) {
    console.error('加载风控告警失败:', error)
  }
}

onMounted(() => {
  loadRiskConfig()
  loadStats()
  loadAlerts()

  setInterval(() => {
    loadStats()
    loadAlerts()
  }, 30000)
})
</script>

<style scoped>
.loss {
  color: #f56c6c;
  font-weight: 600;
}

.profit {
  color: #67c23a;
  font-weight: 600;
}
</style>
