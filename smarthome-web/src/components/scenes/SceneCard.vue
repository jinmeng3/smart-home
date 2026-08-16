<script setup lang="ts">
import { ref } from "vue";
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

const moreMenuOpen = ref(false);

const toggleMoreMenu = () => {
    moreMenuOpen.value = !moreMenuOpen.value;
};

const closeMoreMenu = () => {
    moreMenuOpen.value = false;
};
</script>

<template>
    <article
        class="scene-card"
        :class="{
            'is-selected': selected,
            'is-disabled': !scene.enabled,
            'is-running': running,
        }"
        :style="{
            animationDelay: `${delay}ms`,
            '--scene-color': scene.color,
        }"
        role="button"
        tabindex="0"
        @click="$emit('select', scene)"
        @keydown.enter="$emit('select', scene)"
        @keydown.escape="closeMoreMenu"
    >
        <!-- 第一层：图标 + 名称 + 标签 -->
        <div class="scene-card-layer layer-top">
            <span class="scene-icon" :style="{ background: `color-mix(in srgb, ${scene.color} 16%, transparent)`, color: scene.color }">
                <SvgIcon :name="scene.icon" />
            </span>
            <div class="scene-title-group">
                <div class="scene-name-row">
                    <h3>{{ scene.name }}</h3>
                    <span class="scene-tag" :class="{ 'is-manual': scene.triggerType === 'manual' }">
                        {{ triggerText[scene.triggerType] }}
                    </span>
                    <span v-if="scene.recommended" class="scene-tag is-recommended">推荐</span>
                </div>
            </div>
        </div>

        <!-- 第二层：描述 + 关联设备数 + 触发方式 -->
        <div class="scene-card-layer layer-middle">
            <p class="scene-desc">{{ scene.description }}</p>
            <div class="scene-meta">
                <span class="scene-meta-item">
                    <SvgIcon name="device-management" size="sm" />
                    {{ scene.deviceCount }} 个设备
                </span>
                <span class="scene-meta-divider" aria-hidden="true"></span>
                <span class="scene-meta-item">
                    <SvgIcon name="clock" size="sm" />
                    {{ triggerShortText[scene.triggerType] }}
                </span>
            </div>
        </div>

        <!-- 第三层：执行按钮 + 启用状态 + 更多操作 -->
        <div class="scene-card-layer layer-bottom">
            <button
                class="scene-run-button"
                :disabled="running"
                type="button"
                @click.stop="$emit('run', scene)"
            >
                <SvgIcon name="automation" :class="{ 'is-spinning': running }" />
                {{ running ? "执行中" : "执行" }}
            </button>
            <div class="scene-bottom-actions">
                <label class="scene-enabled-control" @click.stop>
                    <span class="enabled-text" :class="{ 'is-off': !scene.enabled }">
                        {{ scene.enabled ? "已启用" : "已停用" }}
                    </span>
                    <BaseSwitch
                        :model-value="scene.enabled"
                        small
                        @update:model-value="updateEnabled"
                    />
                </label>
                <div class="scene-more-wrapper" @click.stop>
                    <button
                        class="scene-more-trigger"
                        type="button"
                        title="更多操作"
                        @click="toggleMoreMenu"
                    >
                        <SvgIcon name="more" />
                    </button>
                    <Transition name="more-menu">
                        <div
                            v-if="moreMenuOpen"
                            class="scene-more-menu"
                            @click.stop
                        >
                            <button type="button" @click="emit('edit', scene); closeMoreMenu()">
                                <SvgIcon name="edit" size="sm" /> 编辑
                            </button>
                            <button type="button" @click="emit('copy', scene); closeMoreMenu()">
                                <SvgIcon name="layers" size="sm" /> 复制
                            </button>
                            <hr class="more-menu-divider" />
                            <button
                                class="is-danger"
                                type="button"
                                @click="emit('remove', scene); closeMoreMenu()"
                            >
                                <SvgIcon name="delete" size="sm" /> 删除
                            </button>
                        </div>
                    </Transition>
                </div>
            </div>
        </div>
    </article>
</template>

<style scoped>
.scene-card {
    --scene-color: var(--color-primary-600);

    display: grid;
    min-width: 0;
    gap: 0;
    min-height: 120px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    animation: scene-card-enter 260ms var(--motion-ease) both;
    transition:
        transform 180ms var(--motion-ease),
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease),
        opacity 180ms var(--motion-ease);
    overflow: hidden;
    position: relative;
}

/* 顶部渐变条 — 使用场景颜色 */
.scene-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(
        90deg,
        color-mix(in srgb, var(--scene-color) 60%, transparent),
        color-mix(in srgb, var(--scene-color) 30%, transparent)
    );
    opacity: 0.7;
    transition: opacity 180ms var(--motion-ease);
}

.scene-card:hover::before,
.scene-card.is-selected::before {
    opacity: 1;
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
    box-shadow:
        0 0 0 3px var(--color-focus-ring),
        var(--shadow-card);
}

.scene-card.is-disabled {
    opacity: 0.72;
}

.scene-card.is-disabled .scene-desc,
.scene-card.is-disabled .scene-meta-item {
    opacity: 0.6;
}

.scene-card.is-disabled .scene-icon {
    opacity: 0.5;
}

/* === 三层布局 === */
.scene-card-layer {
    padding: 8px 12px 0 12px;
}

.layer-top {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-top: 10px;
}

.layer-middle {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.layer-bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 12px 10px 12px;
    border-top: 1px solid var(--color-border-subtle);
    margin-top: 6px;
}

/* === 图标 === */
.scene-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 999px;
    transition: opacity 180ms var(--motion-ease);
}

/* === 标题区域 === */
.scene-title-group {
    min-width: 0;
    flex: 1;
}

.scene-name-row {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 6px;
}

h3 {
    min-width: 0;
    margin: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.scene-tag {
    flex: 0 0 auto;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 3px 8px;
    color: var(--color-success);
    font-size: 12px;
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

/* === 底部状态与操作 === */
.scene-bottom-actions {
    display: flex;
    min-width: 0;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
}

.scene-enabled-control {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    white-space: nowrap;
}

.enabled-text {
    color: var(--color-success);
    font-size: 12px;
    font-weight: 800;
    transition: color 180ms var(--motion-ease);
}

.enabled-text.is-off {
    color: var(--color-text-tertiary);
}

/* === 描述 === */
.scene-desc {
    margin: 0;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: opacity 180ms var(--motion-ease);
}

/* === 元信息行 === */
.scene-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.scene-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    transition: opacity 180ms var(--motion-ease);
}

.scene-meta-divider {
    width: 3px;
    height: 3px;
    border-radius: 999px;
    background: var(--color-border);
    flex: 0 0 auto;
}

/* === 执行按钮 === */
.scene-run-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    min-width: 80px;
    height: 30px;
    border: 1px solid var(--color-primary-200);
    border-radius: 7px;
    background: var(--color-primary-50);
    padding: 0 14px;
    color: var(--color-primary-700);
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        opacity 160ms var(--motion-ease);
}

.scene-run-button:not(:disabled):hover {
    border-color: var(--color-primary-500);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    transform: translateY(-1px);
}

.scene-run-button:disabled {
    cursor: default;
    opacity: 0.65;
}

.scene-run-button:disabled .is-spinning {
    animation: scene-spin 900ms linear infinite;
}

/* === 更多菜单 === */
.scene-more-wrapper {
    position: relative;
    flex: 0 0 auto;
}

.scene-more-trigger {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border-radius: 6px;
    color: var(--color-text-tertiary);
    transition:
        background-color 140ms var(--motion-ease),
        color 140ms var(--motion-ease);
}

.scene-more-trigger:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-secondary);
}

.scene-more-menu {
    position: absolute;
    right: 0;
    bottom: calc(100% + 4px);
    z-index: 20;
    min-width: 140px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 4px;
    box-shadow: var(--shadow-card-hover);
}

.scene-more-menu button {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    padding: 8px 10px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    text-align: left;
    cursor: pointer;
    transition:
        background-color 140ms var(--motion-ease),
        color 140ms var(--motion-ease);
}

.scene-more-menu button:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.scene-more-menu button.is-danger:hover {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.more-menu-divider {
    margin: 4px 8px;
    border: 0;
    border-top: 1px solid var(--color-border-subtle);
}

/* === 更多菜单动画 === */
.more-menu-enter-active,
.more-menu-leave-active {
    transition:
        opacity 140ms var(--motion-ease),
        transform 140ms var(--motion-ease);
}

.more-menu-enter-from,
.more-menu-leave-to {
    opacity: 0;
    transform: translateY(4px) scale(0.96);
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
    .scene-meta {
        gap: 6px;
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

    .more-menu-enter-active,
    .more-menu-leave-active {
        transition-duration: 1ms;
    }
}
</style>
