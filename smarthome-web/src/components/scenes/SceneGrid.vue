<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import SceneCard from "./SceneCard.vue";
import type { Scene } from "../../types/scene";

defineProps<{
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
}>();

const toggleScene = (scene: Scene, enabled: boolean) => {
    emit("toggle", scene, enabled);
};
</script>

<template>
    <section class="scene-grid-panel">
        <div v-if="loading" class="scene-empty">正在加载场景</div>
        <div v-else-if="!scenes.length" class="scene-empty">暂无匹配场景</div>
        <div v-else class="scene-grid">
            <SceneCard
                v-for="(scene, index) in scenes"
                :key="scene.id"
                :delay="index * 45"
                :running="runningSceneId === scene.id"
                :scene="scene"
                :selected="selectedId === scene.id"
                @copy="emit('copy', $event)"
                @edit="emit('edit', $event)"
                @run="emit('run', $event)"
                @select="emit('select', $event)"
                @toggle="toggleScene"
            />
        </div>
        <button v-if="scenes.length" class="scene-view-all" type="button">
            查看全部场景（12）<SvgIcon name="chevron-down" />
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
    margin-bottom: 12px;
}

.scene-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
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
}
</style>
