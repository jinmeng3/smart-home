<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { fetchSceneTemplates } from "../../api/scenes";
import type { Scene, SceneTemplate } from "../../types/scene";

const props = defineProps<{
    scene: Scene | null;
    running: boolean;
}>();

defineEmits<{
    run: [scene: Scene];
    edit: [scene: Scene];
    copy: [scene: Scene];
    remove: [scene: Scene];
    action: [key: "logs" | "schedule"];
    template: [name: string];
    viewAllTemplates: [];
}>();

const triggerIcon = computed(() => {
    const type = props.scene?.triggerType;
    if (type === "schedule") return "calendar";
    if (type === "location") return "location";
    if (type === "device") return "device-management";
    return "automation";
});

const executionText = computed(() =>
    props.scene?.triggerType === "manual" ? "手动执行" : "自动执行",
);

const detailRows = computed(() => {
    const scene = props.scene;
    if (!scene) return [];

    return [
        {
            icon: triggerIcon.value,
            label: "触发条件",
            value: scene.triggerLabel || "—",
        },
        {
            icon: "automation",
            label: "执行方式",
            value: executionText.value,
            chip: true,
        },
        {
            icon: "device-management",
            label: "关联设备",
            value: `${scene.deviceCount} 个设备`,
        },
    ];
});

const templates = ref<SceneTemplate[]>([]);

onMounted(async () => {
    try {
        const all = await fetchSceneTemplates("", "");
        templates.value = all.filter((t) => t.recommended).slice(0, 4);
        if (!templates.value.length) templates.value = all.slice(0, 4);
    } catch {
        templates.value = [];
    }
});

const displayedTemplates = computed(() => templates.value.slice(0, 2));
const hasMoreTemplates = computed(() => templates.value.length > 2);

const manageActions = [
    { key: "edit", label: "编辑", icon: "edit", danger: false },
    { key: "logs", label: "执行日志", icon: "log", danger: false },
    { key: "schedule", label: "定时管理", icon: "calendar", danger: false },
    { key: "copy", label: "复制", icon: "layers", danger: false },
    { key: "remove", label: "删除", icon: "delete", danger: true },
] as const;
</script>

<template>
    <aside class="scene-detail-panel">
        <Transition name="scene-detail-crossfade" mode="out-in">
            <div v-if="scene" :key="scene.id" class="scene-detail-wrapper">
                <!-- 第一部分：当前场景（吸顶） -->
                <section class="scene-panel-card scene-detail-sticky">
                    <div class="scene-detail-head">
                        <span class="scene-detail-icon" :style="{ color: scene.color, background: `color-mix(in srgb, ${scene.color} 16%, transparent)` }">
                            <SvgIcon :name="scene.icon" />
                        </span>
                        <div class="scene-detail-title">
                            <div class="scene-detail-name-row">
                                <h3>{{ scene.name }}</h3>
                                <span
                                    class="scene-detail-badge"
                                    :class="{ 'is-off': !scene.enabled }"
                                >
                                    <SvgIcon :name="scene.enabled ? 'check-circle' : 'clock'" size="sm" />
                                    {{ scene.enabled ? "已启用" : "已停用" }}
                                </span>
                            </div>
                            <p class="scene-detail-desc">{{ scene.description }}</p>
                        </div>
                    </div>

                    <dl class="scene-detail-info">
                        <div v-for="row in detailRows" :key="row.label" class="info-row">
                            <span class="info-icon"><SvgIcon :name="row.icon" size="sm" /></span>
                            <span class="info-label">{{ row.label }}</span>
                            <span class="info-value">
                                <em
                                    v-if="row.chip"
                                    class="exec-chip"
                                    :class="
                                        scene.triggerType === 'manual'
                                            ? 'is-manual'
                                            : 'is-auto'
                                    "
                                >
                                    {{ row.value }}
                                </em>
                                <template v-else>{{ row.value }}</template>
                            </span>
                        </div>
                    </dl>

                    <button
                        class="scene-execute-button"
                        :disabled="running"
                        type="button"
                        @click="$emit('run', scene)"
                    >
                        <SvgIcon name="power" :class="{ 'is-spinning': running }" />
                        {{ running ? "执行中..." : "立即执行" }}
                    </button>
                </section>

                <!-- 第二部分：场景管理 -->
                <section class="scene-panel-card">
                    <header class="scene-panel-title">
                        <h2><SvgIcon name="device-management" size="sm" /> 场景管理</h2>
                    </header>
                    <div class="scene-manage-actions">
                        <button
                            v-for="item in manageActions"
                            :key="item.key"
                            type="button"
                            :class="{ 'is-danger': item.danger }"
                            @click="
                                item.key === 'edit'
                                    ? $emit('edit', scene)
                                    : item.key === 'copy'
                                      ? $emit('copy', scene)
                                      : item.key === 'remove'
                                        ? $emit('remove', scene)
                                        : $emit('action', item.key as any)
                            "
                        >
                            <SvgIcon :name="item.icon" />
                            <span>{{ item.label }}</span>
                        </button>
                    </div>
                </section>

                <!-- 第三部分：推荐模板 -->
                <section class="scene-panel-card">
                    <header class="scene-panel-title">
                        <h2><SvgIcon name="device-management" size="sm" /> 推荐模板</h2>
                        <button
                            v-if="hasMoreTemplates"
                            type="button"
                            @click="$emit('viewAllTemplates')"
                        >
                            查看全部 <SvgIcon name="chevron-right" size="sm" />
                        </button>
                    </header>
                    <div class="scene-template-list">
                        <button
                            v-for="item in displayedTemplates"
                            :key="item.id"
                            type="button"
                            @click="$emit('template', item.name)"
                        >
                            <span class="scene-template-icon"
                                ><SvgIcon :name="item.icon"
                            /></span>
                            <span>
                                <strong>{{ item.name }}</strong>
                                <small>{{ item.deviceCount }} 个设备</small>
                            </span>
                            <em>使用</em>
                        </button>
                        <p v-if="!templates.length" class="template-empty">暂无推荐模板</p>
                    </div>
                </section>
            </div>

            <!-- 空状态 -->
            <section v-else class="scene-panel-card scene-panel-empty">
                <div class="empty-state">
                    <SvgIcon name="device-management" />
                    <p>选择一个场景</p>
                    <small>查看配置和执行信息</small>
                </div>
            </section>
        </Transition>
    </aside>
</template>

<style scoped>
.scene-detail-panel {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 10px;
    overflow-y: auto;
    border-left: 1px solid var(--color-border);
    background: var(--color-sidebar-bg);
    padding: 0 4px 0 12px;
    scrollbar-gutter: stable;
}

.scene-detail-wrapper {
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 0;
}

.scene-panel-card {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
    box-shadow: var(--shadow-card);
}

/* === 吸顶 === */
.scene-detail-sticky {
    position: sticky;
    top: 0;
    z-index: 2;
}

.scene-panel-title,
.scene-detail-head,
.scene-manage-actions {
    display: flex;
    align-items: center;
}

.scene-panel-title {
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.scene-panel-title h2 {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.scene-panel-title button {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}

/* ═══ 第一部分：当前场景 ═══ */

.scene-detail-head {
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0 10px;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--color-border);
}

.scene-detail-icon {
    display: grid;
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    place-items: center;
    border-radius: 12px;
    box-shadow: inset 0 0 0 1px var(--color-primary-100);
}

.scene-detail-title {
    min-width: 0;
    flex: 1;
}

.scene-detail-name-row {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 6px;
}

.scene-detail-name-row h3 {
    min-width: 0;
    margin: 0;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.scene-detail-badge {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 3px;
    border: 1px solid var(--color-success-border);
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 2px 8px;
    color: var(--color-success);
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
}

.scene-detail-badge.is-off {
    border-color: var(--color-border-default);
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.scene-detail-desc {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    margin: 6px 0 0;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 650;
    line-height: 1.5;
}

.scene-detail-info {
    display: grid;
    gap: 0;
    margin: 0;
    padding: 4px 0 8px;
}

.info-row {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 10px;
    padding: 8px 2px;
    border-bottom: 1px dashed var(--color-border);
}

.info-row:last-child {
    border-bottom: 0;
}

.info-icon {
    display: grid;
    width: 28px;
    height: 28px;
    flex: 0 0 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.info-label {
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

.info-value {
    min-width: 0;
    margin: 0 0 0 auto;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    text-align: right;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.exec-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: 1px solid transparent;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
    white-space: nowrap;
}

.exec-chip.is-manual {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.exec-chip.is-auto {
    border-color: var(--color-success-border);
    background: var(--color-success-soft);
    color: var(--color-success);
}

/* 执行按钮 */
.scene-execute-button {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: 40px;
    border: 0;
    border-radius: 10px;
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--color-primary-600) 92%, #fff),
        var(--color-primary-600)
    );
    color: var(--color-text-on-primary);
    font-size: 14px;
    font-weight: 900;
    cursor: pointer;
    transition:
        transform 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        opacity 160ms var(--motion-ease);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary-600) 24%, transparent);
}

.scene-execute-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px color-mix(in srgb, var(--color-primary-600) 32%, transparent);
}

.scene-execute-button:disabled {
    opacity: 0.6;
    cursor: default;
}

.scene-execute-button:disabled .is-spinning {
    animation: spin 900ms linear infinite;
}

/* ═══ 第二部分：场景管理 ═══ */
.scene-manage-actions {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
}

.scene-manage-actions button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    height: 34px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 8px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
    transition:
        transform 140ms var(--motion-ease),
        background-color 140ms var(--motion-ease),
        border-color 140ms var(--motion-ease),
        color 140ms var(--motion-ease);
}

.scene-manage-actions button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: translateY(-1px);
}

.scene-manage-actions button.is-danger:hover {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

/* ═══ 第三部分：推荐模板 ═══ */
.scene-template-list {
    display: grid;
    gap: 6px;
}

.scene-template-list button {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 9px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: transparent;
    padding: 10px 10px;
    text-align: left;
    cursor: pointer;
    transition:
        transform 140ms var(--motion-ease),
        background-color 140ms var(--motion-ease),
        border-color 140ms var(--motion-ease);
}

.scene-template-list button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    transform: translateY(-1px);
}

.scene-template-list button > span:nth-child(2) {
    display: grid;
    min-width: 0;
    flex: 1;
}

.scene-template-list strong {
    color: var(--color-text-primary);
    font-size: 12px;
    font-weight: 900;
}

.scene-template-list small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 750;
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
    padding: 4px 8px;
    color: var(--color-primary-700);
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
}

.template-empty {
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    text-align: center;
    padding: 12px 0;
}

/* ═══ 空状态 ═══ */
.scene-panel-empty {
    display: grid;
    min-height: 200px;
    place-items: center;
}

.empty-state {
    display: grid;
    place-items: center;
    gap: 8px;
    color: var(--color-text-tertiary);
}

.empty-state svg {
    width: 32px;
    height: 32px;
    opacity: 0.4;
}

.empty-state p {
    margin: 0;
    font-size: 14px;
    font-weight: 900;
}

.empty-state small {
    font-size: 12px;
    font-weight: 700;
}

/* === 过渡 === */
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

button:disabled {
    opacity: 0.55;
    cursor: default;
}

@media (prefers-reduced-motion: reduce) {
    button:hover {
        transform: none;
    }
}
</style>