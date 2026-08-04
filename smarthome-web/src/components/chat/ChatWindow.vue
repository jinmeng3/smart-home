<script setup lang="ts">
import { computed, ref } from "vue";
import { useAutoScroll } from "../../composables/useAutoScroll";
import { useHomeStore } from "../../stores/home";
import AgentExecutionSteps from "../animation/AgentExecutionSteps.vue";
import AIThinking from "../animation/AIThinking.vue";
import AnimatedList from "../animation/AnimatedList.vue";
import ChatMessage from "./ChatMessage.vue";
import { useAuthStore } from "../../stores/auth";

const store = useHomeStore();
const authStore = useAuthStore();
const inputValue = ref("");
const chatScrollRef = ref<HTMLElement | null>(null);

const messageCount = computed(() => store.messages.length);
const visibleMessages = computed(() => store.messages.slice(-30));
const hasMessages = computed(() => visibleMessages.value.length > 0);
const generating = computed(
    () => store.agentStatus === "thinking" || store.agentStatus === "executing",
);
const sendDisabled = computed(
    () =>
        !authStore.isAuthenticated ||
        (!generating.value && !inputValue.value.trim()),
);
const { scrollToBottom, updateStickiness } = useAutoScroll(
    chatScrollRef,
    messageCount,
);

const send = () => {
    if (generating.value) {
        store.stopGenerating();
        return;
    }

    store.sendMessage(inputValue.value);
    inputValue.value = "";
    void scrollToBottom(true);
};

const fillPrompt = (prompt: string) => {
    inputValue.value = prompt;
};

const starterPrompts = [
    {
        title: "全屋状态巡检",
        prompt: "帮我检查全屋设备状态，并标出需要处理的问题",
        icon: "scan",
    },
    {
        title: "晚间回家场景",
        prompt: "帮我设置今晚回家后的灯光、空调和安防联动",
        icon: "home",
    },
    {
        title: "节能建议",
        prompt: "根据当前设备状态，给我一份今日节能建议",
        icon: "energy",
    },
];
</script>

<template>
    <div class="flex min-h-0 flex-1 flex-col px-6 pb-5">
        <section
            ref="chatScrollRef"
            class="page-enter-stagger min-h-0 flex-1 overflow-y-auto pr-2"
            style="animation-delay: 220ms"
            @scroll.passive="updateStickiness"
        >
            <div
                v-if="!hasMessages && store.agentStatus === 'idle'"
                class="empty-chat"
            >
                <img
                    src="/1.png"
                    alt="Empty chat illustration"
                    class="empty-chat-illustration"
                />
                <h2>今天想让家里怎么配合你？</h2>
                <p>
                    从设备巡检、场景联动到节能建议，Orion Home
                    可以先帮你整理可执行方案。
                </p>
                <div class="starter-grid">
                    <button
                        v-for="item in starterPrompts"
                        :key="item.title"
                        class="starter-card"
                        type="button"
                        @click="fillPrompt(item.prompt)"
                    >
                        <span class="starter-icon" aria-hidden="true">
                            <svg
                                v-if="item.icon === 'scan'"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    d="M5 8V5h3M16 5h3v3M19 16v3h-3M8 19H5v-3"
                                />
                                <path d="M8 12h8M12 8v8" />
                            </svg>
                            <svg
                                v-else-if="item.icon === 'home'"
                                viewBox="0 0 24 24"
                            >
                                <path d="M4 11 12 5l8 6" />
                                <path d="M7 10v9h10v-9" />
                                <path d="M10 19v-5h4v5" />
                            </svg>
                            <svg v-else viewBox="0 0 24 24">
                                <path d="M13 3 6 13h5l-1 8 8-11h-5l1-7Z" />
                            </svg>
                        </span>
                        <strong>{{ item.title }}</strong>
                        <span>{{ item.prompt }}</span>
                    </button>
                </div>
            </div>
            <template v-else>
                <AnimatedList tag="div" name="message-list">
                    <ChatMessage
                        v-for="message in visibleMessages"
                        :key="message.id"
                        :message="message"
                    />
                </AnimatedList>
                <AIThinking v-if="store.agentStatus === 'thinking'" />
                <AgentExecutionSteps
                    v-if="store.agentStatus === 'executing'"
                    :steps="store.executionSteps"
                />
            </template>
        </section>

        <form
            class="page-enter-stagger relative mt-4 shrink-0 rounded-2xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-4 shadow-soft transition focus-within:border-[var(--color-border-focus)] focus-within:shadow-[0_0_0_3px_var(--color-focus-ring)]"
            style="animation-delay: 400ms"
            @submit.prevent="send"
        >
            <input
                v-model="inputValue"
                class="h-8 w-full border-0 bg-transparent pr-16 text-sm outline-none placeholder:text-slate-400"
                :disabled="!authStore.isAuthenticated"
                :placeholder="
                    authStore.isAuthenticated
                        ? '向 Orion Home 发送设备控制或自动化需求...'
                        : '登录后可使用智能对话'
                "
            />
            <div
                class="mt-5 flex items-center gap-4 text-[var(--color-primary-600)]"
            >
                <button
                    :disabled="!authStore.isAuthenticated"
                    class="motion-button grid h-8 w-8 place-items-center rounded-full bg-[var(--color-surface-hover)] text-lg"
                    type="button"
                >
                    +
                </button>
                <button
                    :disabled="!authStore.isAuthenticated"
                    class="motion-button"
                    type="button"
                >
                    附件
                </button>
                <button
                    :disabled="!authStore.isAuthenticated"
                    class="motion-button"
                    type="button"
                >
                    @
                </button>
            </div>
            <button
                class="motion-button absolute bottom-4 right-4 grid h-11 w-11 place-items-center rounded-full bg-[var(--color-primary-600)] text-xl text-white shadow-lg shadow-blue-500/20 hover:bg-[var(--color-primary-700)] active:bg-[var(--color-primary-800)] disabled:bg-[var(--color-text-disabled)]"
                type="submit"
                :disabled="sendDisabled"
                :title="generating ? '停止生成' : '发送'"
            >
                <span
                    class="transition-transform group-hover:-translate-y-0.5"
                    >{{ store.agentStatus === "success" ? "✓" : "↑" }}</span
                >
            </button>
        </form>
    </div>
</template>

<style scoped>
.empty-chat {
    display: grid;
    min-height: 100%;
    align-content: center;
    justify-items: center;
    padding: 20px 0;
    text-align: center;
}

.empty-chat-illustration {
    width: clamp(132px, 18vw, 190px);
    max-width: 44%;
    max-height: 148px;
    object-fit: contain;
    filter: drop-shadow(0 8px 18px var(--color-focus-ring));
}

.empty-chat h2 {
    margin-top: 14px;
    color: var(--color-text-primary);
    font-size: 24px;
    font-weight: 800;
    line-height: 1.25;
}

.empty-chat p {
    max-width: 520px;
    margin-top: 10px;
    color: var(--color-text-secondary);
    font-size: 14px;
    line-height: 1.7;
}

.starter-grid {
    display: grid;
    width: min(100%, 680px);
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 24px;
}

.starter-card {
    display: grid;
    grid-template-columns: 38px minmax(0, 1fr);
    gap: 8px 12px;
    min-height: 126px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 16px;
    text-align: left;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    transition:
        border-color 160ms ease,
        box-shadow 160ms ease,
        transform 120ms ease;
}

.starter-card:hover {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
}

.starter-card:active {
    transform: translateY(1px);
}

.starter-card strong {
    align-self: center;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.starter-card span {
    grid-column: 1 / -1;
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.55;
}

.starter-card .starter-icon {
    display: grid;
    width: 38px;
    height: 38px;
    grid-column: auto;
    place-items: center;
    border-radius: 8px;
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.starter-icon svg {
    width: 21px;
    height: 21px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

@media (max-width: 760px) {
    .empty-chat-illustration {
        width: 136px;
        max-width: 58vw;
        max-height: 128px;
    }

    .starter-grid {
        grid-template-columns: 1fr;
    }
}
</style>
