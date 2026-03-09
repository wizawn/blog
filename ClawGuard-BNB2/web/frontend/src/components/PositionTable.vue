<template>
  <el-table :data="positions" style="width: 100%">
    <el-table-column prop="symbol" label="交易对" width="120" />
    <el-table-column label="方向" width="80">
      <template #default="scope">
        <el-tag :type="scope.row.positionSide === 'LONG' ? 'success' : 'danger'" size="small">
          {{ scope.row.positionSide }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="positionAmt" label="持仓量" width="120" />
    <el-table-column prop="entryPrice" label="开仓价" width="120" />
    <el-table-column prop="markPrice" label="标记价" width="120" />
    <el-table-column label="未实现盈亏" width="150">
      <template #default="scope">
        <span :class="parseFloat(scope.row.unRealizedProfit) >= 0 ? 'profit' : 'loss'">
          {{ parseFloat(scope.row.unRealizedProfit).toFixed(2) }}
        </span>
      </template>
    </el-table-column>
    <el-table-column prop="leverage" label="杠杆" width="80" />
    <el-table-column label="操作" width="100">
      <template #default="scope">
        <el-button type="danger" size="small" @click="$emit('close', scope.row)">
          平仓
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
defineProps({
  positions: {
    type: Array,
    default: () => []
  }
})

defineEmits(['close'])
</script>

<style scoped>
.profit {
  color: #67c23a;
  font-weight: 600;
}

.loss {
  color: #f56c6c;
  font-weight: 600;
}
</style>
