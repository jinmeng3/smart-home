<script setup lang="ts">
import { computed, ref } from "vue";
import { ElButton, ElInput, ElMessage } from "element-plus";
import type {
    AiAssistantSettings,
    HomeAssistantSettings,
} from "../../types/settings";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import "element-plus/theme-chalk/el-input.css";
import "element-plus/theme-chalk/el-message.css";

const props = defineProps<{
    ai: AiAssistantSettings;
    homeAssistant: HomeAssistantSettings;
}>();

const emit = defineEmits<{
    sync: [];
}>();

const showApiKey = ref(false);
const dialogVisible = ref(false);
const parametersDraft = ref("{}");
const provider = computed({
    get: () =>
        props.ai.model.split(" · ")[1] ?? props.ai.model.split(" ")[0] ?? "",
    set: (value) => {
        const name = props.ai.model.split(" · ")[0] || "自定义模型";
        props.ai.model = value.trim() ? `${name} · ${value.trim()}` : name;
    },
});
const modelName = computed({
    get: () => props.ai.model.split(" · ")[0] || props.ai.model,
    set: (value) => {
        props.ai.model = provider.value
            ? `${value.trim()} · ${provider.value}`
            : value.trim();
    },
});
const connected = computed(
    () => props.homeAssistant.websocketStatus === "connected",
);
const statusClass = computed(() =>
    connected.value ? "status-online" : "status-offline",
);
const statusText = computed(() => (connected.value ? "已启用" : "未启用"));

const openParametersDialog = () => {
    parametersDraft.value = props.homeAssistant.parameters || "{}";
    dialogVisible.value = true;
};

const applyParameters = () => {
    try {
        JSON.parse(parametersDraft.value || "{}");
    } catch {
        ElMessage.warning("扩展参数必须是合法 JSON");
        return;
    }

    props.homeAssistant.parameters = parametersDraft.value || "{}";
    dialogVisible.value = false;
};
</script>

<template>
    <SettingsSectionCard id="homeAssistant" icon="platform" title="模型添加">
        <label class="settings-field integration-field">
            <span class="integration-label">模型名称</span>
            <input
                v-model="modelName"
                class="settings-input integration-control"
                placeholder="例如 gpt-4.1-mini"
            />
        </label>
        <label class="settings-field integration-field">
            <span class="integration-label">供应商</span>
            <input
                v-model="provider"
                class="settings-input integration-control"
                placeholder="OpenAI / DeepSeek / Azure"
            />
        </label>
        <label class="settings-field integration-field">
            <span class="integration-label">API 地址</span>
            <input
                v-model="homeAssistant.serviceUrl"
                class="settings-input integration-control"
                placeholder="https://api.example.com/v1/chat/completions"
            />
        </label>
        <div class="mt-3 flex justify-center">
            <button
                class="secondary-button"
                type="button"
                @click="openParametersDialog"
            >
                模型配置
            </button>
        </div>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        width="760px"
        title="模型配置"
        description="状态、连接测试和厂商扩展参数"
        icon="platform"
    >

        <section class="model-config-layout">
            <div class="model-config-main">
                <label class="modal-field">
                    <span>API Key</span>
                    <div class="relative">
                        <input
                            v-model="homeAssistant.accessToken"
                            class="settings-input w-full pr-10"
                            :placeholder="
                                homeAssistant.tokenConfigured
                                    ? '已配置，留空表示不修改'
                                    : '请输入 API Key'
                            "
                            :type="showApiKey ? 'text' : 'password'"
                        />
                        <button
                            class="absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center text-[var(--color-text-tertiary)]"
                            type="button"
                            @click="showApiKey = !showApiKey"
                        >
                            <SvgIcon name="eye" size="sm" />
                        </button>
                    </div>
                </label>
                <label class="modal-field">
                    <span>扩展参数 JSON</span>
                    <ElInput
                        v-model="parametersDraft"
                        :autosize="{ minRows: 9, maxRows: 14 }"
                        placeholder='{"deployment":"smart-home-chat","api_version":"2026-01-01"}'
                        type="textarea"
                    />
                </label>
            </div>
            <aside class="model-config-actions">
                <div class="model-config-status">
                    <span>模型状态</span>
                    <strong
                        class="device-status-label rounded-lg px-3 py-1 text-sm font-semibold"
                        :class="statusClass"
                        >{{ statusText }}</strong
                    >
                </div>
                <div class="model-config-status">
                    <span>供应商</span>
                    <strong>{{ provider || "未填写" }}</strong>
                </div>
                <div class="model-config-status">
                    <span>API 地址</span>
                    <strong>{{
                        homeAssistant.serviceUrl || "尚未填写"
                    }}</strong>
                </div>
                <div class="action-stack">
                    <ElButton :disabled="!connected" @click="emit('sync')">
                        测试连接
                    </ElButton>
                    <ElButton @click="dialogVisible = false">取消</ElButton>
                    <ElButton type="primary" @click="applyParameters">
                        应用配置
                    </ElButton>
                </div>
            </aside>
        </section>

        <template #footer>
            <footer class="dialog-footer">
                <span>保存页面更改时会写入模型配置</span>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.integration-field {
    gap: 16px;
}
.integration-label {
    flex: 0 0 96px;
    white-space: nowrap;
}
.integration-control {
    width: auto;
    min-width: 0;
    flex: 1;
}

.model-config-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 16px;
}

.model-config-main,
.model-config-actions {
    display: grid;
    align-content: start;
    gap: 14px;
}

.model-config-actions {
    border-left: 1px solid var(--color-border-subtle);
    padding-left: 16px;
}

.modal-field {
    display: grid;
    gap: 8px;
}

.modal-field > span {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.model-config-status {
    display: grid;
    min-height: 64px;
    align-content: center;
    gap: 5px;
    border: 1px solid var(--color-teal-500);
    border-radius: 16px;
    padding: 10px 12px;
    background: linear-gradient(
        145deg,
        var(--color-card-bg),
        var(--color-teal-soft)
    );
    box-shadow: var(--shadow-card);
}

.model-config-status span {
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.model-config-status strong {
    min-width: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.action-stack {
    display: grid;
    gap: 10px;
    margin-top: 4px;
}

.action-stack :deep(.el-button) {
    width: 100%;
    margin-left: 0;
}

@media (max-width: 640px) {
    .integration-field {
        align-items: stretch;
        flex-direction: column;
        gap: 6px;
    }

    .integration-label {
        flex-basis: auto;
    }

    .model-config-layout {
        grid-template-columns: 1fr;
    }

    .model-config-actions {
        border-left: 0;
        border-top: 1px solid var(--color-border-subtle);
        padding-left: 0;
        padding-top: 14px;
    }
}
</style>
