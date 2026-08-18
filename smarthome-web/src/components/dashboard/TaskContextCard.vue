<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { useHomeStore } from "../../stores/home";

const store = useHomeStore();

/** 阶段文案：与 ChatWindow 中的状态卡保持一致的语气 */
const phaseLabel = computed(() => {
    const status = store.agentStatus;

    if (status === "success") {
        const done = store.executionSteps.filter(
            (s) => s.status === "completed" || s.status === "failed",
        ).length;
        return store.executionSteps.length > 0
            ? `已完成 ${done}/${store.executionSteps.length} 个操作`
            : "回复完成";
    }
    if (status === "error") return "执行出错";
    if (status === "executing") {
        if (store.executionSteps.length > 0) return store.pendingStatus || "正在调用设备";
        return store.pendingStatus || "正在理解";
    }
    return "";
});

const statusTone = computed(() => {
    const status = store.agentStatus;
    if (status === "success") return "is-success";
    if (status === "error") return "is-error";
    return "is-running";
});

const statusText = computed(() => {
    const status = store.agentStatus;
    if (status === "success") return "完成";
    if (status === "error") return "失败";
    if (status === "executing") return "进行中";
    return "待命";
});

/** 当前执行中的请求总数（用于进度显示） */
const totalSteps = computed(() => store.executionSteps.length);
const doneSteps = computed(
    () =>
        store.executionSteps.filter(
            (s) => s.status === "completed" || s.status === "failed",
        ).length,
);
const progressPercent = computed(() => {
    if (totalSteps.value === 0) return store.agentStatus === "executing" ? 30 : 100;
    return Math.round((doneSteps.value / totalSteps.value) * 100);
});

/** 展示完整执行流程，结束后仍保留，便于定位失败环节。 */
const visibleSteps = computed(() => {
    return store.executionSteps;
});

const showTask = computed(
    () =>
        store.agentStatus === "executing" ||
        store.agentStatus === "success" ||
        store.agentStatus === "error",
);
</script>

<template>
    <section
        v-if="showTask"
        class="task-context-card rounded-xl border px-3 py-3"
        :class="statusTone"
    >
        <header class="mb-2 flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 text-sm font-extrabold text-[var(--color-text-primary)]">
                <span class="task-status-dot" aria-hidden="true"></span>
                当前任务
            </h2>
            <span class="task-status-badge" :class="statusTone">
                {{ statusText }}
            </span>
        </header>

        <!-- 主要结论：阶段文案 -->
        <p v-if="phaseLabel" class="task-phase text-[13px] font-bold">
            {{ phaseLabel }}
        </p>

        <!-- 进度条 -->
        <div
            v-if="store.agentStatus === 'executing'"
            class="task-progress mt-2 h-1 overflow-hidden rounded-full bg-[var(--color-surface-subtle)]"
        >
            <div
                class="task-progress-bar h-full rounded-full bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-400)] transition-all duration-400"
                :style="{ width: `${progressPercent}%` }"
            ></div>
        </div>

        <!-- 执行步骤 -->
        <div v-if="visibleSteps.length" class="task-steps mt-2.5 grid gap-1.5">
            <div
                v-for="step in visibleSteps"
                :key="step.id"
                class="task-step-row grid min-w-0 grid-cols-[18px_minmax(0,1fr)] items-start gap-2 text-xs"
                :class="step.status === 'failed' ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-secondary)]'"
            >
                <span
                    class="task-step-dot grid h-4 w-4 shrink-0 place-items-center rounded-full"
                    :class="{
                        'bg-[var(--color-primary-600)] text-white':
                            step.status === 'executing',
                        'bg-[var(--color-success)] text-white':
                            step.status === 'completed',
                        'bg-[var(--color-danger-soft)] text-[var(--color-danger)]':
                            step.status === 'failed',
                    }"
                >
                    <SvgIcon
                        v-if="step.status === 'completed' || step.status === 'failed'"
                        :name="step.status === 'completed' ? 'check' : 'x'"
                        size="sm"
                    />
                </span>
                <span class="min-w-0">
                    <strong class="block truncate font-bold">{{ step.label }}</strong>
                    <small
                        v-if="step.message"
                        class="mt-0.5 block break-words text-[11px] leading-4 text-[var(--color-danger)]"
                    >{{ step.message }}</small>
                </span>
            </div>
        </div>

        <!-- 完成后显示摘要 -->
        <p
            v-else-if="store.agentStatus === 'success'"
            class="mt-2 text-xs font-bold text-[var(--color-text-tertiary)]"
        >
            任务已完成，概览信息已更新
        </p>
    </section>
</template>

<style scoped>
.task-context-card {
    background: color-mix(in srgb, var(--color-primary-50) 55%, var(--color-card-bg));
    border-color: var(--color-primary-200);
    animation: task-card-enter 240ms var(--motion-ease) both;
}

.task-context-card.is-success {
    background: color-mix(in srgb, var(--color-success-soft) 45%, var(--color-card-bg));
    border-color: var(--color-success-border);
}

.task-context-card.is-error {
    background: color-mix(in srgb, var(--color-danger-soft) 35%, var(--color-card-bg));
    border-color: var(--color-danger);
}

@keyframes task-card-enter {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.task-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--color-primary-500);
    animation: task-dot-pulse 1800ms ease-in-out infinite;
}

.task-context-card.is-success .task-status-dot {
    background: var(--color-success);
    animation: none;
}

.task-context-card.is-error .task-status-dot {
    background: var(--color-danger);
    animation: none;
}

@keyframes task-dot-pulse {
    0%,
    100% {
        opacity: 1;
    }
    50% {
        opacity: 0.4;
    }
}

.task-status-badge {
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 800;
    color: var(--color-primary-700);
    background: var(--color-primary-100);
}

.task-status-badge.is-success {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.task-status-badge.is-error {
    color: var(--color-danger);
    background: var(--color-danger-soft);
}

.task-phase {
    color: var(--color-text-secondary);
}

.task-progress-bar {
    transition: width 240ms var(--motion-ease);
}

.task-step-dot {
    position: relative;
}

.task-step-row + .task-step-row {
    position: relative;
}

.task-step-row + .task-step-row::before {
    position: absolute;
    top: -7px;
    left: 7.5px;
    width: 1px;
    height: 8px;
    background: var(--color-border-default);
    content: "";
}
</style>
