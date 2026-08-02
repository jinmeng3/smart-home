<script setup lang="ts">
import { computed, reactive } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

const model = defineModel<boolean>({ required: true });

const emit = defineEmits<{
    create: [];
    draft: [];
}>();

const form = reactive({
    name: "回家模式",
    description: "回到家时自动开启舒适环境",
    icon: "home",
    color: "var(--color-primary-600)",
    triggerType: "location",
    triggerLabel: "到达“家”半径 100m",
    rooms: ["玄关", "客厅", "主卧"],
});

const iconOptions = ["home", "eye", "group", "clock", "energy", "room", "automation"];
const colorOptions = [
    "var(--color-primary-600)",
    "var(--color-success)",
    "var(--color-warning)",
    "var(--color-scene-sleep)",
    "var(--color-danger)",
    "var(--color-teal-600)",
];
const actions = [
    { id: "entry-light", icon: "light", name: "打开玄关灯", target: "玄关灯 · 开" },
    { id: "living-light", icon: "light", name: "客厅灯亮度", target: "客厅灯 · 60%" },
    { id: "ac", icon: "air-conditioner", name: "空调设置", target: "客厅空调 · 26℃ 制冷" },
    { id: "curtain", icon: "curtain", name: "窗帘打开", target: "客厅窗帘 · 50%" },
    { id: "camera", icon: "camera", name: "摄像头切换在家模式", target: "摄像头 · 在家模式" },
];

const triggerLabel = computed(() =>
    form.triggerType === "location"
        ? `位置触发（${form.triggerLabel}）`
        : form.triggerType === "schedule"
          ? "定时触发"
          : form.triggerType === "device"
            ? "设备触发"
            : "手动执行",
);

const createScene = () => {
    emit("create");
    model.value = false;
};
</script>

<template>
    <BaseSmartModal
        v-model="model"
        title="创建场景"
        description="配置场景信息、触发条件与执行动作"
        icon="home"
        width="880px"
        confirm-text="创建场景"
        cancel-text="取消"
        show-footer
        @confirm="createScene"
    >
        <div class="create-dialog">
            <section class="create-form">
                <nav class="create-steps" aria-label="创建步骤">
                    <span class="active">1 基本信息</span>
                    <span>2 触发条件</span>
                    <span>3 执行动作</span>
                    <span>4 预览发布</span>
                </nav>

                <section class="form-block">
                    <h3>1. 基本信息</h3>
                    <div class="form-grid">
                        <label>
                            <span>场景名称</span>
                            <input v-model="form.name" maxlength="32" />
                        </label>
                        <label>
                            <span>场景描述</span>
                            <textarea v-model="form.description" rows="2" />
                        </label>
                    </div>
                    <div class="picker-row">
                        <span>场景图标</span>
                        <button
                            v-for="item in iconOptions"
                            :key="item"
                            :class="{ active: form.icon === item }"
                            type="button"
                            @click="form.icon = item"
                        >
                            <SvgIcon :name="item" />
                        </button>
                    </div>
                    <div class="picker-row">
                        <span>场景主色</span>
                        <button
                            v-for="item in colorOptions"
                            :key="item"
                            :class="{ active: form.color === item }"
                            :style="{ color: item }"
                            type="button"
                            @click="form.color = item"
                        >
                            ●
                        </button>
                    </div>
                </section>

                <section class="form-block">
                    <h3>2. 触发条件</h3>
                    <div class="trigger-tabs">
                        <button :class="{ active: form.triggerType === 'schedule' }" type="button" @click="form.triggerType = 'schedule'">
                            <SvgIcon name="calendar" /> 定时触发
                        </button>
                        <button :class="{ active: form.triggerType === 'location' }" type="button" @click="form.triggerType = 'location'">
                            <SvgIcon name="home" /> 位置触发
                        </button>
                        <button :class="{ active: form.triggerType === 'device' }" type="button" @click="form.triggerType = 'device'">
                            <SvgIcon name="device-management" /> 设备触发
                        </button>
                    </div>
                    <label class="inline-field">
                        <span>触发条件设置</span>
                        <input v-model="form.triggerLabel" />
                    </label>
                </section>

                <section class="form-block">
                    <h3>3. 关联房间与设备</h3>
                    <div class="room-device-row">
                        <label>
                            <span>关联房间</span>
                            <div class="chips">
                                <em v-for="room in form.rooms" :key="room">{{ room }}</em>
                            </div>
                        </label>
                        <label>
                            <span>关联设备</span>
                            <button type="button">共 8 个设备 <SvgIcon name="chevron-right" /></button>
                        </label>
                    </div>
                </section>

                <section class="form-block">
                    <h3>4. 执行动作</h3>
                    <ol class="action-list">
                        <li v-for="(action, index) in actions" :key="action.id">
                            <span>{{ index + 1 }}</span>
                            <SvgIcon :name="action.icon" />
                            <strong>{{ action.name }}</strong>
                            <small>{{ action.target }}</small>
                            <SvgIcon name="more" />
                        </li>
                    </ol>
                    <button class="add-action" type="button">+ 添加执行动作</button>
                </section>
            </section>

            <aside class="create-preview">
                <h3>场景预览</h3>
                <article class="preview-card">
                    <span :style="{ color: form.color }"><SvgIcon :name="form.icon" /></span>
                    <div>
                        <strong>{{ form.name }}</strong>
                        <p>{{ form.description }}</p>
                    </div>
                    <i />
                </article>
                <dl>
                    <div><dt>关联房间</dt><dd>{{ form.rooms.length }} 个</dd></div>
                    <div><dt>关联设备</dt><dd>8 个</dd></div>
                    <div><dt>触发方式</dt><dd>{{ triggerLabel }}</dd></div>
                </dl>
                <h4>执行流程预览</h4>
                <ol>
                    <li v-for="action in actions" :key="action.id">
                        <SvgIcon :name="action.icon" />
                        <span>
                            <strong>{{ action.name }}</strong>
                            <small>{{ action.target }}</small>
                        </span>
                    </li>
                </ol>
                <p class="preview-note">预计将影响 8 个设备</p>
            </aside>
        </div>
        <template #footerHint>
            您可以在创建后随时编辑和调整场景设置。
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.create-dialog {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 310px;
    gap: 16px;
}

.create-form,
.create-preview {
    min-width: 0;
}

.create-steps {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 14px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
}

.create-steps span {
    border-bottom: 2px solid var(--color-border);
    padding-bottom: 8px;
    text-align: center;
}

.create-steps .active {
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
}

.form-block,
.create-preview {
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 12px;
}

.form-block + .form-block {
    margin-top: 10px;
}

h3,
h4,
p,
dl,
ol {
    margin: 0;
}

h3 {
    margin-bottom: 10px;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.form-grid,
.room-device-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

label {
    display: grid;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
}

input,
textarea {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 9px 10px;
    color: var(--color-text-primary);
    font: inherit;
    outline: 0;
}

.picker-row,
.trigger-tabs,
.preview-card,
dl,
.action-list li,
.create-preview li {
    display: flex;
    align-items: center;
}

.picker-row {
    gap: 10px;
    margin-top: 12px;
}

.picker-row > span {
    width: 76px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
}

.picker-row button,
.trigger-tabs button,
.room-device-row button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 34px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    padding: 0 10px;
    font-size: 12px;
    font-weight: 900;
}

.picker-row button {
    width: 34px;
    padding: 0;
}

button.active {
    border-color: var(--color-primary-600);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.trigger-tabs {
    gap: 8px;
    margin-bottom: 10px;
}

.inline-field {
    max-width: 300px;
}

.chips {
    display: flex;
    gap: 6px;
    min-height: 34px;
    align-items: center;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0 8px;
}

.chips em {
    border-radius: 6px;
    background: var(--color-primary-50);
    padding: 4px 7px;
    color: var(--color-primary-700);
    font-style: normal;
}

.action-list {
    display: grid;
    gap: 6px;
    padding: 0;
    list-style: none;
}

.action-list li {
    display: grid;
    grid-template-columns: 24px 28px minmax(0, 1fr) minmax(0, 1fr) 24px;
    gap: 8px;
    min-height: 36px;
    border-bottom: 1px solid var(--color-border);
}

.action-list span {
    color: var(--color-text-tertiary);
    font-weight: 900;
    text-align: center;
}

.action-list strong,
.action-list small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.action-list strong {
    color: var(--color-text-primary);
    font-size: 12px;
}

.action-list small {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.add-action {
    width: 100%;
    height: 34px;
    margin-top: 8px;
    border: 1px dashed var(--color-primary-200);
    border-radius: 8px;
    color: var(--color-primary-600);
    font-weight: 900;
}

.preview-card {
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    padding: 10px;
}

.preview-card > span {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-primary-50);
}

.preview-card div {
    min-width: 0;
    flex: 1;
}

.preview-card strong,
.preview-card p {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-card strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.preview-card p {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.preview-card i {
    width: 30px;
    height: 18px;
    border-radius: 999px;
    background: var(--color-primary-600);
}

dl {
    justify-content: space-between;
    gap: 8px;
    padding: 12px 0;
}

dt,
dd {
    margin: 0;
    font-size: 12px;
}

dt {
    color: var(--color-text-tertiary);
}

dd {
    color: var(--color-text-primary);
    font-weight: 900;
}

.create-preview h4 {
    margin-bottom: 10px;
    font-size: 13px;
    font-weight: 900;
}

.create-preview ol {
    display: grid;
    gap: 8px;
    padding: 0;
    list-style: none;
}

.create-preview li {
    gap: 9px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 8px;
}

.create-preview li > svg {
    color: var(--color-primary-600);
}

.create-preview li span {
    min-width: 0;
}

.create-preview li strong,
.create-preview li small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
}

.create-preview li small,
.preview-note {
    color: var(--color-text-tertiary);
}

.preview-note {
    margin-top: 12px;
    font-size: 12px;
    font-weight: 800;
}

@media (max-width: 980px) {
    .create-dialog {
        grid-template-columns: 1fr;
    }
}
</style>
