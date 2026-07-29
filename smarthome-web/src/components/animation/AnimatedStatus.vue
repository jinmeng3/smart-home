<script setup lang="ts">
import type { DeviceStatus } from '../../types/animation'

defineProps<{
  status: DeviceStatus
  label: string
}>()
</script>

<template>
  <span class="inline-flex items-center gap-1.5">
    <span
      class="h-2 w-2 rounded-full transition-colors"
      :class="{
        'bg-emerald-500': status === 'online',
        'bg-rose-500': status === 'offline',
        'bg-blue-500 status-dot-running': status === 'running',
        'bg-amber-500': status === 'warning',
      }"
    ></span>
    <Transition name="status-crossfade" mode="out-in">
      <span :key="label">{{ label }}</span>
    </Transition>
  </span>
</template>
