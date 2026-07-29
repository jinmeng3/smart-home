<script setup lang="ts">
import type { AgentExecutionStep } from '../../types/animation'

defineProps<{
  steps: AgentExecutionStep[]
}>()
</script>

<template>
  <article class="mb-5 grid grid-cols-[42px_minmax(0,460px)] gap-3 ai-message-enter">
    <div class="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white">✦</div>
    <div class="rounded-xl border border-blue-100 bg-white px-5 py-4 shadow-sm">
      <h3 class="mb-3 text-sm font-bold text-slate-800">正在执行智能控制</h3>
      <div class="grid gap-2">
        <div v-for="step in steps" :key="step.id" class="grid grid-cols-[22px_minmax(0,1fr)] items-center gap-2 text-sm">
          <span
            class="grid h-5 w-5 place-items-center rounded-full text-xs font-bold transition"
            :class="{
              'bg-blue-600 text-white step-progress': step.status === 'executing',
              'bg-emerald-500 text-white': step.status === 'completed',
              'bg-slate-100 text-slate-400': step.status === 'pending',
              'bg-rose-100 text-rose-600': step.status === 'failed',
            }"
          >
            {{ step.status === 'completed' ? '✓' : '' }}
          </span>
          <span class="text-slate-600">{{ step.label }}</span>
        </div>
      </div>
    </div>
  </article>
</template>
