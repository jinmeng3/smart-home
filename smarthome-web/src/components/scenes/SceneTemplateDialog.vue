<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { fetchSceneTemplates } from "../../api/scenes";
import type { SceneTemplate } from "../../types/scene";
import { useLatestRequest } from "../../composables/useLatestRequest";

const model = defineModel<boolean>({ required: true });

const emit = defineEmits<{
    import: [template: SceneTemplate];
    preview: [template: SceneTemplate];
}>();

const sceneTemplates = ref<SceneTemplate[]>([]);
const selectedId = ref("");
const keyword = ref("");
const activeCategory = ref("全部");
const { loading, run } = useLatestRequest();
const loadError = ref("");

const categories = computed(() => {
    const found = Array.from(
        new Set(sceneTemplates.value.map((template) => template.category).filter(Boolean)),
    );
    return ["全部", ...found];
});

const categoryCounts = computed(() => {
    const counts: Record<string, number> = { "全部": sceneTemplates.value.length };
    for (const template of sceneTemplates.value) {
        counts[template.category] = (counts[template.category] ?? 0) + 1;
    }
    return counts;
});

const filteredTemplates = computed(() => {
    const normalizedKeyword = keyword.value.trim();

    return sceneTemplates.value.filter((template) => {
        const matchesKeyword =
            !normalizedKeyword ||
            [template.name, template.description]
                .join(" ")
                .includes(normalizedKeyword);
        const matchesCategory =
            activeCategory.value === "全部" ||
            template.category === activeCategory.value;

        return matchesKeyword && matchesCategory;
    });
});

const selectedTemplate = computed(
    () =>
        sceneTemplates.value.find(
            (template) => template.id === selectedId.value,
        ) ?? sceneTemplates.value[0],
);

const loadTemplates = async () => {
    loadError.value = "";
    await run(
        () => fetchSceneTemplates(keyword.value, activeCategory.value),
        (templates) => {
            sceneTemplates.value = templates;
            selectedId.value = templates[0]?.id ?? "";
        },
        (error) => {
            loadError.value =
                error instanceof Error ? error.message : "模板加载失败";
        },
    );
};

watch(model, (visible) => {
    if (visible) void loadTemplates();
});

const selectTemplate = (template: SceneTemplate) => {
    selectedId.value = template.id;
    emit("preview", template);
};

const importSelectedTemplate = () => {
    if (!selectedTemplate.value) return;
    emit("import", selectedTemplate.value);
    model.value = false;
};
</script>

<template>
    <BaseSmartModal
        v-model="model"
        title="导入模板"
        description="从推荐模板中快速创建场景，导入后可以继续编辑"
        icon="layers"
        width="1060px"
        confirm-text="导入并创建"
        cancel-text="取消"
        show-footer
        @confirm="importSelectedTemplate"
    >
        <div class="template-dialog">
            <section class="template-main">
                <!-- 搜索与分类过滤 -->
                <div class="template-filters">
                    <label class="search-bar">
                        <SvgIcon name="search" size="sm" />
                        <input
                            v-model="keyword"
                            placeholder="搜索模板名称或描述"
                            type="search"
                        />
                    </label>
                    <div class="category-filters">
                        <button
                            v-for="item in categories"
                            :key="item"
                            :class="{ active: activeCategory === item }"
                            type="button"
                            @click="activeCategory = item"
                        >
                            {{ item }}
                            <span v-if="categoryCounts[item]" class="category-count">{{ categoryCounts[item] }}</span>
                        </button>
                    </div>
                </div>

                <!-- 特征快捷入口 -->
                <div class="template-feature-row">
                    <article>
                        <span class="feature-icon is-purple">
                            <SvgIcon name="clock" size="sm" />
                        </span>
                        <div class="feature-body">
                            <strong>最近使用</strong>
                            <span>3 个模板</span>
                        </div>
                    </article>
                    <article>
                        <span class="feature-icon is-blue">
                            <SvgIcon name="light" size="sm" />
                        </span>
                        <div class="feature-body">
                            <strong>编辑推荐</strong>
                            <span>官方精选模板</span>
                        </div>
                    </article>
                    <article>
                        <span class="feature-icon is-orange">
                            <SvgIcon name="warning" size="sm" />
                        </span>
                        <div class="feature-body">
                            <strong>热门模板</strong>
                            <span>大家都在用</span>
                        </div>
                    </article>
                    <article>
                        <span class="feature-icon is-green">
                            <SvgIcon name="energy" size="sm" />
                        </span>
                        <div class="feature-body">
                            <strong>节能环保</strong>
                            <span>绿色生活</span>
                        </div>
                    </article>
                </div>

                <!-- 加载状态 -->
                <div v-if="loading" class="template-skeleton">
                    <div v-for="n in 4" :key="n" class="skeleton-card">
                        <span class="skeleton-icon" />
                        <div class="skeleton-body">
                            <span class="skeleton-line w-60" />
                            <span class="skeleton-line w-80" />
                            <span class="skeleton-line w-40" />
                        </div>
                    </div>
                </div>

                <!-- 错误状态 -->
                <p v-else-if="loadError" class="template-state is-error">
                    <SvgIcon name="warning" size="sm" />
                    {{ loadError }}
                </p>

                <!-- 空状态 -->
                <p v-else-if="filteredTemplates.length === 0" class="template-state">
                    <SvgIcon name="search" size="sm" />
                    {{ keyword ? "没有匹配的模板，试试其他关键词" : "暂无可用模板" }}
                </p>

                <!-- 模板网格 -->
                <div v-else class="template-grid">
                    <article
                        v-for="template in filteredTemplates"
                        :key="template.id"
                        :class="{
                            selected: selectedTemplate?.id === template.id,
                        }"
                        class="template-card"
                        role="button"
                        tabindex="0"
                        @click="selectTemplate(template)"
                        @keydown.enter="selectTemplate(template)"
                    >
                        <span class="template-card-icon" :style="{ color: template.color, background: template.color + '16' }">
                            <SvgIcon :name="template.icon" />
                        </span>
                        <div class="template-card-body">
                            <h3>{{ template.name }}</h3>
                            <p>{{ template.description }}</p>
                            <div class="template-card-meta">
                                <span class="meta-tag">
                                    <SvgIcon name="device-management" size="sm" />
                                    {{ template.deviceCount }} 个设备
                                </span>
                                <span class="meta-tag">
                                    <SvgIcon :name="template.triggerType === 'manual' ? 'automation' : 'calendar'" size="sm" />
                                    {{ template.triggerLabel }}
                                </span>
                            </div>
                        </div>
                        <button
                            type="button"
                            :class="{
                                'is-selected': selectedTemplate?.id === template.id,
                            }"
                            class="template-card-action"
                        >
                            {{
                                selectedTemplate?.id === template.id
                                    ? "已选择"
                                    : "使用模板"
                            }}
                        </button>
                    </article>
                </div>
            </section>

            <aside v-if="selectedTemplate" class="template-preview">
                <div class="preview-header">
                    <SvgIcon name="eye" size="sm" />
                    <span>模板预览</span>
                </div>
                <div class="preview-card">
                    <div class="preview-head">
                        <span class="preview-icon" :style="{ color: selectedTemplate.color, background: selectedTemplate.color + '16' }">
                            <SvgIcon :name="selectedTemplate.icon" />
                        </span>
                        <div class="preview-title">
                            <strong>{{ selectedTemplate.name }}</strong>
                            <p>{{ selectedTemplate.description }}</p>
                        </div>
                        <em
                            :class="selectedTemplate.triggerType === 'manual' ? 'is-manual' : 'is-auto'"
                        >
                            {{ selectedTemplate.triggerType === "manual" ? "手动" : "自动化" }}
                        </em>
                    </div>
                    <div class="preview-meta">
                        <div class="preview-meta-item">
                            <dt>
                                <SvgIcon name="room" size="sm" />
                                适用房间
                            </dt>
                            <dd>{{ selectedTemplate.roomLabels.join("、") || "通用" }}</dd>
                        </div>
                        <div class="preview-meta-item">
                            <dt>
                                <SvgIcon name="device-management" size="sm" />
                                关联设备
                            </dt>
                            <dd>{{ selectedTemplate.deviceCount }} 个</dd>
                        </div>
                        <div class="preview-meta-item">
                            <dt>
                                <SvgIcon name="calendar" size="sm" />
                                触发方式
                            </dt>
                            <dd>{{ selectedTemplate.triggerLabel }}</dd>
                        </div>
                    </div>
                    <div class="preview-steps">
                        <h4>执行动作（共 {{ selectedTemplate.steps.length }} 步）</h4>
                        <ol>
                            <li v-for="step in selectedTemplate.steps" :key="step.id">
                                <span class="step-num">{{ step.order }}</span>
                                <div class="step-body">
                                    <strong>{{ step.name }}</strong>
                                    <p>{{ step.description }}</p>
                                </div>
                            </li>
                        </ol>
                    </div>
                    <div class="preview-benefits">
                        <h4>导入后将包含</h4>
                        <ul>
                            <li>
                                <SvgIcon name="check" size="sm" />
                                场景信息（名称、描述、图标、标签等）
                            </li>
                            <li>
                                <SvgIcon name="check" size="sm" />
                                触发条件（{{ selectedTemplate.triggerLabel }}）
                            </li>
                            <li>
                                <SvgIcon name="check" size="sm" />
                                执行动作（{{ selectedTemplate.steps.length }} 步操作）
                            </li>
                            <li>
                                <SvgIcon name="check" size="sm" />
                                设备映射：根据您的设备自动匹配
                            </li>
                        </ul>
                    </div>
                </div>
            </aside>
        </div>
        <template #footerHint>
            模板会根据您的设备自动映射，导入后可以继续编辑和调整。
        </template>
    </BaseSmartModal>
</template>

<style scoped>
/* ── 布局 ── */
.template-dialog {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 340px;
    gap: 20px;
    align-items: start;
}

.template-main {
    display: grid;
    min-width: 0;
    gap: 14px;
}

.template-preview {
    position: sticky;
    top: 0;
    display: grid;
    min-width: 0;
    gap: 14px;
}

/* ── 搜索与分类 ── */
.template-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
}

.search-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    width: min(100%, 280px);
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-input-bg);
    padding: 0 12px;
    color: var(--color-text-tertiary);
    transition: border-color 200ms, box-shadow 200ms;
}

.search-bar:focus-within {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.search-bar input {
    min-width: 0;
    flex: 1;
    border: 0;
    background: transparent;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 700;
    outline: 0;
}

.search-bar input::placeholder {
    color: var(--color-text-tertiary);
}

.category-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.category-filters button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 12px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
    transition: all 160ms;
}

.category-filters button:hover {
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
}

.category-filters .active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.category-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 0 5px;
    font-size: 10px;
    font-weight: 800;
    color: var(--color-text-tertiary);
}

.category-filters .active .category-count {
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}

/* ── 特征快捷入口 ── */
.template-feature-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
}

.template-feature-row article {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    transition: border-color 180ms, box-shadow 180ms;
}

.template-feature-row article:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 2px 8px var(--color-shadow-sm);
}

.feature-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 10px;
}

.feature-icon.is-purple {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.feature-icon.is-blue {
    background: var(--color-info-soft);
    color: var(--color-info);
}

.feature-icon.is-orange {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.feature-icon.is-green {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.feature-body {
    min-width: 0;
}

.feature-body strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.feature-body span {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    margin-top: 1px;
}

/* ── 骨架屏 ── */
.template-skeleton {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.skeleton-card {
    display: flex;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.skeleton-icon {
    display: block;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    animation: skeleton-pulse 1.6s ease-in-out infinite;
}

.skeleton-body {
    display: grid;
    flex: 1;
    gap: 8px;
}

.skeleton-line {
    display: block;
    height: 12px;
    border-radius: 6px;
    background: var(--color-surface-subtle);
    animation: skeleton-pulse 1.6s ease-in-out infinite;
}

.skeleton-line.w-60 { width: 60%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-line.w-40 { width: 40%; }

@keyframes skeleton-pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

/* ── 状态提示 ── */
.template-state {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: 1px dashed var(--color-border);
    border-radius: 12px;
    padding: 40px 16px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 800;
}

.template-state.is-error {
    border-color: var(--color-danger-border);
    color: var(--color-danger);
    background: var(--color-danger-soft);
}

/* ── 模板网格 ── */
.template-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.template-card {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr);
    grid-template-rows: auto auto;
    gap: 10px;
    align-items: start;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    cursor: pointer;
    transition: border-color 180ms, box-shadow 180ms, transform 180ms;
}

.template-card:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 4px 12px var(--color-shadow-sm);
    transform: translateY(-1px);
}

.template-card.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.template-card-icon {
    display: grid;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    grid-row: span 2;
}

.template-card-body {
    min-width: 0;
}

.template-card-body h3 {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.template-card-body p {
    margin: 4px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.template-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
}

.meta-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 6px;
    background: var(--color-surface-subtle);
    padding: 3px 8px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
}

.template-card-action {
    grid-column: 2;
    justify-self: end;
    align-self: end;
    height: 30px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 14px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
    transition: all 160ms;
    white-space: nowrap;
}

.template-card-action:hover {
    border-color: var(--color-primary-400);
    color: var(--color-primary-600);
}

.template-card-action.is-selected {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

/* ── 预览面板 ── */
.preview-header {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
}

.preview-card {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    overflow: hidden;
}

.preview-head {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--color-border);
}

.preview-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
}

.preview-title {
    min-width: 0;
    flex: 1;
}

.preview-title strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.preview-title p {
    margin: 2px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.preview-head em {
    flex-shrink: 0;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
}

.preview-head .is-auto {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.preview-head .is-manual {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.preview-meta {
    display: grid;
    gap: 10px;
    padding: 14px 16px;
    border-bottom: 1px solid var(--color-border);
}

.preview-meta-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.preview-meta-item dt {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    margin: 0;
}

.preview-meta-item dd {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 12px;
    font-weight: 900;
}

.preview-steps {
    padding: 14px 16px;
    border-bottom: 1px solid var(--color-border);
}

.preview-steps h4 {
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.preview-steps ol {
    display: grid;
    gap: 6px;
    padding: 0;
    margin: 0;
    list-style: none;
}

.preview-steps li {
    display: flex;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    transition: background 150ms;
}

.preview-steps li:hover {
    background: var(--color-primary-50);
}

.step-num {
    display: grid;
    width: 22px;
    height: 22px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    font-size: 11px;
    font-weight: 900;
}

.step-body {
    min-width: 0;
    flex: 1;
}

.step-body strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.step-body p {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    margin: 1px 0 0;
}

.preview-benefits {
    padding: 14px 16px;
}

.preview-benefits h4 {
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.preview-benefits ul {
    display: grid;
    gap: 8px;
    padding: 0;
    margin: 0;
    list-style: none;
}

.preview-benefits li {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 800;
    color: var(--color-success);
}

.preview-benefits li svg {
    flex-shrink: 0;
}

/* ── 响应式 ── */
@media (max-width: 980px) {
    .template-dialog {
        grid-template-columns: 1fr;
    }

    .template-preview {
        position: static;
    }

    .template-feature-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 680px) {
    .template-feature-row,
    .template-grid {
        grid-template-columns: 1fr;
    }

    .template-filters {
        flex-direction: column;
        align-items: stretch;
    }

    .search-bar {
        width: 100%;
    }
}
</style>
