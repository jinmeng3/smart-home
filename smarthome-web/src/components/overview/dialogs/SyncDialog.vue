<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { createSyncJob, getSyncJob } from "../../../api/overview";
import { useTaskPolling } from "../../../composables/useTaskPolling";
import type { SyncJobResult } from "../../../types/overview";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    synced: [];
}>();

const sourceNames = [
    "Home Assistant",
    "Zigbee 网关",
    "蓝牙设备",
    "Matter 设备",
] as const;
const sources = ref<string[]>(["Home Assistant"]);
const submitting = ref(false);
const job = ref<SyncJobResult | null>(null);

const isJobTerminal = (result: SyncJobResult) =>
    !["queued", "pending", "running", "processing"].includes(result.status);

const { error: pollError, polling, start: startPolling } = useTaskPolling<SyncJobResult>(
    () => {
        const id = job.value?.id;
        if (id == null) throw new Error("同步任务不存在");
        return getSyncJob(id);
    },
    (result) => {
        job.value = result;
        if (isJobTerminal(result)) {
            if (result.status === "failed") {
                ElMessage.error("同步任务执行失败");
            } else {
                ElMessage.success("设备同步完成");
                emit("synced");
            }
        }
    },
    { intervalMs: 1500, maxAttempts: 60, isTerminal: isJobTerminal },
);

const statKeys = computed(() => Object.keys(job.value?.statistics ?? {}));

const toggleSource = (name: string) => {
    sources.value = sources.value.includes(name)
        ? sources.value.filter((item) => item !== name)
        : [...sources.value, name];
};

const confirm = async () => {
    if (submitting.value) return;
    if (!sources.value.length) {
        ElMessage.warning("请至少选择一个设备来源");
        return;
    }
    submitting.value = true;
    try {
        job.value = await createSyncJob({
            scope: "all",
            sources: sources.value,
            idempotencyKey: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        });
        void startPolling();
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "同步任务创建失败");
    } finally {
        submitting.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="同步设备状态"
        description="刷新并同步全屋设备的最新状态与连接信息"
        icon="refresh"
        :width="720"
        :loading="submitting"
        confirm-text="开始同步"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div v-if="!job" class="sync-layout">
            <section class="box">
                <b>同步范围</b>
                <p class="section-label">设备来源</p>
                <div class="chips wide">
                    <button
                        v-for="item in sourceNames"
                        :key="item"
                        type="button"
                        :class="{ active: sources.includes(item) }"
                        @click="toggleSource(item)"
                    >
                        {{ item }}
                    </button>
                </div>
                <p class="sync-note">
                    同步范围覆盖当前家庭全部房间与设备；提交后系统会创建异步任务并回读真实统计。
                </p>
            </section>
        </div>

        <div v-else class="sync-result">
            <span
                class="result-mark"
                :class="{
                    'is-success': job.status === 'completed',
                    'is-failed': job.status === 'failed',
                    'is-running': !['completed', 'failed'].includes(job.status),
                }"
                aria-hidden="true"
                >{{ job.status === "failed" ? "×" : job.status === "completed" ? "✓" : "" }}</span
            >
            <strong>{{
                job.status === "failed"
                    ? "同步失败"
                    : job.status === "completed"
                      ? "同步完成"
                      : "同步进行中"
            }}</strong>
            <p v-if="!['completed', 'failed'].includes(job.status)">
                任务已提交，正在等待后端执行结果。
                <template v-if="pollError"> · {{ pollError }}</template>
            </p>
            <dl class="task-meta">
                <div><dt>任务 ID</dt><dd>{{ job.id }}</dd></div>
                <div><dt>状态</dt><dd>{{ job.status }}</dd></div>
            </dl>
            <div v-if="statKeys.length" class="sync-stats">
                <div v-for="key in statKeys" :key="key">
                    <strong>{{ job.statistics[key] }}</strong>
                    <span>{{ key }}</span>
                </div>
            </div>
            <div class="result-actions">
                <button
                    v-if="polling"
                    class="secondary-button"
                    type="button"
                    @click="emit('update:modelValue', false)"
                >
                    后台继续
                </button>
                <button
                    class="primary-button"
                    type="button"
                    @click="emit('update:modelValue', false)"
                >
                    完成
                </button>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.sync-layout {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}
.section-label {
    margin-top: 16px;
    color: var(--color-text-secondary);
    font-size: 12px;
}
.sync-note {
    margin-top: 16px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.6;
}
.sync-result {
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
.sync-result strong {
    font-size: 16px;
}
.sync-result p {
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
.sync-stats {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-top: 8px;
}
.sync-stats > div {
    display: grid;
    min-width: 84px;
    gap: 2px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    padding: 8px 12px;
    background: var(--color-card-bg);
}
.sync-stats strong {
    color: var(--color-primary-600);
    font-size: 18px;
}
.sync-stats span {
    color: var(--color-text-tertiary);
    font-size: 11px;
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
</style>