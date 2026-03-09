<template>
  <div ref="chartRef" style="width: 100%; height: 500px"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { apiClient } from '@/api/client'

const props = defineProps({
  symbol: {
    type: String,
    required: true
  },
  interval: {
    type: String,
    default: '1h'
  }
})

const chartRef = ref(null)
let chart = null

const loadKlines = async () => {
  try {
    const res = await apiClient.get('/api/analysis/klines', {
      params: {
        symbol: props.symbol,
        interval: props.interval,
        limit: 100
      }
    })

    if (res.data.success) {
      const klines = res.data.data

      // 准备数据
      const dates = klines.map(k => new Date(k.time).toLocaleString())
      const data = klines.map(k => [k.open, k.close, k.low, k.high])
      const volumes = klines.map(k => k.volume)

      // 配置图表
      const option = {
        title: {
          text: `${props.symbol} K线图`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['K线', '成交量'],
          top: 30
        },
        grid: [
          {
            left: '10%',
            right: '10%',
            top: '15%',
            height: '50%'
          },
          {
            left: '10%',
            right: '10%',
            top: '70%',
            height: '15%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: {
              show: true
            }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 50,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            top: '90%',
            start: 50,
            end: 100
          }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: data,
            itemStyle: {
              color: '#ef5350',
              color0: '#26a69a',
              borderColor: '#ef5350',
              borderColor0: '#26a69a'
            }
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: '#7fcdbb'
            }
          }
        ]
      }

      chart.setOption(option)
    }
  } catch (error) {
    console.error('加载K线数据失败:', error)
  }
}

onMounted(() => {
  chart = echarts.init(chartRef.value)
  loadKlines()

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
})

watch(() => [props.symbol, props.interval], () => {
  loadKlines()
})
</script>
