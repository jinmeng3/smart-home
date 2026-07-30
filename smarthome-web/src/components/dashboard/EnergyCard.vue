<script setup lang="ts">
import { computed } from 'vue'
import { useHomeStore } from '../../stores/home'
import AnimatedNumber from '../animation/AnimatedNumber.vue'

const store = useHomeStore()
const energyTrend = [3, 8, 6, 10, 14, 7, 13, 11]
const chartWidth = 300
const chartHeight = 88
const chartPadding = 4
const maxValue = Math.max(...energyTrend)
const minValue = Math.min(...energyTrend)
const valueRange = maxValue - minValue || 1

const points = computed(() =>
  energyTrend
    .map((value, index) => {
      const x = chartPadding + (index / (energyTrend.length - 1)) * (chartWidth - chartPadding * 2)
      const y =
        chartPadding +
        ((maxValue - value) / valueRange) * (chartHeight - chartPadding * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' '),
)
const areaPoints = computed(
  () =>
    `${chartPadding},${chartHeight} ${points.value} ${chartWidth - chartPadding},${chartHeight}`,
)
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
    <p class="trend-enter mt-1 text-xs text-slate-500">较昨日 <b class="text-[var(--color-success)]">↓ 8.7%</b></p>
    <svg
      aria-label="今日用电趋势"
      class="h-24 w-full"
      preserveAspectRatio="none"
      role="img"
      :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
    >
      <defs>
        <linearGradient id="energy-area" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stop-color="var(--color-primary-600)" stop-opacity="0.2" />
          <stop offset="1" stop-color="var(--color-primary-600)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <polygon :points="areaPoints" fill="url(#energy-area)" />
      <polyline
        class="sparkline"
        :points="points"
        fill="none"
        stroke="var(--color-primary-600)"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="3"
        vector-effect="non-scaling-stroke"
      />
    </svg>
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

.sparkline {
  stroke-dasharray: 420;
  stroke-dashoffset: 420;
  animation: sparkline-draw 900ms var(--motion-ease) forwards;
}

@keyframes trend-enter {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}

@keyframes sparkline-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sparkline {
    animation: none;
    stroke-dashoffset: 0;
  }
}
</style>
