<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElInputNumber, ElMessage, ElSlider } from "element-plus";
import type { AiAssistantSettings } from "../../types/settings";
import { useSettingsStore } from "../../stores/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import BaseButton from "../common/BaseButton.vue";
import BaseSwitch from "../BaseSwitch.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import ModalSection from "../common/ModalSection.vue";
import SvgIcon from "../common/SvgIcon.vue";
import "element-plus/theme-chalk/el-input-number.css";
import "element-plus/theme-chalk/el-message.css";
import "element-plus/theme-chalk/el-slider.css";

interface ModelSettings {
    language: string;
    detailLevel: number;
    temperature: number;
    maxTokens: number;
}

const props = defineProps<{
    ai: AiAssistantSettings;
}>();

const settingsStore = useSettingsStore();
const dialogVisible = ref(false);
const saving = ref(false);
const draft = reactive<ModelSettings>({
    language: "zh-CN",
    detailLevel: 70,
    temperature: 0.7,
    maxTokens: 4096,
});

const languageOptions: Array<{
    label: string;
    value: string;
}> = [
    { label: "简体中文", value: "zh-CN" },
    { label: "English", value: "en-US" },
    { label: "自动检测", value: "auto" },
];
const tokenPresets = [2048, 4096, 8192];

const copyCurrentSettings = () => {
    Object.assign(draft, {
        language: props.ai.language,
        detailLevel: props.ai.detailLevel,
        temperature: props.ai.temperature,
        maxTokens: props.ai.maxTokens,
    });
};

const openDialog = () => {
    copyCurrentSettings();
    dialogVisible.value = true;
};

const requestClose = async () => {
    if (saving.value) {
        return;
    }

    dialogVisible.value = false;
};

const validateDraft = () => {
    if (draft.temperature < 0 || draft.temperature > 2) {
        ElMessage.warning("创造性必须在 0 到 2 之间");
        return false;
    }

    if (
        !Number.isInteger(draft.maxTokens) ||
        draft.maxTokens < 1 ||
        draft.maxTokens > 32768
    ) {
        ElMessage.warning("回复长度上限必须是 1 到 32768 之间的整数");
        return false;
    }

    return true;
};

const applySettings = async () => {
    if (!validateDraft()) {
        return;
    }

    const previousSettings: ModelSettings = {
        language: props.ai.language,
        detailLevel: props.ai.detailLevel,
        temperature: props.ai.temperature,
        maxTokens: props.ai.maxTokens,
    };

    Object.assign(props.ai, draft);
    saving.value = true;

    try {
        await settingsStore.saveAIModel();
        dialogVisible.value = false;
        ElMessage.success("模型高级设置已保存");
    } catch (error) {
        Object.assign(props.ai, previousSettings);
        ElMessage.error(
            error instanceof Error ? error.message : "模型高级设置保存失败",
        );
    } finally {
        saving.value = false;
    }
};
</script>

<template>
    <SettingsSectionCard id="ai" icon="ai" title="智能助手" tone="indigo">
        <label class="settings-field">
            <span>模型选择</span>
            <select
                v-model="ai.model"
                class="settings-input"
                @change="settingsStore.selectAIModel(ai.model)"
            >
                <option
                    v-for="model in settingsStore.aiModels"
                    :key="model.id"
                    :value="model.name"
                >
                    {{ model.name }} · {{ model.provider }}
                </option>
                <option v-if="!settingsStore.aiModels.length" :value="ai.model">
                    {{ ai.model || "暂无可用模型" }}
                </option>
            </select>
        </label>
        <div class="settings-field">
            <span>低风险操作自动执行</span
            ><BaseSwitch v-model="ai.autoExecuteLowRisk" />
        </div>
        <div class="settings-field">
            <span>高风险操作二次确认</span
            ><BaseSwitch v-model="ai.confirmHighRisk" />
        </div>
        <div class="settings-field">
            <span>模型高级参数</span>
            <BaseButton plain variant="primary" @click="openDialog"
                >更多设置</BaseButton
            >
        </div>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        :loading="saving"
        close-on-overlay
        confirm-text="应用设置"
        description="调整回复的创造性和长度上限。"
        icon="ai"
        tone="indigo"
        title="模型高级设置"
        width="medium"
        @cancel="requestClose"
        @confirm="applySettings"
    >
        <template #status>
            <div class="model-status">
                <span>当前模型</span>
                <strong>{{ ai.model || "Orion GPT-4o" }}</strong>
                <span class="active-status">
                    <SvgIcon name="check-circle" size="sm" />
                    配置生效中
                </span>
            </div>
        </template>

        <div class="advanced-settings-grid">
            <ModalSection>
                <div class="setting-title">
                    <div>
                        <strong>回复语言</strong><span>Response language</span>
                    </div>
                </div>
                <p class="setting-copy">设置助手默认使用的回复语言。</p>
                <select
                    v-model="draft.language"
                    class="settings-input full-width"
                >
                    <option
                        v-for="option in languageOptions"
                        :key="option.value"
                        :value="option.value"
                    >
                        {{ option.label }}
                    </option>
                </select>
            </ModalSection>

            <ModalSection>
                <div class="setting-title">
                    <div>
                        <strong>回复详细程度</strong><span>Detail level</span>
                    </div>
                    <output>{{ draft.detailLevel }}%</output>
                </div>
                <p class="setting-copy">数值越高，回复会包含更多背景和步骤。</p>
                <ElSlider
                    v-model="draft.detailLevel"
                    :max="100"
                    :min="0"
                    :show-tooltip="false"
                />
                <div class="range-labels">
                    <span>简洁</span><span>均衡</span><span>详细</span>
                </div>
            </ModalSection>

            <ModalSection>
                <div class="setting-title">
                    <div><strong>创造性</strong><span>Temperature</span></div>
                    <output>{{ draft.temperature.toFixed(1) }}</output>
                </div>
                <p class="setting-copy">数值越低越稳定，越高则更有创造性。</p>
                <ElSlider
                    v-model="draft.temperature"
                    :max="2"
                    :min="0"
                    :show-tooltip="false"
                    :step="0.1"
                />
                <div class="range-labels">
                    <span>精确 0</span><span>均衡 1</span><span>创意 2</span>
                </div>
            </ModalSection>

            <ModalSection>
                <div class="setting-title">
                    <div>
                        <strong>回复长度上限</strong><span>Max tokens</span>
                    </div>
                    <output class="token-current">当前 {{ draft.maxTokens.toLocaleString() }}</output>
                </div>
                <p class="setting-copy">
                    控制单次回复最多可生成的 token 数量。
                </p>
                <div class="token-input-row">
                    <span class="token-input-icon"><SvgIcon name="message" size="sm" /></span>
                    <ElInputNumber
                        v-model="draft.maxTokens"
                        :max="32768"
                        :min="1"
                        :step="256"
                        class="max-token-input"
                        controls-position="right"
                    />
                    <span class="token-unit">tokens</span>
                </div>
                <div class="token-presets">
                    <button
                        v-for="value in tokenPresets"
                        :key="value"
                        :class="{ active: draft.maxTokens === value }"
                        type="button"
                        @click="draft.maxTokens = value"
                    >
                        <span>{{ value.toLocaleString() }}</span>
                        <small>{{ value === 2048 ? "精简" : value === 4096 ? "推荐" : "长回复" }}</small>
                        <SvgIcon v-if="draft.maxTokens === value" name="check-circle" size="sm" />
                    </button>
                </div>
            </ModalSection>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <p>设置将在保存页面更改后应用到新的对话</p>
                <div>
                    <BaseButton :disabled="saving" @click="requestClose"
                        >取消</BaseButton
                    >
                    <BaseButton
                        :loading="saving"
                        variant="primary"
                        @click="applySettings"
                        >应用设置</BaseButton
                    >
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.advanced-settings-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
}

.advanced-settings-grid :deep(.smart-modal-section) {
    display: flex;
    min-height: 214px;
    flex-direction: column;
    border-color: var(--color-border);
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.model-status {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    color: var(--color-text-tertiary);
    font-size: 14px;
    background: var(--color-surface-subtle);
}

.model-status span,
.model-status strong {
    display: block;
}

.model-status strong {
    min-width: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 14px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.active-status {
    display: flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    padding: 5px 10px;
    color: var(--color-success);
    font-size: 12px;
    font-weight: 700;
    background: var(--color-success-soft);
}

.setting-title {
    display: flex;
    justify-content: space-between;
    gap: 10px;
}

.setting-title strong,
.setting-title span {
    display: block;
}

.setting-title strong {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
}

.setting-title span {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.setting-title output {
    min-width: 64px;
    color: var(--color-primary-600);
    font-size: 20px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    text-align: right;
    white-space: nowrap;
}

.setting-title .token-current {
    min-width: auto;
    align-self: flex-start;
    border: 1px solid var(--color-primary-200);
    border-radius: 999px;
    background: var(--color-primary-50);
    padding: 5px 10px;
    font-size: 13px;
}

.setting-copy {
    min-height: 38px;
    margin: 7px 0 9px;
    color: var(--color-text-tertiary);
    font-size: 14px;
    line-height: 1.5;
}

.full-width {
    width: 100%;
    margin-top: auto;
}

:deep(.el-input-number.full-width) {
    display: block;
    min-height: 44px;
    flex-shrink: 0;
}

:deep(.el-input-number.full-width .el-input__inner) {
    padding-right: 58px;
    padding-left: 14px;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
    text-align: left;
}

:deep(.max-token-input .el-input),
:deep(.max-token-input .el-input__wrapper) {
    width: 100%;
    min-height: 42px;
}

.token-input-row {
    display: grid;
    grid-template-columns: 34px minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    margin-top: auto;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-surface-subtle);
    padding: 5px 10px 5px 7px;
    transition: border-color 160ms, box-shadow 160ms;
}
.token-input-row:focus-within {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}
.token-input-icon {
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.token-unit {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}
:deep(.token-input-row .el-input__wrapper) {
    background: transparent;
    box-shadow: none !important;
}
:deep(.token-input-row .el-input__inner) {
    padding-left: 4px;
    font-size: 16px;
    font-weight: 800;
}

:deep(.smart-modal-section .el-slider) {
    height: 32px;
    margin-top: auto;
}

:deep(.smart-modal-section .el-slider__runway) {
    height: 6px;
    background: var(--color-border-default);
}

:deep(.smart-modal-section .el-slider__bar) {
    height: 6px;
    border-radius: 999px;
    background: var(--color-primary-600);
}

:deep(.smart-modal-section .el-slider__button-wrapper) {
    top: -15px;
    width: 36px;
    height: 36px;
}

:deep(.smart-modal-section .el-slider__button) {
    width: 18px;
    height: 18px;
    border: 3px solid var(--color-primary-600);
    background: var(--color-panel-background);
    box-shadow: 0 2px 8px var(--color-focus-ring);
    transition:
        transform 150ms ease,
        box-shadow 150ms ease;
}

:deep(.smart-modal-section .el-slider__button:hover),
:deep(.smart-modal-section .el-slider__button.hover),
:deep(.smart-modal-section .el-slider__button.dragging) {
    transform: scale(1.08);
    box-shadow: 0 0 0 5px var(--color-focus-ring);
}

:deep(.smart-modal-section .el-select__wrapper),
:deep(.smart-modal-section .el-input__wrapper) {
    min-height: 44px;
    font-size: 16px;
}

.range-labels {
    display: flex;
    justify-content: space-between;
    margin-top: -2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.token-presets {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-top: 10px;
}

.token-presets button {
    position: relative;
    display: grid;
    min-width: 0;
    gap: 1px;
    border: 1px solid var(--color-border-default);
    border-radius: 11px;
    padding: 8px 7px;
    color: var(--color-text-secondary);
    background: var(--color-card-bg);
    text-align: left;
    transition: transform 150ms, border-color 150ms, background-color 150ms;
}
.token-presets button span { font-size: 13px; font-weight: 900; }
.token-presets button small { color: var(--color-text-tertiary); font-size: 10px; }
.token-presets button svg { position: absolute; top: 7px; right: 7px; }
.token-presets button:hover {
    transform: translateY(-1px);
    border-color: var(--color-primary-300);
    color: var(--color-primary-700);
}
.token-presets button.active {
    border-color: var(--color-primary-500);
    color: var(--color-primary-700);
    background: var(--color-primary-50);
    box-shadow: 0 3px 10px var(--color-focus-ring);
}

.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--color-border);
    background: var(--color-card-bg);
}

.dialog-footer p {
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.dialog-footer > div {
    display: flex;
    gap: 12px;
}

.dialog-footer :deep(.el-button--primary) {
    border-color: var(--color-primary-600);
    background: linear-gradient(
        135deg,
        var(--color-primary-600),
        var(--color-primary-500)
    );
    transition:
        background 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.dialog-footer :deep(.el-button--primary:hover) {
    background: linear-gradient(
        135deg,
        var(--color-primary-700),
        var(--color-primary-600)
    );
    box-shadow: 0 8px 18px var(--color-focus-ring);
    transform: translateY(-1px);
}

@media (max-width: 640px) {
    .advanced-settings-grid {
        grid-template-columns: 1fr;
    }

    .advanced-settings-grid :deep(.smart-modal-section) {
        min-height: auto;
    }

    .model-status {
        grid-template-columns: 1fr;
    }

    .active-status {
        width: fit-content;
    }

    .dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .dialog-footer > div {
        justify-content: flex-end;
    }
}

@media (prefers-reduced-motion: reduce) {
    .dialog-footer :deep(.el-button--primary) {
        transition-duration: 1ms;
    }

    .dialog-footer :deep(.el-button--primary:hover) {
        transform: none;
    }
}
</style>
