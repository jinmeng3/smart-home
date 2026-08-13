<script setup lang="ts">
defineProps<{
    label: string;
}>();
</script>

<template>
    <article class="inline-status ai-message-enter mb-5 grid grid-cols-[42px_minmax(0,320px)] gap-3">
        <div class="status-avatar grid h-10 w-10 place-items-center rounded-full">
            <img src="/orion-sidebar-icon.svg" alt="Orion Home" />
        </div>
        <div class="status-body flex min-h-10 items-center gap-2.5 rounded-xl border px-4 py-2.5 shadow-sm">
            <span class="status-pulse" aria-hidden="true"></span>
            <span class="min-w-0 truncate text-sm font-bold text-[var(--color-text-secondary)]">
                {{ label }}
            </span>
            <span class="status-dots ml-auto flex shrink-0 gap-1" aria-hidden="true">
                <i></i><i></i><i></i>
            </span>
        </div>
    </article>
</template>

<style scoped>
.status-avatar {
    border: 1px solid var(--color-primary-200);
    background: var(--color-card-bg);
    box-shadow: 0 5px 12px color-mix(in srgb, var(--color-primary-600) 15%, transparent);
}

.status-avatar img {
    width: 27px;
    height: 27px;
    object-fit: contain;
}

.status-body {
    border-color: var(--color-primary-200);
    background: color-mix(in srgb, var(--color-primary-50) 52%, var(--color-card-bg));
}

.status-pulse {
    width: 8px;
    height: 8px;
    flex: 0 0 8px;
    border-radius: 999px;
    background: var(--color-primary-500);
    box-shadow: 0 0 0 4px var(--color-focus-ring);
    animation: status-pulse 1400ms ease-in-out infinite;
}

.status-dots i {
    width: 5px;
    height: 5px;
    border-radius: 999px;
    background: var(--color-primary-400);
    animation: status-dot 900ms ease-in-out infinite;
}

.status-dots i:nth-child(2) {
    animation-delay: 120ms;
}

.status-dots i:nth-child(3) {
    animation-delay: 240ms;
}

@keyframes status-pulse {
    50% {
        opacity: 0.45;
        transform: scale(0.82);
    }
}

@keyframes status-dot {
    0%,
    60%,
    100% {
        opacity: 0.35;
        transform: translateY(0);
    }
    30% {
        opacity: 1;
        transform: translateY(-2px);
    }
}

@media (prefers-reduced-motion: reduce) {
    .status-pulse,
    .status-dots i {
        animation: none;
    }
}
</style>
