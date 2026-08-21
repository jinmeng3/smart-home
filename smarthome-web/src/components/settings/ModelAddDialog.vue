<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import type { ApiProtocol, AIModelPayload } from "../../api/aiModel";
import { getSupportedProviders, testAIModelConnection } from "../../api/aiModel";
import { useSettingsStore } from "../../stores/settings";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";
import "element-plus/theme-chalk/el-message.css";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    tested: [result: { ok: boolean; latency: number | null; testedAt: Date }];
}>();

const settingsStore = useSettingsStore();
const saving = ref(false);
const testing = ref(false);
const showAdvanced = ref(false);
const showApiKey = ref(false);
const testResult = ref<{ ok: boolean; text: string } | null>(null);
/** 后端支持的供应商 id 列表（GET /ai_model/providers）· 编辑时下拉使用 */
const providerOptions = ref<string[]>([]);
const providersLoading = ref(false);
const form = reactive({
    name: "",
    provider: "",
    endpoint: "",
    apiKey: "",
    api: "openai-completions" as ApiProtocol,
    temperature: 0.7,
    maxTokens: 4096,
    parameters: "{}",
    compat: "",
    setAsDefault: false,
});

const loadProviders = async () => {
    providersLoading.value = true;
    try {
        const providers = await getSupportedProviders();
        providerOptions.value = providers.map((item) => item.id);
        if (form.provider && !providerOptions.value.includes(form.provider)) {
            providerOptions.value = [
                form.provider,
                ...providerOptions.value,
            ];
        }
    } catch {
        providerOptions.value = [];
    } finally {
        providersLoading.value = false;
    }
};

watch(
    () => providersLoading.value,
    (loading) => {
        if (!loading && providerOptions.value.length === 0 && form.provider) {
            providerOptions.value = [form.provider];
        }
    },
);

watch(
    () => props.modelValue,
    (open) => {
        if (open) void loadProviders();
    },
    { immediate: true },
);

const protocols: Array<{ value: ApiProtocol; label: string }> = [
    { value: "openai-completions", label: "OpenAI Completions" },
    { value: "openai-responses", label: "OpenAI Responses" },
    { value: "azure-openai-responses", label: "Azure OpenAI Responses" },
    { value: "openai-codex-responses", label: "OpenAI Codex" },
    { value: "anthropic-messages", label: "Anthropic Messages" },
    { value: "bedrock-converse-stream", label: "AWS Bedrock" },
];

const buildPayload = (): AIModelPayload | null => {
    if (!form.name.trim() || !form.provider.trim() || !form.endpoint.trim()) {
        ElMessage.warning("请填写模型名称、供应商和 API 地址");
        return null;
    }
    try {
        const parameters = JSON.parse(form.parameters || "{}") as Record<string, unknown>;
        const compat = form.compat.trim()
            ? JSON.parse(form.compat) as Record<string, unknown>
            : null;
        return {
            name: form.name.trim(),
            provider: form.provider.trim(),
            api: form.api,
            api_endpoint: form.endpoint.trim(),
            ...(form.apiKey.trim() ? { api_key: form.apiKey.trim() } : {}),
            parameters,
            compat,
            temperature: form.temperature,
            max_tokens: form.maxTokens,
            is_active: form.setAsDefault,
        };
    } catch {
        ElMessage.warning("扩展参数和兼容配置必须是合法 JSON");
        return null;
    }
};

const testConnection = async () => {
    const payload = buildPayload();
    if (!payload) return;
    testing.value = true;
    testResult.value = null;
    try {
        const result = await testAIModelConnection({
            ...payload,
            max_tokens: Math.min(payload.max_tokens ?? 1024, 8192),
        });
        testResult.value = {
            ok: result.ok,
            text: result.ok
                ? `连接成功 · ${result.latency_ms ?? "?"} ms`
                : result.message || "连接失败",
        };
        emit("tested", {
            ok: result.ok,
            latency: result.latency_ms,
            testedAt: new Date(),
        });
    } catch (error) {
        testResult.value = {
            ok: false,
            text: error instanceof Error ? error.message : "连接测试失败",
        };
    } finally {
        testing.value = false;
    }
};

const submit = async () => {
    const payload = buildPayload();
    if (!payload) return;
    saving.value = true;
    try {
        await settingsStore.createModel(payload);
        ElMessage.success(form.setAsDefault ? "模型已添加并设为默认" : "模型已添加");
        emit("update:modelValue", false);
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "模型添加失败");
    } finally {
        saving.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :loading="saving"
        width="680px"
        title="添加模型"
        description="添加新的模型服务配置，不会自动切换当前模型"
        icon="new-device"
        tone="orange"
        body-tone="neutral"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <div class="model-form">
            <section class="form-section">
                <header><span>基础信息</span><small>用于识别模型和服务来源</small></header>
                <div class="form-grid">
                    <label class="modal-field"><span>模型名称 *</span><input v-model="form.name" class="settings-input" placeholder="例如 gpt-4.1-mini" /></label>
                    <label class="modal-field">
                        <span>供应商 *</span>
                        <select
                            v-model="form.provider"
                            class="settings-input"
                            :disabled="providersLoading"
                        >
                            <option value="" disabled>
                                {{
                                    providersLoading
                                        ? "加载中…"
                                        : providerOptions.length
                                          ? "请选择供应商"
                                          : "无可用供应商"
                                }}
                            </option>
                            <option v-for="item in providerOptions" :key="item" :value="item">
                                {{ item }}
                            </option>
                        </select>
                    </label>
                </div>
            </section>

            <section class="form-section">
                <header><span>连接配置</span><small>配置请求协议、地址与访问凭证</small></header>
                <div class="form-grid">
                    <label class="modal-field"><span>API 协议</span><select v-model="form.api" class="settings-input"><option v-for="item in protocols" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
                    <label class="modal-field"><span>API Key</span><div class="secret-input"><input v-model="form.apiKey" class="settings-input" :type="showApiKey ? 'text' : 'password'" placeholder="请输入 API Key" /><button type="button" aria-label="显示或隐藏密钥" @click="showApiKey = !showApiKey"><SvgIcon name="eye" size="sm" /></button></div></label>
                </div>
                <label class="modal-field"><span>API 地址 *</span><input v-model="form.endpoint" class="settings-input" placeholder="https://api.example.com/v1" /></label>
            </section>

            <button class="advanced-toggle" type="button" :aria-expanded="showAdvanced" @click="showAdvanced = !showAdvanced">
                <span><strong>高级参数</strong><small>温度、Token 与协议兼容配置</small></span>
                <SvgIcon name="chevron-down" size="sm" :class="{ 'is-open': showAdvanced }" />
            </button>
            <div v-if="showAdvanced" class="advanced-panel">
                <div class="form-grid compact-grid"><label class="modal-field"><span>温度（0–2）</span><input v-model.number="form.temperature" class="settings-input" type="number" min="0" max="2" step="0.1" /></label><label class="modal-field"><span>最大 Token</span><input v-model.number="form.maxTokens" class="settings-input" type="number" min="1" max="131072" step="512" /></label></div>
                <div class="form-grid"><label class="modal-field"><span>扩展参数 JSON</span><textarea v-model="form.parameters" class="settings-input json-input" rows="3"></textarea></label><label class="modal-field"><span>兼容配置 JSON（可选）</span><textarea v-model="form.compat" class="settings-input json-input" rows="3"></textarea></label></div>
            </div>

            <div class="default-setting"><span><strong>设为默认模型</strong><small>添加成功后切换为当前使用模型</small></span><BaseSwitch v-model="form.setAsDefault" /></div>
            <div v-if="testResult" class="test-result" :class="testResult.ok ? 'is-ok' : 'is-fail'"><span></span>{{ testResult.text }}</div>
        </div>

        <template #footer>
            <footer class="dialog-actions"><BaseButton :loading="testing" :disabled="saving" @click="testConnection">测试连接</BaseButton><BaseButton :disabled="saving || testing" @click="emit('update:modelValue', false)">取消</BaseButton><BaseButton class="model-submit" variant="primary" :loading="saving" :disabled="testing" @click="submit">添加模型</BaseButton></footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.model-form, .modal-field { display: grid; gap: 6px; }
.model-form { gap: 14px; }
.model-form .settings-input { width: 100%; }
.form-section { display: grid; gap: 11px; border: 1px solid color-mix(in srgb, var(--tone-orange) 16%, var(--color-border-subtle)); border-radius: 13px; background: var(--color-card-bg); padding: 13px; }
.form-section > header { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding-bottom: 9px; border-bottom: 1px solid var(--color-border-subtle); }
.form-section > header span { color: color-mix(in srgb, var(--tone-orange) 72%, var(--color-text-primary)); font-size: 13px; font-weight: 900; }
.form-section > header small { color: var(--color-text-muted); font-size: 10px; font-weight: 700; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 11px; }
.modal-field > span { color: var(--color-text-secondary); font-size: 12px; font-weight: 700; }
.secret-input { position: relative; }
.secret-input input { width: 100%; padding-right: 40px; }
.secret-input button { position: absolute; top: 50%; right: 6px; display: grid; width: 30px; height: 30px; place-items: center; color: var(--color-text-tertiary); transform: translateY(-50%); }
.advanced-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid color-mix(in srgb, var(--tone-orange) 18%, var(--color-border-subtle)); border-radius: 12px; background: color-mix(in srgb, var(--tone-orange-soft) 42%, var(--color-card-bg)); padding: 11px 13px; text-align: left; }
.advanced-toggle:hover { border-color: color-mix(in srgb, var(--tone-orange) 42%, var(--color-border)); background: var(--tone-orange-soft); }
.advanced-toggle > span { display: grid; gap: 2px; }
.advanced-toggle strong { color: var(--color-text-secondary); font-size: 12px; }
.advanced-toggle small { color: var(--color-text-muted); font-size: 10px; }
.advanced-toggle svg { color: var(--tone-orange); transition: transform 180ms var(--motion-ease); }
.advanced-toggle svg.is-open { transform: rotate(180deg); }
.advanced-panel { display: grid; gap: 11px; border: 1px solid color-mix(in srgb, var(--tone-orange) 22%, var(--color-border)); border-radius: 13px; background: color-mix(in srgb, var(--tone-orange-soft) 55%, var(--color-card-bg)); padding: 13px; }
.compact-grid { width: min(100%, 460px); gap: 14px; }
.json-input { height: auto; min-height: 82px; padding: 9px 10px; resize: vertical; font-family: ui-monospace, monospace; }
.default-setting { display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid color-mix(in srgb, var(--tone-orange) 28%, var(--color-border)); border-radius: 12px; background: color-mix(in srgb, var(--tone-orange-soft) 62%, var(--color-card-bg)); padding: 12px; }
.default-setting > span { display: grid; gap: 2px; }
.default-setting strong { color: var(--color-text-primary); font-size: 13px; }
.default-setting small { color: var(--color-text-tertiary); font-size: 11px; }
.test-result { display: flex; align-items: center; gap: 7px; border-radius: 10px; padding: 9px 11px; font-size: 12px; font-weight: 700; }
.test-result span { width: 7px; height: 7px; border-radius: 999px; }
.test-result.is-ok { background: var(--color-success-soft); color: var(--color-success); }
.test-result.is-ok span { background: var(--color-success); }
.test-result.is-fail { background: var(--color-danger-soft); color: var(--color-danger); }
.test-result.is-fail span { background: var(--color-danger); }
.dialog-actions { display: flex; justify-content: flex-end; align-items: center; gap: 10px; width: 100%; border-top: 1px solid var(--color-border); background: var(--color-card-bg); padding: 14px 24px; }
.model-form .settings-input:focus { border-color: var(--tone-orange); box-shadow: 0 0 0 3px color-mix(in srgb, var(--tone-orange) 16%, transparent); }
.dialog-actions :deep(.model-submit) { border-color: var(--tone-orange); background: var(--tone-orange); }
.dialog-actions :deep(.model-submit:hover:not(:disabled)) { border-color: color-mix(in srgb, var(--tone-orange) 82%, black); background: linear-gradient(135deg, color-mix(in srgb, var(--tone-orange) 82%, black), var(--tone-orange)); box-shadow: 0 8px 18px color-mix(in srgb, var(--tone-orange) 20%, transparent); }
@media (max-width: 640px) { .form-grid { grid-template-columns: minmax(0, 1fr); } .form-section > header { align-items: flex-start; flex-direction: column; gap: 3px; } .dialog-actions { flex-wrap: wrap; } }
</style>
