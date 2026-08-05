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
}>();

const toggleScene = (scene: Scene, enabled: boolean) => {
    emit("toggle", scene, enabled);
};

const showAll = ref(false);

const toggleShowAll = () => {
    showAll.value = !showAll.value;
    emit("expand", showAll.value);
};

const visibleScenes = computed(() => {
    if (showAll.value) return props.scenes;
    return props.scenes.slice(0, 3);
});
</script>

<template>
    <section class="scene-grid-panel">
        <div v-if="loading" class="scene-empty">正在加载场景</div>
        <div v-else-if="!scenes.length" class="scene-empty">暂无匹配场景</div>
        <div v-else :class="['scene-grid', { 'scene-grid-expanded': showAll }]">
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
        <button v-if="scenes.length > 3" class="scene-view-all" type="button" @click="toggleShowAll">
            {{ showAll ? '收起场景' : `查看全部场景（${scenes.length}）` }}
            <span class="chevron-icon" :class="{ 'is-expanded': showAll }">
                <SvgIcon name="chevron-down" />
            </span>
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
    gap: 12px;
}

.scene-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.scene-grid-expanded {
    max-height: 380px;
    overflow-y: auto;
    scrollbar-gutter: stable;
}

.scene-grid-expanded::-webkit-scrollbar {
    width: 6px;
}

.scene-grid-expanded::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: var(--color-border);
}

.scene-grid-expanded::-webkit-scrollbar-track {
    background: transparent;
}

.scene-view-all {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: fit-content;
    margin: 0 auto;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    border: none;
    background: none;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background-color 150ms;
}

.scene-view-all:hover {
    background: var(--color-primary-50);
}

.chevron-icon {
    display: inline-flex;
    transition: transform 300ms ease;
}

.chevron-icon.is-expanded {
    transform: rotate(180deg);
}

.scene-empty {
    display: grid;
    min-height: 220px;
    place-items: center;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
    font-weight: 800;
}

@media (max-width: 1280px) {
    .scene-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 720px) {
    .scene-grid {
        grid-template-columns: 1fr;
    }

    .scene-grid-expanded {
        max-height: 320px;
    }
}
</style>
