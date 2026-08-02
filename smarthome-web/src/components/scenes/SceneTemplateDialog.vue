<script setup lang="ts">
import { computed, ref } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { sceneTemplates } from "../../mock/sceneTemplates";
import type { SceneTemplate } from "../../types/scene";

const model = defineModel<boolean>({ required: true });

const emit = defineEmits<{
    import: [template: SceneTemplate];
    preview: [template: SceneTemplate];
}>();

const selectedId = ref(sceneTemplates[0]?.id ?? "");
const keyword = ref("");
const activeCategory = ref("全部");
const categories = ["全部", "回家", "离家", "睡眠", "节能", "娱乐", "安防"];

const filteredTemplates = computed(() =>
    sceneTemplates.filter((template) => {
        const matchesKeyword = [template.name, template.description]
            .join(" ")
            .includes(keyword.value.trim());
        const matchesCategory =
            activeCategory.value === "全部" || template.category === activeCategory.value;

        return matchesKeyword && matchesCategory;
    }),
);
const selectedTemplate = computed(
    () =>
        sceneTemplates.find((template) => template.id === selectedId.value) ??
        sceneTemplates[0],
);

const selectTemplate = (template: SceneTemplate) => {
    selectedId.value = template.id;
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
        description="从推荐模板中快速创建场景"
        icon="layers"
        width="980px"
        confirm-text="导入并创建"
        cancel-text="取消"
        show-footer
        @confirm="importSelectedTemplate"
    >
        <div class="template-dialog">
            <section class="template-main">
                <div class="template-filters">
                    <label>
                        <SvgIcon name="search" />
                        <input v-model="keyword" placeholder="搜索模板名称或描述" type="search" />
                    </label>
                    <button
                        v-for="item in categories"
                        :key="item"
                        :class="{ active: activeCategory === item }"
                        type="button"
                        @click="activeCategory = item"
                    >
                        {{ item }}
                    </button>
                </div>

                <div class="template-feature-row">
                    <article>
                        <SvgIcon name="clock" />
                        <strong>最近使用</strong>
                        <span>3 个模板</span>
                    </article>
                    <article>
                        <SvgIcon name="light" />
                        <strong>编辑推荐</strong>
                        <span>官方精选模板</span>
                    </article>
                    <article>
                        <SvgIcon name="warning" />
                        <strong>热门模板</strong>
                        <span>大家都在用</span>
                    </article>
                    <article>
                        <SvgIcon name="energy" />
                        <strong>节能环保</strong>
                        <span>绿色生活</span>
                    </article>
                </div>

                <div class="template-grid">
                    <article
                        v-for="template in filteredTemplates"
                        :key="template.id"
                        :class="{ selected: selectedTemplate?.id === template.id }"
                        class="template-card"
                        role="button"
                        tabindex="0"
                        @click="selectTemplate(template)"
                        @keydown.enter="selectTemplate(template)"
                    >
                        <span :style="{ color: template.color }">
                            <SvgIcon :name="template.icon" />
                        </span>
                        <div>
                            <h3>{{ template.name }}</h3>
                            <p>{{ template.description }}</p>
                            <small>关联设备 {{ template.deviceCount }} 个</small>
                        </div>
                        <button type="button">
                            {{ selectedTemplate?.id === template.id ? "已选择" : "使用模板" }}
                        </button>
                    </article>
                </div>
            </section>

            <aside v-if="selectedTemplate" class="template-preview">
                <h3>模板预览</h3>
                <div class="preview-head">
                    <span :style="{ color: selectedTemplate.color }">
                        <SvgIcon :name="selectedTemplate.icon" />
                    </span>
                    <div>
                        <strong>{{ selectedTemplate.name }}</strong>
                        <p>{{ selectedTemplate.description }}</p>
                    </div>
                    <em>{{ selectedTemplate.triggerType === "manual" ? "手动" : "自动化" }}</em>
                </div>
                <dl>
                    <div><dt>适用房间</dt><dd>{{ selectedTemplate.roomLabels.join("、") }}</dd></div>
                    <div><dt>关联设备</dt><dd>{{ selectedTemplate.deviceCount }} 个</dd></div>
                    <div><dt>触发方式</dt><dd>{{ selectedTemplate.triggerLabel }}</dd></div>
                </dl>
                <h4>执行动作预览（共 {{ selectedTemplate.steps.length }} 步）</h4>
                <ol>
                    <li v-for="step in selectedTemplate.steps" :key="step.id">
                        <span>{{ step.order }}</span>
                        <div>
                            <strong>{{ step.name }}</strong>
                            <p>{{ step.description }}</p>
                        </div>
                    </li>
                </ol>
                <ul>
                    <li>场景信息（名称、描述、图标、标签等）</li>
                    <li>触发条件（{{ selectedTemplate.triggerLabel }}）</li>
                    <li>执行动作（{{ selectedTemplate.steps.length }} 步操作）</li>
                    <li>设备映射（根据您的设备自动匹配）</li>
                </ul>
            </aside>
        </div>
        <template #footerHint>
            模板会根据您的设备自动映射，导入后可以继续编辑。
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.template-dialog {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    gap: 16px;
}

.template-main,
.template-preview {
    min-width: 0;
}

.template-filters,
.template-feature-row,
.preview-head,
dl {
    display: flex;
    align-items: center;
}

.template-filters {
    gap: 8px;
    margin-bottom: 14px;
}

.template-filters label {
    display: flex;
    width: 220px;
    height: 36px;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-text-tertiary);
}

.template-filters input {
    min-width: 0;
    flex: 1;
    border: 0;
    background: transparent;
    outline: 0;
}

.template-filters button,
.template-card button {
    height: 32px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 12px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
}

.template-filters .active,
.template-card.selected button {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.template-feature-row {
    gap: 8px;
    margin-bottom: 14px;
}

.template-feature-row article {
    display: grid;
    min-width: 0;
    flex: 1;
    grid-template-columns: 34px minmax(0, 1fr);
    gap: 8px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 10px;
}

.template-feature-row svg {
    grid-row: span 2;
    color: var(--color-primary-600);
}

.template-feature-row strong,
.template-feature-row span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.template-feature-row strong {
    font-size: 12px;
    font-weight: 900;
}

.template-feature-row span {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.template-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.template-card {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
    min-height: 112px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 12px;
    cursor: pointer;
}

.template-card.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.template-card > span,
.preview-head > span {
    display: grid;
    width: 48px;
    height: 48px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
}

h3,
h4,
p,
dl,
ol,
ul {
    margin: 0;
}

.template-card h3,
.preview-head strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.template-card p,
.preview-head p {
    margin-top: 4px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.template-card small {
    display: block;
    margin-top: 12px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
}

.template-preview {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 14px;
}

.template-preview > h3 {
    margin-bottom: 14px;
    font-size: 14px;
    font-weight: 900;
}

.preview-head {
    gap: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
}

.preview-head div {
    min-width: 0;
    flex: 1;
}

.preview-head em {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 4px 8px;
    color: var(--color-success);
    font-size: 12px;
    font-style: normal;
    font-weight: 900;
}

dl {
    justify-content: space-between;
    gap: 8px;
    padding: 12px 0;
}

dt,
dd {
    margin: 0;
    font-size: 12px;
    font-weight: 800;
}

dt {
    color: var(--color-text-tertiary);
}

dd {
    color: var(--color-text-primary);
}

h4 {
    margin: 4px 0 10px;
    font-size: 13px;
    font-weight: 900;
}

ol,
ul {
    display: grid;
    gap: 8px;
    padding: 0;
    list-style: none;
}

ol li {
    display: flex;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 8px;
}

ol li > span {
    display: grid;
    width: 22px;
    height: 22px;
    flex: 0 0 22px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}

ol strong,
ol p {
    display: block;
    font-size: 12px;
}

ul {
    margin-top: 14px;
    color: var(--color-success);
    font-size: 12px;
    font-weight: 800;
}

ul li::before {
    content: "✓ ";
}

@media (max-width: 980px) {
    .template-dialog {
        grid-template-columns: 1fr;
    }
}
</style>
