<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { executeMode } from "../../../api/overview";
import type { TaskResult } from "../../../types/overview";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const selectedMode = ref<"home" | "away" | "sleep" | "guest">("home");
const runAutomations = ref(true);
const loading = ref(false);
const result = ref<TaskResult | null>(null);

const modes = [
    { key: "home", name: "回家模式", icon: "home", hint: "开启常用照明、舒适空调" },
    { key: "away", name: "离家模式", icon: "security", hint: "关闭灯光、开启安防" },
    { key: "sleep", name: "睡眠模式", icon: "air-quality", hint: "柔和灯光、关闭部分设备" },
    { key: "guest", name: "访客模式", icon: "scene", hint: "基础照明与常用设备" },
] as const;

const modeName = computed(
    () => modes.find((item) => item.key === selectedMode.value)?.name ?? "",
);
const statusText = computed(() => {
    if (!result.value) return "";
    const status = result.value.status;
    if (status === "completed") return "已完成";
    if (status === "failed") return "执行失败";
    if (status === "running") return "执行中";
    if (status === "queued") return "已排队，等待执行";
    return status;
});
/** 任务是否已进入终态（后端当前仅返回执行结果；无终态轮询接口时如实展示） */
const isTerminal = computed(
    () => !!result.value && !["queued", "pending", "running", "processing"].includes(result.value.status),
);
const reset = () => {
    result.value = null;
    selectedMode.value = "home";
    runAutomations.value = true;
};

const confirm = async () => {
    if (loading.value) return;
    loading.value = true;
    try {
        result.value = await executeMode({
            mode: selectedMode.value,
            roomIds: [],
            runAutomations: runAutomations.value,
            idempotencyKey: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        });
        if (result.value.status === "failed") {
            ElMessage.error("模式执行失败");
        } else if (result.value.status === "completed") {
            ElMessage.success("模式执行完成");
        } else {
            ElMessage.success("模式执行任务已提交");
        }
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "模式执行失败");
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="切换全屋模式"
        description="按模式为全屋设备执行对应操作"
        :width="720"
        :loading="loading"
        confirm-text="立即切换"
        @confirm="confirm"
        @update:model-value="$emit('update:modelValue', false)"
    >
        <div v-if="!result" class="mode-layout">
            <div class="mode-grid">
                <button
                    v-for="mode in modes"
                    :key="mode.key"
                    type="button"
                    class="mode-card"
                    :class="{ selected: selectedMode === mode.key }"
                    @click="selectedMode = mode.key"
                >
                    <span><SvgIcon :name="mode.icon" size="lg" /></span>
                    <b>{{ mode.name }}</b
                    ><small>{{ mode.hint }}</small>
                    <i v-if="selectedMode === mode.key">✓</i>
                </button>
            </div>
            <section class="side-stack">
                <label class="switch-row"
                    ><span
                        >同步执行自动化联动<small
                            >切换模式时同时运行关联自动化</small
                        ></span
                    ><input v-model="runAutomations" type="checkbox"
                /></label>
                <div class="box hint-box">
                    <b>执行说明</b>
                    <p>按所选模式对家庭设备批量下发操作指令，范围覆盖当前家庭全部房间。</p>
                </div>
            </section>
        </div>

        <div v-else class="mode-result">
            <template v-if="!isTerminal">
                <span class="result-mark is-running" aria-hidden="true"></span>
                <strong>任务已提交</strong>
                <p>执行任务正在排队/运行中，可通过任务 ID 在任务记录中查看进度。</p>
            </template>
            <template v-else-if="result.status === 'failed'">
                <span class="result-mark is-failed" aria-hidden="true">×</span>
                <strong>模式执行失败</strong>
                <p>未能完成「{{ modeName }}」的全部设备操作。</p>
            </template>
            <template v-else>
                <span class="result-mark is-success" aria-hidden="true">✓</span>
                <strong>模式「{{ modeName }}」已生效</strong>
                <p>共影响 {{ result.affectedDeviceCount ?? 0 }} 台设备。</p>
            </template>
            <dl class="task-meta">
                <div><dt>任务 ID</dt><dd>{{ result.id }}</dd></div>
                <div><dt>状态</dt><dd>{{ statusText }}</dd></div>
                <div v-if="result.affectedDeviceCount !== undefined">
                    <dt>受影响设备</dt><dd>{{ result.affectedDeviceCount }}</dd>
                </div>
            </dl>
            <div class="result-actions">
                <button class="secondary-button" type="button" @click="reset">再次执行</button>
                <button class="primary-button" type="button" @click="$emit('update:modelValue', false)">完成</button>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.mode-layout {
    display: grid;
    grid-template-columns: 1.65fr 1fr;
    gap: 16px;
}
.mode-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.mode-card {
    position: relative;
    display: flex;
    min-height: 150px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
}
.mode-card.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-primary-100);
}
.mode-card > span {
    display: grid;
    width: 54px;
    height: 54px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.mode-card small {
    display: block;
    color: var(--color-text-tertiary);
}
.mode-card i {
    position: absolute;
    right: 8px;
    top: 8px;
    width: 20px;
    border-radius: 50%;
    background: var(--color-primary-500);
    color: #fff;
}
.hint-box p {
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.6;
}
/* === 结果视图 === */
.mode-result {
    display: flex;
    min-height: 320px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 10px;
    text-align: center;
}
.result-mark {
    display: grid;
    width: 56px;
    height: 56px;
    place-items: center;
    border-radius: 50%;
    font-size: 26px;
    font-weight: 900;
}
.result-mark.is-success {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.result-mark.is-failed {
    background: var(--color-warning-soft, var(--color-danger-soft));
    color: var(--color-danger);
}
.result-mark.is-running {
    animation: result-pulse 1.2s ease-in-out infinite;
    background: var(--color-primary-100);
}
.mode-result strong {
    font-size: 16px;
}
.mode-result p {
    max-width: 380px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    line-height: 1.6;
}
.task-meta {
    display: grid;
    width: 100%;
    max-width: 420px;
    gap: 8px;
    margin-top: 8px;
}
.task-meta > div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding-bottom: 6px;
    font-size: 13px;
}
.task-meta dt {
    color: var(--color-text-tertiary);
}
.task-meta dd {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
}
.result-actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
}
@keyframes result-pulse {
    0%,
    100% {
        transform: scale(1);
        opacity: 0.7;
    }
    50% {
        transform: scale(1.06);
        opacity: 1;
    }
}
@media (max-width: 760px) {
    .mode-layout {
        grid-template-columns: 1fr;
    }
    .mode-grid {
        grid-template-columns: 1fr;
    }
}
</style>