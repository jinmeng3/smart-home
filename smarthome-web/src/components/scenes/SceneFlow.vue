<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene, SceneStepStatus } from "../../types/scene";

const props = defineProps<{
    scene: Scene | null;
    stepStatuses: Record<string, SceneStepStatus>;
    running: boolean;
}>();

defineEmits<{
    edit: [];
    preview: [];
    run: [];
}>();

const completedCount = computed(() => {
    if (!props.scene) return 0;
    return props.scene.steps.filter(
        (step) => props.stepStatuses[step.id] === "completed",
    ).length;
});

const failedCount = computed(() => {
    if (!props.scene) return 0;
    return props.scene.steps.filter(
        (step) => props.stepStatuses[step.id] === "failed",
    ).length;
});

const totalSteps = computed(() => props.scene?.steps.length ?? 0);

const isAllCompleted = computed(
    () => props.scene && completedCount.value === totalSteps.value,
);

const resultText = computed(() => {
    if (!props.scene) return "";
    if (failedCount.value > 0) {
        return `已完成 ${completedCount.value}/${totalSteps.value} 个动作 · ${failedCount.value} 步失败`;
    }
    if (isAllCompleted.value) {
        return `已完成 ${totalSteps.value}/${totalSteps.value} 个动作`;
    }
    if (props.running) {
        return `正在执行 ${completedCount.value}/共 ${totalSteps.value} 步操作`;
    }
    return `共 ${totalSteps.value} 步操作`;
});
</script>

<template>
    <section class="scene-flow">
        <header>
            <div>
                <h2>场景流程 / 执行动作</h2>
                <p v-if="scene">触发：{{ scene.triggerLabel }}</p>
            </div>
            <div class="flow-header-actions">
                <button type="button" @click="$emit('edit')">
                    <SvgIcon name="edit" /> 编辑流程
                </button>
                <button
                    :disabled="running || !scene"
                    type="button"
                    @click="$emit('preview')"
                >
                    <SvgIcon name="eye" /> 预览动作链
                </button>
            </div>
        </header>

        <Transition name="scene-crossfade" mode="out-in">
            <div v-if="scene" :key="scene.id" class="scene-flow-body">
                <div class="scene-flow-summary">
                    <span
                        class="scene-flow-icon"
                        :style="{ color: scene.color, background: `color-mix(in srgb, ${scene.color} 16%, transparent)` }"
                    >
                        <SvgIcon :name="scene.icon" />
                    </span>
                    <div>
                        <strong>{{ scene.name }}</strong>
                        <p>{{ scene.description }}</p>
                    </div>
                    <span
                        class="scene-flow-badge"
                        :class="{
                            'is-auto': scene.triggerType !== 'manual',
                            'is-manual': scene.triggerType === 'manual',
                        }"
                    >
                        {{ scene.triggerType === "manual" ? "手动" : "自动化" }}
                    </span>
                </div>

                <div class="scene-flow-steps-wrapper">
                    <ol
                        class="scene-flow-steps"
                        :class="{
                            'is-running': running,
                            'is-completed': isAllCompleted,
                        }"
                    >
                        <li
                            v-for="(step, index) in scene.steps"
                            :key="step.id"
                            :class="`is-${stepStatuses[step.id] ?? 'pending'}`"
                            :style="{ transitionDelay: running ? `${index * 80}ms` : '0ms' }"
                        >
                            <div class="step-node">
                                <span class="step-indicator">
                                    <SvgIcon
                                        :name="
                                            stepStatuses[step.id] === 'completed'
                                                ? 'check-circle'
                                                : stepStatuses[step.id] === 'running'
                                                  ? 'refresh'
                                                  : stepStatuses[step.id] === 'failed'
                                                    ? 'close'
                                                    : 'clock'
                                        "
                                    />
                                </span>
                                <div class="step-content">
                                    <strong>{{ step.name }}</strong>
                                    <p>
                                        {{ step.description }}
                                        <template v-if="stepStatuses[step.id] === 'running'">
                                            · 执行中
                                        </template>
                                    </p>
                                </div>
                                <i
                                    v-if="index < scene.steps.length - 1"
                                    class="step-connector"
                                    aria-hidden="true"
                                />
                            </div>
                            <!-- 失败状态：后端暂无步骤级重试接口，展示提示并支持重新执行场景 -->
                            <div
                                v-if="stepStatuses[step.id] === 'failed'"
                                class="step-error"
                            >
                                <span class="step-error-msg">执行失败</span>
                                <button
                                    class="step-retry-btn"
                                    :disabled="running"
                                    type="button"
                                    @click="$emit('run')"
                                >
                                    <SvgIcon name="refresh" size="sm" />
                                    重新执行场景
                                </button>
                            </div>
                        </li>
                    </ol>
                    <!-- 水平滚动渐隐提示 -->
                    <div class="scroll-fade-right" aria-hidden="true" />
                </div>

                <!-- 执行结果摘要 -->
                <div
                    class="scene-flow-result"
                    :class="{
                        'is-success': isAllCompleted,
                        'is-failed': failedCount > 0,
                        'is-progress': running,
                    }"
                >
                    <span class="result-icon">
                        <SvgIcon
                            :name="
                                isAllCompleted
                                    ? 'check-circle'
                                    : failedCount > 0
                                      ? 'warning'
                                      : 'automation'
                            "
                        />
                    </span>
                    <span class="result-text">{{ resultText }}</span>
                </div>
            </div>
            <div v-else class="scene-flow-empty">请选择场景查看流程</div>
        </Transition>
    </section>
</template>

<style scoped>
.scene-flow {
    display: flex;
    position: relative;
    z-index: 0;
    min-width: 0;
    min-height: 0;
    flex: 1 1 auto;
    flex-direction: column;
    gap: 8px;
    margin-top: 0;
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 10px 12px;
    box-shadow: var(--shadow-card);
}

header,
.flow-header-actions,
.scene-flow-summary,
.scene-flow-steps,
li,
.step-node {
    display: flex;
    align-items: center;
}

.scene-flow-body {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    gap: 8px;
    overflow: hidden;
}

.scene-flow-steps-wrapper {
    position: relative;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

header {
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

h2,
p,
ol {
    margin: 0;
}

h2 {
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

header p,
.scene-flow-summary p,
.step-content p {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 750;
}

header p {
    margin-top: 3px;
}

.flow-header-actions {
    flex: 0 0 auto;
    gap: 8px;
}

button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 30px;
    border: 1px solid var(--color-primary-200);
    border-radius: 7px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

button:hover {
    background: var(--color-primary-50);
    transform: translateY(-1px);
}

button:disabled {
    opacity: 0.55;
    cursor: default;
}

/* === 流程主体 === */


.scene-flow-summary {
    min-width: 0;
    gap: 10px;
}

.scene-flow-icon {
    display: grid;
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    place-items: center;
    border-radius: 999px;
}

.scene-flow-summary div {
    min-width: 0;
    flex: 1;
}

.scene-flow-summary strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.scene-flow-summary p {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.scene-flow-badge {
    flex: 0 0 auto;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 4px 9px;
    color: var(--color-success);
    font-size: 12px;
    font-weight: 900;
}

.scene-flow-badge.is-manual {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.scene-flow-badge.is-auto {
    background: var(--color-success-soft);
    color: var(--color-success);
}

/* === 步骤列表 === */


ol {
    min-width: 0;
    gap: 0;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 2px 2px 4px;
    list-style: none;
    scrollbar-width: thin;
    -ms-overflow-style: none;
    display: flex;
    align-items: center;
}

.scene-flow-steps::-webkit-scrollbar {
    height: 4px;
}

.scene-flow-steps::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border);
}

.scene-flow-steps::-webkit-scrollbar-track {
    background: transparent;
}

li {
    position: relative;
    min-width: 180px;
    flex: 0 0 auto;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    transition:
        opacity 200ms var(--motion-ease),
        transform 200ms var(--motion-ease);
}

.step-node {
    min-width: 0;
    flex: 1 1 0;
    gap: 6px;
    padding: 4px 6px;
    border-radius: 6px;
    transition:
        background-color 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.step-indicator {
    display: grid;
    width: 26px;
    height: 26px;
    flex: 0 0 26px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    color: var(--color-primary-400);
    transition:
        background-color 200ms var(--motion-ease),
        color 200ms var(--motion-ease),
        transform 200ms var(--motion-ease);
}

.step-content {
    min-width: 0;
    flex: 1;
}

.step-content strong {
    display: block;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: color 200ms var(--motion-ease);
}

.step-content p {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* === 连接线 === */
.step-connector {
    position: absolute;
    top: 50%;
    right: -4px;
    width: 16px;
    height: 1px;
    background: var(--color-primary-200);
    transition: background-color 200ms var(--motion-ease);
}

.step-connector::after {
    position: absolute;
    top: -3px;
    right: 0;
    width: 7px;
    height: 7px;
    border-top: 1px solid var(--color-primary-200);
    border-right: 1px solid var(--color-primary-200);
    content: "";
    transform: rotate(45deg);
    transition: border-color 200ms var(--motion-ease);
}

/* === 状态样式 === */

/* pending — 安静 */
.is-pending .step-indicator {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

/* running — 高亮推进 */
.is-running .step-node {
    transform: translateY(-1px);
}

.is-running .step-indicator {
    color: var(--color-info);
    background: var(--color-info-soft);
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-info-soft) 60%, transparent);
}

.is-running .step-indicator svg {
    animation: spin 900ms linear infinite;
}

.is-running .step-content strong {
    color: var(--color-info);
}

.is-running .step-connector {
    background: var(--color-info);
}

.is-running .step-connector::after {
    border-color: var(--color-info);
}

/* completed — 绿色完成 */
.is-completed .step-indicator {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.is-completed .step-content strong {
    color: var(--color-success);
}

.is-completed .step-connector {
    background: var(--color-success);
}

.is-completed .step-connector::after {
    border-color: var(--color-success);
}

/* failed — 红色失败 */
.is-failed .step-indicator {
    color: var(--color-danger);
    background: var(--color-danger-soft);
}

.is-failed .step-content strong {
    color: var(--color-danger);
}

.step-error {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px 6px 46px;
}

.step-error-msg {
    color: var(--color-danger);
    font-size: 12px;
    font-weight: 800;
}

.step-retry-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 26px;
    border: 1px solid var(--color-danger-border);
    border-radius: 6px;
    background: var(--color-danger-soft);
    padding: 0 8px;
    color: var(--color-danger);
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
    transition:
        background-color 140ms var(--motion-ease),
        transform 140ms var(--motion-ease);
}

.step-retry-btn:hover {
    background: var(--color-danger);
    color: var(--color-text-on-primary);
    transform: translateY(-1px);
}

/* === 水平滚动渐隐 === */
.scroll-fade-right {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 32px;
    background: linear-gradient(
        90deg,
        transparent,
        var(--color-card-bg)
    );
    pointer-events: none;
    opacity: 0;
    transition: opacity 200ms var(--motion-ease);
}

.scene-flow-steps-wrapper:hover .scroll-fade-right {
    opacity: 1;
}

/* === 执行结果摘要 === */
.scene-flow-result {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    transition:
        background-color 200ms var(--motion-ease),
        color 200ms var(--motion-ease);
}

.scene-flow-result.is-success {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.scene-flow-result.is-success .result-icon {
    animation: result-glow 400ms var(--motion-ease-out) both;
}

.scene-flow-result.is-failed {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.scene-flow-result.is-progress {
    background: var(--color-info-soft);
    color: var(--color-info);
}

.scene-flow-result .result-icon {
    display: grid;
    width: 18px;
    height: 18px;
    flex: 0 0 18px;
    place-items: center;
}

.result-text {
    min-width: 0;
}

/* === 空状态 === */
.scene-flow-empty {
    display: grid;
    min-height: 80px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 800;
    font-size: 13px;
}

/* === 过渡动画 === */
.scene-crossfade-enter-active,
.scene-crossfade-leave-active {
    transition:
        opacity 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.scene-crossfade-enter-from,
.scene-crossfade-leave-to {
    opacity: 0;
    transform: translateY(8px);
animation: spin 900ms linear infinite;
}

@keyframes result-glow {
    0% {
        transform: scale(0.8);
        opacity: 0.5;
    }
    50% {
        transform: scale(1.15);
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

/* === 响应式 === */
@media (max-width: 980px) {
    .scene-flow-steps {
        overflow-x: auto;
    }

    li {
        min-width: 160px;
    }

    .scroll-fade-right {
        width: 24px;
    }
}

@media (max-width: 860px) {
    header {
        align-items: flex-start;
        flex-direction: column;
    }
}

@media (prefers-reduced-motion: reduce) {
    button,
    li,
    .scene-crossfade-enter-active,
    .scene-crossfade-leave-active {
        transition-duration: 1ms;
    }

    button:hover,
    .is-running {
        transform: none;
    }

    .scene-flow-result.is-success .result-icon {
        animation: none;
    }
}
</style>