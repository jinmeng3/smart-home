<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import {
    ElButton,
    ElInputNumber,
    ElMessage,
    ElMessageBox,
    ElSlider,
} from "element-plus";
import type {
    AiAssistantSettings,
    ModelAdvancedSettings,
} from "../../types/settings";
import { useSettingsStore } from "../../stores/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import BaseSwitch from "../BaseSwitch.vue";
import BaseModal from "../common/BaseModal.vue";
import "element-plus/theme-chalk/el-input-number.css";
import "element-plus/theme-chalk/el-message.css";
import "element-plus/theme-chalk/el-message-box.css";
import "element-plus/theme-chalk/el-slider.css";

const props = defineProps<{
    ai: AiAssistantSettings;
}>();

const settingsStore = useSettingsStore();
const dialogVisible = ref(false);
const saving = ref(false);
const savedDraft = ref("");
const draft = reactive<ModelAdvancedSettings>({
    language: "zh-CN",
    detailLevel: 70,
    temperature: 0.7,
    maxTokens: 4096,
});

const languageOptions: Array<{
    label: string;
    value: ModelAdvancedSettings["language"];
}> = [
    { label: "简体中文", value: "zh-CN" },
    { label: "English", value: "en-US" },
    { label: "自动检测", value: "auto" },
];
const tokenPresets = [2048, 4096, 8192];
const currentDraft = computed(() => JSON.stringify(draft));
const hasUnsavedChanges = computed(
    () => currentDraft.value !== savedDraft.value,
);

const copyCurrentSettings = () => {
    Object.assign(draft, {
        language: props.ai.language,
        detailLevel: props.ai.detailLevel,
        temperature: props.ai.temperature,
        maxTokens: props.ai.maxTokens,
    });
    savedDraft.value = currentDraft.value;
};

const openDialog = () => {
    copyCurrentSettings();
    dialogVisible.value = true;
};

const confirmDiscard = async () => {
    if (!hasUnsavedChanges.value) {
        return true;
    }

    try {
        await ElMessageBox.confirm(
            "当前设置尚未应用，确定放弃修改吗？",
            "放弃修改",
            {
                confirmButtonText: "放弃",
                cancelButtonText: "继续编辑",
                type: "warning",
            },
        );
        return true;
    } catch {
        return false;
    }
};

const requestClose = async () => {
    if (saving.value || !(await confirmDiscard())) {
        return;
    }

    dialogVisible.value = false;
};

const handleBeforeClose = async (done: () => void) => {
    if (saving.value || !(await confirmDiscard())) {
        return;
    }

    done();
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

    const previousSettings: ModelAdvancedSettings = {
        language: props.ai.language,
        detailLevel: props.ai.detailLevel,
        temperature: props.ai.temperature,
        maxTokens: props.ai.maxTokens,
    };

    Object.assign(props.ai, draft);
    saving.value = true;

    try {
        await settingsStore.saveAIModel();
        savedDraft.value = currentDraft.value;
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
    <SettingsSectionCard id="ai" icon="✦" title="智能助手">
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
            <ElButton plain type="primary" @click="openDialog"
                >更多设置</ElButton
            >
        </div>
    </SettingsSectionCard>

    <BaseModal
        v-model="dialogVisible"
        :before-close="handleBeforeClose"
        :close-on-click-modal="true"
        :close-on-press-escape="true"
        :lock-scroll="true"
        :modal="true"
        :show-close="false"
        append-to-body
        class="model-advanced-dialog"
        modal-class="model-advanced-overlay"
        width="720px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="ai-icon" aria-hidden="true">✦</span>
                <div>
                    <h2>模型高级设置</h2>
                    <p>调整回复的创造性和长度上限</p>
                </div>
                <ElButton
                    aria-label="关闭"
                    class="close-button"
                    text
                    @click="requestClose"
                    >×</ElButton
                >
            </header>
        </template>

        <div class="model-status">
            <span>当前模型</span>
            <strong>{{ ai.model }}</strong>
            <span class="active-status"><i />配置生效中</span>
        </div>

        <div class="settings-grid">
            <section class="setting-card">
                <div class="setting-title">
                    <div>
                        <strong>回复语言</strong><span>Response language</span>
                    </div>
                </div>
                <p>选择助手默认使用的回复语言。</p>
                <div class="language-options">
                    <button
                        v-for="option in languageOptions"
                        :key="option.value"
                        :class="{ active: draft.language === option.value }"
                        type="button"
                        @click="draft.language = option.value"
                    >
                        {{ option.label }}
                    </button>
                </div>
            </section>

            <section class="setting-card">
                <div class="setting-title">
                    <div>
                        <strong>回复详细程度</strong><span>Detail level</span>
                    </div>
                    <output>{{ draft.detailLevel }}%</output>
                </div>
                <p>数值越高，回复会包含更多背景和步骤。</p>
                <ElSlider
                    v-model="draft.detailLevel"
                    :max="100"
                    :min="0"
                    :show-tooltip="false"
                />
                <div class="range-labels">
                    <span>简洁</span><span>均衡</span><span>详细</span>
                </div>
            </section>

            <section class="setting-card">
                <div class="setting-title">
                    <div><strong>创造性</strong><span>Temperature</span></div>
                    <output>{{ draft.temperature.toFixed(1) }}</output>
                </div>
                <p>数值越低越稳定，越高则更有创造性。</p>
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
            </section>

            <section class="setting-card">
                <div class="setting-title">
                    <div>
                        <strong>回复长度上限</strong><span>Max tokens</span>
                    </div>
                    <output>{{ draft.maxTokens.toLocaleString() }}</output>
                </div>
                <p>控制单次回复最多可生成的 token 数量。</p>
                <ElInputNumber
                    v-model="draft.maxTokens"
                    :max="32768"
                    :min="1"
                    :step="256"
                    class="full-width"
                    controls-position="right"
                    size="large"
                />
                <div class="token-presets">
                    <ElButton
                        v-for="value in tokenPresets"
                        :key="value"
                        :class="{ active: draft.maxTokens === value }"
                        @click="draft.maxTokens = value"
                    >
                        {{ value.toLocaleString() }}
                    </ElButton>
                </div>
            </section>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <p>设置将在保存页面更改后应用到新的对话</p>
                <div>
                    <ElButton :disabled="saving" @click="requestClose"
                        >取消</ElButton
                    >
                    <ElButton
                        :loading="saving"
                        type="primary"
                        @click="applySettings"
                        >应用设置</ElButton
                    >
                </div>
            </footer>
        </template>
    </BaseModal>
</template>

<style scoped>
:global(.model-advanced-dialog) {
    display: flex;
    max-height: calc(100vh - 48px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-panel-background);
    box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.model-advanced-overlay) {
    background: var(--color-overlay);
    backdrop-filter: blur(4px);
}

:global(.model-advanced-dialog .el-dialog__header),
:global(.model-advanced-dialog .el-dialog__footer) {
    padding: 0;
}

:global(.model-advanced-dialog .el-dialog__body) {
    min-height: 0;
    padding: 0;
    overflow-y: auto;
}

.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(
        135deg,
        var(--color-dialog-header-start),
        var(--color-dialog-header-end)
    );
}

.ai-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    font-size: 18px;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
    box-shadow: 0 8px 20px rgb(59 130 246 / 24%);
}

.dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 20px;
    font-weight: 800;
}

.dialog-header p {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 14px;
}

.close-button {
    margin: -4px -6px 0 auto;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.model-status {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 9px;
    margin: 16px 20px 0;
    padding: 10px 12px;
    border: 1px solid var(--color-divider);
    border-radius: 11px;
    color: var(--color-text-tertiary);
    font-size: 14px;
    background: var(--color-workspace-background);
}

.model-status strong {
    min-width: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.active-status {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-success);
    font-weight: 700;
}

.active-status i {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}

.settings-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: stretch;
    gap: 12px;
    padding: 14px 20px 20px;
}

.setting-card {
    display: flex;
    min-width: 0;
    min-height: 180px;
    flex-direction: column;
    padding: 14px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-workspace-background);
    transition:
        border-color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.setting-card:hover {
    border-color: var(--color-border-focus);
    box-shadow: 0 8px 20px rgb(15 23 42 / 6%);
    transform: translateY(-1px);
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
}

.setting-title span {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.setting-title output {
    color: var(--color-primary-600);
    font-size: 18px;
    font-weight: 800;
}

.setting-card > p {
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

.language-options {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin-top: auto;
    padding: 4px;
    border: 1px solid var(--color-border-default);
    border-radius: 11px;
    background: var(--color-surface-subtle);
}

.language-options button {
    min-width: 0;
    height: 40px;
    border: 1px solid transparent;
    border-radius: 8px;
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 650;
    background: transparent;
    transition:
        color 160ms ease,
        border-color 160ms ease,
        background 160ms ease,
        box-shadow 160ms ease;
}

.language-options button:hover {
    color: var(--color-primary-700);
    background: var(--color-surface-hover);
}

.language-options button.active {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    background: var(--color-panel-background);
    box-shadow: 0 2px 8px rgb(15 23 42 / 8%);
}

.setting-card :deep(.el-slider) {
    height: 32px;
    margin-top: auto;
}

.setting-card :deep(.el-slider__runway) {
    height: 6px;
    background: var(--color-border-default);
}

.setting-card :deep(.el-slider__bar) {
    height: 6px;
    border-radius: 999px;
    background: var(--color-primary-600);
}

.setting-card :deep(.el-slider__button-wrapper) {
    top: -15px;
    width: 36px;
    height: 36px;
}

.setting-card :deep(.el-slider__button) {
    width: 18px;
    height: 18px;
    border: 3px solid var(--color-primary-600);
    background: var(--color-panel-background);
    box-shadow: 0 2px 8px var(--color-focus-ring);
    transition:
        transform 150ms ease,
        box-shadow 150ms ease;
}

.setting-card :deep(.el-slider__button:hover),
.setting-card :deep(.el-slider__button.hover),
.setting-card :deep(.el-slider__button.dragging) {
    transform: scale(1.08);
    box-shadow: 0 0 0 5px var(--color-focus-ring);
}

.setting-card :deep(.el-select__wrapper),
.setting-card :deep(.el-input__wrapper) {
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
    display: flex;
    gap: 7px;
    margin-top: 9px;
}

.token-presets :deep(.el-button) {
    flex: 1;
    height: 36px;
    margin-left: 0;
    padding: 0 8px;
    border-color: var(--color-border-default);
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 700;
    background: var(--color-panel-background);
}

.token-presets :deep(.el-button:hover) {
    border-color: var(--color-primary-300);
    color: var(--color-primary-700);
}

.token-presets :deep(.el-button.active) {
    border-color: var(--color-primary-500);
    color: var(--color-text-on-primary);
    background: var(--color-primary-600);
    box-shadow: 0 4px 10px var(--color-focus-ring);
}

.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    border-top: 1px solid var(--color-divider);
    background: var(--color-workspace-background);
}

.dialog-footer p {
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.dialog-footer > div {
    display: flex;
    gap: 8px;
}

@media (max-width: 640px) {
    :global(.model-advanced-dialog) {
        width: calc(100% - 24px) !important;
    }

    .settings-grid {
        grid-template-columns: 1fr;
    }

    .model-status {
        grid-template-columns: auto minmax(0, 1fr);
    }

    .active-status {
        grid-column: 1 / -1;
    }

    .dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .dialog-footer > div {
        justify-content: flex-end;
    }
}
</style>
