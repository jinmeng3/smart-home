<script setup lang="ts">
import { computed } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene } from "../../types/scene";
import { getHighRiskSteps } from "../../utils/sceneRiskPolicy";

const props = defineProps<{
    modelValue: boolean;
    scene: Scene | null;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    confirm: [];
    cancel: [];
}>();

const riskySteps = computed(() =>
    props.scene ? getHighRiskSteps(props.scene) : [],
);

const riskIcon = (deviceId: string) =>
    deviceId.toLowerCase().includes("lock") ? "lock" : "camera";

const onCancel = () => emit("update:modelValue", false);
const onConfirm = () => emit("confirm");
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :description="`${scene?.name ?? ''} 包含门锁或安防相关动作，确认执行？`"
        title="高风险动作确认"
        icon="lock"
        width="560px"
        confirm-text="确认执行"
        cancel-text="取消"
        @update:model-value="onCancel"
        @confirm="onConfirm"
    >
        <div class="risk-dialog">
            <!-- 场景概览 -->
            <div v-if="scene" class="risk-scene-head">
                <span
                    class="risk-scene-icon"
                    :style="{
                        background: scene.color + '20',
                        color: scene.color,
                    }"
                >
                    <SvgIcon :name="scene.icon" />
                </span>
                <div class="risk-scene-meta">
                    <strong>{{ scene.name }}</strong>
                    <small>高风险场景 · 需要二次确认</small>
                </div>
                <em class="risk-kicker"><SvgIcon name="lock" size="sm" /> 高风险</em>
            </div>

            <!-- 风险提示 -->
            <div class="risk-warning">
                <SvgIcon name="info" class="risk-warning-icon" />
                <p>
                    执行后将联动<b>门锁</b>或<b>安防监控</b>设备，可能影响家庭安全。
                    请确认你已了解相关影响后再执行。
                </p>
            </div>

            <!-- 敏感动作列表 -->
            <div v-if="riskySteps.length" class="risk-actions-block">
                <div class="risk-actions-title">
                    <h3>涉及的敏感动作（{{ riskySteps.length }}）</h3>
                    <span>以下步骤将改变家庭安全状态</span>
                </div>
                <ul class="risk-action-list">
                    <li v-for="step in riskySteps" :key="step.id">
                        <span class="risk-action-icon">
                            <SvgIcon :name="riskIcon(step.deviceId)" />
                        </span>
                        <div class="risk-action-info">
                            <strong>{{ step.name }}</strong>
                            <small>{{ step.description }}</small>
                        </div>
                    </li>
                </ul>
            </div>

            <p class="risk-note">
                <SvgIcon name="info" size="sm" />
                取消执行不会对设备产生任何影响。
            </p>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.risk-dialog {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 14px;
}

/* 场景概览 */
.risk-scene-head {
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 12px 14px;
}

.risk-scene-icon {
    display: grid;
    width: 42px;
    height: 42px;
    flex: none;
    place-items: center;
    border-radius: 11px;
}

.risk-scene-meta {
    display: flex;
    min-width: 0;
    flex: 1;
    flex-direction: column;
}

.risk-scene-meta strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.risk-scene-meta small {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.risk-kicker {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex: none;
    border-radius: 999px;
    background: var(--color-danger-soft);
    padding: 4px 10px;
    color: var(--color-danger);
    font-size: 11px;
    font-style: normal;
    font-weight: 800;
}

/* 风险提示 */
.risk-warning {
    display: flex;
    gap: 10px;
    border: 1px solid var(--color-warning-border);
    border-radius: 10px;
    background: var(--color-warning-soft);
    padding: 12px 14px;
}

.risk-warning-icon {
    flex: none;
    color: var(--color-warning);
    margin-top: 2px;
}

.risk-warning p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.6;
}

.risk-warning b {
    color: var(--color-warning);
    font-weight: 900;
}

/* 敏感动作 */
.risk-actions-block {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 12px 14px;
}

.risk-actions-title {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 10px;
}

.risk-actions-title h3 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.risk-actions-title span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.risk-action-list {
    margin: 0;
    padding: 0;
    list-style: none;
}

.risk-action-list li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 2px;
    border-top: 1px solid var(--color-border-subtle);
}

.risk-action-list li:first-child {
    border-top: 0;
}

.risk-action-icon {
    display: grid;
    width: 34px;
    height: 34px;
    flex: none;
    place-items: center;
    border-radius: 9px;
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.risk-action-info {
    display: flex;
    min-width: 0;
    flex: 1;
    flex-direction: column;
}

.risk-action-info strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.risk-action-info small {
    margin-top: 2px;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.risk-note {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
}
</style>