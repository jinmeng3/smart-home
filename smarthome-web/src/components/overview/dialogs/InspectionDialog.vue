<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import { createInspection, getInspection } from "../../../api/overview";
import { useTaskPolling } from "../../../composables/useTaskPolling";
import type { TaskResult } from "../../../types/overview";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const checks = ref([
    "在线状态",
    "电量",
    "网络连接",
    "响应延迟",
    "固件版本",
    "异常告警",
]);
const submitting = ref(false);
const task = ref<TaskResult | null>(null);

const isTerminalByTask = (result: TaskResult) =>
    !["queued", "pending", "running", "processing"].includes(result.status);

const { error: pollError, polling, start: startPolling } = useTaskPolling<TaskResult>(
    () => {
        const id = task.value?.id;
        if (id == null) throw new Error("巡检任务不存在");
        return getInspection(id);
    },
    (result) => {
        task.value = result;
        if (isTerminalByTask(result)) {
            if (result.status === "failed") {
                ElMessage.error("巡检执行失败");
            } else {
                ElMessage.success("巡检完成");
            }
        }
    },
    { intervalMs: 1500, maxAttempts: 60, isTerminal: isTerminalByTask },
);

const progressText = computed(() => {
    if (!task.value) return "";
    const { checkedCount, deviceCount } = task.value;
    if (deviceCount != null) return `已检查 ${checkedCount ?? 0} / ${deviceCount} 台`;
    return "任务进行中";
});

const confirm = async () => {
    if (submitting.value) return;
    submitting.value = true;
    try {
        const created = await createInspection({
            scope: "all",
            roomIds: [],
            deviceTypes: [],
            checks: checks.value,
        });
        task.value = created;
        void startPolling();
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "巡检创建失败");
    } finally {
        submitting.value = false;
    }
};

const close = () => {
    emit("update:modelValue", false);
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="全屋巡检"
        description="快速检测全屋设备、网络与自动化状态"
        :width="720"
        :loading="submitting"
        confirm-text="开始巡检"
        @confirm="confirm"
        @update:model-value="close"
    >
        <div v-if="!task" class="inspection">
            <section class="box">
                <b>巡检范围</b>
                <p class="scope-note">全部设备（含网络与自动化状态）</p>
                <b>巡检项目</b>
                <div class="check-grid">
                    <label v-for="item in checks" :key="item"
                        ><input type="checkbox" checked />{{ item }}</label
                    >
                </div>
            </section>
        </div>

        <div v-else class="inspection-result">
            <span
                class="result-mark"
                :class="{
                    'is-success': task.status === 'completed',
                    'is-failed': task.status === 'failed',
                    'is-running': !['completed', 'failed'].includes(task.status),
                }"
                aria-hidden="true"
                >{{ task.status === "failed" ? "×" : task.status === "completed" ? "✓" : "" }}</span
            >
            <strong>{{
                task.status === "failed"
                    ? "巡检失败"
                    : task.status === "completed"
                      ? "巡检完成"
                      : "巡检进行中"
            }}</strong>
            <p v-if="!['completed', 'failed'].includes(task.status)">
                {{ progressText }}
                <template v-if="pollError"> · {{ pollError }}</template>
            </p>
            <dl class="task-meta">
                <div><dt>任务 ID</dt><dd>{{ task.id }}</dd></div>
                <div><dt>状态</dt><dd>{{ task.status }}</dd></div>
                <div v-if="task.deviceCount !== undefined">
                    <dt>设备总数</dt><dd>{{ task.deviceCount }}</dd>
                </div>
                <div v-if="task.checkedCount !== undefined">
                    <dt>已检查</dt><dd>{{ task.checkedCount }}</dd>
                </div>
            </dl>
            <div class="result-actions">
                <button
                    v-if="polling"
                    class="secondary-button"
                    type="button"
                    @click="close"
                >
                    后台继续
                </button>
                <button class="primary-button" type="button" @click="close">完成</button>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.scope-note {
    margin: 4px 0 14px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.check-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-top: 14px;
}
.check-grid input {
    accent-color: var(--color-primary-500);
}
.inspection-result {
    display: flex;
    min-height: 300px;
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
.inspection-result strong {
    font-size: 16px;
}
.inspection-result p {
    max-width: 380px;
    color: var(--color-text-tertiary);
    font-size: 13px;
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
    .check-grid {
        grid-template-columns: 1fr;
    }
}
</style>