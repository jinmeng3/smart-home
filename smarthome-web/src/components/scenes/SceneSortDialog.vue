<script setup lang="ts">
import { onScopeDispose, ref, watch, nextTick } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { gsap, registerDraggable, useMotionMode } from "../../motion";
import { useGsapFlip } from "../../composables/useGsapFlip";
import type { Scene } from "../../types/scene";

const props = defineProps<{ modelValue: boolean; scenes: Scene[] }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean]; apply: [sceneIds: string[]] }>();
const ordered = ref<Scene[]>([]);
watch(() => props.modelValue, (open) => { if (open) ordered.value = [...props.scenes]; }, { immediate: true });

/* === GSAP Flip 排序项重排 === */
const sortListRef = ref<HTMLElement | null>(null);
const { capture: captureSortList, flip: flipSortList } = useGsapFlip({
    container: sortListRef,
    itemSelector: ".sort-list > li",
    duration: 240,
});

const move = (index: number, offset: number) => {
    const target = index + offset;
    if (target < 0 || target >= ordered.value.length) return;
    captureSortList();
    const next = [...ordered.value];
    [next[index], next[target]] = [next[target]!, next[index]!];
    ordered.value = next;
    void flipSortList();
};

/* === Draggable 拖拽排序（真正需要拖拽时按需引入） === */
const { isReduced } = useMotionMode();
let draggables: Array<{ kill: () => void }> = [];
let draggableReady = false;
let dragFromIndex = -1;

const reorderByDrag = (toIndex: number) => {
    if (dragFromIndex < 0 || dragFromIndex === toIndex) return;
    captureSortList();
    const next = [...ordered.value];
    const [moved] = next.splice(dragFromIndex, 1);
    next.splice(toIndex, 0, moved!);
    ordered.value = next;
    dragFromIndex = -1;
    void flipSortList();
};

const initDraggable = async () => {
    if (isReduced.value) return;
    await registerDraggable();
    draggableReady = true;
    void nextTick(() => destroyDraggable());
    void nextTick(setupDraggable);
};

const setupDraggable = () => {
    if (!draggableReady || !sortListRef.value || isReduced.value) return;
    const items = Array.from(
        sortListRef.value.querySelectorAll<HTMLElement>(".sort-list > li"),
    );
    if (!items.length) return;

    items.forEach((item, index) => {
        // Draggable 通过动态 import 注册，类型上以 any 访问
        const draggable = (gsap as any).Draggable;
        const drag = draggable.create(item, {
            type: "y",
            trigger: item,
            cursor: "grab",
            activeCursor: "grabbing",
            // 垂直方向对齐相邻项间隔
            snap: {
                y: (value: number) =>
                    Math.round(value / item.offsetHeight) * item.offsetHeight,
            },
            onDragStart: () => {
                dragFromIndex = ordered.value.findIndex(
                    (scene: Scene) => scene.id === item.dataset.sceneId,
                );
                gsap.set(item, { zIndex: 10, opacity: 0.92 });
            },
            onDragEnd: () => {
                gsap.set(item, { zIndex: "", opacity: "" });
                // 根据位移换算新索引
                const offset = Math.round(
                    (gsap.getProperty(item, "y") as number) / item.offsetHeight,
                );
                const from = dragFromIndex >= 0 ? dragFromIndex : index;
                reorderByDrag(
                    Math.max(
                        0,
                        Math.min(ordered.value.length - 1, from + offset),
                    ),
                );
            },
        });
        draggables.push(...drag);
    });
};

const destroyDraggable = () => {
    draggables.forEach((d) => d.kill());
    draggables = [];
};

watch(
    () => props.modelValue,
    (open) => {
        if (open) void initDraggable();
    },
);

onScopeDispose(destroyDraggable);
</script>

<template>
    <BaseSmartModal :model-value="modelValue" title="场景排序" description="调整场景展示顺序并保存到后端" icon="layers" width="620px" confirm-text="保存排序" show-footer @confirm="emit('apply', ordered.map((scene) => scene.id))" @update:model-value="emit('update:modelValue', $event)">
        <div class="sort-summary">
            <span><SvgIcon name="layers" /></span>
            <div><strong>自定义展示顺序</strong><small>拖拽列表项或使用右侧按钮调整，排名靠前的场景优先展示</small></div>
        </div>
        <ol ref="sortListRef" class="sort-list">
            <li v-for="(scene, index) in ordered" :key="scene.id" :data-scene-id="scene.id">
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
.sort-list li { display:flex; align-items:center; gap:11px; border:1px solid var(--color-border); border-radius:12px; background:var(--color-card-bg); padding:11px 12px; transition:160ms var(--motion-ease); touch-action:none; }
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
