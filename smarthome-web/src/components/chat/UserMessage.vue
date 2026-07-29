<script setup lang="ts">
import type { ChatMessage } from '../../types/chat'

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <article class="user-message-enter mb-5 ml-auto grid max-w-[620px] grid-cols-[minmax(0,1fr)_42px] gap-3">
    <div class="rounded-lg bg-gradient-to-br from-blue-600 to-blue-500 px-5 py-3 text-sm font-semibold leading-6 text-white">
      {{ message.content }}
    </div>
    <div class="grid h-10 w-10 place-items-center rounded-full bg-blue-100 text-blue-700">●</div>
    <time class="col-start-1 justify-self-end text-xs text-slate-400">{{ message.timestamp }}</time>
  </article>
</template>
