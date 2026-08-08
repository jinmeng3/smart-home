<script setup lang="ts">
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene } from "../../types/scene";

const props = defineProps<{
    scene: Scene;
    selected: boolean;
    running: boolean;
    delay: number;
}>();

const emit = defineEmits<{
    select: [scene: Scene];
    toggle: [scene: Scene, enabled: boolean];
    run: [scene: Scene];
    edit: [scene: Scene];
    copy: [scene: Scene];
    remove: [scene: Scene];
}>();

const triggerText: Record<Scene["triggerType"], string> = {
    manual: "手动",
    schedule: "自动化",
    location: "自动化",
    device: "自动化",
};

const triggerShortText: Record<Scene["triggerType"], string> = {
    manual: "手动执行",
    schedule: "定时触发",
    location: "位置触发",
    device: "设备触发",
};

const updateEnabled = (enabled: boolean) => {
    emit("toggle", props.scene, enabled);
};
</script>

<template>
    <article
        class="scene-card"
        :class="{ 'is-selected': selected, 'is-disabled': !scene.enabled }"
        :style="{ animationDelay: `${delay}ms` }"
        role="button"
        tabindex="0"
        @click="$emit('select', scene)"
        @keydown.enter="$emit('select', scene)"
    >
        <header>
            <span class="scene-icon" :style="{ color: scene.color }">
                <SvgIcon :name="scene.icon" />
            </span>
            <div class="scene-title">
                <div>
                    <h3>{{ scene.name }}</h3>
                    <span class="scene-tag" :class="{ 'is-manual': scene.triggerType === 'manual' }">
                        {{ triggerText[scene.triggerType] }}
                    </span>
                    <span v-if="scene.recommended" class="scene-tag is-recommended">推荐</span>
                </div>
                <p>{{ scene.description }}</p>
            </div>
            <button class="scene-more" type="button" title="更多操作" @click.stop="$emit('edit', scene)">
                <SvgIcon name="more" />
            </button>
        </header>

        <dl>
            <div>
                <dt>关联设备</dt>
                <dd>{{ scene.deviceCount }} 个</dd>
            </div>
            <div>
                <dt>触发方式</dt>
                <dd>{{ triggerShortText[scene.triggerType] }}</dd>
            </div>
        </dl>

        <footer>
            <button
                class="scene-run-button"
                :disabled="running"
                type="button"
                @click.stop="$emit('run', scene)"
            >
                <SvgIcon name="automation" />
                {{ running ? "执行中" : "执行" }}
            </button>
            <div class="scene-footer-actions" @click.stop>
                <label class="scene-enabled-control">
                    <span>{{ scene.enabled ? "已启用" : "已停用" }}</span>
                    <BaseSwitch
                        :model-value="scene.enabled"
                        small
                        @update:model-value="updateEnabled"
                    />
                </label>
                <button
                    class="scene-delete-button"
                    type="button"
                    title="删除场景"
                    @click="$emit('remove', scene)"
                >
                    <SvgIcon name="delete" size="sm" />
                </button>
            </div>
        </footer>
    </article>
</template>

<style scoped>
.scene-card {
    display: grid;
    min-width: 0;
    gap: 11px;
    min-height: 150px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    animation: scene-card-enter 260ms var(--motion-ease) both;
    transition:
        transform 180ms var(--motion-ease),
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease),
        opacity 180ms var(--motion-ease);
}

.scene-card:hover,
.scene-card:focus-visible {
    border-color: var(--color-primary-200);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
    outline: none;
}

.scene-card.is-selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring), var(--shadow-card);
}

.scene-card.is-disabled {
    opacity: 0.72;
}

header,
.scene-title > div,
dl,
footer {
    display: flex;
    align-items: center;
}

header {
    min-width: 0;
    gap: 11px;
}

.scene-icon {
    display: grid;
    width: 46px;
    height: 46px;
    flex: 0 0 46px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.scene-title {
    min-width: 0;
    flex: 1;
}

.scene-title > div {
    min-width: 0;
    gap: 6px;
}

h3,
p,
dl {
    margin: 0;
}

h3 {
    min-width: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

p {
    margin-top: 5px;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.scene-tag {
    flex: 0 0 auto;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 3px 7px;
    color: var(--color-success);
    font-size: 11px;
    font-weight: 900;
}

.scene-tag.is-manual {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.scene-tag.is-recommended {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.scene-more {
    display: grid;
    width: 28px;
    height: 28px;
    flex: 0 0 28px;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
}

.scene-more:hover {
    background: var(--color-surface-hover);
}

dl {
    min-width: 0;
    gap: 22px;
}

dl > div {
    display: flex;
    min-width: 0;
    align-items: center;
}

dt {
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

dd {
    min-width: 0;
    margin: 0 0 0 6px;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

footer {
    justify-content: space-between;
    gap: 10px;
    padding-top: 2px;
}

.scene-run-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-width: 92px;
    height: 36px;
    border: 1px solid var(--color-primary-200);
    border-radius: 8px;
    background: var(--color-primary-50);
    padding: 0 12px;
    color: var(--color-primary-700);
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.scene-footer-actions,
.scene-enabled-control {
    display: flex;
    align-items: center;
}

.scene-footer-actions {
    min-width: 0;
    gap: 10px;
}

.scene-enabled-control {
    gap: 7px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 800;
    cursor: pointer;
    white-space: nowrap;
}

.scene-run-button:not(:disabled):hover {
    border-color: var(--color-primary-500);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    transform: translateY(-1px);
}

.scene-run-button:disabled svg {
    animation: scene-spin 900ms linear infinite;
}

.scene-delete-button {
    display: grid;
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    place-items: center;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    color: var(--color-text-tertiary);
    transition: color 160ms, border-color 160ms, background-color 160ms;
}

.scene-delete-button:hover {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.scene-delete-button svg {
    transition: transform 160ms var(--motion-ease);
}

.scene-delete-button:hover svg {
    transform: rotate(90deg);
}

button:disabled {
    cursor: default;
    opacity: 0.55;
}

@keyframes scene-card-enter {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes scene-spin {
    to { transform: rotate(360deg); }
}

@media (max-width: 1380px) {
    dl {
        gap: 14px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .scene-card,
    button {
        animation-duration: 1ms;
        animation-delay: 0ms !important;
        transition-duration: 1ms;
    }

    .scene-card:hover,
    .scene-run-button:not(:disabled):hover {
        transform: none;
    }
}
</style>
