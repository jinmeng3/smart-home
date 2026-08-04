<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { sleep } from "../../../utils/async";
import { toggleValue } from "../../../utils/array";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    "room-created": [name: string];
}>();

const loading = ref(false);
const roomName = ref("");
const roomType = ref("书房");
const floor = ref("二楼");
const selectedIcon = ref("room");
const selectedColor = ref("#3478f6");
const roomDevices = reactive(["灯光", "空调", "传感器", "窗帘"]);

const roomTypes = ["书房", "儿童房", "影音室", "储物间"];
const roomIcons = [
    "room",
    "home",
    "device-management",
    "air-conditioner",
    "curtain",
    "more",
];
const colors = [
    "#3478f6",
    "#20b86a",
    "#19b6bd",
    "#825bea",
    "#ff8a1f",
    "#f05252",
];

const confirm = async () => {
    if (!roomName.value.trim()) {
        ElMessage.warning("请输入房间名称");
        return;
    }
    loading.value = true;
    await sleep(450);
    emit("room-created", roomName.value.trim());
    ElMessage.success("添加房间操作成功");
    loading.value = false;
    emit("update:modelValue", false);
};

watch(
    () => props.modelValue,
    (value) => {
        if (value) roomName.value = "";
    },
);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="添加房间"
        description="创建新的房间并绑定设备，完善家庭空间管理"
        :width="760"
        :loading="loading"
        confirm-text="创建房间"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="room-layout">
            <div class="form-stack">
                <label
                    >房间名称<input
                        v-model="roomName"
                        maxlength="20"
                        placeholder="请输入房间名称"
                    /><small>{{ roomName.length }}/20</small></label
                >
                <div class="form-row">
                    <label
                        >房间类型<select v-model="roomType">
                            <option v-for="type in roomTypes" :key="type">
                                {{ type }}
                            </option>
                        </select></label
                    ><label
                        >楼层/区域<select v-model="floor">
                            <option>一楼</option>
                            <option>二楼</option>
                            <option>地下室</option>
                        </select></label
                    >
                </div>
                <fieldset>
                    <legend>房间图标</legend>
                    <button
                        v-for="icon in roomIcons"
                        :key="icon"
                        type="button"
                        :class="{ active: selectedIcon === icon }"
                        @click="selectedIcon = icon"
                    >
                        <SvgIcon :name="icon" />
                    </button>
                </fieldset>
                <fieldset>
                    <legend>图标颜色</legend>
                    <button
                        v-for="color in colors"
                        :key="color"
                        type="button"
                        class="color-dot"
                        :class="{ active: selectedColor === color }"
                        :style="{ background: color }"
                        @click="selectedColor = color"
                    />
                </fieldset>
                <fieldset class="device-bind">
                    <legend>绑定设备</legend>
                    <button
                        v-for="device in [
                            '灯光',
                            '空调',
                            '传感器',
                            '窗帘',
                            '摄像头',
                            '门锁',
                        ]"
                        :key="device"
                        type="button"
                        :class="{ active: roomDevices.includes(device) }"
                        @click="toggleValue(roomDevices, device)"
                    >
                        <SvgIcon
                            :name="
                                device === '传感器'
                                    ? 'sensor'
                                    : device === '摄像头'
                                      ? 'camera'
                                      : device === '门锁'
                                        ? 'lock'
                                        : device === '灯光'
                                          ? 'light'
                                          : device === '空调'
                                            ? 'air-conditioner'
                                            : 'curtain'
                            "
                        />{{ device }}
                    </button>
                </fieldset>
            </div>
            <aside class="room-preview">
                <b>房间预览</b>
                <div>
                    <span :style="{ color: selectedColor }"
                        ><SvgIcon :name="selectedIcon" size="lg"
                    /></span>
                    <h3>{{ roomName || roomType }}</h3>
                    <p>{{ roomDevices.length }} 个设备</p>
                    <small>当前未启用自动化</small>
                </div>
                <ul>
                    <li>
                        楼层/区域 <b>{{ floor }}</b>
                    </li>
                    <li>
                        房间类型 <b>{{ roomType }}</b>
                    </li>
                    <li>
                        设备数量 <b>{{ roomDevices.length }}</b>
                    </li>
                </ul>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.room-preview {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
}
.room-layout {
    display: grid;
    grid-template-columns: 1.65fr 1fr;
    gap: 16px;
}
.form-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.form-stack > label,
.form-row label {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 7px;
    font-weight: 700;
}
.form-stack input,
.form-stack select {
    height: 38px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 0 11px;
}
.form-stack > label > small {
    position: absolute;
    right: 10px;
    bottom: 10px;
    color: var(--color-text-tertiary);
}
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
fieldset {
    display: flex;
    gap: 9px;
    border: 0;
}
legend {
    margin-bottom: 8px;
    font-weight: 700;
}
fieldset button {
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 7px 12px;
}
fieldset button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.color-dot {
    width: 22px;
    height: 22px;
    padding: 0;
    border-radius: 50%;
}
.device-bind {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
}
.device-bind button {
    display: flex;
    align-items: center;
    gap: 7px;
}
.room-preview {
    text-align: center;
}
.room-preview > div {
    padding: 20px;
}
.room-preview > div > span {
    display: grid;
    width: 54px;
    height: 54px;
    margin: auto;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.room-preview h3 {
    margin: 10px 0 2px;
    font-size: 20px;
}
.room-preview ul {
    list-style: none;
    text-align: left;
}
.room-preview li {
    display: flex;
    justify-content: space-between;
    padding: 7px;
}
@media (max-width: 760px) {
    .room-layout {
        grid-template-columns: 1fr;
    }
    .device-bind {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
