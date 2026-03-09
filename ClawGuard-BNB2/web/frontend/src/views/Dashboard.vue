<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 账户概览 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>账户概览</span>
              <el-button text @click="loadOverview">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="account-info">
            <div class="balance-item">
              <span class="label">总资产</span>
              <h2 class="value">{{ totalBalance.toFixed(2) }} USDT</h2>
            </div>
            <div class="balance-item">
              <span class="label">今日盈亏</span>
              <h3 :class="['value', pnlClass]">
                {{ todayPnl >= 0 ? '+' : '' }}{{ todayPnl.toFixed(2) }} USDT
              </h3>
            </div>
            <div class="balance-item">
              <span class="label">持仓数量</span>
              <h3 class="value">{{ positionCount }}</h3>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 实时价格 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>实时价格</span>
              <el-button text @click="loadPrices">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="price-list">
            <price-card
              v-for="ticker in tickers"
              :key="ticker.symbol"
              :ticker="ticker"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 策略状态 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>运行中的策略</span>
              <el-button type="primary" size="small" @click="$router.push('/strategy')">
                管理策略
              </el-button>
            </div>
          </template>
          <el-table :data="strategies" style="width: 100%">
            <el-table-column prop="name" label="策略名称" />
            <el-table-column prop="symbol" label="交易对" width="120" />
            <el-table-column label="盈亏" width="120">
              <template #default="scope">
                <span :class="scope.row.profit >= 0 ? 'profit-positive' : 'profit-negative'">
                  {{ scope.row.profit >= 0 ? '+' : '' }}{{ scope.row.profit.toFixed(2) }}
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
          </el-table>
        </el-card>
      </el-col>

      <!-- 最近订单 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近订单</span>
              <el-button type="primary" size="small" @click="$router.push('/trading')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="recentOrders" style="width: 100%">
            <el-table-column prop="symbol" label="交易对" width="120" />
            <el-table-column label="方向" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.side === 'BUY' ? 'success' : 'danger'" size="small">
                  {{ scope.row.side === 'BUY' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="120" />
            <el-table-column prop="quantity" label="数量" width="120" />
            <el-table-column prop="time" label="时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import PriceCard from '@/components/PriceCard.vue'

const totalBalance = ref(0)
const todayPnl = ref(0)
const positionCount = ref(0)
const tickers = ref([])
const strategies = ref([])
const recentOrders = ref([])

const pnlClass = computed(() => {
  return todayPnl.value >= 0 ? 'profit-positive' : 'profit-negative'
})

const loadOverview = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/overview')
    if (res.data.success) {
      totalBalance.value = res.data.data.total_balance
      todayPnl.value = res.data.data.today_pnl
      positionCount.value = res.data.data.position_count
    }
  } catch (error) {
    console.error('加载概览失败:', error)
  }
}

const loadPrices = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/prices')
    if (res.data.success) {
      tickers.value = res.data.data
    }
  } catch (error) {
    console.error('加载价格失败:', error)
  }
}

const loadStrategies = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/strategies')
    if (res.data.success) {
      strategies.value = res.data.data.strategies
    }
  } catch (error) {
    console.error('加载策略失败:', error)
  }
}

const loadRecentOrders = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/recent-orders')
    if (res.data.success) {
      recentOrders.value = res.data.data
    }
  } catch (error) {
    console.error('加载订单失败:', error)
  }
}

onMounted(() => {
  loadOverview()
  loadPrices()
  loadStrategies()
  loadRecentOrders()

  // 定时刷新
  setInterval(loadPrices, 5000)
  setInterval(loadOverview, 10000)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.account-info {
  padding: 10px 0;
}

.balance-item {
  margin-bottom: 20px;
}

.balance-item:last-child {
  margin-bottom: 0;
}

.label {
  font-size: 14px;
  color: #909399;
}

.value {
  margin: 5px 0 0 0;
  font-weight: 600;
}

.profit-positive {
  color: #67c23a;
}

.profit-negative {
  color: #f56c6c;
}

.price-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}
</style>
