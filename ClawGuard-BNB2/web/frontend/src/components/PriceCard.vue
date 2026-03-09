<template>
  <div class="price-card">
    <div class="symbol">{{ ticker.symbol }}</div>
    <div class="price">{{ ticker.price?.toFixed(2) }}</div>
    <div :class="['change', changeClass]">
      {{ ticker.change_percent >= 0 ? '+' : '' }}{{ ticker.change_percent?.toFixed(2) }}%
    </div>
    <div class="volume">
      <span class="label">24h量:</span>
      <span>{{ formatVolume(ticker.volume) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  ticker: {
    type: Object,
    required: true
  }
})

const changeClass = computed(() => {
  return props.ticker.change_percent >= 0 ? 'positive' : 'negative'
})

const formatVolume = (volume) => {
  if (!volume) return '0'
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(2) + 'M'
  }
  if (volume >= 1000) {
    return (volume / 1000).toFixed(2) + 'K'
  }
  return volume.toFixed(2)
}
</script>

<style scoped>
.price-card {
  padding: 15px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.price-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.symbol {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.price {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 5px;
}

.change {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.change.positive {
  color: #67c23a;
}

.change.negative {
  color: #f56c6c;
}

.volume {
  font-size: 12px;
  color: #909399;
}

.label {
  margin-right: 5px;
}
</style>
