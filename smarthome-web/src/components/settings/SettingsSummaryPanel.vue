<script setup lang="ts">
import type { SettingsSummary } from "../../types/settings";
import { ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    summary: SettingsSummary;
    memberCount?: number;
}>();

const refreshing = ref(false);

const handleRefresh = () => {
    refreshing.value = true;
    // 触发外部刷新
    setTimeout(() => {
        refreshing.value = false;
    }, 800);
};
</script>

<template>
    <section
        class="summary-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 text-sm font-extrabold text-[var(--color-text-primary)]">
                <span class="grid h-7 w-7 place-items-center rounded-lg bg-[var(--color-ai-soft)] text-[var(--color-ai)]">
                    <SvgIcon name="account" size="sm" />
                </span>
                当前家庭
            </h2>
            <button
                class="summary-refresh"
                type="button"
                title="刷新同步时间"
                aria-label="刷新同步时间"
                :class="{ 'is-refreshing': refreshing }"
                @click="handleRefresh"
            >
                <SvgIcon name="refresh" size="sm" />
            </button>
        </div>

        <div class="summary-grid mt-3">
            <div class="summary-item">
                <span class="summary-label">家庭</span>
                <strong class="summary-value" :title="summary.currentHome">{{ summary.currentHome }}</strong>
            </div>
            <div class="summary-item">
                <span class="summary-label">成员</span>
                <strong class="summary-value">{{ memberCount ?? '-' }} 人</strong>
            </div>
            <div class="summary-item">
                <span class="summary-label">平台</span>
                <span class="summary-value">
                    <span class="inline-flex items-center gap-1">
                        <span
                            class="status-dot-inline"
                            :class="summary.homeAssistantStatus === 'online' ? 'is-online' : 'is-offline'"
                        ></span>
                        {{ summary.homeAssistantStatus === 'online' ? '在线' : '离线' }}
                    </span>
                </span>
            </div>
            <div class="summary-item">
                <span class="summary-label">同步</span>
                <span class="summary-value">{{ summary.lastSync }}</span>
            </div>
        </div>
    </section>
</template>

<style scoped>
.summary-card {
    box-shadow: var(--shadow-card);
}

.summary-refresh {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border-radius: 6px;
    color: var(--color-text-tertiary);
    opacity: 0;
    transition:
        opacity 150ms ease,
        background-color 150ms ease,
        color 150ms ease;
}

.summary-card:hover .summary-refresh {
    opacity: 1;
}

.summary-refresh:hover {
    background: var(--color-surface-hover);
    color: var(--color-primary-600);
}

.summary-refresh.is-refreshing svg {
    animation: spin 600ms linear infinite;
}

.summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 12px;
}

.summary-item {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
}

.summary-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-muted);
}

.summary-value {
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.status-dot-inline {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 999px;
}

.status-dot-inline.is-online {
    background: var(--color-success);
}

.status-dot-inline.is-offline {
    background: var(--color-text-muted);
}
</style>