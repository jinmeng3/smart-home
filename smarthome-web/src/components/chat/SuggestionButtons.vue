<script setup lang="ts">
import { useHomeStore } from '../../stores/home'

const store = useHomeStore()
const suggestions = ['帮我创建离家模式', '查看二楼所有设备', '分析本周用电趋势', '设置门锁提醒']
</script>

<template>
  <section class="mt-3 shrink-0">
    <p class="mb-2 text-sm text-slate-500">你可以这样问我：</p>
    <div class="flex flex-wrap gap-3">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion"
        class="h-9 rounded-full border border-blue-100 bg-blue-50/70 px-4 text-sm font-semibold text-blue-700 transition hover:bg-blue-100"
        type="button"
        @click="store.sendMessage(suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>
  </section>
</template>
