<script setup lang="ts">
import { computed, watch, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { AgentExecutionStep } from "../../types/chat";

const props = defineProps<{
    status: string;
    steps: AgentExecutionStep[];
    phase: "pending" | "working" | "done";
}>();

// 步骤状态统计
const completedCount = computed(
    () =>
        props.steps.filter(
            (s) => s.status === "completed" || s.status === "failed",
        ).length,
);
const allFinished = computed(() => {
    if (props.steps.length === 0) return false;
    return completedCount.value === props.steps.length;
});

// 阶段文案：同一卡片内渐变切换，避免切换跳动
const label = computed(() => {
    if (props.phase === "pending") return props.status || "正在理解";
    if (props.phase === "done") {
        return props.steps.length > 0
            ? `已完成 ${props.steps.length} 个操作`
            : "回复完成";
    }
    if (allFinished.value) return "正在整理结果";
    return "正在调用设备";
});

// 折叠控制：完成后收起步骤列表
const collapsed = ref(false);
watch(
    () => props.phase,
    (phase) => {
        if (phase === "done") {
            // 等"正在整理结果"文案展示一小段时间后折叠
            window.setTimeout(() => {
                collapsed.value = true;
            }, 420);
        } else {
            collapsed.value = false;
        }
    },
);
</script>

<template>
    <article
        class="agent-status-panel mb-5 grid grid-cols-[42px_minmax(0,460px)] gap-3 ai-message-enter"
        :class="{ 'is-done': phase === 'done' }"
    >
        <div
            class="status-icon grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white shadow-md shadow-blue-500/10"
        >
            <!-- 完成：对勾；进行中：脉冲思考灯泡（动态 name 连续 Morph） -->
            <div :class="{ 'status-icon-pulse': phase !== 'done' }">
                <SvgIcon :name="phase === 'done' ? 'check' : 'light'" />
            </div>
        </div>

        <div
            class="status-card rounded-xl border border-[var(--color-ai-border)] bg-gradient-to-br from-[var(--color-card-bg)] to-[var(--color-ai-soft)] shadow-sm"
            :class="{ 'is-done': phase === 'done' }"
        >
            <!-- 状态行 -->
            <div class="flex items-center gap-2.5">
                <span class="status-label">{{ label }}</span>
                <span v-if="phase !== 'done'" class="thinking-dots flex gap-1">
                    <i></i><i></i><i></i>
                </span>
            </div>

            <!-- 折叠区域：步骤列表 + 进度条 -->
            <div
                class="status-collapse"
                :class="{ 'is-collapsed': collapsed }"
            >
                <div class="status-collapse-inner">
                    <!-- 进度条（等待 / 执行中） -->
                    <div
                        v-if="phase !== 'done' && steps.length > 0"
                        class="mt-3 h-1 w-full overflow-hidden rounded-full bg-[var(--color-ai-border)]"
                    >
                        <div
                            class="thinking-progress h-full rounded-full bg-gradient-to-r from-[var(--color-ai)] to-[var(--color-primary-400)]"
                        ></div>
                    </div>

                    <!-- 步骤列表 -->
                    <div v-if="steps.length > 0" class="step-list-wrap">
                        <TransitionGroup
                            name="step-item"
                            tag="div"
                            class="grid gap-2.5"
                        >
                            <div
                                v-for="step in steps"
                                :key="step.id"
                                class="step-row grid grid-cols-[22px_minmax(0,1fr)] items-center gap-2.5 text-sm"
                            >
                                <span
                                    class="step-dot grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold"
                                    :class="{
                                        'bg-[var(--color-primary-600)] text-white':
                                            step.status === 'executing',
                                        'bg-[var(--color-success)] text-white':
                                            step.status === 'completed',
                                        'bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)]':
                                            step.status === 'pending',
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
                                <div class="flex min-w-0 flex-col gap-0.5">
                                    <span
                                        class="truncate font-medium"
                                        :class="
                                            step.status === 'failed'
                                                ? 'text-[var(--color-danger)]'
                                                : 'text-[var(--color-text-secondary)]'
                                        "
                                    >
                                        {{ step.label }}
                                    </span>
                                    <span
                                        v-if="step.status === 'failed' && step.message"
                                        class="truncate text-xs text-[var(--color-danger)]"
                                    >
                                        {{ step.message }}
                                    </span>
                                </div>
                            </div>
                        </TransitionGroup>
                    </div>
                </div>
            </div>
        </div>
    </article>
</template>

<style scoped>
/* 卡片内部过渡保持一致节奏 */
.status-card {
    transition:
        padding 200ms ease,
        box-shadow 200ms ease;
    padding: 14px 16px;
}

.status-card.is-done {
    padding: 12px 16px;
    box-shadow: none;
}

.status-label {
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
    animation: status-label-swap 200ms ease;
}

/* 折叠区域：grid-template-rows 0fr→1fr 做高度渐变 */
.status-collapse {
    display: grid;
    grid-template-rows: 1fr;
    transition: grid-template-rows 240ms var(--motion-ease);
}

.status-collapse.is-collapsed {
    grid-template-rows: 0fr;
}

.status-collapse-inner {
    overflow: hidden;
    min-height: 0;
}

.step-list-wrap {
    margin-top: 10px;
}

.step-row {
    animation: step-in 300ms var(--motion-ease) both;
}

@keyframes step-in {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes status-label-swap {
    from {
        opacity: 0;
        transform: translateY(-3px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.status-icon-pulse {
    animation: icon-pulse 2500ms ease-in-out infinite;
}

@keyframes icon-pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.08);
    }
}

.step-item-enter-active {
    transition:
        opacity 300ms var(--motion-ease),
        transform 300ms var(--motion-ease);
}
.step-item-enter-from {
    opacity: 0;
    transform: translateY(6px);
}
.step-item-leave-active {
    transition:
        opacity 200ms ease,
        transform 200ms ease;
}
.step-item-leave-to {
    opacity: 0;
    transform: translateX(-8px);
}
.step-item-move {
    transition: transform 300ms ease;
}
</style>