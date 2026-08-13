<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useHomeStore } from "../../stores/home";
import DeviceListCard from "./DeviceListCard.vue";
import EnergyCard from "./EnergyCard.vue";
import ScheduleCard from "./ScheduleCard.vue";
import SecurityCard from "./SecurityCard.vue";
import TaskContextCard from "./TaskContextCard.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { AgentExecutionStep } from "../../types/chat";

const props = defineProps<{
    collapsed: boolean;
    phase?: "expanded" | "collapsing" | "collapsed" | "expanding";
}>();

const emit = defineEmits<{
    toggle: [];
}>();

const store = useHomeStore();

/* ── 对话状态判定：有消息或正在执行 → 对话上下文模式 ─────────── */
const hasConversation = computed(
    () => store.messages.length > 0 || store.agentStatus !== "idle",
);

/* ── 与对话联动的相关设备名（用于设备卡高亮） ───────────────── */
// 建立设备名索引，避免嵌套循环 O(n×m)
const deviceNameIndex = computed<Map<string, string>>(() => {
    const map = new Map<string, string>();
    for (const device of store.devices) {
        map.set(device.name, device.id);
    }
    return map;
});

const relatedDeviceNames = computed<string[]>(() => {
    if (store.agentStatus === "idle") return [];
    const names = new Set<string>();
    const nameMap = deviceNameIndex.value;

    // 从尾部遍历查找最近用户消息，避免复制整个数组
    const messages = store.messages;
    for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i];
        if (msg && msg.role === "user") {
            for (const deviceName of nameMap.keys()) {
                if (msg.content.includes(deviceName)) {
                    names.add(deviceName);
                }
            }
            break;
        }
    }

    // 从执行步骤 label 提取（使用 nameMap 的 keys 直接遍历）
    const stepLabels = (store.executionSteps as AgentExecutionStep[]).map(
        (s) => s.label,
    );
    for (const label of stepLabels) {
        for (const deviceName of nameMap.keys()) {
            if (label.includes(deviceName)) {
                names.add(deviceName);
            }
        }
    }

    return [...names];
});

/* ── 收起状态栏信息 ─────────────────────────────────────────── */
const taskActive = computed(() => store.agentStatus === "executing");
const alertCount = computed(() => store.alertCount);

/* ── 滚动渐隐 ───────────────────────────────────────────────── */
const railScrollRef = ref<HTMLElement | null>(null);
const scrollAtBottom = ref(true);
const canScroll = ref(false);
const updateScrollState = () => {
    const el = railScrollRef.value;
    if (!el) return;
    canScroll.value = el.scrollHeight > el.clientHeight + 4;
    scrollAtBottom.value =
        el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
};

watch(
    () => [store.messages.length, store.agentStatus, store.devices.length] as const,
    () => {
        void nextTickUpdate();
    },
);

let tickId = 0;
const nextTickUpdate = () => {
    window.clearTimeout(tickId);
    tickId = window.setTimeout(updateScrollState, 30);
};

const toggleCollapsed = () => {
    emit("toggle");
};
</script>

<template>
    <aside
        class="assistant-rail flex min-h-0 min-w-0 flex-col overflow-hidden rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-rail-bg, var(--color-workspace-background))] shadow-soft"
        :class="[
            collapsed ? 'is-collapsed' : '',
            `phase-${props.phase || 'expanded'}`,
        ]"
        :style="{
            width: collapsed ? '46px' : '330px',
            transition: 'width 300ms cubic-bezier(0.22, 1, 0.36, 1)',
        }"
    >
        <!-- 收起状态栏 -->
        <div v-if="collapsed" class="rail-collapsed">
            <button
                class="rail-toggle"
                type="button"
                :title="'展开右侧栏'"
                @click="toggleCollapsed"
            >
                <SvgIcon name="chevron-left" size="sm" />
            </button>
            <span
                class="rail-task-dot"
                :class="{ 'is-active': taskActive }"
                :title="taskActive ? '任务执行中' : '当前无任务'"
            ></span>
            <span
                v-if="alertCount > 0"
                class="rail-alert-badge"
                :title="`${alertCount} 条告警`"
            >
                {{ alertCount }}
            </span>
        </div>

        <!-- 展开状态 -->
        <template v-else>
            <header class="rail-header shrink-0 rail-detail">
                <div class="min-w-0">
                    <h2>{{ hasConversation ? "对话上下文" : "家庭状态" }}</h2>
                    <p v-if="!hasConversation" class="rail-subtitle">
                        今日概览与设备状态
                    </p>
                </div>
                <button
                    class="rail-toggle"
                    type="button"
                    title="收起右侧栏"
                    aria-label="收起右侧栏"
                    @click="toggleCollapsed"
                >
                    <SvgIcon name="chevron-right" size="sm" />
                </button>
            </header>

            <div
                ref="railScrollRef"
                class="rail-scroll min-h-0 flex-1 overflow-y-auto px-2 pb-3 pt-2.5 rail-detail"
                @scroll.passive="updateScrollState"
            >
                <!-- 对话上下文模式：任务卡置顶，概览折叠下方 -->
                <template v-if="hasConversation">
                    <div class="rail-task-sticky">
                        <TaskContextCard />
                    </div>
                </template>

                <div class="rail-card-list grid gap-2.5">
                    <ScheduleCard />
                    <DeviceListCard :highlight-names="relatedDeviceNames" />
                    <EnergyCard />
                    <SecurityCard />
                </div>
            </div>

            <!-- 底部渐隐 -->
            <div
                class="rail-fade"
                :class="{ 'is-visible': canScroll && !scrollAtBottom }"
                aria-hidden="true"
            ></div>
        </template>
    </aside>
</template>

<style scoped>
/* 布局：单一滚动容器 */
.assistant-rail {
    position: relative;
    transition:
        border-radius 300ms cubic-bezier(0.22, 1, 0.36, 1),
        box-shadow 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.rail-collapsed,
.rail-header,
.rail-scroll {
    animation: rail-content-enter 220ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes rail-content-enter {
    from {
        opacity: 0;
        transform: scale(0.98) translateY(4px);
    }
    to {
        opacity: 1;
        transform: none;
    }
}

@media (prefers-reduced-motion: reduce) {
    .assistant-rail,
    .rail-collapsed,
    .rail-header,
    .rail-scroll {
        animation: none;
        transition-duration: 1ms;
    }
}

/* 收起状态：窄状态栏 */
.rail-collapsed {
    display: flex;
    width: 46px;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    padding-top: 16px;
    margin: 0 auto;
}

.rail-header {
    display: flex;
    min-height: 40px;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 10px 12px 9px;
    background: color-mix(
        in srgb,
        var(--color-panel-background) 72%,
        transparent
    );
}

.rail-header h2 {
    margin: 0;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.3;
}

.rail-subtitle {
    margin: 2px 0 0;
    font-size: 11px;
    color: var(--color-text-muted);
}

.rail-scroll {
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
}

.rail-card-list {
    padding-top: 0;
}

.rail-toggle {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.rail-toggle:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.rail-task-dot {
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: var(--color-border-strong);
    transition:
        background 200ms ease,
        box-shadow 200ms ease;
}

.rail-task-dot.is-active {
    background: var(--color-primary-500);
    box-shadow: 0 0 0 4px var(--color-focus-ring);
    animation: rail-dot-pulse 1800ms ease-in-out infinite;
}

@keyframes rail-dot-pulse {
    0%,
    100% {
        opacity: 1;
    }
    50% {
        opacity: 0.45;
    }
}

.rail-alert-badge {
    display: grid;
    min-width: 18px;
    height: 18px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-danger);
    color: white;
    font-size: 10px;
    font-weight: 900;
}

/* 任务卡吸顶 */
.rail-task-sticky {
    position: sticky;
    top: 0;
    z-index: 3;
    margin-bottom: 12px;
}

/* 滚动条弱化 */
.rail-scroll {
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
}

.rail-card-list {
    padding-top: 10px;
}

.rail-card-list > :deep(section) {
    border-color: var(--color-border-subtle);
    box-shadow: 0 3px 12px rgb(15 23 42 / 5%);
}

.rail-scroll::-webkit-scrollbar {
    width: 4px;
}

.rail-scroll::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: transparent;
    transition: background 180ms ease;
}

.assistant-rail:hover .rail-scroll::-webkit-scrollbar-thumb {
    background: var(--color-border);
}

/* 底部渐隐遮罩 */
.rail-fade {
    position: absolute;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 2;
    height: 26px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 200ms ease;
    background: linear-gradient(
        to top,
        var(--color-rail-bg, var(--color-workspace-background)),
        transparent
    );
}

.rail-fade.is-visible {
    opacity: 1;
}

/* ── 三阶段折叠动画 ─────────────────────────────────────── */
/* 收起：内容先向右移动淡出，宽度再收缩 */
aside.phase-collapsing {
    overflow: hidden;
}

aside.phase-collapsing .rail-detail,
aside.phase-expanding .rail-detail {
    transition:
        opacity 140ms ease,
        transform 180ms cubic-bezier(0.22, 1, 0.36, 1);
}

aside.phase-collapsing .rail-detail {
    opacity: 0;
    transform: translateX(8px);
}

aside.phase-collapsed .rail-detail,
aside.phase-collapsing .rail-detail {
    pointer-events: none;
}

aside.phase-expanding .rail-detail {
    opacity: 1;
    transform: translateX(0);
}

aside.phase-collapsed .rail-detail {
    display: none;
}
</style>
