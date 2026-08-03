<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { Room } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const selectedScene = ref("休闲模式");
const sceneScope = ref("客厅设备");
const syncAutomation = ref(true);

const title = "房间场景切换";
const description = `为${props.room?.name ?? "房间"}快速切换常用场景并预览影响设备`;

const scenes = [
    {
        name: "休闲模式",
        icon: "comfort",
        note: "放松身心，舒适休闲",
        tags: ["柔和灯光", "舒适温度", "轻松氛围"],
    },
    {
        name: "观影模式",
        icon: "device-management",
        note: "沉浸观影，最佳体验",
        tags: ["影院灯光", "窗帘闭合", "增强音效"],
    },
    {
        name: "阅读模式",
        icon: "room",
        note: "专注阅读，保护眼睛",
        tags: ["明亮灯光", "适中温度", "安静环境"],
    },
    {
        name: "离开模式",
        icon: "lock",
        note: "节能安全，安心离家",
        tags: ["关闭电器", "安防布防", "节能省电"],
    },
];

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        confirm-text="立即切换"
        width="large"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="scene-dialog">
            <section>
                <div class="scene-grid">
                    <button
                        v-for="scene in scenes"
                        :key="scene.name"
                        :class="{ active: selectedScene === scene.name }"
                        type="button"
                        @click="selectedScene = scene.name"
                    >
                        <span><SvgIcon :name="scene.icon" size="lg" /></span
                        ><strong>{{ scene.name }}</strong
                        ><small>{{ scene.note }}</small
                        ><i>{{ scene.tags.join("　") }}</i
                        ><b v-if="selectedScene === scene.name">✓</b>
                    </button>
                </div>
                <div class="recommendation">
                    <strong>推荐原因</strong>
                    <p>
                        当前光照适中，温度舒适，适合切换为“{{ selectedScene }}”
                    </p>
                </div>
            </section>
            <aside>
                <h3>应用范围</h3>
                <div class="scope-row">
                    <button
                        v-for="scope in [
                            '客厅设备',
                            '客厅主区',
                            '阳台',
                            '玄关联动',
                        ]"
                        :key="scope"
                        :class="{ active: sceneScope === scope }"
                        type="button"
                        @click="sceneScope = scope"
                    >
                        {{ scope }}
                    </button>
                </div>
                <label class="toggle-row"
                    ><span>同步执行自动化联动</span
                    ><input v-model="syncAutomation" type="checkbox"
                /></label>
                <div class="impact">
                    <h3>预览影响</h3>
                    <p><SvgIcon name="light" />灯光 <b>5 个</b></p>
                    <p><SvgIcon name="air-conditioner" />空调 <b>1 个</b></p>
                    <p><SvgIcon name="curtain" />窗帘 <b>2 个</b></p>
                    <p><SvgIcon name="plug" />插座 <b>1 个</b></p>
                </div>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.scene-dialog {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 16px;
}
.scene-dialog h3 {
    margin: 0 0 9px;
    font-size: 13px;
}
.scene-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.scene-grid > button {
    position: relative;
    display: flex;
    min-height: 155px;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    border: 1px solid var(--color-border);
    border-radius: 11px;
    background: var(--color-card-bg);
}
.scene-grid > button.active {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}
.scene-grid > button > span {
    display: grid;
    width: 52px;
    height: 52px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.scene-grid small {
    color: var(--color-text-tertiary);
}
.scene-grid i {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-style: normal;
}
.scene-grid > button > b {
    position: absolute;
    top: 8px;
    right: 8px;
    display: grid;
    width: 20px;
    height: 20px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-600);
    color: white;
}
.recommendation {
    margin-top: 12px;
    border: 1px solid var(--color-border);
    border-radius: 11px;
    padding: 12px;
}
.recommendation p {
    margin: 6px 0 0;
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.scene-dialog > aside {
    border-left: 1px solid var(--color-border);
    padding-left: 16px;
}
.scope-row {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
}
.scope-row button {
    min-width: 30px;
    height: 30px;
    padding: 0 11px;
    border: 1px solid var(--color-border);
    border-radius: 7px;
    background: var(--color-card-bg);
}
.scope-row button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--color-border-subtle);
    padding: 8px 0;
    font-size: 11px;
}
.toggle-row input {
    width: 36px;
    height: 19px;
    accent-color: var(--color-primary-600);
}
.impact {
    margin-top: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 13px;
}
.impact p {
    display: flex;
    align-items: center;
    gap: 8px;
}
.impact p b {
    margin-left: auto;
}
@media (max-width: 760px) {
    .scene-dialog {
        grid-template-columns: 1fr;
    }
    .scene-dialog > aside {
        border-left: 0;
        padding-left: 0;
    }
}
</style>
