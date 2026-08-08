<script setup lang="ts">
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { SceneLog } from "../../types/scene";

defineProps<{
    modelValue: boolean;
    sceneName: string;
    logs: SceneLog[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const sourceLabels: Record<string, string> = {
    manual: "手动执行",
    schedule: "定时触发",
    location: "位置触发",
    device: "设备触发",
};

const statusLabel = (status: string) =>
    status === "completed" || status === "enabled" ? "执行成功" :
    status === "failed" ? "执行失败" : "执行中";

const formatTime = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN", { hour12: false });
};

const formatDuration = (log: SceneLog) => {
    if (!log.finishedAt) return "未完成";
    const duration = new Date(log.finishedAt).getTime() - new Date(log.startedAt).getTime();
    return Number.isFinite(duration) ? `${Math.max(duration, 0)} ms` : "--";
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        width="640px"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <header class="log-dialog-header">
                <span class="log-dialog-icon"><SvgIcon name="log" /></span>
                <div>
                    <h2>场景日志</h2>
                    <p>{{ sceneName }} <b>{{ logs.length }}</b> 条执行记录</p>
                </div>
                <button type="button" aria-label="关闭" @click="emit('update:modelValue', false)">
                    <SvgIcon name="close" size="sm" />
                </button>
            </header>
        </template>

        <section class="log-dialog-body">
            <div v-if="!logs.length" class="log-empty">
                <SvgIcon name="log" size="lg" />
                <span>该场景暂无执行日志</span>
            </div>
            <div v-else class="log-timeline">
                <article v-for="(log, index) in logs" :key="log.id" class="log-item" :style="{ '--i': index }">
                    <div class="log-timeline-node">
                        <span class="log-dot" :class="`is-${log.status}`" />
                        <span v-if="index < logs.length - 1" class="log-line" />
                    </div>
                    <div class="log-card" :class="`is-${log.status}`">
                        <div class="log-card-top">
                            <span>{{ sourceLabels[log.source] ?? log.source }}</span>
                            <time>{{ formatTime(log.startedAt) }}</time>
                        </div>
                        <p>{{ log.message || statusLabel(log.status) }}</p>
                        <footer>
                            <em :class="log.status === 'failed' ? 'is-failed' : 'is-success'">{{ statusLabel(log.status) }}</em>
                            <small>耗时 {{ formatDuration(log) }}</small>
                        </footer>
                    </div>
                </article>
            </div>
        </section>
    </BaseSmartModal>
</template>

<style scoped>
.log-dialog-header { display:flex; align-items:center; gap:16px; padding:20px 24px; border-bottom:1px solid var(--color-border); background:linear-gradient(180deg,var(--color-card-bg) 60%,var(--color-primary-50)); }
.log-dialog-icon { display:grid; width:48px; height:48px; flex:0 0 48px; place-items:center; border-radius:14px; background:linear-gradient(135deg,var(--color-primary-100),var(--color-primary-50)); color:var(--color-primary-600); box-shadow:0 2px 8px var(--color-focus-ring); }
.log-dialog-header h2,.log-dialog-header p { margin:0; }
.log-dialog-header h2 { color:var(--color-text-primary); font-size:22px; font-weight:900; }
.log-dialog-header p { display:flex; align-items:center; gap:7px; margin-top:6px; color:var(--color-text-secondary); font-size:14px; font-weight:700; }
.log-dialog-header p b { border-radius:999px; background:var(--color-primary-100); padding:3px 8px; color:var(--color-primary-700); font-size:12px; }
.log-dialog-header button { display:grid; width:36px; height:36px; margin-left:auto; place-items:center; border-radius:10px; color:var(--color-text-tertiary); }
.log-dialog-header button:hover { background:var(--color-surface-hover); color:var(--color-text-primary); }
.log-dialog-body { max-height:480px; overflow-y:auto; padding:20px 24px 16px; }
.log-empty { display:flex; min-height:140px; flex-direction:column; align-items:center; justify-content:center; gap:12px; color:var(--color-text-tertiary); font-size:15px; font-weight:700; }
.log-timeline { display:grid; }
.log-item { display:grid; grid-template-columns:20px minmax(0,1fr); gap:14px; animation:log-enter 300ms ease both; animation-delay:calc(var(--i) * 40ms); }
.log-timeline-node { display:flex; flex-direction:column; align-items:center; }
.log-dot { z-index:1; width:12px; height:12px; flex:0 0 12px; border-radius:50%; background:var(--color-primary-500); box-shadow:0 0 0 3px var(--color-card-bg); }
.log-dot.is-failed { background:var(--color-danger); }
.log-line { width:2px; min-height:12px; flex:1; background:var(--color-primary-200); }
.log-card { display:grid; gap:7px; margin-bottom:12px; border:1px solid var(--color-border); border-left:3px solid var(--color-primary-500); border-radius:12px; background:var(--color-card-bg); padding:14px 16px; transition:200ms var(--motion-ease); }
.log-card.is-failed { border-left-color:var(--color-danger); }
.log-card:hover { border-color:var(--color-primary-200); box-shadow:0 4px 16px var(--color-focus-ring); transform:translateY(-1px); }
.log-card-top,.log-card footer { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.log-card-top span { color:var(--color-text-primary); font-size:15px; font-weight:900; }
.log-card time,.log-card small { color:var(--color-text-tertiary); font-size:12px; font-weight:700; }
.log-card p { margin:0; color:var(--color-text-secondary); font-size:14px; line-height:1.5; }
.log-card footer em { border-radius:999px; padding:3px 8px; font-size:11px; font-style:normal; font-weight:900; }
.log-card footer .is-success { background:var(--color-success-soft); color:var(--color-success); }
.log-card footer .is-failed { background:var(--color-danger-soft); color:var(--color-danger); }
@keyframes log-enter { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
</style>
