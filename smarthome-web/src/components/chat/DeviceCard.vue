<script setup lang="ts">
const statusItems = [
  ['客厅灯', '关闭'],
  ['卧室空调', '26℃ 制冷'],
  ['厨房窗户', '关闭'],
  ['门锁状态', '正常'],
  ['摄像头', '在线(3/3)'],
  ['空气质量', '良好 AQI 28'],
]
</script>

<template>
  <section class="rounded-lg border border-blue-100 bg-white p-4">
    <h2 class="mb-3 text-base font-bold text-emerald-600">📊 当前家庭状态</h2>
    <div v-for="[name, value] in statusItems" :key="name" class="grid grid-cols-[1fr_auto] gap-3 py-1.5 text-sm">
      <span class="font-medium text-slate-600">{{ name }}</span>
      <strong class="text-slate-800">{{ value }}</strong>
    </div>
  </section>
</template>
