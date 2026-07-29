<script setup lang="ts">
import { useHomeStore } from '../../stores/home'
import type { Automation } from '../../types/automation'

defineProps<{
  automation: Automation
}>()

const store = useHomeStore()
</script>

<template>
  <article class="rounded-lg border border-blue-100 bg-white p-3">
    <div class="flex items-start justify-between gap-3">
      <div>
        <strong class="block text-sm text-slate-800">{{ automation.name }}</strong>
        <span class="mt-1 block text-xs text-slate-500">{{ automation.trigger }}</span>
      </div>
      <el-switch :model-value="automation.enabled" size="small" @change="store.toggleAutomation(automation.id)" />
    </div>
    <p class="mt-2 text-xs leading-5 text-slate-500">{{ automation.actions.join(' · ') }}</p>
  </article>
</template>
