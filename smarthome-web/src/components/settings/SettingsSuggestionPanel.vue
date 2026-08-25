<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import type { SettingsSectionId } from "../../types/settings";
import type { SettingsSuggestionItem } from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";
import { useSettingsStore } from "../../stores/settings";

const props = defineProps<{
    suggestions: SettingsSuggestionItem[];
}>();

const emit = defineEmits<{
    select: [target: SettingsSuggestionItem["target"]];
}>();

const settingsStore = useSettingsStore();

const SHOW_DEFAULT = 3;
const expanded = ref(false);
const rootRef = ref<HTMLElement | null>(null);
let lastAiCount = 0;

/** 合并本地规则建议 + AI 补充建议，AI 项以 ai- 前缀 id 标识来源 */
const mergedSuggestions = computed<SettingsSuggestionItem[]>(() => {
    const local = props.suggestions;
    const ai = settingsStore.aiSuggestions;
    if (!ai || ai.length === 0) return local;
    const seen = new Set(local.map((item) => `${item.target}:${item.title}`));
    const aiUnique = ai.filter(
        (item) => !seen.has(`${item.target}:${item.title}`),
    );
    return [...local, ...aiUnique];
});

const visibleSuggestions = computed(() =>
    expanded.value
        ? mergedSuggestions.value
        : mergedSuggestions.value.slice(0, SHOW_DEFAULT),
);

const hasMore = computed(() => mergedSuggestions.value.length > SHOW_DEFAULT);
const completedCount = computed(
    () => props.suggestions.filter((s) => s.target === "account").length,
);

const isHighPriority = (item: SettingsSuggestionItem): boolean => {
    return item.target === "security" || item.target === "backup";
};

const priorityLabel = (item: SettingsSuggestionItem): string => {
    if (isHighPriority(item)) return "高优先级";
    return item.id.startsWith("settings-") || item.id.startsWith("ai-")
        ? "AI"
        : "建议";
};

const priorityClass = (item: SettingsSuggestionItem): string => {
    if (isHighPriority(item)) return "is-high";
    if (item.id.startsWith("settings-") || item.id.startsWith("ai-")) {
        return "is-ai";
    }
    return "is-normal";
};

const isAiSource = (item: SettingsSuggestionItem): boolean =>
    item.id.startsWith("settings-") || item.id.startsWith("ai-");

const aiLoading = computed(() => settingsStore.aiSuggestionsLoading);
const aiError = computed(() => settingsStore.aiSuggestionsError);
const hasAiLoaded = computed(() => settingsStore.aiSuggestions.length > 0);

const requestAiSuggestions = () => {
    void settingsStore.loadAiSuggestions(false);
};

// AI 建议从无→有时，滚动到 panel 顶部让新项可见。
// 仅在 count 实际增加且 panel 不在视口可见区域时触发，避免每次都干扰用户。
watch(
    () => settingsStore.aiSuggestions.length,
    (newCount) => {
        if (newCount <= lastAiCount) {
            lastAiCount = newCount;
            return;
        }
        lastAiCount = newCount;
        void nextTick(() => {
            const el = rootRef.value;
            if (!el) return;
            // scrollIntoView 在祖先是 overflow:auto 的元素中会作用于最近的滚动容器。
            // block:"nearest" 避免不必要的跳动；只在 panel 不可见时才滚。
            el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        });
    },
);
</script>

<template>
    <section
        ref="rootRef"
        class="suggestion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="flex items-center justify-between gap-2">
            <h2
                class="flex items-center gap-2 text-sm font-extrabold text-[var(--color-text-primary)]"
            >
                <span
                    class="grid h-7 w-7 place-items-center rounded-lg bg-[var(--color-warning-soft)] text-[var(--color-warning)]"
                >
                    <SvgIcon name="settings" size="sm" />
                </span>
                待处理建议
            </h2>
            <div class="flex items-center gap-2">
                <button
                    v-if="!hasAiLoaded && !aiLoading"
                    class="ai-trigger"
                    type="button"
                    title="调用 AI 补充建议"
                    @click="requestAiSuggestions"
                >
                    <SvgIcon name="sparkles" size="sm" />
                    AI 补充
                </button>
                <button
                    v-else-if="aiLoading"
                    class="ai-trigger is-loading"
                    type="button"
                    disabled
                >
                    <SvgIcon name="sparkles" size="sm" />
                    生成中
                </button>
                <button
                    v-else
                    class="ai-trigger"
                    type="button"
                    title="重新生成 AI 建议"
                    @click="requestAiSuggestions"
                >
                    <SvgIcon name="sparkles" size="sm" />
                    刷新 AI
                </button>
                <span
                    v-if="mergedSuggestions.length > 0"
                    class="text-xs font-extrabold text-[var(--color-warning)]"
                >
                    {{ mergedSuggestions.length }}
                </span>
                <SvgIcon
                    v-else
                    name="check-circle"
                    class="text-[var(--color-success)]"
                    size="sm"
                />
            </div>
        </div>

        <!-- AI 错误提示 -->
        <div v-if="aiError" class="mt-2 text-xs text-[var(--color-danger)]">
            AI 建议生成失败：{{ aiError }}
        </div>

        <!-- 无建议 -->
        <div
            v-if="mergedSuggestions.length === 0"
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
                        <SvgIcon
                            :name="isAiSource(item) ? 'sparkles' : 'circle'"
                            size="sm"
                        />
                    </span>
                    <span class="suggestion-body">
                        <span class="suggestion-title">{{ item.title }}</span>
                        <span class="suggestion-desc">{{
                            item.description
                        }}</span>
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
            {{
                expanded
                    ? "收起"
                    : "查看全部 (" + mergedSuggestions.length + ")"
            }}
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

.suggestion-priority.is-ai {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.ai-trigger {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    transition: background-color 150ms ease;
}

.ai-trigger:hover {
    background: var(--color-primary-100);
}

.ai-trigger.is-loading {
    color: var(--color-text-tertiary);
    background: var(--color-surface-subtle);
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
    transition:
        opacity 200ms ease,
        transform 200ms ease;
}
.suggestion-item-enter-from {
    opacity: 0;
    transform: translateY(-4px);
}
.suggestion-item-leave-active {
    transition:
        opacity 200ms ease,
        max-height 200ms ease;
}
.suggestion-item-leave-to {
    opacity: 0;
    max-height: 0;
}
</style>
