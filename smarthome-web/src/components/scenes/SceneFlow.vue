<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene, SceneStepStatus } from "../../types/scene";

defineProps<{
    scene: Scene | null;
    stepStatuses: Record<string, SceneStepStatus>;
    running: boolean;
}>();

defineEmits<{
    edit: [];
    preview: [];
}>();
</script>

<template>
    <section class="scene-flow">
        <header>
            <div>
                <h2>场景流程 / 执行动作</h2>
                <p v-if="scene">触发：{{ scene.triggerLabel }}</p>
            </div>
            <div>
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
                        :style="{ color: scene.color }"
                    >
                        <SvgIcon :name="scene.icon" />
                    </span>
                    <div>
                        <strong>{{ scene.name }}</strong>
                        <p>{{ scene.description }}</p>
                    </div>
                    <span class="scene-flow-badge">{{
                        scene.triggerType === "manual" ? "手动" : "自动化"
                    }}</span>
                </div>

                <ol>
                    <li
                        v-for="(step, index) in scene.steps"
                        :key="step.id"
                        :class="`is-${stepStatuses[step.id] ?? 'pending'}`"
                    >
                        <span class="scene-step-icon">
                            <SvgIcon
                                :name="
                                    stepStatuses[step.id] === 'completed'
                                        ? 'check-circle'
                                        : stepStatuses[step.id] === 'running'
                                          ? 'refresh'
                                          : 'device-management'
                                "
                            />
                        </span>
                        <div>
                            <strong>{{ step.name }}</strong>
                            <p>{{ step.description }}</p>
                        </div>
                        <i
                            v-if="index < scene.steps.length - 1"
                            aria-hidden="true"
                        />
                    </li>
                </ol>
                <small>共 {{ scene.steps.length }} 步操作</small>
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
    flex-direction: column;
    gap: 12px;
    margin-top: 6px;
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 16px;
    box-shadow: var(--shadow-card);
}

header,
header > div:last-child,
.scene-flow-summary,
ol,
li {
    display: flex;
    align-items: center;
}

header {
    justify-content: space-between;
    gap: 12px;
}

h2,
p,
ol {
    margin: 0;
}

h2 {
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 900;
}

header p,
.scene-flow-summary p,
li p {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 750;
}

header p {
    margin-top: 3px;
}

header > div:last-child {
    flex: 0 0 auto;
    gap: 8px;
}

button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 36px;
    border: 1px solid var(--color-primary-200);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 12px;
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
}

.scene-flow-body {
    display: grid;
    min-width: 0;
    gap: 16px;
}

.scene-flow-summary {
    min-width: 0;
    gap: 12px;
}

.scene-flow-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
}

.scene-flow-summary div {
    min-width: 0;
    flex: 1;
}

.scene-flow-summary strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 15px;
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

ol {
    min-width: 0;
    gap: 12px;
    overflow: hidden;
    padding: 0 2px;
    list-style: none;
}

li {
    position: relative;
    min-width: 0;
    flex: 1 1 0;
    gap: 8px;
    transition:
        opacity 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.scene-step-icon {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

li div {
    min-width: 0;
    flex: 1;
}

li strong {
    display: block;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

li p {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

li i {
    position: absolute;
    top: 16px;
    right: -4px;
    width: 20px;
    height: 1px;
    background: var(--color-primary-300);
}

li i::after {
    position: absolute;
    top: -3px;
    right: 0;
    width: 7px;
    height: 7px;
    border-top: 1px solid var(--color-primary-300);
    border-right: 1px solid var(--color-primary-300);
    content: "";
    transform: rotate(45deg);
}

.is-running {
    transform: translateY(-2px);
}

.is-running .scene-step-icon {
    color: var(--color-info);
    background: var(--color-info-soft);
}

.is-running .scene-step-icon svg {
    animation: scene-flow-spin 900ms linear infinite;
}

.is-completed .scene-step-icon {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.scene-flow-body > small {
    justify-self: center;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
}

.scene-flow-empty {
    display: grid;
    min-height: 160px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 800;
}

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
}

@keyframes scene-flow-spin {
    to {
        transform: rotate(360deg);
    }
}

@media (max-width: 980px) {
    ol {
        overflow-x: auto;
    }

    li {
        min-width: 150px;
        flex-basis: 150px;
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
}
</style>
