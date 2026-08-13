<script setup lang="ts">
import type { AgentExecutionStep } from "../../types/chat";

defineProps<{
    steps: AgentExecutionStep[];
}>();
</script>

<template>
    <TransitionGroup
        tag="article"
        name="step-list"
        class="mb-5 grid grid-cols-[42px_minmax(0,460px)] gap-3 ai-message-enter"
        v-if="steps.length > 0"
    >
        <div
            class="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white shadow-md shadow-blue-500/10"
            key="icon"
        >
            <svg viewBox="0 0 24 24" class="h-5 w-5 fill-none stroke-white" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
                <path d="M12 2v4M12 18v4M4 12H2M22 12h-2M6.3 6.3l-1.4-1.4M19.1 19.1l-1.4-1.4M17.7 6.3l1.4-1.4M4.9 19.1l1.4-1.4" />
            </svg>
        </div>
        <div
            class="step-card rounded-xl border border-[var(--color-ai-border)] bg-gradient-to-br from-[var(--color-card-bg)] to-[var(--color-ai-soft)] px-5 py-4 shadow-sm"
            key="card"
        >
            <h3 class="mb-3 text-sm font-bold text-[var(--color-text-primary)]">
                正在执行智能控制
            </h3>
            <div class="grid gap-2.5">
                <TransitionGroup name="step-item" tag="div" class="grid gap-2.5">
                    <div
                        v-for="step in steps"
                        :key="step.id"
                        class="step-row grid grid-cols-[22px_minmax(0,1fr)] items-center gap-2.5 text-sm"
                    >
                        <span
                            class="step-dot grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold transition-all duration-300"
                            :class="{
                                'bg-[var(--color-primary-600)] text-white shadow-sm':
                                    step.status === 'executing',
                                'bg-[var(--color-success)] text-white shadow-sm':
                                    step.status === 'completed',
                                'bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)]':
                                    step.status === 'pending',
                                'bg-[var(--color-danger-soft)] text-[var(--color-danger)]':
                                    step.status === 'failed',
                            }"
                        >
                            <svg
                                v-if="step.status === 'completed'"
                                viewBox="0 0 24 24"
                                class="h-3 w-3 fill-none stroke-white"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="3"
                            >
                                <path d="M5 13l4 4L19 7" />
                            </svg>
                            <svg
                                v-else-if="step.status === 'failed'"
                                viewBox="0 0 24 24"
                                class="h-3 w-3 fill-none stroke-[var(--color-danger)]"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="3"
                            >
                                <path d="M18 6L6 18M6 6l12 12" />
                            </svg>
                        </span>
                        <div class="flex min-w-0 flex-col gap-0.5">
                            <span
                                class="truncate font-medium"
                                :class="step.status === 'failed' ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-secondary)]'"
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
    </TransitionGroup>
</template>

<style scoped>
.step-card {
    transition:
        transform 200ms var(--motion-ease),
        box-shadow 200ms var(--motion-ease);
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

.step-list-enter-active,
.step-list-leave-active {
    transition: opacity 200ms ease;
}
.step-list-enter-from,
.step-list-leave-to {
    opacity: 0;
}

.step-item-enter-active {
    transition: opacity 300ms var(--motion-ease), transform 300ms var(--motion-ease);
}
.step-item-enter-from {
    opacity: 0;
    transform: translateY(6px);
}
.step-item-leave-active {
    transition: opacity 200ms ease, transform 200ms ease;
}
.step-item-leave-to {
    opacity: 0;
    transform: translateX(-8px);
}
.step-item-move {
    transition: transform 300ms ease;
}
</style>