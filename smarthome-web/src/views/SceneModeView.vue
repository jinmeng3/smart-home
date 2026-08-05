<script setup lang="ts">
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { ApiError } from "../api/client";
import { storeToRefs } from "pinia";
import BaseSmartModal from "../components/common/BaseSmartModal.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import SceneCreateDialog from "../components/scenes/SceneCreateDialog.vue";
import SceneDetailPanel from "../components/scenes/SceneDetailPanel.vue";
import SceneFlow from "../components/scenes/SceneFlow.vue";
import SceneGrid from "../components/scenes/SceneGrid.vue";
import HighRiskConfirmDialog from "../components/scenes/HighRiskConfirmDialog.vue";
import SceneStats from "../components/scenes/SceneStats.vue";
import SceneTemplateDialog from "../components/scenes/SceneTemplateDialog.vue";
import SceneToolbar from "../components/scenes/SceneToolbar.vue";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
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

const sceneGridExpanded = ref(false);

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

useAuthenticatedLoader(() => void loadScenes());
</script>

<template>
    <div class="app-page-layout">
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
                v-if="!sceneGridExpanded"
                :automation="stats.automation"
                :enabled="stats.enabled"
                :manual="stats.manual"
                :monthly-executions="stats.monthlyExecutions"
            />

            <div class="scene-grid-wrapper" :class="{ 'is-expanded': sceneGridExpanded }">
                <SceneGrid
                    :loading="loading"
                    :running-scene-id="runningSceneId"
                    :scenes="scenes"
                    :selected-id="selectedSceneId"
                    @copy="controller.copyScene"
                    @edit="controller.editScene"
                    @expand="sceneGridExpanded = $event"
                    @remove="controller.removeScene"
                    @run="controller.runScene"
                    @select="store.selectScene($event.id)"
                    @toggle="controller.toggleScene"
                />
            </div>

            <div class="scene-flow-wrapper">
                <SceneFlow
                    :running="runningSceneId === selectedScene?.id"
                    :scene="selectedScene"
                    :step-statuses="stepStatuses"
                    @edit="selectedScene && controller.editScene(selectedScene)"
                    @preview="selectedScene && controller.runScene(selectedScene)"
                />
            </div>
        </section>

        <SceneDetailPanel
            :running="runningSceneId === selectedScene?.id"
            :scene="selectedScene"
            @action="controller.runAction"
            @copy="controller.copyScene"
            @edit="controller.editScene"
            @remove="controller.removeScene"
            @run="controller.runScene"
            @template="controller.openTemplateDialog"
        />

        <SceneCreateDialog
            v-model="controller.createDialogOpen.value"
            :scene="controller.editingScene.value"
            @create="controller.createScene"
            @update="controller.saveEditScene"
            @draft="controller.saveDraft"
        />
        <SceneTemplateDialog
            v-model="controller.templateDialogOpen.value"
            @import="controller.importTemplate"
        />

        <BaseSmartModal
            :closable="!controller.deleting.value"
            :loading="controller.deleting.value"
            :model-value="controller.deleteDialogOpen.value"
            width="520px"
            @update:model-value="
                $event
                    ? (controller.deleteDialogOpen.value = true)
                    : controller.cancelRemoveScene()
            "
        >
            <template #header>
                <header class="dialog-header">
                    <span class="dialog-icon" aria-hidden="true">
                        <SvgIcon name="warning" />
                    </span>
                    <div>
                        <h2>删除场景</h2>
                        <p>此操作将从场景列表中移除该场景。</p>
                    </div>
                    <button
                        class="close-button"
                        :disabled="controller.deleting.value"
                        type="button"
                        aria-label="关闭"
                        @click="controller.cancelRemoveScene"
                    >
                        <SvgIcon name="close" size="sm" />
                    </button>
                </header>
            </template>

            <section
                v-if="controller.deletingScene.value"
                class="scene-delete-dialog-body"
            >
                <div class="scene-delete-summary">
                    <span
                        class="scene-delete-thumb"
                        :style="{
                            '--scene-delete-color': controller.deletingScene.value.color,
                        }"
                        aria-hidden="true"
                    >
                        <SvgIcon :name="controller.deletingScene.value.icon" />
                    </span>
                    <div class="scene-delete-summary-info">
                        <strong>{{ controller.deletingScene.value.name }}</strong>
                        <p>
                            {{ controller.deletingScene.value.description }}
                        </p>
                    </div>
                </div>
                <p class="scene-delete-warning">
                    <SvgIcon name="warning" />
                    删除后将从场景列表中移除，关联的执行步骤与日志也会一并清除。
                </p>
            </section>

            <template #footer>
                <footer class="dialog-footer">
                    <span>此操作不可撤销</span>
                    <div>
                        <button
                            class="scene-delete-cancel-button"
                            :disabled="controller.deleting.value"
                            type="button"
                            @click="controller.cancelRemoveScene"
                        >
                            取消
                        </button>
                        <button
                            class="scene-delete-confirm-button"
                            :disabled="controller.deleting.value"
                            type="button"
                            @click="controller.confirmRemoveScene"
                        >
                            <SvgIcon
                                :name="
                                    controller.deleting.value
                                        ? 'refresh'
                                        : 'warning'
                                "
                                size="sm"
                            />
                            {{
                                controller.deleting.value
                                    ? "删除中"
                                    : "确认删除"
                            }}
                        </button>
                    </div>
                </footer>
            </template>
        </BaseSmartModal>

        <HighRiskConfirmDialog
            :model-value="controller.riskConfirmOpen.value"
            :scene="controller.riskScene.value"
            @confirm="controller.resolveRiskConfirm(true)"
            @update:model-value="controller.resolveRiskConfirm(false)"
        />
    </div>
</template>

<style scoped>
.scene-mode-page {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    gap: 14px;
    overflow: hidden;
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

.scene-grid-wrapper {
    flex: 0 0 auto;
    min-height: 0;
}

.scene-grid-wrapper.is-expanded {
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.scene-grid-wrapper.is-expanded:deep(.scene-grid-panel) {
    height: 100%;
}

.scene-flow-wrapper {
    flex: 0 0 auto;
    display: flex;
    flex-direction: column;
}

.scene-flow-wrapper:deep(.scene-flow) {
    flex: 0 0 auto;
    margin-top: 0;
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

/* ── 删除确认弹窗 ── */
/* 头部 / 底部复用 BaseSmartModal 通用 .dialog-header / .dialog-footer 样式 */

/* 头部图标保留轻微脉冲动效 */
.dialog-header .dialog-icon svg {
    animation: scene-delete-icon-pulse 1.6s ease-in-out infinite;
}

@keyframes scene-delete-icon-pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.06);
    }
}

.scene-delete-dialog-body {
    display: grid;
    gap: 14px;
}

.scene-delete-summary {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 18px;
    border: 1px solid var(--color-primary-200);
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    box-shadow: var(--shadow-card);
}

.scene-delete-thumb {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 50%;
    color: var(--color-text-on-primary);
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--scene-delete-color) 78%, #fff),
        var(--scene-delete-color)
    );
    box-shadow: 0 6px 16px
        color-mix(in srgb, var(--scene-delete-color) 28%, transparent);
}

.scene-delete-summary-info {
    min-width: 0;
    flex: 1;
}

.scene-delete-summary-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
}

.scene-delete-summary-info p {
    margin: 4px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-secondary);
    font-size: 13px;
}

.scene-delete-warning {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    margin: 0;
    border-radius: 12px;
    background: color-mix(
        in srgb,
        var(--color-danger-soft) 62%,
        transparent
    );
    padding: 12px 16px;
    color: var(--color-danger);
    font-size: 14px;
    font-weight: 700;
    line-height: 1.5;
}

.scene-delete-warning svg {
    flex: 0 0 auto;
    margin-top: 2px;
    opacity: 0.85;
}

.scene-delete-cancel-button,
.scene-delete-confirm-button {
    min-width: 96px;
    height: 38px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 140ms var(--motion-ease),
        box-shadow 140ms var(--motion-ease),
        border-color 140ms,
        background-color 140ms;
}

.scene-delete-cancel-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.scene-delete-confirm-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px solid var(--color-danger);
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--color-danger) 92%, #fff),
        var(--color-danger)
    );
    color: var(--color-text-on-primary);
    box-shadow: 0 4px 12px var(--color-danger-border);
}

.scene-delete-cancel-button:hover {
    border-color: var(--color-text-secondary);
    color: var(--color-text-primary);
}

.scene-delete-confirm-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px var(--color-danger-border);
}

.scene-delete-cancel-button:active,
.scene-delete-confirm-button:active {
    transform: translateY(0);
}

.scene-delete-cancel-button:focus-visible,
.scene-delete-confirm-button:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
}

.scene-delete-confirm-button:disabled svg {
    animation: scene-delete-spin 900ms linear infinite;
}

@keyframes scene-delete-spin {
    to {
        transform: rotate(360deg);
    }
}

@media (prefers-reduced-motion: reduce) {
    .dialog-header .dialog-icon svg,
    .scene-delete-confirm-button:disabled svg {
        animation: none;
    }

    .scene-delete-cancel-button,
    .scene-delete-confirm-button {
        transform: none;
    }
}
</style>
