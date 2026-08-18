<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
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
                    <SvgIcon name="copy" size="sm" />
                    <span>{{ copied ? "已复制" : "复制" }}</span>
                </button>
                <button
                    class="action-btn"
                    :disabled="generating"
                    type="button"
                    title="重新生成"
                    @click="handleRegenerateClick"
                >
                    <SvgIcon
                        name="rotate-cw"
                        size="sm"
                        :class="{ 'is-spinning': regeneratingBtn }"
                    />
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

/* 图标按钮样式 —— SvgIcon 接管图标渲染 */
.action-btn .is-spinning {
    animation: btn-spin 300ms ease;
}

@keyframes btn-spin {
    to {
        transform: rotate(360deg);
    }
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
