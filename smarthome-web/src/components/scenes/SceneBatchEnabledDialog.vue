<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene } from "../../types/scene";

const props = defineProps<{ modelValue: boolean; scenes: Scene[] }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    apply: [sceneIds: string[], enabled: boolean];
}>();
const selectedIds = ref<string[]>([]);
const enabled = ref(true);
const allSelected = computed(() => selectedIds.value.length === props.scenes.length);

watch(() => props.modelValue, (open) => {
    if (open) {
        selectedIds.value = props.scenes.map((scene) => scene.id);
        enabled.value = true;
    }
}, { immediate: true });

const toggle = (id: string) => {
    selectedIds.value = selectedIds.value.includes(id)
        ? selectedIds.value.filter((item) => item !== id)
        : [...selectedIds.value, id];
};
</script>

<template>
    <BaseSmartModal :model-value="modelValue" title="批量启用" description="选择场景并统一更新启用状态" icon="check-circle" width="620px" confirm-text="应用更改" show-footer @confirm="selectedIds.length && emit('apply', selectedIds, enabled)" @update:model-value="emit('update:modelValue', $event)">
        <div class="batch-toolbar">
            <div class="mode-switch">
                <button type="button" :class="{ active: enabled }" @click="enabled = true">启用</button>
                <button type="button" :class="{ active: !enabled }" @click="enabled = false">停用</button>
            </div>
            <button type="button" class="select-all" @click="selectedIds = allSelected ? [] : scenes.map((scene) => scene.id)">{{ allSelected ? '取消全选' : '全选' }}</button>
        </div>
        <div class="batch-summary" :class="enabled ? 'is-enable' : 'is-disable'">
            <span><SvgIcon :name="enabled ? 'check-circle' : 'close'" /></span>
            <div>
                <strong>{{ enabled ? '批量启用场景' : '批量停用场景' }}</strong>
                <small>确认后将更新 {{ selectedIds.length }} 个场景的运行状态</small>
            </div>
        </div>
        <div class="scene-options">
            <button v-for="scene in scenes" :key="scene.id" type="button" :class="{ selected: selectedIds.includes(scene.id) }" @click="toggle(scene.id)">
                <span class="check"><SvgIcon v-if="selectedIds.includes(scene.id)" name="check-circle" size="sm" /></span>
                <span><strong>{{ scene.name }}</strong><small>{{ scene.enabled ? '当前已启用' : '当前已停用' }}</small></span>
                <em>{{ scene.triggerType === 'manual' ? '手动' : '自动化' }}</em>
            </button>
        </div>
        <template #footerHint>已选择 {{ selectedIds.length }} / {{ scenes.length }} 个场景</template>
    </BaseSmartModal>
</template>

<style scoped>
.batch-toolbar,.batch-summary,.scene-options button { display:flex; align-items:center; }
.batch-toolbar { justify-content:space-between; gap:12px; margin-bottom:12px; }
.mode-switch { display:grid; grid-template-columns:1fr 1fr; min-width:220px; gap:4px; border:1px solid var(--color-border); border-radius:11px; background:var(--color-surface-subtle); padding:4px; }
.mode-switch button,.select-all { border-radius:8px; padding:8px 16px; color:var(--color-text-secondary); font-size:13px; font-weight:900; transition:160ms var(--motion-ease); }
.mode-switch button.active { background:linear-gradient(135deg,var(--color-primary-600),var(--color-primary-500)); color:white; box-shadow:0 4px 12px var(--color-focus-ring); }
.select-all { border:1px solid var(--color-primary-200); background:var(--color-primary-50); color:var(--color-primary-700); }
.batch-summary { gap:12px; margin-bottom:14px; border:1px solid var(--color-primary-200); border-radius:12px; background:linear-gradient(135deg,var(--color-primary-50),var(--color-card-bg)); padding:12px 14px; }
.batch-summary > span { display:grid; width:38px; height:38px; flex:0 0 38px; place-items:center; border-radius:11px; background:var(--color-primary-100); color:var(--color-primary-600); }
.batch-summary.is-disable { border-color:var(--color-warning-soft); background:linear-gradient(135deg,var(--color-warning-soft),var(--color-card-bg)); }
.batch-summary.is-disable > span { background:var(--color-warning-soft); color:var(--color-warning); }
.batch-summary div { display:grid; gap:2px; }
.batch-summary strong { color:var(--color-text-primary); font-size:14px; font-weight:900; }
.batch-summary small { color:var(--color-text-tertiary); font-size:12px; font-weight:700; }
.scene-options { display:grid; max-height:340px; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; overflow-y:auto; padding:2px; scrollbar-gutter:stable; }
.scene-options button { min-width:0; gap:11px; border:1px solid var(--color-border); border-radius:12px; background:var(--color-card-bg); padding:12px; text-align:left; transition:160ms var(--motion-ease); }
.scene-options button:hover { border-color:var(--color-primary-200); transform:translateY(-1px); box-shadow:var(--shadow-card); }
.scene-options button.selected { border-color:var(--color-primary-400); background:linear-gradient(135deg,var(--color-primary-50),var(--color-card-bg)); box-shadow:inset 0 0 0 1px var(--color-focus-ring); }
.check { display:grid; width:24px; height:24px; flex:0 0 24px; place-items:center; border:1px solid var(--color-border); border-radius:8px; background:var(--color-surface-subtle); color:var(--color-primary-600); }
.scene-options button.selected .check { border-color:var(--color-primary-300); background:var(--color-primary-100); }
.scene-options button > span:nth-child(2) { display:grid; min-width:0; flex:1; }
.scene-options strong { color:var(--color-text-primary); font-size:14px; font-weight:900; }
.scene-options small { color:var(--color-text-tertiary); font-size:12px; font-weight:700; }
.scene-options em { border-radius:999px; background:var(--color-surface-subtle); padding:4px 8px; color:var(--color-text-secondary); font-size:11px; font-style:normal; font-weight:800; }
@media (max-width:640px) { .scene-options { grid-template-columns:1fr; } .mode-switch { min-width:0; } }
</style>
