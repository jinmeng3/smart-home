<script setup lang="ts">
import { ref, watch } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Scene } from "../../types/scene";

const props = defineProps<{ modelValue: boolean; scenes: Scene[] }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean]; apply: [sceneIds: string[]] }>();
const ordered = ref<Scene[]>([]);
watch(() => props.modelValue, (open) => { if (open) ordered.value = [...props.scenes]; }, { immediate: true });
const move = (index: number, offset: number) => {
    const target = index + offset;
    if (target < 0 || target >= ordered.value.length) return;
    const next = [...ordered.value];
    [next[index], next[target]] = [next[target]!, next[index]!];
    ordered.value = next;
};
</script>

<template>
    <BaseSmartModal :model-value="modelValue" title="场景排序" description="调整场景展示顺序并保存到后端" icon="layers" width="620px" confirm-text="保存排序" show-footer @confirm="emit('apply', ordered.map((scene) => scene.id))" @update:model-value="emit('update:modelValue', $event)">
        <div class="sort-summary">
            <span><SvgIcon name="layers" /></span>
            <div><strong>自定义展示顺序</strong><small>使用右侧按钮调整，排名靠前的场景优先展示</small></div>
        </div>
        <ol class="sort-list">
            <li v-for="(scene, index) in ordered" :key="scene.id">
                <b>{{ index + 1 }}</b>
                <i :style="{ color: scene.color }"><SvgIcon :name="scene.icon" size="sm" /></i>
                <span><strong>{{ scene.name }}</strong><small>{{ scene.triggerLabel }}</small></span>
                <div>
                    <button class="move-up" type="button" title="上移" :disabled="index === 0" @click="move(index, -1)"><SvgIcon name="chevron-down" size="sm" /></button>
                    <button type="button" title="下移" :disabled="index === ordered.length - 1" @click="move(index, 1)"><SvgIcon name="chevron-down" size="sm" /></button>
                </div>
            </li>
        </ol>
        <template #footerHint>排序保存后会立即刷新场景列表</template>
    </BaseSmartModal>
</template>

<style scoped>
.sort-summary { display:flex; align-items:center; gap:12px; margin-bottom:14px; border:1px solid var(--color-primary-200); border-radius:12px; background:linear-gradient(135deg,var(--color-primary-50),var(--color-card-bg)); padding:13px 14px; }
.sort-summary > span { display:grid; width:40px; height:40px; flex:0 0 40px; place-items:center; border-radius:12px; background:var(--color-primary-100); color:var(--color-primary-600); }
.sort-summary div { display:grid; gap:2px; }
.sort-summary strong { color:var(--color-text-primary); font-size:14px; font-weight:900; }
.sort-summary small { color:var(--color-text-tertiary); font-size:12px; font-weight:700; }
.sort-list { display:grid; max-height:380px; gap:8px; overflow-y:auto; margin:0; padding:2px; list-style:none; scrollbar-gutter:stable; }
.sort-list li { display:flex; align-items:center; gap:11px; border:1px solid var(--color-border); border-radius:12px; background:var(--color-card-bg); padding:11px 12px; transition:160ms var(--motion-ease); }
.sort-list li:hover { border-color:var(--color-primary-200); box-shadow:var(--shadow-card); transform:translateY(-1px); }
.sort-list b { display:grid; width:30px; height:30px; flex:0 0 30px; place-items:center; border-radius:9px; background:linear-gradient(135deg,var(--color-primary-100),var(--color-primary-50)); color:var(--color-primary-700); font-size:12px; }
.sort-list i { display:grid; width:34px; height:34px; flex:0 0 34px; place-items:center; border-radius:10px; background:var(--color-surface-subtle); font-style:normal; }
.sort-list > li > span { display:grid; min-width:0; flex:1; }
.sort-list strong { color:var(--color-text-primary); font-size:14px; font-weight:900; }
.sort-list small { overflow:hidden; color:var(--color-text-tertiary); font-size:12px; font-weight:700; text-overflow:ellipsis; white-space:nowrap; }
.sort-list li div { display:flex; gap:5px; }
.sort-list button { display:grid; width:34px; height:34px; place-items:center; border:1px solid var(--color-border); border-radius:9px; background:var(--color-card-bg); color:var(--color-primary-600); transition:150ms var(--motion-ease); }
.sort-list button:hover:not(:disabled) { border-color:var(--color-primary-300); background:var(--color-primary-50); }
.sort-list button.move-up svg { transform:rotate(180deg); }
.sort-list button:disabled { opacity:.3; }
</style>
