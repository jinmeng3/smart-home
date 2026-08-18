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

const handleManagedTest = (modelId: number, result: ConnectionState) => {
    if (activeModel.value?.id === modelId) activeConnection.value = result;
};
</script>

<template>
    <SettingsSectionCard id="homeAssistant" icon="platform" title="模型服务" tone="orange">
        <div v-if="activeModel" class="current-model">
            <div class="model-identity">
                <span class="model-logo"><SvgIcon name="ai" /></span>
                <div>
                    <small>当前默认模型</small>
                    <strong>{{ activeModel.name }}</strong>
                    <span>{{ activeModel.provider }}</span>
                </div>
                <span class="default-badge">默认</span>
            </div>
            <div class="model-status-grid">
                <div><span>连接状态</span><strong class="connection-label" :class="activeConnection ? (activeConnection.ok ? 'is-online' : 'is-error') : ''"><i></i>{{ connectionLabel }}</strong></div>
                <div><span>API 协议</span><strong>{{ activeModel.api }}</strong></div>
            </div>
        </div>

        <div v-else class="empty-model">
            <span><SvgIcon name="platform" /></span>
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
.current-model {
    display: grid;
    gap: 12px;
    border: 1px solid color-mix(in srgb, var(--tone-orange) 24%, var(--color-border-default));
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-card-bg), var(--tone-orange-soft));
    padding: 13px;
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

.model-identity > div {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.model-identity small,
.model-status-grid span,
.empty-model small {
    color: var(--color-text-tertiary);
    font-size: 10px;
    font-weight: 700;
}

.model-identity strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 14px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.model-identity div > span {
    color: var(--color-text-secondary);
    font-size: 11px;
}

.default-badge {
    border-radius: 999px;
    background: var(--color-primary-100);
    padding: 3px 8px;
    color: var(--color-primary-700);
    font-size: 10px;
    font-weight: 900;
}

.model-status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
}

.model-status-grid > div {
    display: grid;
    min-width: 0;
    gap: 3px;
    border-radius: 9px;
    background: color-mix(in srgb, var(--color-card-bg) 78%, transparent);
    padding: 8px 10px;
}

.model-status-grid strong {
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.connection-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.connection-label i {
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
    background: var(--color-text-muted);
}

.connection-label.is-online { color: var(--color-success); }
.connection-label.is-online i { background: var(--color-success); }
.connection-label.is-error { color: var(--color-danger); }
.connection-label.is-error i { background: var(--color-danger); }

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
    margin-top: 12px;
}

.model-card-actions :deep(.base-button) { width: 100%; }

@media (max-width: 520px) {
    .model-card-actions,
    .model-status-grid {
        grid-template-columns: minmax(0, 1fr);
    }
}
</style>
