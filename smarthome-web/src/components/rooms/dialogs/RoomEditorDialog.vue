<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { Room } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
    mode: "edit" | "create";
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    create: [room: Pick<Room, "name" | "floor" | "roomType">];
    update: [room: Room];
}>();

const roomForm = reactive({ name: "", floor: "1F", roomType: "living" });
const selectedIcon = ref("room");
const selectedColor = ref("#2563eb");

const roomIcons = [
    "room",
    "home",
    "device-management",
    "comfort",
    "scene",
    "automation",
];
const roomColors = [
    "#2563eb",
    "#8b5cf6",
    "#14b8a6",
    "#22c55e",
    "#f59e0b",
    "#f43f5e",
    "#94a3b8",
];
const bindDevices = ["灯光", "空调", "窗帘", "插座", "电视", "空气净化器"];
const bindDeviceIcons = [
    "light",
    "air-conditioner",
    "curtain",
    "plug",
    "device-management",
    "sensor",
];

const title = props.mode === "edit" ? "编辑房间" : "添加房间";
const description =
    props.mode === "edit"
        ? "修改房间信息、设备分组与控制偏好"
        : "创建新房间并绑定设备，完善家庭空间管理";
const confirmText = props.mode === "edit" ? "保存修改" : "创建房间";

watch(
    () => [props.modelValue, props.room, props.mode] as const,
    () => {
        if (props.mode === "edit" && props.room) {
            roomForm.name = props.room.name;
            roomForm.floor = props.room.floor;
            roomForm.roomType = props.room.roomType;
        } else if (props.mode === "create") {
            roomForm.name = "书房";
            roomForm.floor = "2F";
            roomForm.roomType = "study";
        }
    },
    { immediate: true },
);

const close = () => emit("update:modelValue", false);

const confirm = () => {
    if (props.mode === "edit" && props.room) {
        emit("update", { ...props.room, ...roomForm });
    } else {
        emit("create", { ...roomForm });
    }

    close();
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        :confirm-text="confirmText"
        width="large"
        @cancel="close"
        @confirm="confirm"
        @update:model-value="close"
    >
        <div class="room-editor">
            <section class="editor-form">
                <div class="field-row">
                    <label>房间名称<input v-model="roomForm.name" /></label>
                    <label
                        >楼层 / 区域<select v-model="roomForm.floor">
                            <option>1F</option>
                            <option>2F</option>
                            <option>地下室</option>
                        </select></label
                    >
                    <label v-if="mode === 'create'"
                        >房间类型<select v-model="roomForm.roomType">
                            <option value="living">客厅</option>
                            <option value="bedroom">卧室</option>
                            <option value="study">书房</option>
                            <option value="kitchen">厨房</option>
                        </select></label
                    >
                </div>
                <fieldset>
                    <legend>房间图标</legend>
                    <button
                        v-for="icon in roomIcons"
                        :key="icon"
                        :class="{ active: selectedIcon === icon }"
                        type="button"
                        @click="selectedIcon = icon"
                    >
                        <SvgIcon :name="icon" />
                    </button>
                </fieldset>
                <fieldset>
                    <legend>主题颜色</legend>
                    <button
                        v-for="color in roomColors"
                        :key="color"
                        class="color-dot"
                        :class="{ active: selectedColor === color }"
                        :style="{ background: color }"
                        type="button"
                        @click="selectedColor = color"
                    />
                </fieldset>
                <fieldset class="device-binding">
                    <legend>
                        {{
                            mode === "edit"
                                ? "已绑定设备（6）"
                                : "绑定设备（可多选）"
                        }}
                    </legend>
                    <button
                        v-for="(device, index) in bindDevices"
                        :key="device"
                        class="active"
                        type="button"
                    >
                        <SvgIcon
                            :name="bindDeviceIcons[index] ?? 'room'"
                            size="sm"
                        />{{ device }}<b>✓</b>
                    </button>
                </fieldset>
                <section v-if="mode === 'edit'" class="preference-card">
                    <h3>快捷控制偏好</h3>
                    <label
                        v-for="item in [
                            '常用设备置顶',
                            '显示环境卡片',
                            '显示场景快捷入口',
                        ]"
                        :key="item"
                        ><span
                            >{{ item
                            }}<small>在房间卡片中显示此功能</small></span
                        ><input checked type="checkbox"
                    /></label>
                </section>
            </section>
            <aside class="room-preview">
                <h3>房间预览</h3>
                <div class="preview-room">
                    <span :style="{ color: selectedColor }"
                        ><SvgIcon :name="selectedIcon" size="lg"
                    /></span>
                    <div>
                        <strong>{{ roomForm.name }}</strong
                        ><small>● {{ bindDevices.length }} 个设备</small>
                    </div>
                    <b>{{ room?.comfort ?? 81 }}<small>分</small></b>
                </div>
                <div class="preview-metrics">
                    <span>🌡 {{ room?.temperature ?? "--" }}°C</span
                    ><span>◉ {{ room?.humidity ?? "--" }}%</span
                    ><span>☀ {{ room?.illuminance ?? "--" }} lux</span>
                </div>
                <h3>关联能力</h3>
                <p
                    v-for="item in ['集中控制', '自动化联动', '能耗统计']"
                    :key="item"
                    class="ability"
                >
                    <SvgIcon name="automation" size="sm" /><span
                        ><b>{{ item }}</b
                        ><small>配置房间智能能力</small></span
                    ><SvgIcon name="chevron-right" size="sm" />
                </p>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.room-editor {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 16px;
}
.editor-form {
    display: grid;
    gap: 14px;
}
.field-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.field-row label {
    display: grid;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
}
.field-row input,
.field-row select {
    width: 100%;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
}
.editor-form fieldset {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    border: 0;
    padding: 0;
}
.editor-form legend {
    width: 100%;
    margin-bottom: 7px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
}
.editor-form fieldset button {
    display: inline-flex;
    min-width: 46px;
    height: 38px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
}
.editor-form fieldset button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.editor-form .color-dot {
    min-width: 24px;
    width: 24px;
    height: 24px;
    border: 3px solid transparent;
    border-radius: 50%;
}
.editor-form .color-dot.active {
    box-shadow: 0 0 0 2px var(--color-primary-200);
}
.device-binding {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr);
}
.device-binding legend {
    grid-column: 1/-1;
}
.device-binding b {
    margin-left: auto;
}
.preference-card,
.room-preview {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 13px;
}
.preference-card h3,
.room-preview h3 {
    margin: 0 0 9px;
    font-size: 13px;
}
.preference-card label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--color-border-subtle);
    padding: 8px 0;
    font-size: 11px;
}
.preference-card small {
    display: block;
    color: var(--color-text-tertiary);
}
.preference-card input {
    width: 36px;
    height: 19px;
    accent-color: var(--color-primary-600);
}
.room-preview {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.preview-room {
    display: grid;
    grid-template-columns: 56px 1fr auto;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    padding: 12px;
}
.preview-room > span {
    display: grid;
    width: 56px;
    height: 56px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-primary-50);
}
.preview-room div,
.preview-room > div small,
.preview-room > b small {
    display: block;
}
.preview-room > div small {
    margin-top: 5px;
    color: var(--color-success);
}
.preview-room > b {
    font-size: 22px;
}
.preview-room > b small {
    font-size: 9px;
}
.preview-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
}
.preview-metrics span {
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 9px 4px;
    font-size: 10px;
    text-align: center;
}
.ability {
    display: grid;
    grid-template-columns: 24px 1fr 16px;
    align-items: center;
    margin: 0;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 9px;
}
.ability span,
.ability small {
    display: block;
}
.ability small {
    color: var(--color-text-tertiary);
}
@media (max-width: 760px) {
    .room-editor {
        grid-template-columns: 1fr;
    }
    .field-row {
        grid-template-columns: 1fr;
    }
    .device-binding {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
