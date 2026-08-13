<script setup lang="ts">
defineProps<{
    side: "left" | "right";
    timestamp?: string;
    regenerating?: boolean;
}>();
</script>

<template>
    <article
        class="message-shell mb-5 grid gap-3"
        :class="[
            side === 'left' ? 'ai-message-enter side-left' : 'user-message-enter side-right',
            { 'is-regenerating': regenerating },
        ]"
    >
        <!-- 头像列 -->
        <div class="avatar-col">
            <slot name="avatar" />
        </div>

        <!-- 内容列 -->
        <div class="content-col min-w-0">
            <slot />
            <!-- 操作栏 + 时间 -->
            <div
                v-if="timestamp || $slots.actions"
                class="meta-row"
            >
                <slot name="actions" />
                <time
                    v-if="timestamp"
                    class="message-time"
                >{{ timestamp }}</time>
            </div>
        </div>
    </article>
</template>

<style scoped>
/* 左侧（AI）：头像在左，内容在右，最大 720px */
.message-shell.side-left {
    grid-template-columns: 42px minmax(0, 720px);
}

/* 右侧（用户）：头像在右，内容在左，自适应宽度 */
.message-shell.side-right {
    grid-template-columns: minmax(0, max-content) 42px;
    max-width: 75%;
    margin-left: auto;
    justify-content: end;
}

.message-shell.side-right .avatar-col {
    order: 2;
}

.message-shell.side-right .content-col {
    order: 1;
}

/* 操作栏 */
.meta-row {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 6px;
}

.message-shell.side-right .meta-row {
    justify-content: flex-end;
}

/* 重新生成中的退场动画 */
.message-shell.is-regenerating {
    animation: message-regenerating 180ms var(--motion-ease-in) both;
    pointer-events: none;
}

@keyframes message-regenerating {
    from {
        opacity: 1;
        transform: scale(1);
    }
    to {
        opacity: 0;
        transform: scale(0.95) translateY(-4px);
    }
}

.message-time {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-muted);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
</style>