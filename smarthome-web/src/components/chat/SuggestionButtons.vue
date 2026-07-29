<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import type { SuggestionStatus } from '../../types/animation'
import AnimatedList from '../animation/AnimatedList.vue'

const emit = defineEmits<{
  select: [prompt: string]
}>()

const suggestions = ['帮我创建离家模式', '查看二楼所有设备', '分析本周用电趋势', '设置门锁提醒']
const statuses = ref<Record<string, SuggestionStatus>>({})
const timerIds: number[] = []

const selectSuggestion = (suggestion: string) => {
  statuses.value = { ...statuses.value, [suggestion]: 'executing' }
  emit('select', suggestion)

  const timerId = window.setTimeout(() => {
    statuses.value = { ...statuses.value, [suggestion]: 'completed' }
  }, 420)
  timerIds.push(timerId)
}

const statusOf = (suggestion: string): SuggestionStatus => statuses.value[suggestion] ?? 'pending'

onBeforeUnmount(() => {
  timerIds.forEach((timerId) => window.clearTimeout(timerId))
})
</script>

<template>
  <section class="mt-3 shrink-0">
    <p class="mb-2 text-sm text-slate-500">你可以这样问我：</p>
    <AnimatedList tag="div" name="suggestion-list" class="flex flex-wrap gap-3">
      <button
        v-for="(suggestion, index) in suggestions"
        :key="suggestion"
        class="motion-button group h-9 rounded-full border border-[var(--color-border-default)] bg-[var(--color-action-subtle)] px-4 text-sm font-semibold text-[var(--color-primary-700)] transition hover:border-[var(--color-primary-200)] hover:bg-[var(--color-primary-100)] active:bg-[var(--color-primary-200)]"
        :style="{ transitionDelay: `${index * 70}ms` }"
        type="button"
        @click="selectSuggestion(suggestion)"
      >
        <span v-if="statusOf(suggestion) === 'completed'" class="text-emerald-600">✓</span>
        <span v-else-if="statusOf(suggestion) === 'executing'" class="inline-block h-2 w-2 rounded-full bg-blue-600 step-progress"></span>
        {{ suggestion }}
        <span class="inline-block text-[var(--color-text-tertiary)] transition group-hover:translate-x-0.5 group-hover:text-[var(--color-primary-600)]">›</span>
      </button>
    </AnimatedList>
  </section>
</template>
