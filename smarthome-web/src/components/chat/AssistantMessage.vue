<script setup lang="ts">
import type { ChatMessage } from '../../types/chat'
import DeviceCard from './DeviceCard.vue'

defineProps<{
  message: ChatMessage
}>()

const recommendations = ['开启回家模式', '晚上10点切换睡眠模式', '无人活动自动关闭灯光', '空调节能运行']
</script>

<template>
  <article class="mb-5 grid grid-cols-[42px_minmax(0,720px)] gap-3">
    <div class="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white">✦</div>
    <div class="rounded-xl bg-slate-50 px-5 py-4">
      <p class="mb-4 text-sm font-medium text-slate-600">{{ message.content }}</p>
      <div v-if="message.content.includes('当前状态')" class="grid grid-cols-[1fr_1.2fr] gap-3">
        <DeviceCard />
        <section class="rounded-lg border border-blue-100 bg-white p-4">
          <h2 class="mb-3 text-base font-bold">🌙 今晚建议</h2>
          <ol class="grid gap-3">
            <li v-for="(item, index) in recommendations" :key="item" class="grid grid-cols-[24px_minmax(0,1fr)] items-center gap-2 text-sm font-medium text-slate-700">
              <span class="grid h-5 w-5 place-items-center rounded-full bg-blue-600 text-xs font-bold text-white">{{ index + 1 }}</span>
              {{ item }}
            </li>
          </ol>
        </section>
      </div>
      <div class="mt-4 flex gap-4 text-slate-500">
        <button type="button">♡</button>
        <button type="button">♧</button>
        <button type="button">□</button>
        <button type="button">⟳</button>
      </div>
    </div>
  </article>
</template>
