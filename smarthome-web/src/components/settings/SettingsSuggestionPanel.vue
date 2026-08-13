<script setup lang="ts">
import { ref, computed } from "vue";
import type { SettingsSectionId } from "../../types/settings";
import type { SettingsSuggestionItem } from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    suggestions: SettingsSuggestionItem[];
}>();

const emit = defineEmits<{
    select: [target: SettingsSuggestionItem["target"]];
}>();

const SHOW_DEFAULT = 3;
const expanded = ref(false);

const visibleSuggestions = computed(() =>
    expanded.value ? props.suggestions : props.suggestions.slice(0, SHOW_DEFAULT),
);

const hasMore = computed(() => props.suggestions.length > SHOW_DEFAULT);
const completedCount = computed(
    () => props.suggestions.filter((s) => s.target === "account").length,
);

const isHighPriority = (item: SettingsSuggestionItem): boolean => {
    return item.target === "security" || item.target === "backup";
};

const priorityLabel = (item: SettingsSuggestionItem): string => {
    if (isHighPriority(item)) return "高优先级";
    return "建议";
};

const priorityClass = (item: SettingsSuggestionItem): string => {
    if (isHighPriority(item)) return "is-high";
    return "is-normal";
};
</script>

<template>
    <section
        class="suggestion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 text-sm font-extrabold text-[var(--color-text-primary)]">
                <span class="grid h-7 w-7 place-items-center rounded-lg bg-[var(--color-warning-soft)] text-[var(--color-warning)]">
                    <SvgIcon name="settings" size="sm" />
                </span>
                待处理建议
            </h2>
            <span
                v-if="suggestions.length > 0"
                class="text-xs font-extrabold text-[var(--color-warning)]"
            >
                {{ suggestions.length }}
            </span>
            <SvgIcon
                v-else
                name="check-circle"
                class="text-[var(--color-success)]"
                size="sm"
            />
        </div>

        <!-- 无建议 -->
        <div
            v-if="suggestions.length === 0"
            class="mt-3 flex items-center gap-2 text-xs font-bold text-[var(--color-success)]"
        >
            <SvgIcon name="check-circle" size="sm" />
            所有设置已完善
        </div>

        <!-- 建议列表 -->
        <div v-else class="mt-3 grid gap-1">
            <TransitionGroup name="suggestion-item">
                <button
                    v-for="item in visibleSuggestions"
                    :key="item.id"
                    class="suggestion-row"
                    type="button"
                    @click="emit('select', item.target)"
                >
                    <span class="suggestion-check">
                        <SvgIcon name="circle" size="sm" />
                    </span>
                    <span class="suggestion-body">
                        <span class="suggestion-title">{{ item.title }}</span>
                        <span class="suggestion-desc">{{ item.description }}</span>
                    </span>
                    <span
                        class="suggestion-priority"
                        :class="priorityClass(item)"
                    >
                        {{ priorityLabel(item) }}
                    </span>
                </button>
            </TransitionGroup>
        </div>

        <!-- 展开按钮 -->
        <button
            v-if="hasMore"
            class="suggestion-expand"
            type="button"
            @click="expanded = !expanded"
        >
            {{ expanded ? "收起" : "查看全部 (" + suggestions.length + ")" }}
            <SvgIcon
                name="chevron-down"
                size="sm"
                :class="{ 'is-open': expanded }"
            />
        </button>
    </section>
</template>

<style scoped>
.suggestion-card {
    box-shadow: var(--shadow-card);
}

.suggestion-row {
    display: flex;
    width: 100%;
    align-items: flex-start;
    gap: 8px;
    border-radius: 8px;
    padding: 8px;
    text-align: left;
    transition: background-color 150ms ease;
}

.suggestion-row:hover {
    background: var(--color-surface-hover);
}

.suggestion-check {
    flex: 0 0 16px;
    margin-top: 2px;
    color: var(--color-text-muted);
}

.suggestion-body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
}

.suggestion-title {
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.suggestion-desc {
    font-size: 11px;
    color: var(--color-text-tertiary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.suggestion-priority {
    flex-shrink: 0;
    margin-top: 1px;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    white-space: nowrap;
}

.suggestion-priority.is-high {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.suggestion-priority.is-normal {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.suggestion-expand {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-top: 6px;
    padding: 6px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-primary-600);
    transition: background-color 150ms ease;
}

.suggestion-expand:hover {
    background: var(--color-primary-50);
}

.suggestion-expand svg {
    transition: transform 200ms ease;
}

.suggestion-expand svg.is-open {
    transform: rotate(180deg);
}

.suggestion-item-enter-active {
    transition: opacity 200ms ease, transform 200ms ease;
}
.suggestion-item-enter-from {
    opacity: 0;
    transform: translateY(-4px);
}
.suggestion-item-leave-active {
    transition: opacity 200ms ease, max-height 200ms ease;
}
.suggestion-item-leave-to {
    opacity: 0;
    max-height: 0;
}
</style>