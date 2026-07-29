<script setup lang="ts">
import AnimatedNumber from '../animation/AnimatedNumber.vue'

const statusItems = [
  { id: 'light', name: '客厅灯', value: '关闭', icon: '☼', tone: 'light' },
  { id: 'ac', name: '卧室空调', value: '26℃ 制冷', icon: '▤', tone: 'air' },
  { id: 'window', name: '厨房窗户', value: '关闭', icon: '▥', tone: 'window' },
  { id: 'lock', name: '门锁状态', value: '正常', icon: '▧', tone: 'lock' },
  { id: 'camera', name: '摄像头', value: '在线(3/3)', icon: '●', tone: 'camera' },
  { id: 'air', name: '空气质量', value: '良好 AQI ', icon: '☁', tone: 'aqi', aqi: 28 },
]
</script>

<template>
  <section class="motion-card rounded-lg border border-blue-100 bg-white p-4">
    <h2 class="mb-3 text-base font-bold text-emerald-600">📊 当前家庭状态</h2>
    <div
      v-for="item in statusItems"
      :key="item.id"
      class="status-row grid grid-cols-[24px_1fr_auto] gap-2 py-1.5 text-sm"
      :class="`status-${item.tone}`"
    >
      <span class="status-icon text-center">{{ item.icon }}</span>
      <span class="font-medium text-slate-600">{{ item.name }}</span>
      <strong class="text-slate-800">
        {{ item.value }}<AnimatedNumber v-if="item.aqi" :value="item.aqi" />
      </strong>
    </div>
  </section>
</template>

<style scoped>
.status-icon {
  transition:
    color 240ms var(--motion-ease),
    transform 240ms var(--motion-ease),
    text-shadow 240ms var(--motion-ease);
}

.status-row:hover .status-icon {
  transform: translateX(1px) scale(1.08);
}

.status-light:hover .status-icon {
  color: #2563eb;
  text-shadow: 0 0 14px rgba(37, 99, 235, 0.28);
}

.status-air:hover .status-icon {
  color: #38bdf8;
  text-shadow: 8px 0 12px rgba(56, 189, 248, 0.2);
}

.status-lock:hover .status-icon {
  color: #10b981;
  transform: rotate(-8deg);
}

.status-camera .status-icon {
  color: #2563eb;
}

.status-camera .status-icon::after {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-left: 3px;
  border-radius: 999px;
  background: #ef4444;
}

.status-window:hover .status-icon {
  transform: translateX(3px);
}
</style>
