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
const visibleMessages = computed(() => store.messages.slice(-50))
const sendDisabled = computed(() => !inputValue.value.trim() || store.agentStatus === 'thinking' || store.agentStatus === 'executing')
const statusToneClass = computed(() =>
  store.hasWarning
    ? 'border-[var(--color-warning-border)] bg-[var(--color-warning-soft)] text-[var(--color-text-primary)]'
    : 'border-[var(--color-success-border)] bg-[var(--color-success-soft)] text-[var(--color-text-primary)]',
)

const { scrollToBottom, updateStickiness } = useAutoScroll(chatScrollRef, messageCount)

const send = () => {
  store.sendMessage(inputValue.value)
  inputValue.value = ''
  void scrollToBottom(true)
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
        <span v-else class="warning-shake grid h-8 w-8 place-items-center rounded-lg bg-[var(--color-warning)] text-white">!</span>
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

    <section ref="chatScrollRef" class="page-enter-stagger min-h-0 flex-1 overflow-y-auto pr-2" style="animation-delay: 220ms" @scroll.passive="updateStickiness">
      <AnimatedList tag="div" name="message-list">
        <ChatMessage v-for="message in visibleMessages" :key="message.id" :message="message" />
      </AnimatedList>
      <AIThinking v-if="store.agentStatus === 'thinking'" />
      <AgentExecutionSteps v-if="store.agentStatus === 'executing'" :steps="store.executionSteps" />
    </section>

    <SuggestionButtons class="page-enter-stagger" style="animation-delay: 300ms" @select="fillPrompt" />

    <form class="page-enter-stagger relative mt-4 shrink-0 rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4 shadow-[0_1px_3px_rgba(15,23,42,0.04)] transition focus-within:border-[var(--color-border-focus)] focus-within:shadow-[0_0_0_3px_var(--color-focus-ring)]" style="animation-delay: 400ms" @submit.prevent="send">
      <input
        v-model="inputValue"
        class="h-8 w-full border-0 bg-transparent pr-16 text-sm outline-none placeholder:text-slate-400"
        placeholder="向 Orion Home Assistant 发送设备控制或自动化需求..."
      />
      <div class="mt-5 flex items-center gap-4 text-[var(--color-primary-600)]">
        <button class="motion-button grid h-8 w-8 place-items-center rounded-full bg-[var(--color-surface-hover)] text-lg" type="button">+</button>
        <button class="motion-button" type="button">附件</button>
        <button class="motion-button" type="button">@</button>
      </div>
      <button
        class="motion-button absolute bottom-4 right-4 grid h-11 w-11 place-items-center rounded-full bg-[var(--color-primary-600)] text-xl text-white shadow-lg shadow-blue-500/20 hover:bg-[var(--color-primary-700)] active:bg-[var(--color-primary-800)] disabled:bg-[var(--color-text-disabled)]"
        type="submit"
        :disabled="sendDisabled"
      >
        <span class="transition-transform group-hover:-translate-y-0.5">{{ store.agentStatus === 'success' ? '✓' : '↑' }}</span>
      </button>
    </form>
  </div>
</template>
