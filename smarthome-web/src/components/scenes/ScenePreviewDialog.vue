<script setup lang="ts">
import { computed } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { ScenePreview } from "../../types/scene";

const props = defineProps<{
    modelValue: boolean;
    loading: boolean;
    preview: ScenePreview | null;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    run: [];
}>();

const steps = computed(() => props.preview?.steps ?? []);
const highRiskCount = computed(
    () => steps.value.filter((step) => step.riskLevel === "high").length,
);
const totalEstimatedMs = computed(() =>
    steps.value.reduce((total, step) => total + step.estimatedMs, 0),
);

const formatMs = (ms: number) =>
    ms >= 1000 ? `${(ms / 1000).toFixed(1)} 秒` : `${ms} 毫秒`;

const onClose = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :description="`${preview?.triggerLabel ?? ''} · 预览不实际控制设备`"
        :loading="loading"
        :model-value="modelValue"
        cancel-text="关闭"
        confirm-text="执行此场景"
        icon="eye"
        title="场景动作预览"
        width="620px"
        @confirm="$emit('run')"
        @update:model-value="onClose"
    >
        <div class="preview-dialog">
            <template v-if="loading">
                <div class="preview-loading">
                    <SvgIcon name="refresh" size="sm" />
                    正在生成动作链预览…
                </div>
            </template>

            <template v-else-if="preview">
                <div class="preview-risk">
                    <SvgIcon :name="preview.highRisk ? 'warning' : 'check-circle'" />
                    <span v-if="preview.highRisk">
                        该场景包含 <b>{{ highRiskCount }}</b> 个高风险动作，执行前需要二次确认
                    </span>
                    <span v-else>该场景动作均安全，可放心执行</span>
                </div>

                <ol class="preview-step-list">
                    <li
                        v-for="(step, index) in steps"
                        :key="step.stepId"
                        class="preview-step"
                        :class="`is-${step.riskLevel}`"
                    >
                        <span class="preview-step-index">{{ index + 1 }}</span>
                        <div class="preview-step-body">
                            <strong>{{ step.name }}</strong>
                            <small>{{ step.deviceId }}</small>
                        </div>
                        <div class="preview-step-meta">
                            <em :class="`is-${step.riskLevel}`">
                                {{ step.riskLevel === "high" ? "高风险" : "低风险" }}
                            </em>
                            <span>{{ formatMs(step.estimatedMs) }}</span>
                        </div>
                    </li>
                </ol>

                <footer class="preview-footer">
                    <SvgIcon name="clock" size="sm" />
                    预计共 {{ steps.length }} 步 · 预估耗时
                    <b>{{ formatMs(totalEstimatedMs) }}</b>
                </footer>
            </template>

            <p v-else class="preview-empty">暂无预览数据</p>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.preview-dialog {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 14px;
}

.preview-loading {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 120px;
    place-content: center;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.preview-loading svg {
    animation: spin 900ms linear infinite;
    color: var(--color-primary-600);
}

.preview-risk {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    border: 1px solid var(--color-success-border);
    border-radius: 10px;
    background: var(--color-success-soft);
    padding: 11px 14px;
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.5;
}

.preview-risk svg {
    flex: none;
    margin-top: 2px;
    color: var(--color-success);
}

.preview-risk b {
    color: var(--color-success);
    font-weight: 900;
}

.preview-dialog .preview-risk:has(> svg[name="warning"]) {
    border-color: var(--color-warning-border);
    background: var(--color-warning-soft);
}
.preview-dialog .preview-risk:has(> svg[name="warning"]) svg,
.preview-dialog .preview-risk:has(> svg[name="warning"]) b {
    color: var(--color-warning);
}

.preview-step-list {
    margin: 0;
    padding: 0;
    list-style: none;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    overflow: hidden;
}

.preview-step {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    border-top: 1px solid var(--color-border-subtle);
}

.preview-step:first-child {
    border-top: 0;
}

.preview-step-index {
    display: grid;
    width: 26px;
    height: 26px;
    flex: none;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
}

.preview-step.is-high .preview-step-index {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.preview-step-body {
    display: flex;
    min-width: 0;
    flex: 1;
    flex-direction: column;
}

.preview-step-body strong {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
}

.preview-step-body small {
    margin-top: 2px;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-step-meta {
    display: flex;
    flex: none;
    align-items: center;
    gap: 10px;
}

.preview-step-meta em {
    border-radius: 999px;
    padding: 3px 9px;
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
}

.preview-step-meta em.is-low {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.preview-step-meta em.is-high {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.preview-step-meta span {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}

.preview-footer {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.preview-footer svg {
    color: var(--color-info);
}

.preview-footer b {
    color: var(--color-text-primary);
    font-weight: 900;
}

.preview-empty {
    margin: 0;
    color: var(--color-text-tertiary);
    padding: 24px 0;
    text-align: center;
    font-weight: 800;
animation: spin 900ms linear infinite;
}
</style>