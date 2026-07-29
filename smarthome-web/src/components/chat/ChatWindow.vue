<script setup lang="ts">
import { computed, ref } from 'vue'
import { useHomeStore } from '../../stores/home'
import ChatMessage from './ChatMessage.vue'
import SuggestionButtons from './SuggestionButtons.vue'

const store = useHomeStore()
const inputValue = ref('')

const statusText = computed(() => `全屋在线 · ${store.deviceSummary.total} 台设备 · ${store.enabledAutomationCount} 个自动化运行中`)

const send = () => {
  store.sendMessage(inputValue.value)
  inputValue.value = ''
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col px-6 pb-5">
    <button class="my-3 flex h-12 shrink-0 items-center justify-between rounded-lg border border-blue-100 bg-white px-5 text-left shadow-sm" type="button">
      <span class="flex items-center gap-3">
        <span class="grid h-8 w-8 place-items-center rounded-lg bg-emerald-500 text-white">✓</span>
        <strong>{{ statusText }}</strong>
      </span>
      <span class="text-xl text-slate-400">›</span>
    </button>

    <section class="min-h-0 flex-1 overflow-y-auto pr-2">
      <ChatMessage v-for="message in store.messages" :key="message.id" :message="message" />
    </section>

    <SuggestionButtons />

    <form class="relative mt-4 shrink-0 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm" @submit.prevent="send">
      <input
        v-model="inputValue"
        class="h-8 w-full border-0 bg-transparent pr-16 text-sm outline-none placeholder:text-slate-400"
        placeholder="向 Orion Home Assistant 发送设备控制或自动化需求..."
      />
      <div class="mt-5 flex items-center gap-4 text-blue-600">
        <button class="grid h-8 w-8 place-items-center rounded-full bg-blue-50 text-lg" type="button">+</button>
        <button type="button">附件</button>
        <button type="button">@</button>
      </div>
      <button class="absolute bottom-4 right-4 grid h-11 w-11 place-items-center rounded-full bg-blue-600 text-xl text-white shadow-lg shadow-blue-500/20" type="submit">
        ↑
      </button>
    </form>
  </div>
</template>
