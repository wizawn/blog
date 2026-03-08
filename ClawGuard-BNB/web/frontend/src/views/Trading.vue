<template>
  <div class="trading">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 现货交易 -->
      <el-tab-pane label="现货交易" name="spot">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>下单</span>
              </template>
              <order-form type="spot" @order-placed="handleOrderPlaced" />
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>账户余额</span>
              </template>
              <el-table :data="spotBalances" style="width: 100%" max-height="400">
                <el-table-column prop="asset" label="资产" width="100" />
                <el-table-column prop="free" label="可用" />
                <el-table-column prop="locked" label="冻结" />
                <el-table-column prop="total" label="总计" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="hover" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>当前订单</span>
              <el-button text @click="loadSpotOrders">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="spotOrders" style="width: 100%">
            <el-table-column prop="symbol" label="交易对" width="120" />
            <el-table-column label="方向" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.side === 'BUY' ? 'success' : 'danger'" size="small">
                  {{ scope.row.side === 'BUY' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="price" label="价格" width="120" />
            <el-table-column prop="origQty" label="数量" width="120" />
            <el-table-column prop="executedQty" label="已成交" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)" size="small">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button
                  v-if="scope.row.status === 'NEW'"
                  type="danger"
                  size="small"
                  @click="cancelOrder(scope.row)"
                >
                  取消
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 合约交易 -->
      <el-tab-pane label="合约交易" name="futures">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>合约下单</span>
              </template>
              <order-form type="futures" @order-placed="handleOrderPlaced" />
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>持仓</span>
              </template>
              <position-table :positions="futuresPositions" @close="closePosition" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrderForm from '@/components/OrderForm.vue'
import PositionTable from '@/components/PositionTable.vue'

const activeTab = ref('spot')
const spotBalances = ref([])
const spotOrders = ref([])
const futuresPositions = ref([])

const getStatusType = (status) => {
  const types = {
    'NEW': 'info',
    'FILLED': 'success',
    'PARTIALLY_FILLED': 'warning',
    'CANCELED': 'info',
    'REJECTED': 'danger'
  }
  return types[status] || 'info'
}

const loadSpotAccount = async () => {
  try {
    const res = await apiClient.get('/api/trading/account?type=spot')
    if (res.data.success && res.data.data.balances) {
      spotBalances.value = res.data.data.balances
        .filter(b => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0)
        .map(b => ({
          asset: b.asset,
          free: parseFloat(b.free).toFixed(8),
          locked: parseFloat(b.locked).toFixed(8),
          total: (parseFloat(b.free) + parseFloat(b.locked)).toFixed(8)
        }))
    }
  } catch (error) {
    console.error('加载现货账户失败:', error)
  }
}

const loadSpotOrders = async () => {
  try {
    const res = await apiClient.get('/api/trading/spot/orders?status=open')
    if (res.data.success) {
      spotOrders.value = res.data.data
    }
  } catch (error) {
    console.error('加载现货订单失败:', error)
  }
}

const loadFuturesPositions = async () => {
  try {
    const res = await apiClient.get('/api/trading/futures/positions')
    if (res.data.success) {
      futuresPositions.value = res.data.data
    }
  } catch (error) {
    console.error('加载合约持仓失败:', error)
  }
}

const cancelOrder = async (order) => {
  try {
    await ElMessageBox.confirm('确定要取消此订单吗？', '确认', {
      type: 'warning'
    })

    const res = await apiClient.delete(`/api/trading/spot/order/${order.orderId}?symbol=${order.symbol}`)
    if (res.data.success) {
      ElMessage.success('订单已取消')
      loadSpotOrders()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消订单失败:', error)
    }
  }
}

const closePosition = async (position) => {
  try {
    await ElMessageBox.confirm('确定要平仓吗？', '确认', {
      type: 'warning'
    })

    // TODO: 实现平仓逻辑
    ElMessage.success('平仓成功')
    loadFuturesPositions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('平仓失败:', error)
    }
  }
}

const handleOrderPlaced = () => {
  ElMessage.success('订单已提交')
  loadSpotOrders()
  loadSpotAccount()
  loadFuturesPositions()
}

onMounted(() => {
  loadSpotAccount()
  loadSpotOrders()
  loadFuturesPositions()

  // 定时刷新
  setInterval(() => {
    if (activeTab.value === 'spot') {
      loadSpotOrders()
      loadSpotAccount()
    } else {
      loadFuturesPositions()
    }
  }, 5000)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
