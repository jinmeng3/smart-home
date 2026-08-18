<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type {
    AiAssistantSettings,
    HomeAssistantSettings,
} from "../../types/settings";
import { useSettingsStore } from "../../stores/settings";
import BaseButton from "../common/BaseButton.vue";
import SvgIcon from "../common/SvgIcon.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import ModelAddDialog from "./ModelAddDialog.vue";
import ModelManageDialog from "./ModelManageDialog.vue";

defineProps<{
    ai: AiAssistantSettings;
    homeAssistant: HomeAssistantSettings;
}>();

interface ConnectionState {
    ok: boolean;
    latency: number | null;
    message: string;
    testedAt: Date;
}

const settingsStore = useSettingsStore();
const addDialogVisible = ref(false);
const manageDialogVisible = ref(false);
const activeConnection = ref<ConnectionState | null>(null);
const activeModel = computed(() =>
    settingsStore.aiModels.find((model) => model.is_active),
);

watch(
    () => activeModel.value?.id,
    () => {
        activeConnection.value = null;
    },
);

const connectionLabel = computed(() => {
    if (!activeModel.value) return "未配置";
    if (!activeConnection.value) return "未检测";
    return activeConnection.value.ok
        ? `连接正常 · ${activeConnection.value.latency ?? "?"} ms`
        : "连接失败";
});

const connectionIcon = computed(() => {
    if (!activeConnection.value) return "scan";
    return activeConnection.value.ok ? "check-circle" : "warning";
});

const connectionHint = computed(() => {
    const testedAt = activeConnection.value?.testedAt;
    if (!testedAt) return "可在模型管理中执行连接测试";

    return `最近检测 ${testedAt.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
    })}`;
});

const handleManagedTest = (modelId: number, result: ConnectionState) => {
    if (activeModel.value?.id === modelId) activeConnection.value = result;
};
</script>

<template>
    <SettingsSectionCard id="homeAssistant" icon="database" title="模型服务" tone="orange">
        <div v-if="activeModel" class="current-model">
            <div class="model-identity">
                <span class="model-logo"><SvgIcon name="ai" /></span>
                <div class="model-copy">
                    <span class="model-kicker">当前默认模型</span>
                    <strong>{{ activeModel.name }}</strong>
                    <span class="model-provider">{{ activeModel.provider }}</span>
                </div>
                <span class="default-badge">默认</span>
            </div>
            <p class="model-description">
                新建智能对话将优先使用此模型服务
            </p>
            <div class="model-status-grid">
                <div class="status-item">
                    <span class="status-icon" :class="activeConnection ? (activeConnection.ok ? 'is-online' : 'is-error') : ''">
                        <SvgIcon :name="connectionIcon" size="sm" />
                    </span>
                    <div>
                        <span>连接状态</span>
                        <strong
                            class="connection-label"
                            :class="activeConnection ? (activeConnection.ok ? 'is-online' : 'is-error') : ''"
                            aria-live="polite"
                        >{{ connectionLabel }}</strong>
                        <small>{{ connectionHint }}</small>
                    </div>
                </div>
                <div class="status-item">
                    <span class="status-icon is-protocol">
                        <SvgIcon name="plug" size="sm" />
                    </span>
                    <div>
                        <span>API 协议</span>
                        <strong class="protocol-name">{{ activeModel.api }}</strong>
                        <small>请求与响应兼容模式</small>
                    </div>
                </div>
            </div>
        </div>

        <div v-else class="empty-model">
            <span><SvgIcon name="layers" /></span>
            <div><strong>尚未配置模型</strong><small>添加模型后即可使用智能对话服务</small></div>
        </div>

        <div class="model-card-actions">
            <BaseButton variant="primary" @click="addDialogVisible = true">
                <SvgIcon name="plus" size="sm" />添加模型
            </BaseButton>
            <BaseButton plain @click="manageDialogVisible = true">
                <SvgIcon name="settings" size="sm" />管理模型
            </BaseButton>
        </div>
    </SettingsSectionCard>

    <ModelAddDialog v-if="addDialogVisible" v-model="addDialogVisible" />
    <ModelManageDialog
        v-if="manageDialogVisible"
        v-model="manageDialogVisible"
        @tested="handleManagedTest"
    />
</template>

<style scoped>
/* 让卡片内容撑满网格等高高度：内容区弹性拉伸，操作按钮固定在底部 */
.settings-section {
    display: flex;
    flex-direction: column;
}

.current-model,
.empty-model {
    flex: 1;
}

.current-model {
    display: flex;
    flex-direction: column;
    gap: 14px;
    border: 1px solid color-mix(in srgb, var(--tone-orange) 22%, var(--color-border-default));
    border-radius: 16px;
    background:
        radial-gradient(circle at 100% 0, color-mix(in srgb, var(--tone-orange) 9%, transparent), transparent 42%),
        var(--color-card-bg);
    padding: 18px;
}

.model-identity {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr) auto;
    align-items: center;
    gap: 11px;
}

.model-logo,
.empty-model > span {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 12px;
    background: var(--tone-orange);
    color: white;
}

.model-copy {
    display: grid;
    min-width: 0;
    gap: 3px;
}

.model-status-grid span,
.empty-model small {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.model-kicker {
    color: var(--tone-orange);
    font-size: 12.5px;
    letter-spacing: 0.02em;
}

.model-identity strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 17px;
    line-height: 1.3;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.model-provider {
    color: var(--color-text-secondary);
    font-size: 13px;
}

.default-badge {
    border-radius: 999px;
    border: 1px solid color-mix(in srgb, var(--color-primary-600) 18%, transparent);
    background: var(--color-primary-50);
    padding: 4px 9px;
    color: var(--color-primary-700);
    font-size: 11px;
    font-weight: 900;
}

.model-description {
    margin: -3px 0 0 53px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.5;
}

.model-status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: auto;
}

.status-item {
    display: grid;
    grid-template-columns: 32px minmax(0, 1fr);
    align-items: start;
    min-width: 0;
    gap: 10px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: color-mix(in srgb, var(--color-panel-background) 72%, transparent);
    padding: 12px;
}

.status-item > div {
    display: grid;
    min-width: 0;
    gap: 3px;
}

.status-icon {
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.status-icon.is-online {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.status-icon.is-error {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.status-icon.is-protocol {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.model-status-grid strong {
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.35;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.connection-label {
    display: block;
}

.status-item small {
    overflow: hidden;
    color: var(--color-text-muted);
    font-size: 11.5px;
    line-height: 1.4;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.connection-label.is-online { color: var(--color-success); }
.connection-label.is-error { color: var(--color-danger); }

.protocol-name {
    font-family: var(--font-mono);
}

.empty-model {
    display: flex;
    align-items: center;
    gap: 11px;
    border: 1px dashed var(--color-border-default);
    border-radius: 14px;
    padding: 14px;
}

.empty-model > span {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}

.empty-model > div { display: grid; gap: 3px; }
.empty-model strong { color: var(--color-text-primary); font-size: 13px; }

.model-card-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: auto;
    padding-top: 14px;
}

.model-card-actions :deep(.base-button) { width: 100%; }

@media (max-width: 520px) {
    .model-card-actions,
    .model-status-grid {
        grid-template-columns: minmax(0, 1fr);
    }

    .model-description {
        margin-left: 0;
    }
}
</style>
