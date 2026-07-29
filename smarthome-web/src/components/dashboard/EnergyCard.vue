<script setup lang="ts">
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useHomeStore } from '../../stores/home'
import { useChart } from '../../composables/useChart'
import AnimatedNumber from '../animation/AnimatedNumber.vue'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const store = useHomeStore()
const chartRef = ref<HTMLDivElement | null>(null)
const { initChart } = useChart(chartRef)

const chartOptions = {
  animationDuration: 900,
  animationEasing: 'cubicOut' as const,
  grid: { left: 4, right: 4, top: 10, bottom: 4 },
  tooltip: { trigger: 'axis' as const },
  xAxis: { type: 'category' as const, show: false, data: ['00', '03', '06', '09', '12', '15', '18', '21'] },
  yAxis: { type: 'value' as const, show: false },
  series: [
    {
      data: [3, 8, 6, 10, 14, 7, 13, 11],
      type: 'line' as const,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 3, color: getComputedStyle(document.documentElement).getPropertyValue('--color-primary-600').trim() },
      areaStyle: { color: 'rgba(37, 99, 235, 0.12)' },
    },
  ],
}

onMounted(() => {
  initChart(chartOptions)
})
</script>

<template>
  <section class="motion-card page-enter-stagger min-w-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft" style="animation-delay: 340ms">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-extrabold text-slate-800">能耗概览</h2>
      <a class="motion-button text-xs font-bold text-blue-600" href="#">更多</a>
    </div>
    <span class="text-xs text-slate-500">今日用电</span>
    <strong class="mt-1 block text-2xl text-slate-900">
      <AnimatedNumber :value="store.energyToday" :decimals="2" />
      <small class="text-sm"> kWh</small>
    </strong>
    <p class="mt-1 text-xs text-slate-500 trend-enter">较昨日 <b class="text-[var(--color-success)]">↘ -8.7%</b></p>
    <div ref="chartRef" class="h-24 w-full"></div>
    <span class="text-xs text-slate-500">本月用电</span>
    <strong class="block text-sm">
      <AnimatedNumber :value="326.8" :decimals="1" suffix=" kWh" />
    </strong>
  </section>
</template>

<style scoped>
.trend-enter {
  animation: trend-enter 300ms var(--motion-ease) both;
}

@keyframes trend-enter {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
