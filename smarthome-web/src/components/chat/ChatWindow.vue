<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useAutoScroll } from "../../composables/useAutoScroll";
import { useHomeStore } from "../../stores/home";
import { useAuthStore } from "../../stores/auth";
import AnimatedList from "../animation/AnimatedList.vue";
import SvgIcon from "../common/SvgIcon.vue";
import ChatComposer from "./ChatComposer.vue";
import ChatInlineStatus from "./ChatInlineStatus.vue";
import ChatMessage from "./ChatMessage.vue";
import AgentConfirmationCard from "./AgentConfirmationCard.vue";

const store = useHomeStore();
const authStore = useAuthStore();
const chatScrollRef = ref<HTMLElement | null>(null);

const visibleMessages = computed(() => store.messages.slice(-30));
const hasMessages = computed(() => visibleMessages.value.length > 0);
const { scrollToBottom, shouldStickToBottom, updateStickiness } = useAutoScroll(
    chatScrollRef,
);

/** 用于填充提示词到输入框 */
const pendingPrompt = ref("");

/** 当前正在流式输出的助手消息 id（用于显示流式光标） */
const streamingMessageId = computed<string | null>(() => {
    if (store.agentStatus !== "executing") return null;
    const last = store.messages[store.messages.length - 1];
    if (!last || last.role !== "assistant") return null;
    return last.id;
});

const hasStreamingContent = computed(() => {
    if (!streamingMessageId.value) return false;
    const message = store.messages.find(
        (item) => item.id === streamingMessageId.value,
    );
    return Boolean(message?.content.trim());
});

/* === 重新生成状态：点击按钮后延迟执行 splice，让退场动画先播放 === */
const regeneratingMessageId = ref<string | null>(null);
let regeneratingTimer = 0;
const handleRegenerate = (messageId: string) => {
    if (regeneratingMessageId.value) return; // 正在处理中
    regeneratingMessageId.value = messageId;
    window.clearTimeout(regeneratingTimer);
    regeneratingTimer = window.setTimeout(() => {
        regeneratingMessageId.value = null;
        store.regenerateMessage(messageId);
    }, 180);
};

/* === 发送与停止 === */
const handleSend = (content: string) => {
    store.sendMessage(content);
    void scrollToBottom(true);
};

const handleStop = () => {
    store.stopGenerating();
};

const handleApprove = () => {
    store.handleDecision("approve");
};

const handleReject = () => {
    store.handleDecision("reject");
};

const fillPrompt = (prompt: string) => {
    pendingPrompt.value = prompt;
};

onMounted(() => {
    void store.fetchModels();
});

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
    <div class="chat-workspace relative flex min-h-0 flex-1 flex-col px-6 pb-5 pt-4">
        <section
            ref="chatScrollRef"
            :inert="!authStore.isAuthenticated"
            :aria-disabled="!authStore.isAuthenticated"
            class="page-enter-stagger chat-scroll-area min-h-0 flex-1 overflow-y-auto pr-2"
            :class="{ 'has-messages': hasMessages }"
            style="animation-delay: 220ms"
            @scroll.passive="updateStickiness"
        >
            <Transition name="empty-to-chat" mode="out-in">
                <div
                    :key="hasMessages ? 'chat' : 'empty'"
                    class="chat-content-wrapper"
                >
                    <div
                        v-if="!hasMessages && store.agentStatus === 'idle'"
                        class="empty-chat"
                    >
                        <div class="empty-chat-illustration stagger-in" style="animation-delay: 60ms">
                    <svg viewBox="0 0 200 160" class="h-full w-full" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="orb-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="var(--color-primary-400)" stop-opacity="0.35" />
                                <stop offset="50%" stop-color="var(--color-primary-500)" stop-opacity="0.25" />
                                <stop offset="100%" stop-color="var(--color-primary-600)" stop-opacity="0.15" />
                            </linearGradient>
                            <linearGradient id="beam-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="var(--color-primary-400)" stop-opacity="0" />
                                <stop offset="50%" stop-color="var(--color-primary-400)" stop-opacity="0.12" />
                                <stop offset="100%" stop-color="var(--color-primary-400)" stop-opacity="0" />
                            </linearGradient>
                            <filter id="orb-glow">
                                <feGaussianBlur stdDeviation="8" result="blur" />
                                <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                            </filter>
                        </defs>
                        <!-- 光束 -->
                        <ellipse cx="100" cy="145" rx="80" ry="6" fill="url(#beam-grad)" class="orb-beam" />
                        <!-- 光环 -->
                        <circle cx="100" cy="70" r="42" fill="none" stroke="var(--color-primary-200)" stroke-width="0.8" opacity="0.5" class="orb-ring-1" />
                        <circle cx="100" cy="70" r="52" fill="none" stroke="var(--color-primary-200)" stroke-width="0.6" opacity="0.3" class="orb-ring-2" />
                        <!-- 主球体渐变 -->
                        <circle cx="100" cy="70" r="36" fill="url(#orb-grad)" filter="url(#orb-glow)" class="orb-main" />
                        <!-- 核心高光 -->
                        <circle cx="100" cy="70" r="18" fill="var(--color-primary-100)" opacity="0.4" class="orb-core" />
                        <circle cx="92" cy="58" r="8" fill="white" opacity="0.25" class="orb-highlight" />
                        <!-- 浮动粒子 -->
                        <circle cx="64" cy="42" r="3" fill="var(--color-primary-400)" opacity="0.3" class="particle p1" />
                        <circle cx="140" cy="38" r="2.5" fill="var(--color-primary-500)" opacity="0.25" class="particle p2" />
                        <circle cx="48" cy="80" r="2" fill="var(--color-primary-400)" opacity="0.2" class="particle p3" />
                        <circle cx="155" cy="85" r="2.5" fill="var(--color-primary-500)" opacity="0.2" class="particle p4" />
                        <circle cx="70" cy="55" r="1.5" fill="var(--color-primary-300)" opacity="0.3" class="particle p5" />
                        <circle cx="130" cy="50" r="1.8" fill="var(--color-primary-400)" opacity="0.25" class="particle p6" />
                        <circle cx="56" cy="68" r="1.2" fill="var(--color-primary-300)" opacity="0.2" class="particle p7" />
                        <circle cx="148" cy="72" r="1.5" fill="var(--color-primary-400)" opacity="0.2" class="particle p8" />
                    </svg>
                </div>
                <h2 class="stagger-in" style="animation-delay: 140ms">
                    今天想让家里怎么配合你？
                </h2>
                <p class="stagger-in" style="animation-delay: 220ms">
                    从设备巡检、场景联动到节能建议，Orion Home
                    可以先帮你整理可执行方案。
                </p>
                <div class="starter-grid">
                    <button
                        v-for="(item, index) in starterPrompts"
                        :key="item.title"
                        class="starter-card stagger-in"
                        :class="`is-${item.icon}`"
                        :style="{ animationDelay: `${300 + index * 90}ms` }"
                        type="button"
                        @click="fillPrompt(item.prompt)"
                    >
                        <span class="starter-icon" aria-hidden="true">
                            <SvgIcon :name="item.icon" />
                        </span>
                        <strong>{{ item.title }}</strong>
                        <span>{{ item.prompt }}</span>
                    </button>
                </div>
                    </div>
                    <template v-else>
                <div v-if="store.hasMoreMessages" class="load-earlier-wrapper">
                    <button
                        class="load-earlier-btn"
                        type="button"
                        @click="store.loadEarlierMessages"
                    >
                        加载更早消息
                    </button>
                </div>
                <AnimatedList tag="div" name="message-list">
                    <ChatMessage
                        v-for="message in visibleMessages"
                        :key="message.id"
                        :message="message"
                        :streaming="message.id === streamingMessageId"
                        :generating="store.agentStatus === 'executing'"
                        :regenerating="message.id === regeneratingMessageId"
                        @regenerate="handleRegenerate"
                    />
                </AnimatedList>
                <ChatInlineStatus
                    v-if="
                        store.agentStatus === 'executing' &&
                        !hasStreamingContent
                    "
                    :label="store.pendingStatus || '正在等待智能体响应'"
                />
                <AgentConfirmationCard
                    v-if="
                        store.agentStatus === 'awaiting_approval' &&
                        store.pendingApproval
                    "
                    :approval="store.pendingApproval"
                    :submitting="store.decisionSubmitting"
                    @approve="handleApprove"
                    @reject="handleReject"
                />
            </template>
                </div>
            </Transition>
        </section>

        <!-- 滚动到底部按钮 -->
        <Transition name="status-crossfade">
            <button
                v-if="hasMessages && !shouldStickToBottom && store.agentStatus !== 'executing' && store.agentStatus !== 'thinking'"
                class="scroll-bottom-btn"
                type="button"
                title="滚动到最新消息"
                @click="scrollToBottom(true)"
            >
                <SvgIcon name="chevron-down" size="sm" />
            </button>
        </Transition>

        <div class="mode-toggle">
            <button
                class="mode-btn"
                :class="{ active: store.agentMode === 'agent' }"
                type="button"
                @click="store.agentMode = 'agent'"
            >
                Agent
            </button>
            <button
                class="mode-btn"
                :class="{ active: store.agentMode === 'chat' }"
                type="button"
                @click="store.agentMode = 'chat'"
            >
                对话
            </button>
        </div>

        <ChatComposer
            :prompt="pendingPrompt"
            @send="handleSend"
            @stop="handleStop"
        />
    </div>
</template>

<style scoped>
.chat-workspace {
    background:
        linear-gradient(
            180deg,
            color-mix(in srgb, var(--color-primary-50) 38%, transparent),
            transparent 88px
        ),
        var(--color-workspace-background);
}

.empty-chat {
    display: grid;
    min-height: 100%;
    align-content: center;
    justify-items: center;
    padding: 20px 0;
    text-align: center;
}

.stagger-in {
    animation: fade-up 360ms var(--motion-ease) both;
}

@keyframes fade-up {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.empty-chat-illustration {
    width: clamp(132px, 18vw, 190px);
    max-width: 44%;
    max-height: 148px;
}

.empty-chat-illustration svg {
    display: block;
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 8px 18px var(--color-focus-ring));
}

/* SVG 动画 */
.orb-main {
    animation: orb-pulse 4s ease-in-out infinite;
    transform-origin: center;
}

.orb-ring-1 {
    animation: ring-rotate 8s linear infinite;
    transform-origin: center;
}

.orb-ring-2 {
    animation: ring-rotate 12s linear infinite reverse;
    transform-origin: center;
}

.orb-beam {
    animation: beam-pulse 3s ease-in-out infinite;
}

.orb-core {
    animation: core-breathe 3s ease-in-out infinite;
}

.particle {
    animation: particle-float 6s ease-in-out infinite;
}
.particle.p2 { animation-delay: -1s; }
.particle.p3 { animation-delay: -2s; }
.particle.p4 { animation-delay: -3s; }
.particle.p5 { animation-delay: -0.5s; }
.particle.p6 { animation-delay: -1.5s; }
.particle.p7 { animation-delay: -2.5s; }
.particle.p8 { animation-delay: -3.5s; }

@keyframes orb-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.04); opacity: 0.85; }
}

@keyframes ring-rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes beam-pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}

@keyframes core-breathe {
    0%, 100% { opacity: 0.35; r: 18px; }
    50% { opacity: 0.55; r: 20px; }
}

@keyframes particle-float {
    0%, 100% {
        transform: translateY(0) scale(1);
        opacity: 0.3;
    }
    50% {
        transform: translateY(-6px) scale(1.15);
        opacity: 0.5;
    }
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
    border-radius: 12px;
    padding: 16px;
    text-align: left;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    transition:
        border-color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms var(--motion-ease-out);
}

.starter-card:hover {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
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

.starter-card.is-scan .starter-icon {
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.starter-card.is-home .starter-icon {
    color: var(--tone-purple);
    background: var(--tone-purple-soft);
}

.starter-card.is-energy .starter-icon {
    color: var(--color-teal-600);
    background: var(--color-teal-soft);
}

.starter-card.is-scan:hover {
    border-color: var(--color-primary-300);
}

.starter-card.is-home:hover {
    border-color: color-mix(in srgb, var(--tone-purple) 40%, transparent);
}

.starter-card.is-energy:hover {
    border-color: var(--color-teal-border);
}

.starter-icon svg {
    transition: transform 200ms var(--motion-ease-out);
}

.starter-card:hover .starter-icon svg {
    transform: scale(1.12) rotate(-3deg);
}

.model-menu {
    max-width: min(240px, 42%);
}

/* 滚动到底部按钮 */
.scroll-bottom-btn {
    position: absolute;
    bottom: 104px;
    left: 50%;
    z-index: 10;
    display: grid;
    height: 36px;
    width: 36px;
    place-items: center;
    border-radius: 999px;
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
    box-shadow: 0 4px 16px rgb(15 23 42 / 12%);
    cursor: pointer;
    transform: translateX(-50%);
    transition:
        border-color 200ms ease,
        color 200ms ease,
        box-shadow 200ms ease,
        transform 200ms ease;
    will-change: transform, opacity;
}

.scroll-bottom-btn:hover {
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
    box-shadow: 0 6px 20px rgb(15 23 42 / 15%);
    transform: translateX(-50%) translateY(-2px);
}

.scroll-bottom-btn:active {
    transform: translateX(-50%) scale(0.95);
}

/* 聊天区域自定义滚动条 */
.chat-scroll-area::-webkit-scrollbar {
    display: block;
    width: 4px;
    height: 4px;
}

.chat-scroll-area::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: var(--color-border);
    transition: background 200ms ease;
}

.chat-scroll-area::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-strong);
}

.chat-scroll-area::-webkit-scrollbar-track {
    background: transparent;
}

@media (max-width: 520px) {
    .composer-tools {
        gap: 10px;
    }

    .model-menu {
        max-width: none;
        flex: 1 1 0;
    }
}

@media (max-width: 760px) {
    .empty-chat-illustration {
        width: 140px;
        height: 112px;
    }
	
    .starter-grid {
        grid-template-columns: 1fr;
    }
}

/* === 加载更早消息按钮 === */
.load-earlier-wrapper {
    display: flex;
    justify-content: center;
    padding: 8px 0;
}

.load-earlier-btn {
    padding: 6px 18px;
    border: 1px solid var(--color-border-default);
    border-radius: 999px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: background 150ms, border-color 150ms;
}

.load-earlier-btn:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-primary-400);
}

/* === 模式切换按钮 === */
.mode-toggle {
    display: flex;
    gap: 4px;
    padding: 4px 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-surface-subtle);
    margin: 0 6px 6px;
    align-self: flex-start;
}

.mode-btn {
    padding: 3px 12px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: background 150ms, color 150ms;
}

.mode-btn.active {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.mode-btn:hover:not(.active) {
    color: var(--color-text-secondary);
}
</style>
