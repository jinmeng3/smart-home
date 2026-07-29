<script setup lang="ts">
import { computed } from 'vue'
import { useHomeStore } from '../../stores/home'
import type { Device } from '../../types/device'

const store = useHomeStore()

const statusClass = (device: Device) => {
  if (!device.online) {
    return 'bg-rose-50 text-rose-500'
  }

  if (device.type === 'lock') {
    return 'bg-emerald-50 text-emerald-600'
  }

  return 'bg-blue-50 text-blue-600'
}

const detailText = computed(() => {
  const device = store.selectedDevice

  if (!device) {
    return '点击设备查看详情'
  }

  return `${device.room} · ${device.status}${device.value ? ` · ${device.value}` : ''} · ${device.updatedAt}`
})
</script>

<template>
  <section class="min-w-0 shrink-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft">
    <div class="mb-2 flex items-center justify-between">
      <h2 class="text-sm font-extrabold text-slate-800">▣ 设备清单</h2>
      <a class="text-xs font-bold text-blue-600" href="#">更多</a>
    </div>

    <div class="mb-2 flex justify-between text-sm text-slate-500">
      <span>在线 <strong class="text-emerald-600">{{ store.deviceSummary.online }} 台</strong></span>
      <span>离线 <strong class="text-rose-500">{{ store.deviceSummary.offline }} 台</strong></span>
    </div>

    <div class="grid gap-2">
      <button
        v-for="device in store.devices"
        :key="device.id"
        class="grid h-10 min-w-0 grid-cols-[26px_minmax(0,1fr)_minmax(66px,88px)] items-center gap-2 rounded-lg border border-slate-200 bg-white px-2 text-left transition hover:border-blue-200 hover:bg-blue-50/40"
        type="button"
        @click="store.selectDevice(device)"
      >
        <span class="grid h-6 w-6 place-items-center rounded-lg bg-slate-100 text-xs">{{ device.type.slice(0, 1).toUpperCase() }}</span>
        <strong class="truncate text-sm text-slate-700">{{ device.name }}</strong>
        <em class="truncate rounded-md px-2 py-1 text-center text-xs not-italic font-bold" :class="statusClass(device)">{{ device.value ?? device.status }}</em>
      </button>
    </div>

    <p class="mt-2 truncate rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">{{ detailText }}</p>
    <a class="mt-2 block text-center text-xs font-bold text-blue-600" href="#">查看全部设备</a>
  </section>
</template>
