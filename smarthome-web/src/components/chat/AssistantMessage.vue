<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import type { ChatMessage } from "../../types/chat";
import MarkdownRenderer from "./MarkdownRenderer.vue";
import ChatMessageShell from "./ChatMessageShell.vue";

const props = defineProps<{
    message: ChatMessage;
    streaming?: boolean;
    generating?: boolean;
    regenerating?: boolean;
}>();

const copied = ref(false);
let copyTimer = 0;

/** 重新生成按钮点击旋转动画 */
const regeneratingBtn = ref(false);
let regenBtnTimer = 0;

const emit = defineEmits<{
    regenerate: [messageId: string];
}>();

const copyMessage = async (content: string) => {
    await navigator.clipboard?.writeText(content);
    copied.value = true;

    window.clearTimeout(copyTimer);
    copyTimer = window.setTimeout(() => {
        copied.value = false;
    }, 1500);
};

const handleRegenerateClick = () => {
    regeneratingBtn.value = true;
    window.clearTimeout(regenBtnTimer);
    regenBtnTimer = window.setTimeout(() => {
        regeneratingBtn.value = false;
    }, 600);
    emit('regenerate', props.message.id);
};

onBeforeUnmount(() => {
    window.clearTimeout(copyTimer);
    window.clearTimeout(regenBtnTimer);
});
</script>

<template>
    <ChatMessageShell side="left" :timestamp="message.timestamp" :regenerating="regenerating">
        <template #avatar>
            <div
                class="mt-1 grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white shadow-md shadow-blue-500/10 ring-2 ring-white/60 avatar-in"
                style="animation-delay: 20ms"
            >
                <img src="/orion-sidebar-icon.svg" alt="Orion Home" class="h-5 w-5" />
            </div>
        </template>

        <div
            class="assistant-card rounded-2xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-5 py-4"
        >
            <MarkdownRenderer :content="message.content" :streaming="streaming" />
            <span
                v-if="streaming"
                class="streaming-cursor"
                aria-hidden="true"
            ></span>
        </div>

        <template #actions>
            <div
                v-if="!streaming"
                class="actions-fade-in flex gap-1 border-t border-[var(--color-border-subtle)] px-1 pt-2"
            >
                <button
                    class="action-btn"
                    type="button"
                    title="复制"
                    @click="copyMessage(message.content)"
                >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M8 16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2M16 10h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-2" />
                    </svg>
                    <span>{{ copied ? "已复制" : "复制" }}</span>
                </button>
                <button
                    class="action-btn"
                    :disabled="generating"
                    type="button"
                    title="重新生成"
                    @click="handleRegenerateClick"
                >
                    <svg
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                        :class="{ 'is-spinning': regeneratingBtn }"
                    >
                        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                        <path d="M3 3v5h5M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                        <path d="M21 21v-5h-5" />
                    </svg>
                    <span>重新生成</span>
                </button>
            </div>
        </template>
    </ChatMessageShell>
</template>

<style scoped>
.assistant-card {
    transition: background-color 200ms ease;
}

.action-btn {
    display: inline-flex;
    height: 30px;
    align-items: center;
    gap: 6px;
    border-radius: 6px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    transition:
        color 150ms ease,
        background-color 150ms ease;
}

.action-btn svg {
    width: 15px;
    height: 15px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.8;
    transition: transform 300ms var(--motion-ease-out);
}

.action-btn svg.is-spinning {
    transform: rotate(360deg);
}

.action-btn:hover {
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.action-btn:disabled {
    cursor: not-allowed;
    opacity: 0.45;
}

.actions-fade-in {
    animation: actions-fade-in 200ms var(--motion-ease) both;
}

@keyframes actions-fade-in {
    from {
        opacity: 0;
        transform: translateY(4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
