
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

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
