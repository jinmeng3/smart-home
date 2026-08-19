<script setup lang="ts">
import { computed, ref } from "vue";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

type SyncPhase = "select" | "syncing" | "result";

/** 同步 Timeline 步骤：连接平台 → 读取设备 → 更新状态 → 完成 */
const syncSteps = [
    { key: "connect", label: "连接平台" },
    { key: "read", label: "读取设备" },
    { key: "update", label: "更新状态" },
    { key: "done", label: "完成" },
] as const;
type SyncStepKey = (typeof syncSteps)[number]["key"];

const props = defineProps<{
    modelValue: boolean;
    platforms: {
        name: string;
        connected: boolean;
        deviceCount: number;
    }[];
    syncing?: boolean;
    /** 同步处理函数——调用后等待完成，弹窗自动切换到结果阶段 */
    syncHandler?: (platformName: string) => Promise<number | undefined | void>;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const phase = ref<SyncPhase>("select");
const selectedPlatform = ref("");
const progress = ref(0);
const syncResult = ref<{ updated: number; failed: number } | null>(null);
/** 当前推进到的步骤下标 */
const activeStepIndex = ref(0);
let stepTimer: ReturnType<typeof setTimeout> | undefined;
const connectedPlatforms = computed(() =>
    props.platforms.filter((platform) => platform.connected),
);

const stepState = (index: number) => {
    if (index < activeStepIndex.value) return "completed";
    if (index === activeStepIndex.value) return "running";
    return "pending";
};

const startSync = async () => {
    if (!selectedPlatform.value || !props.syncHandler) return;
    phase.value = "syncing";
    progress.value = 0;
    syncResult.value = null;
    activeStepIndex.value = 0;

    // 视觉步骤推进（业务结果仍由真实 Promise 驱动，不阻塞操作）
    stepTimer = setInterval(() => {
        if (activeStepIndex.value < syncSteps.length - 1) {
            activeStepIndex.value += 1;
        }
    }, 600);

    try {
        const result = await props.syncHandler(selectedPlatform.value);
        syncResult.value = {
            updated: (result as number) ?? 0,
            failed: 0,
        };
    } catch {
        syncResult.value = { updated: 0, failed: 1 };
    }
    clearInterval(stepTimer);
    stepTimer = undefined;
    activeStepIndex.value = syncSteps.length - 1;
    phase.value = "result";
};

const handleSyncComplete = (updated: number, failed: number) => {
    syncResult.value = { updated, failed };
    phase.value = "result";
};

const reset = () => {
    phase.value = "select";
    selectedPlatform.value = "";
    progress.value = 0;
    syncResult.value = null;
    activeStepIndex.value = 0;
    if (stepTimer) {
        clearInterval(stepTimer);
        stepTimer = undefined;
    }
};

const close = () => {
    emit("update:modelValue", false);
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        width="560px"
        @update:model-value="emit('update:modelValue', $event)"
        @confirm="phase === 'result' ? close() : undefined"
    >
        <template #header>
            <header class="sync-dialog-header">
                <span class="sync-dialog-icon" aria-hidden="true">
                    <SvgIcon name="refresh" />
                </span>
                <div>
                    <h2>同步设备</h2>
                    <p>{{ phase === "select" ? "选择要同步的平台" : phase === "syncing" ? "正在同步设备数据" : "同步完成" }}</p>
                </div>
                <button
                    class="sync-dialog-close"
                    type="button"
                    aria-label="关闭"
                    :disabled="phase === 'syncing'"
                    @click="close"
                >
                    <SvgIcon name="close" size="sm" />
                </button>
            </header>
        </template>

        <!-- 阶段 1：选择平台 -->
        <div v-if="phase === 'select'" class="sync-select">
            <div class="sync-select-summary">
                <span class="sync-select-summary-icon">
                    <SvgIcon name="platform" size="sm" />
                </span>
                <span>
                    <strong>选择数据来源</strong>
                    <small>{{ connectedPlatforms.length }} 个平台可同步，仅支持单选</small>
                </span>
            </div>
            <button
                v-for="platform in platforms"
                :key="platform.name"
                class="sync-platform-card"
                :class="{
                    'is-selected': selectedPlatform === platform.name,
                    'is-disabled': !platform.connected,
                }"
                type="button"
                :disabled="!platform.connected"
                @click="selectedPlatform = platform.name"
            >
                <span class="sync-platform-icon">
                    <SvgIcon name="platform" size="sm" />
                </span>
                <span class="sync-platform-main">
                    <strong>{{ platform.name }}</strong>
                    <span class="sync-platform-meta">
                        <i
                            class="sync-platform-dot"
                            :class="platform.connected ? 'is-online' : 'is-offline'"
                        ></i>
                        {{ platform.connected ? "已连接" : "未配置" }}
                        · {{ platform.deviceCount }} 台设备
                    </span>
                </span>
                <span
                    v-if="selectedPlatform === platform.name"
                    class="sync-platform-check"
                >
                    <SvgIcon name="check-circle" size="sm" />
                </span>
            </button>
        </div>

        <!-- 阶段 2：同步中（步骤 Timeline） -->
        <div v-if="phase === 'syncing'" class="sync-progress">
            <div class="sync-progress-spinner" aria-hidden="true"></div>
            <ol class="sync-steps">
                <li
                    v-for="(step, index) in syncSteps"
                    :key="step.key"
                    class="sync-step"
                    :class="`is-${stepState(index)}`"
                >
                    <span class="sync-step-icon">
                        <SvgIcon
                            v-if="stepState(index) === 'completed'"
                            name="check"
                            size="sm"
                        /><SvgIcon
                            v-else-if="stepState(index) === 'running'"
                            name="refresh"
                            size="sm"
                            class="is-spinning"
                        /><i v-else></i>
                    </span>
                    <span class="sync-step-label">{{ step.label }}</span>
                </li>
            </ol>
            <span class="sync-progress-label">正在同步设备数据和状态…</span>
        </div>

        <!-- 阶段 3：完成 -->
        <div v-if="phase === 'result' && syncResult" class="sync-result">
            <div class="sync-result-icon">
                <SvgIcon
                    name="check-circle"
                    size="lg"
                    class="sync-result-check"
                />
            </div>
            <div class="sync-result-stats">
                <div class="sync-result-stat">
                    <strong class="sync-result-count is-success">{{
                        syncResult.updated
                    }}</strong>
                    <span>台已更新</span>
                </div>
                <div class="sync-result-divider"></div>
                <div class="sync-result-stat">
                    <strong
                        class="sync-result-count"
                        :class="
                            syncResult.failed > 0 ? 'is-danger' : 'is-muted'
                        "
                        >{{ syncResult.failed }}</strong
                    >
                    <span>台失败</span>
                </div>
            </div>
            <p class="sync-result-hint">
                设备数据已同步，可在设备列表查看最新状态。
            </p>
        </div>

        <template #footer>
            <footer class="dialog-footer sync-dialog-footer">
                <span>{{
                    phase === "select"
                        ? "同步会将平台设备信息更新到本地"
                        : phase === "syncing"
                          ? "请勿关闭弹窗"
                          : "设备数据已同步完成"
                }}</span>
                <div>
                    <BaseButton
                        v-if="phase !== 'syncing'"
                        @click="close"
                    >
                        {{ phase === "result" ? "关闭" : "取消" }}
                    </BaseButton>
                    <BaseButton
                        v-if="phase === 'select'"
                        :disabled="!selectedPlatform"
                        variant="primary"
                        @click="startSync"
                    >
                        <SvgIcon name="refresh" size="sm" />
                        开始同步
                    </BaseButton>
                    <BaseButton
                        v-if="phase === 'result'"
                        variant="primary"
                        @click="close"
                    >
                        <SvgIcon name="check-circle" size="sm" />
                        完成
                    </BaseButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.sync-dialog-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg) 60%,
        var(--color-primary-50)
    );
}

.sync-dialog-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.sync-dialog-icon svg {
    width: 22px;
    height: 22px;
}

.sync-dialog-header h2,
.sync-dialog-header p {
    margin: 0;
}

.sync-dialog-header h2 {
    font-size: 20px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.sync-dialog-header p {
    margin-top: 4px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
}

.sync-dialog-close {
    display: grid;
    width: 34px;
    height: 34px;
    margin-left: auto;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
    transition: background-color 160ms, color 160ms;
}

.sync-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

/* === 选择平台 === */
.sync-select {
    display: grid;
    gap: 10px;
    padding: 2px 0;
}

.sync-select-summary {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 2px;
    border: 1px solid var(--color-primary-200);
    border-radius: 12px;
    padding: 10px 12px;
    background: color-mix(in srgb, var(--color-primary-50) 72%, var(--color-card-bg));
}

.sync-select-summary-icon {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
}

.sync-select-summary > span:last-child {
    display: grid;
    gap: 1px;
}

.sync-select-summary strong {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.sync-select-summary small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.sync-platform-card {
    display: grid;
    width: 100%;
    grid-template-columns: 38px minmax(0, 1fr) 22px;
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-border);
    min-height: 66px;
    border-radius: 12px;
    padding: 10px 12px;
    text-align: left;
    background: var(--color-card-bg);
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease);
}

.sync-platform-card:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 2px 8px var(--color-focus-ring);
    transform: translateY(-1px);
}

.sync-platform-card.is-selected {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.sync-platform-card.is-disabled {
    opacity: 0.62;
    cursor: not-allowed;
    background: var(--color-surface-subtle);
}

.sync-platform-card.is-disabled:hover {
    border-color: var(--color-border);
    box-shadow: none;
    transform: none;
}

.sync-platform-icon {
    display: grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.sync-platform-main {
    min-width: 0;
    display: grid;
    gap: 2px;
}

.sync-platform-main strong {
    overflow: hidden;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sync-platform-meta {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.sync-platform-dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: var(--color-text-muted);
}

.sync-platform-dot.is-online {
    background: var(--color-success);
}

.sync-platform-check {
    display: grid;
    width: 22px;
    height: 22px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-600);
    color: #fff;
    animation: sync-check-enter 180ms var(--motion-ease) both;
}

@keyframes sync-check-enter {
    from { opacity: 0; transform: scale(0.7); }
    to { opacity: 1; transform: scale(1); }
}

/* === 同步进度 === */
.sync-progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    padding: 40px 20px;
}

.sync-progress-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 800ms linear infinite;
}

.sync-progress-label {
    font-size: 14px;
    font-weight: 700;
    color: var(--color-text-secondary);
}

/* === 同步步骤 Timeline === */
.sync-steps {
    display: flex;
    align-items: stretch;
    gap: 0;
    margin: 0;
    padding: 0;
    list-style: none;
}

.sync-step {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 68px;
}

/* 步骤间连接线 */
.sync-step:not(:last-child)::after {
    position: absolute;
    top: 9px;
    left: calc(50% + 13px);
    width: 40px;
    height: 1px;
    background: var(--color-border);
    content: "";
    transition: background-color 200ms var(--motion-ease);
}

.sync-step.is-completed:not(:last-child)::after,
.sync-step.is-running:not(:last-child)::after {
    background: var(--color-primary-400);
}

.sync-step-icon {
    display: grid;
    width: 19px;
    height: 19px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    color: var(--color-text-muted);
    font-style: normal;
    font-weight: 900;
    font-size: 10px;
    z-index: 1;
    transition:
        background-color 200ms var(--motion-ease),
        color 200ms var(--motion-ease);
}

.sync-step.is-running .sync-step-icon {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.sync-step.is-completed .sync-step-icon {
    background: var(--color-success);
    color: #fff;
}

.sync-step-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    transition: color 200ms var(--motion-ease);
}

.sync-step.is-running .sync-step-label {
    color: var(--color-primary-700);
}

.sync-step.is-completed .sync-step-label {
    color: var(--color-text-secondary);
}

/* === 同步结果 === */
.sync-result {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 32px 20px;
}

.sync-result-icon svg {
    color: var(--color-success);
}

.sync-result-stats {
    display: flex;
    align-items: center;
    gap: 20px;
}

.sync-result-stat {
    display: grid;
    gap: 4px;
    text-align: center;
}

.sync-result-count {
    font-size: 28px;
    font-weight: 900;
    line-height: 1;
}

.sync-result-count.is-success {
    color: var(--color-success);
}

.sync-result-count.is-danger {
    color: var(--color-danger);
}

.sync-result-count.is-muted {
    color: var(--color-text-muted);
}

.sync-result-stat span {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.sync-result-divider {
    width: 1px;
    height: 32px;
    background: var(--color-border);
}

.sync-result-hint {
    margin: 0;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-muted);
}

/* === 底部操作栏 === */
.sync-dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    box-sizing: border-box;
}

.sync-dialog-footer > span {
    color: var(--color-text-muted);
    font-size: 12px;
    font-weight: 700;
}

.sync-dialog-footer > div {
    display: flex;
    gap: 10px;
}

@media (prefers-reduced-motion: reduce) {
    .sync-platform-card,
    .sync-platform-check {
        animation: none;
    }
}
</style>
