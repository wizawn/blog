<template>
  <div class="analysis">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>市场分析</span>
              <div>
                <el-select v-model="selectedSymbol" @change="loadData" style="width: 150px; margin-right: 10px">
                  <el-option label="BTCUSDT" value="BTCUSDT" />
                  <el-option label="ETHUSDT" value="ETHUSDT" />
                  <el-option label="BNBUSDT" value="BNBUSDT" />
                </el-select>
                <el-select v-model="selectedInterval" @change="loadData" style="width: 100px">
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="15分钟" value="15m" />
                  <el-option label="1小时" value="1h" />
                  <el-option label="4小时" value="4h" />
                  <el-option label="1天" value="1d" />
                </el-select>
              </div>
            </div>
          </template>
          <k-line-chart :symbol="selectedSymbol" :interval="selectedInterval" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>技术指标</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="RSI">
              <el-tag :type="getRsiType(indicators.rsi)">
                {{ indicators.rsi?.value?.toFixed(2) || '-' }}
              </el-tag>
              <span style="margin-left: 10px">{{ indicators.rsi?.signal || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="MACD">
              <el-tag :type="indicators.macd?.trend === 'bullish' ? 'success' : 'danger'">
                {{ indicators.macd?.trend || '-' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="MA20">
              {{ indicators.ma?.ma20?.toFixed(2) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="MA50">
              {{ indicators.ma?.ma50?.toFixed(2) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="布林带上轨">
              {{ indicators.bollinger?.upper?.toFixed(2) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="布林带下轨">
              {{ indicators.bollinger?.lower?.toFixed(2) || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>综合分析</span>
          </template>
          <div v-if="summary" class="summary">
            <div class="summary-signal">
              <span class="label">综合信号:</span>
              <el-tag :type="getSignalType(summary.overall_signal)" size="large">
                {{ summary.overall_signal }}
              </el-tag>
              <span class="confidence">置信度: {{ summary.confidence }}%</span>
            </div>
            <div class="summary-price">
              <span class="label">当前价格:</span>
              <span class="price">{{ summary.current_price?.toFixed(2) }}</span>
            </div>
            <el-divider />
            <div class="signals-list">
              <h4>信号详情:</h4>
              <div v-for="signal in summary.signals" :key="signal.indicator" class="signal-item">
                <el-tag :type="getSignalType(signal.signal)" size="small">
                  {{ signal.indicator }}
                </el-tag>
                <span class="signal-reason">{{ signal.reason }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import KLineChart from '@/components/KLineChart.vue'

const selectedSymbol = ref('BTCUSDT')
const selectedInterval = ref('1h')
const indicators = ref({})
const summary = ref(null)

const getRsiType = (rsi) => {
  if (!rsi || !rsi.value) return 'info'
  if (rsi.value > 70) return 'danger'
  if (rsi.value < 30) return 'success'
  return 'warning'
}

const getSignalType = (signal) => {
  const types = {
    'BUY': 'success',
    'SELL': 'danger',
    'NEUTRAL': 'info'
  }
  return types[signal] || 'info'
}

const loadIndicators = async () => {
  try {
    const res = await apiClient.get('/api/analysis/indicators', {
      params: {
        symbol: selectedSymbol.value,
        interval: selectedInterval.value,
        type: 'all'
      }
    })
    if (res.data.success) {
      indicators.value = res.data.data
    }
  } catch (error) {
    console.error('加载技术指标失败:', error)
  }
}

const loadSummary = async () => {
  try {
    const res = await apiClient.get('/api/analysis/summary', {
      params: {
        symbol: selectedSymbol.value,
        interval: selectedInterval.value
      }
    })
    if (res.data.success) {
      summary.value = res.data.data
    }
  } catch (error) {
    console.error('加载分析摘要失败:', error)
  }
}

const loadData = () => {
  loadIndicators()
  loadSummary()
}

onMounted(() => {
  loadData()
  setInterval(loadData, 30000)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary {
  padding: 10px 0;
}

.summary-signal {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.summary-price {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.label {
  font-weight: 600;
  color: #606266;
}

.price {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.confidence {
  color: #909399;
}

.signals-list h4 {
  margin: 10px 0;
  color: #303133;
}

.signal-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.signal-reason {
  color: #606266;
  font-size: 14px;
}
</style>
