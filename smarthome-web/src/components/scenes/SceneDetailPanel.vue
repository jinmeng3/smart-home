<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene } from "../../types/scene";

defineProps<{
    scene: Scene | null;
    running: boolean;
}>();

defineEmits<{
    run: [scene: Scene];
    edit: [scene: Scene];
    copy: [scene: Scene];
    action: [key: "batch" | "schedule" | "sort" | "logs"];
    template: [name: string];
}>();

const templates = [
    { name: "浪漫晚餐模式", count: 6, icon: "light" },
    { name: "聚会模式", count: 7, icon: "group" },
    { name: "学习模式", count: 5, icon: "room" },
    { name: "午休模式", count: 4, icon: "clock" },
];

const actions = [
    { key: "batch", label: "批量启用", note: "启用多个场景", icon: "check-circle" },
    { key: "schedule", label: "定时设置", note: "统一定时管理", icon: "calendar" },
    { key: "sort", label: "场景排序", note: "自定义排序", icon: "layers" },
    { key: "logs", label: "查看日志", note: "执行记录与日志", icon: "log" },
] as const;
</script>

<template>
    <aside class="scene-detail-panel">
        <Transition name="scene-detail-crossfade" mode="out-in">
            <section v-if="scene" :key="scene.id" class="scene-panel-card">
                <header class="scene-panel-title">
                    <h2><SvgIcon name="device-management" /> 场景详情</h2>
                    <button type="button" title="刷新详情"><SvgIcon name="refresh" /></button>
                </header>

                <div class="scene-detail-head">
                    <span :style="{ color: scene.color }"><SvgIcon :name="scene.icon" /></span>
                    <div>
                        <h3>{{ scene.name }}</h3>
                        <p>{{ scene.description }}</p>
                    </div>
                    <strong>{{ scene.enabled ? "已启用" : "已停用" }}</strong>
                </div>

                <dl>
                    <div><dt>触发条件</dt><dd>{{ scene.triggerLabel }}</dd></div>
                    <div><dt>执行方式</dt><dd>{{ scene.triggerType === "manual" ? "手动执行" : "自动执行" }}</dd></div>
                    <div><dt>关联房间</dt><dd>玄关、客厅、餐厅、主卧</dd></div>
                    <div><dt>关联设备</dt><dd>{{ scene.deviceCount }} 个设备</dd></div>
                    <div><dt>创建时间</dt><dd>{{ scene.createdAt }}</dd></div>
                    <div><dt>更新时间</dt><dd>{{ scene.updatedAt }}</dd></div>
                </dl>

                <div class="scene-detail-actions">
                    <button class="is-primary" :disabled="running" type="button" @click="$emit('run', scene)">
                        <SvgIcon name="power" /> 执行
                    </button>
                    <button type="button" @click="$emit('edit', scene)">
                        <SvgIcon name="edit" /> 编辑
                    </button>
                    <button type="button" @click="$emit('copy', scene)">
                        <SvgIcon name="layers" /> 复制
                    </button>
                </div>
            </section>
            <section v-else class="scene-panel-card scene-panel-empty">
                请选择场景
            </section>
        </Transition>

        <section class="scene-panel-card">
            <header class="scene-panel-title">
                <h2><SvgIcon name="device-management" /> 快捷操作</h2>
            </header>
            <div class="scene-quick-actions">
                <button
                    v-for="item in actions"
                    :key="item.key"
                    type="button"
                    @click="$emit('action', item.key)"
                >
                    <SvgIcon :name="item.icon" />
                    <span>
                        <strong>{{ item.label }}</strong>
                        <small>{{ item.note }}</small>
                    </span>
                </button>
            </div>
        </section>

        <section class="scene-panel-card">
            <header class="scene-panel-title">
                <h2><SvgIcon name="device-management" /> 推荐模板</h2>
                <button type="button" title="更多模板">更多 <SvgIcon name="chevron-right" /></button>
            </header>
            <div class="scene-template-list">
                <button
                    v-for="item in templates"
                    :key="item.name"
                    type="button"
                    @click="$emit('template', item.name)"
                >
                    <span class="scene-template-icon"><SvgIcon :name="item.icon" /></span>
                    <span>
                        <strong>{{ item.name }}</strong>
                        <small>{{ item.count }} 个设备</small>
                    </span>
                    <em>使用</em>
                </button>
            </div>
        </section>
    </aside>
</template>

<style scoped>
.scene-detail-panel {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    border-left: 1px solid var(--color-border);
    background: var(--color-sidebar-bg);
    padding: 0 4px 0 12px;
}

.scene-panel-card {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
    box-shadow: var(--shadow-card);
}

.scene-panel-title,
.scene-detail-head,
.scene-detail-actions,
.scene-quick-actions,
.scene-template-list button {
    display: flex;
    align-items: center;
}

.scene-panel-title {
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
}

.scene-panel-title h2 {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin: 0;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

.scene-panel-title button {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}

.scene-detail-head {
    gap: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
}

.scene-detail-head > span {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.scene-detail-head div {
    min-width: 0;
    flex: 1;
}

h3,
p,
dl {
    margin: 0;
}

h3 {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
}

p {
    margin-top: 4px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 750;
}

.scene-detail-head > strong {
    flex: 0 0 auto;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 4px 9px;
    color: var(--color-success);
    font-size: 12px;
    font-weight: 900;
}

dl {
    display: grid;
    gap: 10px;
    padding: 13px 0;
}

dl > div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

dt {
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

dd {
    min-width: 0;
    margin: 0;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    text-align: right;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.scene-detail-actions {
    display: grid;
    width: 100%;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
}

.scene-detail-actions button,
.scene-quick-actions button,
.scene-template-list button {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.scene-detail-actions button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-width: 0;
    gap: 6px;
    height: 36px;
    font-size: 12px;
    font-weight: 900;
}

.scene-detail-actions .is-primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.scene-quick-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
}

.scene-quick-actions button {
    justify-content: flex-start;
    gap: 9px;
    min-height: 58px;
    padding: 8px 10px;
    text-align: left;
}

.scene-quick-actions svg {
    flex: 0 0 auto;
    color: var(--color-primary-600);
}

.scene-quick-actions span,
.scene-template-list button > span:nth-child(2) {
    display: grid;
    min-width: 0;
}

.scene-quick-actions strong,
.scene-template-list strong {
    color: var(--color-text-primary);
    font-size: 12px;
    font-weight: 900;
}

.scene-quick-actions small,
.scene-template-list small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 750;
}

.scene-template-list {
    display: grid;
    gap: 0;
}

.scene-template-list button {
    justify-content: space-between;
    gap: 9px;
    min-height: 52px;
    border-width: 0 0 1px;
    border-radius: 0;
    padding: 8px 0;
    text-align: left;
}

.scene-template-list button:last-child {
    border-bottom: 0;
}

.scene-template-icon {
    display: grid;
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.scene-template-list em {
    flex: 0 0 auto;
    border: 1px solid var(--color-primary-200);
    border-radius: 7px;
    background: var(--color-primary-50);
    padding: 5px 9px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-style: normal;
    font-weight: 900;
}

button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: translateY(-1px);
}

button:disabled {
    opacity: 0.55;
}

.scene-panel-empty {
    display: grid;
    min-height: 180px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 800;
}

.scene-detail-crossfade-enter-active,
.scene-detail-crossfade-leave-active {
    transition:
        opacity 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.scene-detail-crossfade-enter-from,
.scene-detail-crossfade-leave-to {
    opacity: 0;
    transform: translateY(8px);
}

@media (prefers-reduced-motion: reduce) {
    button,
    .scene-detail-crossfade-enter-active,
    .scene-detail-crossfade-leave-active {
        transition-duration: 1ms;
    }

    button:hover,
    .scene-detail-crossfade-enter-from,
    .scene-detail-crossfade-leave-to {
        transform: none;
    }
}
</style>
