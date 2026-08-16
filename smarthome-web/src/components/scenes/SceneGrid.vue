<script setup lang="ts">
import { computed, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import SceneCard from "./SceneCard.vue";
import type { Scene } from "../../types/scene";

const props = defineProps<{
    scenes: Scene[];
    selectedId: string | null;
    runningSceneId: string | null;
    loading: boolean;
}>();

const emit = defineEmits<{
    select: [scene: Scene];
    toggle: [scene: Scene, enabled: boolean];
    run: [scene: Scene];
    edit: [scene: Scene];
    copy: [scene: Scene];
    remove: [scene: Scene];
    expand: [value: boolean];
    create: [];
    importTemplate: [];
}>();

const toggleScene = (scene: Scene, enabled: boolean) => {
    emit("toggle", scene, enabled);
};

const showAll = ref(false);
const sortBy = ref<"frequent" | "recent" | "name" | "custom">("frequent");
const sortMenuOpen = ref(false);

const toggleShowAll = () => {
    showAll.value = !showAll.value;
    emit("expand", showAll.value);
};

const sortedScenes = computed(() => {
    const list = [...props.scenes];
    switch (sortBy.value) {
        case "frequent":
            // 已启用优先，然后按默认顺序
            return list.sort((a, b) => {
                if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
                return (a.sortOrder ?? 999) - (b.sortOrder ?? 999);
            });
        case "recent":
            return list.sort(
                (a, b) =>
                    new Date(b.updatedAt).getTime() -
                    new Date(a.updatedAt).getTime(),
            );
        case "name":
            return list.sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
        case "custom":
            return list.sort(
                (a, b) => (a.sortOrder ?? 999) - (b.sortOrder ?? 999),
            );
        default:
            return list;
    }
});

const visibleScenes = computed(() => {
    if (showAll.value) return sortedScenes.value;
    return sortedScenes.value.slice(0, 3);
});

const sortOptions = [
    { value: "frequent" as const, label: "常用优先" },
    { value: "recent" as const, label: "最近执行" },
    { value: "name" as const, label: "名称" },
    { value: "custom" as const, label: "自定义" },
];

const selectSort = (value: "frequent" | "recent" | "name" | "custom") => {
    sortBy.value = value;
    sortMenuOpen.value = false;
};

const currentSortLabel = computed(
    () => sortOptions.find((o) => o.value === sortBy.value)?.label ?? "",
);
</script>

<template>
    <section class="scene-grid-panel">
        <!-- 头部：标题 + 排序 -->
        <div class="scene-grid-header">
            <span class="scene-grid-label">
                {{ showAll ? "全部场景" : "常用场景" }}
                <small v-if="!showAll && scenes.length > 3" class="scene-count">
                    · 最近 {{ Math.min(3, scenes.length) }} 个
                </small>
            </span>
            <div class="scene-grid-actions">
                <div class="sort-wrapper">
                    <button
                        class="sort-trigger"
                        type="button"
                        @click="sortMenuOpen = !sortMenuOpen"
                        @blur="sortMenuOpen = false"
                    >
                        <SvgIcon name="layers" size="sm" />
                        {{ currentSortLabel }}
                        <SvgIcon name="chevron-down" size="sm" :class="{ 'is-flipped': sortMenuOpen }" />
                    </button>
                    <Transition name="sort-menu">
                        <div
                            v-if="sortMenuOpen"
                            class="sort-dropdown"
                        >
                            <button
                                v-for="opt in sortOptions"
                                :key="opt.value"
                                type="button"
                                :class="{ 'is-active': sortBy === opt.value }"
                                @mousedown.prevent="selectSort(opt.value)"
                            >
                                {{ opt.label }}
                            </button>
                        </div>
                    </Transition>
                </div>
            </div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="scene-empty">
            <SvgIcon name="automation" />
            <p>正在加载场景</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!scenes.length" class="scene-empty">
            <SvgIcon name="device-management" />
            <p>暂无场景</p>
            <small>创建场景或从模板导入，快速开始智能联动</small>
            <div class="empty-actions">
                <button
                    class="empty-primary-btn"
                    type="button"
                    @click="$emit('create')"
                >
                    <SvgIcon name="plus" /> 创建第一个场景
                </button>
                <button
                    class="empty-secondary-btn"
                    type="button"
                    @click="$emit('importTemplate')"
                >
                    <SvgIcon name="layers" /> 从模板导入
                </button>
            </div>
        </div>

        <!-- 卡片列表 -->
        <div
            v-else
            :class="['scene-grid', { 'scene-grid-expanded': showAll }]"
        >
            <SceneCard
                v-for="(scene, index) in visibleScenes"
                :key="scene.id"
                :delay="index * 45"
                :running="runningSceneId === scene.id"
                :scene="scene"
                :selected="selectedId === scene.id"
                @copy="emit('copy', $event)"
                @edit="emit('edit', $event)"
                @remove="emit('remove', $event)"
                @run="emit('run', $event)"
                @select="emit('select', $event)"
                @toggle="toggleScene"
            />
        </div>

        <!-- 展开/收起切换 -->
        <button
            v-if="scenes.length > 3"
            class="scene-view-all"
            type="button"
            @click="toggleShowAll"
        >
            {{ showAll ? '收起场景' : `查看全部场景（${scenes.length}）` }}
            <SvgIcon name="chevron-right" size="sm" :class="{ 'is-flipped': showAll }" />
        </button>
    </section>
</template>

<style scoped>
.scene-grid-panel {
    position: relative;
    z-index: 1;
    display: flex;
    min-height: 0;
    flex-direction: column;
    gap: 6px;
}

/* === 头部 === */
.scene-grid-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.scene-grid-label {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.scene-count {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

.scene-grid-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* === 排序 === */
.sort-wrapper {
    position: relative;
}

.sort-trigger {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 32px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
    transition:
        border-color 140ms var(--motion-ease),
        color 140ms var(--motion-ease),
        background-color 140ms var(--motion-ease);
}

.sort-trigger:hover {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.sort-trigger .is-flipped {
    transform: rotate(180deg);
}

.sort-trigger svg {
    transition: transform 200ms var(--motion-ease);
}

.sort-dropdown {
    position: absolute;
    right: 0;
    top: calc(100% + 4px);
    z-index: 20;
    min-width: 130px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 4px;
    box-shadow: var(--shadow-card-hover);
}

.sort-dropdown button {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    padding: 8px 10px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    text-align: left;
    cursor: pointer;
    transition:
        background-color 140ms var(--motion-ease),
        color 140ms var(--motion-ease);
}

.sort-dropdown button:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.sort-dropdown button.is-active {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}

/* === 卡片网格 === */
.scene-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
}

.scene-grid-expanded {
    min-height: auto;
    overflow: visible;
}

/* === 展开/收起 === */
.scene-view-all {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: fit-content;
    margin: 0 auto;
    border: 0;
    background: none;
    padding: 6px 10px;
    border-radius: 6px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    transition: background-color 150ms, color 150ms;
}

.scene-view-all:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.scene-view-all .is-flipped {
    transform: rotate(90deg);
}

.scene-view-all svg {
    transition: transform 200ms var(--motion-ease);
}

/* === 空状态 === */
.scene-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 120px;
    border: 1px dashed var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
    font-weight: 800;
}

.scene-empty svg {
    width: 36px;
    height: 36px;
    opacity: 0.35;
}

.scene-empty p {
    margin: 0;
    font-size: 15px;
    font-weight: 900;
}

.scene-empty small {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    opacity: 0.75;
}

.empty-actions {
    display: flex;
    gap: 8px;
    margin-top: 4px;
}

.empty-primary-btn,
.empty-secondary-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 36px;
    border-radius: 8px;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    transition:
        transform 140ms var(--motion-ease),
        background-color 140ms var(--motion-ease),
        border-color 140ms var(--motion-ease);
}

.empty-primary-btn {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.empty-primary-btn:hover {
    transform: translateY(-1px);
}

.empty-secondary-btn {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.empty-secondary-btn:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: translateY(-1px);
}

/* === 排序菜单动画 === */
.sort-menu-enter-active,
.sort-menu-leave-active {
    transition:
        opacity 140ms var(--motion-ease),
        transform 140ms var(--motion-ease);
}

.sort-menu-enter-from,
.sort-menu-leave-to {
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
}

/* === 响应式 === */
@media (max-width: 1280px) {
    .scene-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 720px) {
    .scene-grid {
        grid-template-columns: 1fr;
    }
}
</style>