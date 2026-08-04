<script setup lang="ts">
import { onMounted, watch } from "vue";
import { ElMessage } from "element-plus";
import { ApiError } from "../api/client";
import { storeToRefs } from "pinia";
import SceneCreateDialog from "../components/scenes/SceneCreateDialog.vue";
import SceneDetailPanel from "../components/scenes/SceneDetailPanel.vue";
import SceneFlow from "../components/scenes/SceneFlow.vue";
import SceneGrid from "../components/scenes/SceneGrid.vue";
import SceneStats from "../components/scenes/SceneStats.vue";
import SceneTemplateDialog from "../components/scenes/SceneTemplateDialog.vue";
import SceneToolbar from "../components/scenes/SceneToolbar.vue";
import { useSceneModeController } from "../composables/useSceneModeController";
import { useAuthStore } from "../stores/auth";
import { useScenesStore } from "../stores/scenes";

const store = useScenesStore();
const authStore = useAuthStore();
const {
    filters,
    loading,
    runningSceneId,
    scenes,
    selectedScene,
    selectedSceneId,
    stats,
    stepStatuses,
} = storeToRefs(store);
const controller = useSceneModeController(store);

const loadScenes = async () => {
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

    try {
        await store.loadScenes();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) return;
        ElMessage.error(
            error instanceof Error ? error.message : "场景数据加载失败",
        );
    }
};

watch(
    () => [
        filters.value.keyword,
        filters.value.triggerType,
        filters.value.enabled,
    ],
    () => {
        void loadScenes();
    },
);

watch(
    () => authStore.isAuthenticated,
    (authenticated) => {
        if (authenticated) void loadScenes();
    },
);

onMounted(() => {
    void loadScenes();
});
</script>

<template>
    <div class="contents">
        <section class="scene-mode-page page-shell page-enter">
            <header class="scene-page-header">
                <div class="scene-page-title">
                    <h1>场景模式</h1>
                    <p>一键管理家庭场景与智能联动</p>
                </div>
                <SceneToolbar
                    v-model:enabled="filters.enabled"
                    v-model:keyword="filters.keyword"
                    v-model:trigger-type="filters.triggerType"
                    @create="controller.openCreateDialog"
                    @import="controller.openTemplateDialog"
                />
            </header>

            <SceneStats
                :automation="stats.automation"
                :enabled="stats.enabled"
                :manual="stats.manual"
                :monthly-executions="stats.monthlyExecutions"
            />

            <SceneGrid
                :loading="loading"
                :running-scene-id="runningSceneId"
                :scenes="scenes"
                :selected-id="selectedSceneId"
                @copy="controller.copyScene"
                @edit="controller.editScene"
                @run="controller.runScene"
                @select="store.selectScene($event.id)"
                @toggle="controller.toggleScene"
            />

            <SceneFlow
                :running="runningSceneId === selectedScene?.id"
                :scene="selectedScene"
                :step-statuses="stepStatuses"
                @edit="selectedScene && controller.editScene(selectedScene)"
                @preview="selectedScene && controller.runScene(selectedScene)"
            />
        </section>

        <SceneDetailPanel
            :running="runningSceneId === selectedScene?.id"
            :scene="selectedScene"
            @action="controller.runAction"
            @copy="controller.copyScene"
            @edit="controller.editScene"
            @run="controller.runScene"
            @template="controller.openTemplateDialog"
        />

        <SceneCreateDialog
            v-model="controller.createDialogOpen.value"
            @create="controller.createScene"
            @draft="controller.saveDraft"
        />
        <SceneTemplateDialog
            v-model="controller.templateDialogOpen.value"
            @import="controller.importTemplate"
        />
    </div>
</template>

<style scoped>
.scene-mode-page {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 14px;
    overflow-y: auto;
    padding: 18px;
}

.scene-page-header {
    display: grid;
    grid-template-columns: minmax(210px, auto) minmax(0, 1fr);
    gap: 18px;
    align-items: start;
}

.scene-page-title h1 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 24px;
    font-weight: 900;
    line-height: 1.15;
}

.scene-page-title p {
    margin: 8px 0 0;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 750;
}

@media (max-width: 1180px) {
    .scene-page-header {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 720px) {
    .scene-mode-page {
        padding: 12px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .scene-mode-page {
        animation-duration: 1ms;
    }
}
</style>
