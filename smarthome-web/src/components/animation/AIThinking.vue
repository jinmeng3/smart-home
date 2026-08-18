<script setup lang="ts">
defineProps<{
    status: string;
}>();
</script>

<template>
    <article
        class="mb-5 grid grid-cols-[42px_minmax(0,460px)] gap-3 ai-message-enter"
    >
        <div class="thinking-icon relative grid h-10 w-10 place-items-center">
            <div class="thinking-ring"></div>
            <div
                class="thinking-avatar grid h-10 w-10 place-items-center overflow-hidden rounded-full border border-[var(--color-primary-200)] bg-[var(--color-card-bg)] shadow-md shadow-blue-500/20"
            >
                <img src="/orion-sidebar-icon.svg" alt="Orion Home" />
            </div>
        </div>
        <div
            class="thinking-card rounded-xl border border-[var(--color-ai-border)] bg-gradient-to-br from-[var(--color-card-bg)] to-[var(--color-ai-soft)] px-5 py-4 shadow-sm"
        >
            <div
                class="flex items-center gap-3 text-sm font-semibold text-[var(--color-text-secondary)]"
            >
                <span class="thinking-text">{{ status }}</span>
                <span class="thinking-dots flex gap-1">
                    <i></i>
                    <i></i>
                    <i></i>
                </span>
            </div>
            <div class="mt-3 h-1 w-full overflow-hidden rounded-full bg-[var(--color-ai-border)]">
                <div
                    class="thinking-progress h-full rounded-full bg-gradient-to-r from-[var(--color-ai)] to-[var(--color-primary-400)]"
                ></div>
            </div>
        </div>
    </article>
</template>

        <style scoped>
        .thinking-icon {
            animation: icon-pulse 2500ms ease-in-out infinite;
        }

        .thinking-avatar {
            box-shadow:
                0 6px 14px color-mix(in srgb, var(--color-primary-600) 18%, transparent),
                inset 0 0 0 3px var(--color-primary-50);
        }

        .thinking-avatar img {
            width: 28px;
            height: 28px;
            object-fit: contain;
            filter: saturate(1.12) contrast(1.08);
        }

        .thinking-ring {
            position: absolute;
            inset: -3px;
            border-radius: 999px;
            border: 2px solid var(--color-primary-300, #93c5fd);
            animation: ring-expand 2500ms ease-out infinite;
            opacity: 0;
        }

        .thinking-card {
            animation: card-glide 320ms ease-out both;
        }

        .thinking-text {
            animation: text-fade 300ms ease-out;
        }

        /* 不确定进度条：使用 xPercent 和 scaleX 替换 width/margin-left 布局动画 */
        .thinking-progress {
            animation: progress-indeterminate 2000ms ease-in-out infinite;
            transform-origin: left center;
        }

        @keyframes ring-expand {
            0% {
                transform: scale(0.85);
                opacity: 0.6;
            }
            60% {
                opacity: 0.2;
            }
            100% {
                transform: scale(1.35);
                opacity: 0;
            }
        }

        @keyframes card-glide {
            from {
                opacity: 0;
                transform: translateY(6px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes text-fade {
            from {
                opacity: 0;
                transform: translateY(-2px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* 使用 transform 替换 xPercent/scaleX（CSS 不支持 xPercent 属性） */
        @keyframes progress-indeterminate {
            0% {
                transform: translateX(0%) scaleX(0.08);
            }
            25% {
                transform: translateX(20%) scaleX(0.3);
            }
            50% {
                transform: translateX(60%) scaleX(0.18);
            }
            75% {
                transform: translateX(30%) scaleX(0.4);
            }
            100% {
                transform: translateX(92%) scaleX(0.08);
            }
        }
        </style>
