<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAutoScroll } from '../../composables/useAutoScroll'
import { useHomeStore } from '../../stores/home'
import AgentExecutionSteps from '../animation/AgentExecutionSteps.vue'
import AIThinking from '../animation/AIThinking.vue'
import AnimatedList from '../animation/AnimatedList.vue'
import StatusPulse from '../animation/StatusPulse.vue'
import ChatMessage from './ChatMessage.vue'
import SuggestionButtons from './SuggestionButtons.vue'

const store = useHomeStore()
const inputValue = ref('')
const chatScrollRef = ref<HTMLElement | null>(null)

const messageCount = computed(() => store.messages.length)
const sendDisabled = computed(() => !inputValue.value.trim() || store.agentStatus === 'thinking' || store.agentStatus === 'executing')
const statusToneClass = computed(() => (store.hasWarning ? 'border-amber-200 bg-amber-50/90 text-amber-900' : 'border-blue-100 bg-white text-slate-800'))

useAutoScroll(chatScrollRef, messageCount)

const send = () => {
  store.sendMessage(inputValue.value)
  inputValue.value = ''
}

const fillPrompt = (prompt: string) => {
  inputValue.value = prompt
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col px-6 pb-5">
    <button
      class="motion-card page-enter-stagger my-3 flex h-12 shrink-0 items-center justify-between rounded-lg border px-5 text-left shadow-sm"
      :class="statusToneClass"
      style="animation-delay: 120ms"
      type="button"
    >
      <span class="flex items-center gap-3">
        <StatusPulse v-if="!store.hasWarning" />
        <span v-else class="warning-shake grid h-8 w-8 place-items-center rounded-lg bg-amber-400 text-white">!</span>
        <strong class="flex items-center gap-1">
          <span>全屋在线 ·</span>
          <Transition name="status-crossfade" mode="out-in">
            <span :key="store.deviceSummary.total">{{ store.deviceSummary.total }}</span>
          </Transition>
          <span>台设备 ·</span>
          <Transition name="status-crossfade" mode="out-in">
            <span :key="store.enabledAutomationCount">{{ store.enabledAutomationCount }}</span>
          </Transition>
          <span>个自动化运行中</span>
        </strong>
      </span>
      <span class="text-xl text-slate-400">›</span>
    </button>

    <section ref="chatScrollRef" class="page-enter-stagger min-h-0 flex-1 overflow-y-auto pr-2" style="animation-delay: 220ms">
      <AnimatedList tag="div" name="message-list">
        <ChatMessage v-for="message in store.messages" :key="message.id" :message="message" />
      </AnimatedList>
      <AIThinking v-if="store.agentStatus === 'thinking'" />
      <AgentExecutionSteps v-if="store.agentStatus === 'executing'" :steps="store.executionSteps" />
    </section>

    <SuggestionButtons class="page-enter-stagger" style="animation-delay: 300ms" @select="fillPrompt" />

    <form class="page-enter-stagger relative mt-4 shrink-0 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition focus-within:border-blue-300 focus-within:shadow-[0_0_0_4px_rgba(37,99,235,0.08)]" style="animation-delay: 400ms" @submit.prevent="send">
      <input
        v-model="inputValue"
        class="h-8 w-full border-0 bg-transparent pr-16 text-sm outline-none placeholder:text-slate-400"
        placeholder="向 Orion Home Assistant 发送设备控制或自动化需求..."
      />
      <div class="mt-5 flex items-center gap-4 text-blue-600">
        <button class="motion-button grid h-8 w-8 place-items-center rounded-full bg-blue-50 text-lg" type="button">+</button>
        <button class="motion-button" type="button">附件</button>
        <button class="motion-button" type="button">@</button>
      </div>
      <button
        class="motion-button absolute bottom-4 right-4 grid h-11 w-11 place-items-center rounded-full bg-blue-600 text-xl text-white shadow-lg shadow-blue-500/20 disabled:bg-slate-300"
        type="submit"
        :disabled="sendDisabled"
      >
        <span class="transition-transform group-hover:-translate-y-0.5">{{ store.agentStatus === 'success' ? '✓' : '↑' }}</span>
      </button>
    </form>
  </div>
</template>
