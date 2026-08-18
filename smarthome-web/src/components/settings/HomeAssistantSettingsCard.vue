<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElInput, ElInputNumber, ElMessage } from "element-plus";
import type { ApiProtocol } from "../../api/aiModel";
import type {
    AiAssistantSettings,
    HomeAssistantSettings,
} from "../../types/settings";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import { useSettingsStore } from "../../stores/settings";
import "element-plus/theme-chalk/el-input.css";
import "element-plus/theme-chalk/el-message.css";

const props = defineProps<{
    ai: AiAssistantSettings;
    homeAssistant: HomeAssistantSettings;
}>();
const settingsStore = useSettingsStore();

const emit = defineEmits<{
    sync: [];
}>();

const showApiKey = ref(false);
const dialogVisible = ref(false);
const saving = ref(false);
const apiProtocolOptions = [
    { value: "openai-completions", label: "OpenAI Completions" },
    { value: "openai-responses", label: "OpenAI Responses" },
    { value: "azure-openai-responses", label: "Azure OpenAI Responses" },
    { value: "openai-codex-responses", label: "OpenAI Codex" },
    { value: "anthropic-messages", label: "Anthropic Messages" },
    { value: "bedrock-converse-stream", label: "AWS Bedrock" },
] as const;
const draft = reactive({
    name: "",
    provider: "",
    endpoint: "",
    apiKey: "",
    apiProtocol: "openai-completions" as ApiProtocol,
    parameters: "{}",
    compat: "",
    temperature: 0.7,
    maxTokens: 4096,
    active: true,
    description: "",
});
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
const openParametersDialog = () => {
    Object.assign(draft, {
        name: modelName.value,
        provider: provider.value,
        endpoint: props.homeAssistant.serviceUrl,
        apiKey: "",
        apiProtocol: props.homeAssistant.apiProtocol ?? "openai-completions",
        parameters: props.homeAssistant.parameters || "{}",
        compat: props.homeAssistant.compat || "",
        temperature: props.ai.temperature,
        maxTokens: props.ai.maxTokens,
        active: connected.value,
        description: props.ai.language,
    });
    dialogVisible.value = true;
};

const applyParameters = async () => {
    if (!draft.name.trim() || !draft.provider.trim() || !draft.endpoint.trim()) {
        ElMessage.warning("请完整填写模型名称、供应商和 API 地址");
        return;
    }
    try {
        JSON.parse(draft.parameters || "{}");
    } catch {
        ElMessage.warning("扩展参数必须是合法 JSON");
        return;
    }

    modelName.value = draft.name;
    provider.value = draft.provider;
    props.homeAssistant.serviceUrl = draft.endpoint;
    props.homeAssistant.accessToken = draft.apiKey;
    props.homeAssistant.apiProtocol = draft.apiProtocol;
    props.homeAssistant.parameters = draft.parameters || "{}";
    props.homeAssistant.compat = draft.compat || "";
    props.homeAssistant.websocketStatus = draft.active ? "connected" : "disconnected";
    props.ai.temperature = draft.temperature;
    props.ai.maxTokens = draft.maxTokens;
    props.ai.language = draft.description === "en-US" || draft.description === "auto" ? draft.description : "zh-CN";
    saving.value = true;
    try {
        await settingsStore.saveAIModel();
        dialogVisible.value = false;
        ElMessage.success("模型配置已保存到后端");
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "模型保存失败");
    } finally {
        saving.value = false;
    }
};
</script>

<template>
    <SettingsSectionCard id="homeAssistant" icon="platform" title="模型添加" tone="orange">
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
        <div class="mt-3">
            <button
                class="model-entry-button"
                type="button"
                @click="openParametersDialog"
            >
                <span><SvgIcon name="platform" /></span>
                <span><strong>模型配置</strong><small>配置连接、密钥与推理参数</small></span>
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        width="760px"
        title="模型配置"
        description="按照模型服务商参数配置连接与推理能力"
        icon="platform"
        tone="orange"
    >

        <section class="model-config-layout">
            <div class="model-config-main">
                <div class="model-basic-grid">
                    <label class="modal-field"><span>模型名称 *</span><input v-model="draft.name" class="settings-input" placeholder="例如 gpt-4.1-mini" /></label>
                    <label class="modal-field"><span>供应商 *</span><input v-model="draft.provider" class="settings-input" placeholder="例如 OpenAI" /></label>
                </div>
                <label class="modal-field"><span>API 地址 *</span><input v-model="draft.endpoint" class="settings-input" placeholder="https://api.example.com/v1" /></label>
                <label class="modal-field">
                    <span>API 协议</span>
                    <select v-model="draft.apiProtocol" class="settings-input">
                        <option
                            v-for="opt in apiProtocolOptions"
                            :key="opt.value"
                            :value="opt.value"
                        >
                            {{ opt.label }}
                        </option>
                    </select>
                </label>
                <label class="modal-field">
                    <span>API Key</span>
                    <div class="relative">
                        <input
                            v-model="draft.apiKey"
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
                <div class="model-basic-grid">
                    <label class="modal-field"><span>温度（0–2）</span><ElInputNumber v-model="draft.temperature" :min="0" :max="2" :step="0.1" /></label>
                    <label class="modal-field"><span>最大 Token</span><ElInputNumber v-model="draft.maxTokens" :min="1" :max="131072" :step="512" /></label>
                </div>
                <label class="modal-field">
                    <span>扩展参数 JSON</span>
                    <ElInput
                        v-model="draft.parameters"
                        :autosize="{ minRows: 5, maxRows: 10 }"
                        placeholder='{"deployment":"smart-home-chat","api_version":"2026-01-01"}'
                        type="textarea"
                    />
                </label>
                <label class="modal-field">
                    <span>兼容配置 JSON（可选）</span>
                    <ElInput
                        v-model="draft.compat"
                        :autosize="{ minRows: 4, maxRows: 8 }"
                        placeholder='{"thinking_format":"deepseek","max_tokens_field":"max_tokens"}'
                        type="textarea"
                    />
                </label>
            </div>
            <aside class="model-config-actions">
                <div class="active-setting">
                    <span><strong>启用模型</strong><small>保存后设为当前使用模型</small></span>
                    <BaseSwitch v-model="draft.active" />
                </div>
                <div class="model-config-status">
                    <span>模型状态</span>
                    <strong
                        class="device-status-label rounded-lg px-3 py-1 text-sm font-semibold"
                        :class="draft.active ? 'status-online' : 'status-offline'"
                        >{{ draft.active ? "保存后启用" : "保持停用" }}</strong
                    >
                </div>
                <div class="model-config-status">
                    <span>供应商</span>
                    <strong>{{ draft.provider || "未填写" }}</strong>
                </div>
                <div class="model-config-status">
                    <span>API 地址</span>
                    <strong>{{
                        draft.endpoint || "尚未填写"
                    }}</strong>
                </div>
                <div class="action-stack">
                    <BaseButton :disabled="!draft.endpoint" @click="emit('sync')">
                        测试连接
                    </BaseButton>
                    <BaseButton :disabled="saving" @click="dialogVisible = false">取消</BaseButton>
                    <BaseButton :loading="saving" variant="primary" @click="applyParameters">
                        保存模型
                    </BaseButton>
                </div>
            </aside>
        </section>

        <template #footer>
            <footer class="dialog-footer">
                <span>带 * 的字段为后端必填项；API Key 不会在页面中回显</span>
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

.model-entry-button {
    display: grid;
    width: 100%;
    grid-template-columns: 40px minmax(0, 1fr) 18px;
    align-items: center;
    gap: 12px;
    border: 1px solid color-mix(in srgb, var(--tone-orange) 28%, var(--color-border));
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-card-bg), var(--tone-orange-soft));
    padding: 11px 14px;
    text-align: left;
    transition: transform 160ms var(--motion-ease), border-color 160ms, box-shadow 160ms;
}
.model-entry-button:hover { transform: translateY(-2px); border-color: var(--tone-orange); box-shadow: 0 9px 22px color-mix(in srgb, var(--tone-orange) 14%, transparent); }
.model-entry-button > span:first-child { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 12px; background: var(--tone-orange); color: white; }
.model-entry-button > span:nth-child(2) { display: grid; gap: 2px; }
.model-entry-button strong { color: var(--color-text-primary); font-size: 14px; }
.model-entry-button small { color: var(--color-text-tertiary); font-size: 12px; }
.model-entry-button > svg { color: var(--tone-orange); }

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

.model-basic-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.model-basic-grid :deep(.el-input-number) { width: 100%; }

.active-setting {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    border: 1px solid var(--color-primary-200);
    border-radius: 14px;
    background: var(--color-primary-50);
    padding: 12px;
}
.active-setting > span { display: grid; gap: 2px; }
.active-setting strong { color: var(--color-text-primary); font-size: 13px; }
.active-setting small { color: var(--color-text-tertiary); font-size: 10px; }

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

    .model-basic-grid { grid-template-columns: 1fr; }

    .model-config-actions {
        border-left: 0;
        border-top: 1px solid var(--color-border-subtle);
        padding-left: 0;
        padding-top: 14px;
    }
}
</style>
