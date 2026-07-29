<script setup lang="ts">
const knowledgeItems = ['如何创建回家模式', '空调节能设置指南', '智能门锁使用说明']
</script>

<template>
  <section class="min-w-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-extrabold text-slate-800">安防与知识库</h2>
      <a class="text-xs font-bold text-blue-600" href="#">更多</a>
    </div>

    <article class="mb-4 flex gap-2 rounded-lg bg-rose-50 p-3">
      <span class="text-rose-500">▲</span>
      <div class="min-w-0">
        <strong class="block text-sm text-slate-800">门窗传感器异常</strong>
        <p class="mt-1 text-xs text-slate-500">厨房窗户 · 10:15</p>
      </div>
    </article>

    <h3 class="mb-2 text-sm font-bold">知识库</h3>
    <a v-for="item in knowledgeItems" :key="item" class="mb-2 block truncate text-xs text-slate-600 hover:text-blue-600" href="#">
      {{ item }}
    </a>
  </section>
</template>
