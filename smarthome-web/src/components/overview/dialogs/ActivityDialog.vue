<script setup lang="ts">
import { computed, ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";

export interface ActivityItem {
    time: string;
    icon: string;
    title: string;
    description: string;
    tone: string;
}

const props = defineProps<{
    modelValue: boolean;
    activities: ActivityItem[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

type Category = "all" | "security" | "climate" | "lighting" | "other";

const selectedCategory = ref<Category>("all");
const searchQuery = ref("");

const categoryMap: { key: Category; label: string; icon: string }[] = [
    { key: "all", label: "全部", icon: "list" },
    { key: "security", label: "安全", icon: "security" },
    { key: "climate", label: "气候", icon: "temperature" },
    { key: "lighting", label: "灯光", icon: "light" },
    { key: "other", label: "其他", icon: "more" },
];

const categoryIcons = new Set(["lock", "camera", "security"]);
const categoryClimate = new Set(["air-conditioner", "temperature", "humidity", "air-quality", "sensor"]);
const categoryLighting = new Set(["light", "curtain"]);

const getCategory = (icon: string): Category => {
    if (categoryIcons.has(icon)) return "security";
    if (categoryClimate.has(icon)) return "climate";
    if (categoryLighting.has(icon)) return "lighting";
    return "other";
};

const filteredActivities = computed(() => {
    let items = props.activities;

    if (selectedCategory.value !== "all") {
        items = items.filter((a) => getCategory(a.icon) === selectedCategory.value);
    }

    const q = searchQuery.value.trim().toLocaleLowerCase();
    if (q) {
        items = items.filter(
            (a) =>
                a.title.toLocaleLowerCase().includes(q) ||
                a.description.toLocaleLowerCase().includes(q),
        );
    }

    return items;
});

const groupedActivities = computed(() => {
    const groups: { label: string; items: ActivityItem[] }[] = [];
    const morning: ActivityItem[] = [];
    const afternoon: ActivityItem[] = [];
    const evening: ActivityItem[] = [];

    for (const item of filteredActivities.value) {
        const hour = parseInt(item.time.split(":")[0] ?? "0", 10);
        if (hour < 12) morning.push(item);
        else if (hour < 18) afternoon.push(item);
        else evening.push(item);
    }

    if (morning.length) groups.push({ label: "上午", items: morning });
    if (afternoon.length) groups.push({ label: "下午", items: afternoon });
    if (evening.length) groups.push({ label: "晚上", items: evening });

    return groups;
});

const categoryCount = computed(() => {
    const total = props.activities.length;
    const security = props.activities.filter((a) => getCategory(a.icon) === "security").length;
    const climate = props.activities.filter((a) => getCategory(a.icon) === "climate").length;
    const lighting = props.activities.filter((a) => getCategory(a.icon) === "lighting").length;
    const other = total - security - climate - lighting;
    return { total, security, climate, lighting, other };
});

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="活动记录"
        description="查看今日全屋设备动态与事件记录"
        width="700px"
        closable
        :close-on-overlay="true"
        @update:model-value="close"
    >
        <div class="activity-layout">
            <!-- === Summary Bar === -->
            <header class="activity-summary">
                <div class="as-stat is-primary">
                    <span class="as-icon"><SvgIcon name="clock" size="sm" /></span>
                    <div class="as-body">
                        <b>{{ activities.length }}</b>
                        <small>今日记录</small>
                    </div>
                </div>
                <div class="as-stat">
                    <span class="as-icon is-security"><SvgIcon name="security" size="sm" /></span>
                    <div class="as-body">
                        <b>{{ categoryCount.security }}</b>
                        <small>安全</small>
                    </div>
                </div>
                <div class="as-stat">
                    <span class="as-icon is-climate"><SvgIcon name="temperature" size="sm" /></span>
                    <div class="as-body">
                        <b>{{ categoryCount.climate }}</b>
                        <small>气候</small>
                    </div>
                </div>
                <div class="as-stat">
                    <span class="as-icon is-lighting"><SvgIcon name="light" size="sm" /></span>
                    <div class="as-body">
                        <b>{{ categoryCount.lighting }}</b>
                        <small>灯光</small>
                    </div>
                </div>
                <div class="as-stat">
                    <span class="as-icon is-other"><SvgIcon name="more" size="sm" /></span>
                    <div class="as-body">
                        <b>{{ categoryCount.other }}</b>
                        <small>其他</small>
                    </div>
                </div>
            </header>

            <!-- === Toolbar: Category Tabs + Search === -->
            <div class="activity-toolbar">
                <nav class="category-tabs">
                    <button
                        v-for="cat in categoryMap"
                        :key="cat.key"
                        type="button"
                        :class="['cat-tab', { active: selectedCategory === cat.key }]"
                        @click="selectedCategory = cat.key"
                    >
                        <SvgIcon :name="cat.icon" size="sm" />
                        {{ cat.label }}
                    </button>
                </nav>
                <label class="activity-search">
                    <SvgIcon name="search" size="sm" />
                    <input
                        v-model="searchQuery"
                        type="text"
                        placeholder="搜索…"
                        maxlength="30"
                    />
                </label>
            </div>

            <!-- === Timeline === -->
            <div v-if="groupedActivities.length" class="timeline">
                <template v-for="(group, gi) in groupedActivities" :key="gi">
                    <div class="tl-group-header">
                        <span class="tl-group-label">{{ group.label }}</span>
                        <span class="tl-group-count">{{ group.items.length }} 条</span>
                    </div>
                    <article
                        v-for="(item, ii) in group.items"
                        :key="gi + '-' + ii"
                        class="tl-item"
                        :style="{ '--i': ii }"
                    >
                        <time class="tl-time">{{ item.time }}</time>
                        <span class="tl-node" :class="item.tone" />
                        <div class="tl-card">
                            <i :class="item.tone">
                                <SvgIcon :name="item.icon" size="sm" />
                            </i>
                            <div class="tl-content">
                                <div class="tl-title-row">
                                    <b>{{ item.title }}</b>
                                    <span class="tl-tag" :class="item.tone">{{ getCategory(item.icon) === "security" ? "安全" : getCategory(item.icon) === "climate" ? "气候" : getCategory(item.icon) === "lighting" ? "灯光" : "其他" }}</span>
                                </div>
                                <small>{{ item.description }}</small>
                            </div>
                        </div>
                    </article>
                </template>
            </div>

            <!-- === Empty State === -->
            <div v-else class="activity-empty">
                <SvgIcon name="search" size="lg" />
                <p>未找到匹配的活动记录</p>
                <button
                    v-if="searchQuery || selectedCategory !== 'all'"
                    type="button"
                    class="reset-btn"
                    @click="searchQuery = ''; selectedCategory = 'all'"
                >
                    清除筛选条件
                </button>
            </div>
        </div>

        <template #footer></template>
    </BaseSmartModal>
</template>

<style scoped>
.activity-layout {
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 2px 0;
    max-height: 540px;
    overflow-y: auto;
}

/* === Summary Bar === */
.activity-summary {
    display: flex;
    gap: 0;
    padding: 14px 16px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-surface-subtle) 0%,
        var(--color-card-bg) 100%
    );
}

.as-stat {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 8px;
    justify-content: center;
}

.as-stat + .as-stat {
    border-left: 1px solid var(--color-border);
    padding-left: 8px;
}

.as-icon {
    display: grid;
    width: 34px;
    height: 34px;
    flex: none;
    place-items: center;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    transition: transform 200ms var(--motion-ease);
}

.as-stat:hover .as-icon {
    transform: scale(1.08);
}

.as-icon.is-primary {
    background: linear-gradient(135deg, #e9f2ff, #d6e5ff);
    color: #2871f5;
}

.as-icon.is-security {
    background: linear-gradient(135deg, #eee9ff, #e0d8ff);
    color: #7651ee;
}

.as-icon.is-climate {
    background: linear-gradient(135deg, #e7f9ee, #d0f3de);
    color: #20b86a;
}

.as-icon.is-lighting {
    background: linear-gradient(135deg, #fff3e0, #ffe8c8);
    color: #f07821;
}

.as-icon.is-other {
    background: linear-gradient(135deg, #e0f7f5, #c8f0ed);
    color: #0d9488;
}

.as-body {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
}

.as-body b {
    font-size: 17px;
    font-weight: 900;
    line-height: 1.1;
    color: var(--color-text-primary);
}

.as-body small {
    font-size: 10px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    white-space: nowrap;
}

/* === Toolbar === */
.activity-toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
}

.category-tabs {
    display: flex;
    gap: 4px;
    flex: 1;
    min-width: 0;
}

.cat-tab {
    display: flex;
    align-items: center;
    gap: 5px;
    height: 32px;
    padding: 0 10px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    font-size: 11px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    cursor: pointer;
    transition:
        border-color 160ms var(--motion-ease),
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
    white-space: nowrap;
}

.cat-tab:hover {
    border-color: var(--color-border-default);
    color: var(--color-text-secondary);
}

.cat-tab.active {
    border-color: var(--color-primary-400, #3478f6);
    background: var(--color-primary-50, #eef4ff);
    color: var(--color-primary-600, #2563eb);
}

.cat-tab :deep(.orion-icon) {
    opacity: 0.6;
}

.cat-tab.active :deep(.orion-icon) {
    opacity: 1;
}

.activity-search {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 140px;
    flex: none;
    height: 32px;
    padding: 0 10px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    transition: border-color 160ms var(--motion-ease);
}

.activity-search:focus-within {
    border-color: var(--color-primary-400, #3478f6);
}

.activity-search :deep(.orion-icon) {
    flex: none;
    opacity: 0.35;
}

.activity-search input {
    flex: 1;
    min-width: 0;
    border: 0;
    background: transparent;
    padding: 0;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-primary);
    outline: none;
}

.activity-search input::placeholder {
    color: var(--color-text-tertiary);
    font-weight: 500;
}

/* === Timeline === */
.timeline {
    display: flex;
    flex-direction: column;
    gap: 2px;
    position: relative;
    padding-left: 72px;
}

/* Vertical line */
.timeline::before {
    content: "";
    position: absolute;
    left: 96px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--color-border-subtle);
    border-radius: 2px;
}

/* === Group Header === */
.tl-group-header {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 4px 0 2px -72px;
    padding: 4px 0 4px 72px;
    background: var(--color-card-bg);
}

.tl-group-header:first-child {
    margin-top: 0;
}

.tl-group-label {
    font-size: 12px;
    font-weight: 900;
    color: var(--color-text-primary);
    letter-spacing: 0.3px;
}

.tl-group-count {
    font-size: 10px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    padding: 1px 8px;
    border-radius: 10px;
    background: var(--color-surface-subtle);
}

/* === Timeline Item === */
.tl-item {
    display: flex;
    align-items: stretch;
    gap: 14px;
    animation: tl-enter 320ms var(--motion-ease) both;
    animation-delay: calc(var(--i, 0) * 50ms);
}

@keyframes tl-enter {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.tl-time {
    width: 40px;
    flex: none;
    padding-top: 14px;
    font-size: 11px;
    font-weight: 900;
    color: var(--color-text-tertiary);
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.tl-node {
    position: relative;
    z-index: 1;
    width: 12px;
    flex: none;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.tl-node::after {
    content: "";
    display: block;
    width: 10px;
    height: 10px;
    margin-top: 15px;
    border-radius: 50%;
    border: 2px solid var(--color-border-subtle);
    background: var(--color-card-bg);
    transition:
        border-color 200ms var(--motion-ease),
        transform 200ms var(--motion-ease),
        box-shadow 200ms var(--motion-ease);
}

.tl-item:hover .tl-node::after {
    transform: scale(1.3);
}

.tl-node.blue::after {
    border-color: #2871f5;
    background: #e9f2ff;
    box-shadow: 0 0 0 3px rgba(40, 113, 245, 0.12);
}

.tl-node.green::after {
    border-color: #20b86a;
    background: #e7f9ee;
    box-shadow: 0 0 0 3px rgba(32, 184, 106, 0.12);
}

.tl-node.orange::after {
    border-color: #f07821;
    background: #fff3e0;
    box-shadow: 0 0 0 3px rgba(240, 120, 33, 0.12);
}

.tl-node.purple::after {
    border-color: #7651ee;
    background: #eee9ff;
    box-shadow: 0 0 0 3px rgba(118, 81, 238, 0.12);
}

.tl-node.teal::after {
    border-color: #0d9488;
    background: #e0f7f5;
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.12);
}

/* === Card === */
.tl-card {
    display: flex;
    flex: 1;
    gap: 12px;
    min-width: 0;
    margin: 6px 0;
    padding: 12px 14px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
    cursor: default;
    transition:
        border-color 200ms var(--motion-ease),
        box-shadow 200ms var(--motion-ease),
        transform 200ms var(--motion-ease);
}

.tl-item:hover .tl-card {
    border-color: var(--color-border-default);
    box-shadow:
        0 2px 8px rgba(0, 0, 0, 0.04),
        0 1px 2px rgba(0, 0, 0, 0.03);
    transform: translateX(2px);
}

.tl-card i {
    display: grid;
    width: 34px;
    height: 34px;
    flex: none;
    place-items: center;
    border-radius: 10px;
    transition: transform 200ms var(--motion-ease);
}

.tl-item:hover .tl-card i {
    transform: scale(1.06);
}

.tl-card i.blue {
    background: linear-gradient(135deg, #e9f2ff, #d6e5ff);
    color: #2871f5;
}

.tl-card i.green {
    background: linear-gradient(135deg, #e7f9ee, #d0f3de);
    color: #20b86a;
}

.tl-card i.orange {
    background: linear-gradient(135deg, #fff3e0, #ffe8c8);
    color: #f07821;
}

.tl-card i.purple {
    background: linear-gradient(135deg, #eee9ff, #e0d8ff);
    color: #7651ee;
}

.tl-card i.teal {
    background: linear-gradient(135deg, #e0f7f5, #c8f0ed);
    color: #0d9488;
}

.tl-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.tl-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.tl-content b {
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.tl-tag {
    font-size: 9px;
    font-weight: 800;
    padding: 1px 7px;
    border-radius: 6px;
    white-space: nowrap;
    letter-spacing: 0.3px;
}

.tl-tag.blue {
    background: #e9f2ff;
    color: #2871f5;
}

.tl-tag.green {
    background: #e7f9ee;
    color: #20b86a;
}

.tl-tag.orange {
    background: #fff3e0;
    color: #f07821;
}

.tl-tag.purple {
    background: #eee9ff;
    color: #7651ee;
}

.tl-tag.teal {
    background: #e0f7f5;
    color: #0d9488;
}

.tl-content small {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-text-tertiary);
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* === Empty State === */
.activity-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 48px 0;
    color: var(--color-text-tertiary);
}

.activity-empty :deep(.orion-icon) {
    opacity: 0.3;
}

.activity-empty p {
    font-size: 13px;
    font-weight: 700;
}

.reset-btn {
    padding: 6px 16px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    font-size: 12px;
    font-weight: 800;
    color: var(--color-primary-600, #2563eb);
    cursor: pointer;
    transition:
        border-color 160ms var(--motion-ease),
        background 160ms var(--motion-ease);
}

.reset-btn:hover {
    border-color: var(--color-primary-400, #3478f6);
    background: var(--color-primary-50, #eef4ff);
}

/* === Scrollbar === */
.activity-layout::-webkit-scrollbar {
    width: 4px;
}

.activity-layout::-webkit-scrollbar-track {
    background: transparent;
}

.activity-layout::-webkit-scrollbar-thumb {
    border-radius: 4px;
    background: var(--color-border-subtle);
}

/* === Responsive === */
@media (max-width: 560px) {
    .activity-summary {
        flex-wrap: wrap;
        gap: 6px;
        padding: 12px;
    }

    .as-stat {
        flex: 1 1 30%;
        justify-content: flex-start;
    }

    .as-stat + .as-stat {
        border-left: none;
        padding-left: 0;
    }

    .activity-toolbar {
        flex-direction: column;
        align-items: stretch;
    }

    .activity-search {
        width: auto;
    }

    .timeline {
        padding-left: 56px;
    }

    .timeline::before {
        left: 78px;
    }

    .tl-group-header {
        margin-left: -56px;
        padding-left: 56px;
    }

    .tl-time {
        width: 32px;
        font-size: 10px;
    }
}
</style>