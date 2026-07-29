<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsType } from 'echarts/core'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const chartRef = ref<HTMLDivElement | null>(null)
let chart: EChartsType | null = null

const renderChart = () => {
  if (!chartRef.value) {
    return
  }

  chart = echarts.init(chartRef.value)
  chart.setOption({
    grid: { left: 4, right: 4, top: 10, bottom: 4 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', show: false, data: ['00', '03', '06', '09', '12', '15', '18', '21'] },
    yAxis: { type: 'value', show: false },
    series: [
      {
        data: [3, 8, 6, 10, 14, 7, 13, 11],
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#2563eb' },
        areaStyle: { color: 'rgba(37, 99, 235, 0.08)' },
      },
    ],
  })
}

const resizeChart = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
})
</script>

<template>
  <section class="min-w-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-extrabold text-slate-800">能耗概览</h2>
      <a class="text-xs font-bold text-blue-600" href="#">更多</a>
    </div>
    <span class="text-xs text-slate-500">今日用电</span>
    <strong class="mt-1 block text-2xl text-slate-900">18.62 <small class="text-sm">kWh</small></strong>
    <p class="mt-1 text-xs text-slate-500">较昨日 <b class="text-emerald-600">-8.7%</b></p>
    <div ref="chartRef" class="h-24 w-full"></div>
    <span class="text-xs text-slate-500">本月用电</span>
    <strong class="block text-sm">326.8 kWh</strong>
  </section>
</template>
