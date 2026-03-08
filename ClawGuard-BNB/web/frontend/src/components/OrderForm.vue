<template>
  <el-form :model="form" label-width="100px">
    <el-form-item label="交易对">
      <el-input v-model="form.symbol" placeholder="例如: BTCUSDT" />
    </el-form-item>

    <el-form-item label="方向">
      <el-radio-group v-model="form.side">
        <el-radio label="BUY">买入</el-radio>
        <el-radio label="SELL">卖出</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="类型">
      <el-radio-group v-model="form.type">
        <el-radio label="MARKET">市价</el-radio>
        <el-radio label="LIMIT">限价</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item v-if="form.type === 'LIMIT'" label="价格">
      <el-input-number v-model="form.price" :min="0" :precision="2" />
    </el-form-item>

    <el-form-item label="数量">
      <el-input-number v-model="form.quantity" :min="0" :precision="8" />
      <span v-if="form.side === 'BUY' && form.type === 'MARKET'" style="margin-left: 10px">
        USDT
      </span>
    </el-form-item>

    <el-form-item v-if="type === 'futures'" label="持仓方向">
      <el-radio-group v-model="form.positionSide">
        <el-radio label="BOTH">单向</el-radio>
        <el-radio label="LONG">多头</el-radio>
        <el-radio label="SHORT">空头</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="submitOrder" :loading="loading">
        提交订单
      </el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  type: {
    type: String,
    default: 'spot' // spot or futures
  }
})

const emit = defineEmits(['order-placed'])

const form = ref({
  symbol: 'BTCUSDT',
  side: 'BUY',
  type: 'MARKET',
  price: 0,
  quantity: 0,
  positionSide: 'BOTH'
})

const loading = ref(false)

const submitOrder = async () => {
  try {
    // 验证
    if (!form.value.symbol || !form.value.quantity) {
      ElMessage.warning('请填写完整信息')
      return
    }

    if (form.value.type === 'LIMIT' && !form.value.price) {
      ElMessage.warning('限价单需要填写价格')
      return
    }

    // 确认
    const action = form.value.side === 'BUY' ? '买入' : '卖出'
    const orderType = form.value.type === 'MARKET' ? '市价' : '限价'
    let message = `确认${orderType}${action} ${form.value.quantity} ${form.value.symbol}？`

    await ElMessageBox.confirm(message, '确认订单', {
      type: 'warning'
    })

    loading.value = true

    const endpoint = props.type === 'futures'
      ? '/api/trading/futures/order'
      : '/api/trading/spot/order'

    const res = await apiClient.post(endpoint, form.value)

    if (res.data.success) {
      ElMessage.success('订单已提交')
      emit('order-placed')
      resetForm()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交订单失败:', error)
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    symbol: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    price: 0,
    quantity: 0,
    positionSide: 'BOTH'
  }
}
</script>
