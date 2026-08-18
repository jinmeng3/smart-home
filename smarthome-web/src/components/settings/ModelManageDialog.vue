<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { AIModelRead } from "../../api/aiModel";
import { testSavedAIModel } from "../../api/aiModel";
import { useSettingsStore } from "../../stores/settings";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import ConfirmActionDialog from "../common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../common/ConfirmEntitySummary.vue";
import SvgIcon from "../common/SvgIcon.vue";
import ModelEditDialog from "./ModelEditDialog.vue";
import "element-plus/theme-chalk/el-message.css";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    tested: [modelId: number, result: ConnectionResult];
}>();

interface ConnectionResult {
    ok: boolean;
    latency: number | null;
    message: string;
    testedAt: Date;
}

const settingsStore = useSettingsStore();
const loadingId = ref<number | null>(null);
const selectedModel = ref<AIModelRead | null>(null);
const pendingDeleteModel = ref<AIModelRead | null>(null);
const pendingActivateModel = ref<AIModelRead | null>(null);
const activateLoading = ref(false);
const deleteLoading = ref(false);
const connectionResults = reactive<Record<number, ConnectionResult>>({});

const models = computed(() => settingsStore.aiModels);
const activeModel = computed(() => models.value.find((model) => model.is_active));

const formatDate = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("zh-CN");
};

const testModel = async (model: AIModelRead) => {
    loadingId.value = model.id;
    try {
        const response = await testSavedAIModel(model.id);
        const result: ConnectionResult = {
            ok: response.ok,
            latency: response.latency_ms,
            message: response.ok ? `连接成功 · ${response.latency_ms ?? "?"} ms` : response.message || "连接失败",
            testedAt: new Date(),
        };
        connectionResults[model.id] = result;
        emit("tested", model.id, result);
    } catch (error) {
        const result: ConnectionResult = {
            ok: false,
            latency: null,
            message: error instanceof Error ? error.message : "连接测试失败",
            testedAt: new Date(),
        };
        connectionResults[model.id] = result;
        emit("tested", model.id, result);
    } finally {
        loadingId.value = null;
    }
};

const activate = async (model: AIModelRead) => {
    if (model.is_active) return;
    pendingActivateModel.value = model;
};

const confirmActivate = async () => {
    const model = pendingActivateModel.value;
    if (!model) return;
    activateLoading.value = true;
    try {
        await settingsStore.activateModel(model.id);
        ElMessage.success("默认模型已切换");
        pendingActivateModel.value = null;
    } catch (error) {
        if (error instanceof Error) ElMessage.error(error.message);
    } finally {
        activateLoading.value = false;
    }
};

const remove = async (model: AIModelRead) => {
    if (model.is_active && models.value.length > 1) {
        ElMessage.warning("请先将其他模型设为默认，再删除当前模型");
        return;
    }
    pendingDeleteModel.value = model;
};

const confirmRemove = async () => {
    const model = pendingDeleteModel.value;
    if (!model) return;
    deleteLoading.value = true;
    try {
        await settingsStore.removeModel(model.id);
        pendingDeleteModel.value = null;
        ElMessage.success("模型已删除");
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "模型删除失败");
    } finally {
        deleteLoading.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        width="820px"
        title="管理模型"
        description="查看并维护模型连接，默认模型将用于新的智能对话"
        icon="sliders"
        tone="orange"
        body-tone="neutral"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <div v-if="models.length" class="model-list">
            <article v-for="model in models" :key="model.id" class="model-item" :class="{ 'is-active': model.is_active }">
                <div class="model-head">
                    <span class="model-icon"><SvgIcon name="ai" /></span>
                    <div class="model-title"><div><strong>{{ model.name }}</strong><span v-if="model.is_active">默认</span></div><small>{{ model.provider }} · {{ model.api }}</small></div>
                    <div class="connection-state" :class="connectionResults[model.id] ? (connectionResults[model.id]!.ok ? 'is-ok' : 'is-fail') : ''"><i></i>{{ connectionResults[model.id]?.message ?? "未检测" }}</div>
                </div>
                <div class="model-meta"><span>API Key <strong>{{ model.has_api_key ? "••••••••" : "未配置" }}</strong></span><span>最大 Token <strong>{{ model.max_tokens.toLocaleString() }}</strong></span><span>添加于 <strong>{{ formatDate(model.created_at) }}</strong></span></div>
                <div class="model-actions">
                    <BaseButton size="sm" :loading="loadingId === model.id" @click="testModel(model)">测试连接</BaseButton>
                    <BaseButton size="sm" @click="selectedModel = model">编辑</BaseButton>
                    <BaseButton v-if="!model.is_active" size="sm" plain variant="primary" @click="activate(model)">设为默认</BaseButton>
                    <BaseButton size="sm" plain variant="danger" @click="remove(model)">删除</BaseButton>
                </div>
            </article>
        </div>
        <div v-else class="empty-state"><span><SvgIcon name="database" /></span><strong>还没有模型</strong><p>关闭窗口后使用“添加模型”创建第一个模型配置。</p></div>

        <template #footer>
            <footer class="dialog-footer"><span>当前默认：{{ activeModel?.name ?? "未配置" }}</span><BaseButton @click="emit('update:modelValue', false)">完成</BaseButton></footer>
        </template>
    </BaseSmartModal>

    <ModelEditDialog
        v-if="selectedModel"
        :model-value="true"
        :model="selectedModel"
        @update:model-value="!$event && (selectedModel = null)"
        @saved="selectedModel = null"
    />

    <ConfirmActionDialog
        v-if="pendingDeleteModel"
        :model-value="true"
        title="删除模型"
        :description="pendingDeleteModel.is_active ? '删除唯一的默认模型后，模型服务将进入未配置状态。' : '删除后将无法继续使用该模型配置。'"
        confirm-text="确认删除"
        :loading="deleteLoading"
        warning="模型配置及保存的访问凭证将被永久删除，此操作无法恢复。"
        @confirm="confirmRemove"
        @update:model-value="!$event && (pendingDeleteModel = null)"
    >
        <ConfirmEntitySummary
            icon="ai"
            :title="pendingDeleteModel.name"
            :description="`${pendingDeleteModel.provider} · ${pendingDeleteModel.api}`"
            color="var(--color-danger)"
        />
    </ConfirmActionDialog>

    <ConfirmActionDialog
        v-if="pendingActivateModel"
        :model-value="true"
        tone="warning"
        title="切换默认模型"
        :description="'切换后，新的智能对话将默认使用该模型。'"
        confirm-text="确认切换"
        :loading="activateLoading"
        warning="当前活动会话不受影响，仅影响后续新建对话。"
        footer-hint="可在管理列表随时改回"
        @confirm="confirmActivate"
        @update:model-value="!$event && (pendingActivateModel = null)"
    >
        <ConfirmEntitySummary
            icon="ai"
            :title="pendingActivateModel.name"
            :description="`${pendingActivateModel.provider} · ${pendingActivateModel.api}`"
            color="var(--color-warning)"
        />
    </ConfirmActionDialog>
</template>

<style scoped>
.model-list { display: grid; gap: 12px; }
.model-item { display: grid; gap: 12px; border: 1px solid var(--color-border-default); border-radius: 14px; background: var(--color-panel-background); padding: 14px; box-shadow: var(--shadow-card); }
.model-item.is-active { border-color: color-mix(in srgb, var(--tone-orange) 28%, var(--color-border)); background: linear-gradient(135deg, var(--color-panel-background), var(--tone-orange-soft)); }
.model-head { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 11px; }
.model-icon { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 12px; background: var(--tone-orange-soft); color: var(--tone-orange); }
.model-title { min-width: 0; display: grid; gap: 3px; }
.model-title > div { display: flex; align-items: center; gap: 7px; }
.model-title strong { overflow: hidden; color: var(--color-text-primary); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.model-title span { border-radius: 999px; background: var(--tone-orange-soft); padding: 2px 7px; color: color-mix(in srgb, var(--tone-orange) 78%, black); font-size: 10px; font-weight: 900; }
.model-title small { color: var(--color-text-tertiary); font-size: 11px; }
.connection-state { display: inline-flex; align-items: center; gap: 6px; color: var(--color-text-muted); font-size: 11px; font-weight: 800; white-space: nowrap; }
.connection-state i { width: 7px; height: 7px; border-radius: 999px; background: var(--color-text-muted); }
.connection-state.is-ok { color: var(--color-success); }.connection-state.is-ok i { background: var(--color-success); }
.connection-state.is-fail { color: var(--color-danger); }.connection-state.is-fail i { background: var(--color-danger); }
.model-meta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.model-meta span { display: grid; gap: 3px; border-radius: 9px; background: var(--color-panel-secondary); padding: 8px 10px; color: var(--color-text-muted); font-size: 10px; }
.model-meta strong { overflow: hidden; color: var(--color-text-secondary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.model-actions { display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }
.empty-state { display: grid; justify-items: center; gap: 7px; padding: 44px 20px; text-align: center; }
.empty-state > span { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 14px; background: var(--tone-orange-soft); color: var(--tone-orange); }
.empty-state strong { color: var(--color-text-primary); }.empty-state p { margin: 0; color: var(--color-text-tertiary); font-size: 12px; }
.dialog-footer { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 12px; }.dialog-footer > span { color: var(--color-text-tertiary); font-size: 12px; font-weight: 700; }
@media (max-width: 640px) { .model-head { grid-template-columns: 42px minmax(0, 1fr); }.connection-state { grid-column: 2; }.model-meta { grid-template-columns: minmax(0, 1fr); } }
</style>
