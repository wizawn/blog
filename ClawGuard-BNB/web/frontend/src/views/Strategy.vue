<template>
  <div class="strategy">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>策略列表</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建策略
          </el-button>
        </div>
      </template>

      <el-table :data="strategies" style="width: 100%">
        <el-table-column prop="name" label="策略名称" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="symbol" label="交易对" width="120" />
        <el-table-column label="盈亏" width="150">
          <template #default="scope">
            <span :class="scope.row.profit >= 0 ? 'profit-positive' : 'profit-negative'">
              {{ scope.row.profit >= 0 ? '+' : '' }}{{ scope.row.profit.toFixed(2) }} USDT
              ({{ scope.row.profit_percent.toFixed(2) }}%)
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'running' ? 'success' : 'info'">
              {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'running'"
              type="warning"
              size="small"
              @click="stopStrategy(scope.row.id)"
            >
              停止
            </el-button>
            <el-button
              v-else
              type="success"
              size="small"
              @click="startStrategy(scope.row.id)"
            >
              启动
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteStrategy(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建策略对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建策略" width="600px">
      <el-form :model="strategyForm" label-width="120px">
        <el-form-item label="策略类型">
          <el-select v-model="strategyForm.type" placeholder="选择策略类型">
            <el-option label="网格策略" value="grid" />
            <el-option label="均线交叉" value="ma_crossover" />
          </el-select>
        </el-form-item>
        <el-form-item label="交易对">
          <el-input v-model="strategyForm.symbol" placeholder="例如: BTCUSDT" />
        </el-form-item>
        <el-form-item v-if="strategyForm.type === 'grid'" label="下限价格">
          <el-input-number v-model="strategyForm.lower_price" :min="0" />
        </el-form-item>
        <el-form-item v-if="strategyForm.type === 'grid'" label="上限价格">
          <el-input-number v-model="strategyForm.upper_price" :min="0" />
        </el-form-item>
        <el-form-item v-if="strategyForm.type === 'grid'" label="网格数量">
          <el-input-number v-model="strategyForm.grids" :min="2" :max="100" />
        </el-form-item>
        <el-form-item label="投入金额">
          <el-input-number v-model="strategyForm.amount" :min="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createStrategy">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const strategies = ref([])
const showCreateDialog = ref(false)
const strategyForm = ref({
  type: 'grid',
  symbol: 'BTCUSDT',
  lower_price: 65000,
  upper_price: 70000,
  grids: 20,
  amount: 1000
})

const loadStrategies = async () => {
  try {
    const res = await apiClient.get('/api/strategy/list')
    if (res.data.success) {
      strategies.value = res.data.data
    }
  } catch (error) {
    console.error('加载策略失败:', error)
  }
}

const createStrategy = async () => {
  try {
    const res = await apiClient.post('/api/strategy/create', {
      type: strategyForm.value.type,
      symbol: strategyForm.value.symbol,
      config: {
        lower_price: strategyForm.value.lower_price,
        upper_price: strategyForm.value.upper_price,
        grids: strategyForm.value.grids,
        amount: strategyForm.value.amount
      }
    })

    if (res.data.success) {
      ElMessage.success('策略创建成功')
      showCreateDialog.value = false
      loadStrategies()
    }
  } catch (error) {
    console.error('创建策略失败:', error)
  }
}

const stopStrategy = async (id) => {
  try {
    await ElMessageBox.confirm('确定要停止此策略吗？', '确认', { type: 'warning' })
    const res = await apiClient.post(`/api/strategy/${id}/stop`)
    if (res.data.success) {
      ElMessage.success('策略已停止')
      loadStrategies()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止策略失败:', error)
    }
  }
}

const startStrategy = async (id) => {
  try {
    const res = await apiClient.post(`/api/strategy/${id}/start`)
    if (res.data.success) {
      ElMessage.success('策略已启动')
      loadStrategies()
    }
  } catch (error) {
    console.error('启动策略失败:', error)
  }
}

const deleteStrategy = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除此策略吗？', '确认', { type: 'warning' })
    const res = await apiClient.delete(`/api/strategy/${id}`)
    if (res.data.success) {
      ElMessage.success('策略已删除')
      loadStrategies()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除策略失败:', error)
    }
  }
}

onMounted(() => {
  loadStrategies()
  setInterval(loadStrategies, 10000)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profit-positive {
  color: #67c23a;
  font-weight: 600;
}

.profit-negative {
  color: #f56c6c;
  font-weight: 600;
}
</style>
