<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { SceneTriggerType } from "../../types/scene";

defineProps<{
    keyword: string;
    triggerType: SceneTriggerType | "";
    enabled: "all" | "enabled" | "disabled";
}>();

defineEmits<{
    "update:keyword": [value: string];
    "update:triggerType": [value: SceneTriggerType | ""];
    "update:enabled": [value: "all" | "enabled" | "disabled"];
    create: [];
    import: [];
    batchEnabled: [];
    batchSchedule: [];
    sort: [];
}>();
</script>

<template>
    <section class="scene-toolbar">
        <label class="scene-search">
            <SvgIcon name="search" />
            <input
                :value="keyword"
                placeholder="搜索场景名称或描述"
                type="search"
                @input="
                    $emit(
                        'update:keyword',
                        ($event.target as HTMLInputElement).value,
                    )
                "
            />
        </label>
        <select
            :value="triggerType"
            title="触发方式"
            @change="
                $emit(
                    'update:triggerType',
                    ($event.target as HTMLSelectElement).value as
                        SceneTriggerType | '',
                )
            "
        >
            <option value="">全部触发</option>
            <option value="manual">手动</option>
            <option value="schedule">定时</option>
            <option value="location">位置</option>
            <option value="device">设备</option>
        </select>
        <select
            :value="enabled"
            title="启用状态"
            @change="
                $emit(
                    'update:enabled',
                    ($event.target as HTMLSelectElement).value as
                        'all' | 'enabled' | 'disabled',
                )
            "
        >
            <option value="all">全部状态</option>
            <option value="enabled">已启用</option>
            <option value="disabled">已停用</option>
        </select>
        <button
            class="scene-primary-button"
            type="button"
            @click="$emit('create')"
        >
            <SvgIcon name="plus" /> 创建场景
        </button>
        <button
            class="scene-secondary-button"
            type="button"
            @click="$emit('import')"
        >
            <SvgIcon name="layers" /> 导入模板
        </button>
        <div class="batch-actions-wrapper">
            <button
                class="batch-trigger"
                type="button"
                title="批量操作"
            >
                <SvgIcon name="more" />
            </button>
            <div class="batch-dropdown">
                <button type="button" @click="$emit('batchEnabled')">
                    <SvgIcon name="check-circle" size="sm" /> 批量启用
                </button>
                <button type="button" @click="$emit('batchSchedule')">
                    <SvgIcon name="calendar" size="sm" /> 批量定时
                </button>
                <button type="button" @click="$emit('sort')">
                    <SvgIcon name="layers" size="sm" /> 场景排序
                </button>
            </div>
        </div>
    </section>
</template>

<style scoped>
.scene-toolbar {
    display: grid;
    grid-template-columns: minmax(190px, 1fr) 96px 96px auto auto auto;
    gap: 8px;
    align-items: center;
}

.scene-search {
    display: flex;
    min-width: 0;
    height: 38px;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 12px;
    color: var(--color-text-tertiary);
    box-shadow: var(--shadow-card);
    transition:
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}

.scene-search:focus-within {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.scene-search input {
    min-width: 0;
    flex: 1;
    border: 0;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    outline: none;
}

select {
    width: 100%;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    padding: 0 9px;
    font-size: 12px;
    font-weight: 800;
    outline: none;
    box-shadow: var(--shadow-card);
}

.scene-primary-button,
.scene-secondary-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: 38px;
    border-radius: 10px;
    padding: 0 13px;
    font-size: 13px;
    font-weight: 900;
    white-space: nowrap;
    box-shadow: var(--shadow-card);
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.scene-primary-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.scene-secondary-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.scene-secondary-button:hover,
select:focus {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
}

button:hover {
    transform: translateY(-1px);
}

/* === 批量操作 === */
.batch-actions-wrapper {
    position: relative;
}

.batch-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.batch-trigger:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.batch-dropdown {
    display: none;
    position: absolute;
    right: 0;
    top: calc(100% + 4px);
    z-index: 20;
    min-width: 150px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 4px;
    box-shadow: var(--shadow-card-hover);
}

.batch-actions-wrapper:hover .batch-dropdown,
.batch-dropdown:hover {
    display: block;
}

.batch-dropdown button {
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
    transform: none;
}

.batch-dropdown button:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: none;
}

@media (max-width: 1180px) {
    .scene-toolbar {
        grid-template-columns: minmax(180px, 1fr) repeat(2, 92px);
    }

    .scene-primary-button,
    .scene-secondary-button {
        justify-self: start;
    }

    .batch-actions-wrapper {
        justify-self: end;
    }
}

@media (max-width: 720px) {
    .scene-toolbar {
        grid-template-columns: 1fr;
    }
}
</style>