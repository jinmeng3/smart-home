<script setup lang="ts">
import { useHomeStore } from '../../stores/home'
import AutomationCard from '../chat/AutomationCard.vue'

const store = useHomeStore()
</script>

<template>
  <section class="shrink-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-extrabold text-slate-800">▣ 家庭日程 / 自动化计划</h2>
      <a class="text-xs font-bold text-blue-600" href="#">更多</a>
    </div>

    <div class="mb-3 flex items-center justify-between text-sm">
      <button class="text-lg text-slate-400" type="button">‹</button>
      <strong>2025年5月20日 星期二</strong>
      <button class="text-lg text-slate-400" type="button">›</button>
    </div>

    <div class="mb-3 grid gap-2">
      <article v-for="automation in store.automations" :key="automation.id" class="grid grid-cols-[54px_minmax(0,1fr)] gap-3">
        <time class="text-sm font-bold text-slate-700">{{ automation.time }}</time>
        <div class="relative pl-4 before:absolute before:left-0 before:top-1.5 before:h-2 before:w-2 before:rounded-full before:bg-blue-600">
          <strong class="block text-sm">{{ automation.name }}</strong>
          <p class="mt-1 text-xs leading-5 text-slate-500">{{ automation.description }}</p>
        </div>
      </article>
    </div>

    <div class="grid gap-2">
      <AutomationCard v-for="automation in store.automations.slice(0, 2)" :key="automation.id" :automation="automation" />
    </div>
  </section>
</template>
