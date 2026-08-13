<script setup lang="ts">
import { computed } from "vue";
import ChatWindow from "../components/chat/ChatWindow.vue";
import Header from "../components/layout/Header.vue";
import BaseCollapsibleRail from "../components/common/BaseCollapsibleRail.vue";
import TaskContextCard from "../components/dashboard/TaskContextCard.vue";
import DeviceListCard from "../components/dashboard/DeviceListCard.vue";
import EnergyCard from "../components/dashboard/EnergyCard.vue";
import ScheduleCard from "../components/dashboard/ScheduleCard.vue";
import SecurityCard from "../components/dashboard/SecurityCard.vue";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useAuthStore } from "../stores/auth";
import { useHomeStore } from "../stores/home";
import type { AgentExecutionStep } from "../types/chat";

const store = useHomeStore();
const authStore = useAuthStore();

const refreshHomeData = () => {
    return Promise.all([
        store.loadDevices(),
        store.refreshRecentConversations(),
    ]).then(() => undefined);
};

useAuthenticatedLoader(refreshHomeData);

/* ── 对话状态（来自 AssistantRail 迁移） ────────────────────────── */
const hasConversation = computed(
    () => store.messages.length > 0 || store.agentStatus !== "idle",
);

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

const taskActive = computed(() => store.agentStatus === "executing");
const alertCount = computed(() => store.alertCount);
</script>

<template>
    <div class="app-page-layout">
        <section
            :inert="!authStore.isAuthenticated"
            :aria-disabled="!authStore.isAuthenticated"
            class="page-enter chat-section flex min-h-0 flex-col rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft"
        >
            <Header :compact="store.messages.length > 0" />
            <ChatWindow />
        </section>
        <BaseCollapsibleRail
            :title="hasConversation ? '对话上下文' : '家庭状态'"
            :subtitle="hasConversation ? '' : '今日概览与设备状态'"
            storage-key="orion.assistant-rail-collapsed"
        >
            <template #collapsed>
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
            </template>

            <template #default>
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
            </template>
        </BaseCollapsibleRail>
    </div>
</template>

<style scoped>
/* 与 components.css 的 .app-page-layout 保持一致，便于收起时切换列宽。
   仅桌面端（≥1024px）为双栏；移动端保持 components.css 的单栏布局。
   使用 auto 列 + rail 自身 width 过渡实现平滑动画。 */
@media (min-width: 1024px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

.chat-section {
    overflow: hidden;
    min-width: 0;
}

@media (min-width: 1024px) and (max-width: 1279px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

@media (prefers-reduced-motion: reduce) {
    .app-page-layout {
        transition: none;
    }
}

/* ── 折叠状态栏指示器（来自 AssistantRail） ───────────────────── */
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

.rail-card-list {
    padding-top: 10px;
}

.rail-card-list > :deep(section) {
    border-color: var(--color-border-subtle);
    box-shadow: 0 3px 12px rgb(15 23 42 / 5%);
}

@media (prefers-reduced-motion: reduce) {
    .rail-task-dot.is-active {
        animation: none;
    }
}
</style>