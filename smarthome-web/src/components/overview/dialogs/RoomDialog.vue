<script setup lang="ts">
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { createRoom } from "../../../api/room";
import { getErrorMessage } from "../../../utils/error";

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
const nameError = ref("");

const roomTypes = ["书房", "儿童房", "影音室", "储物间", "衣帽间", "茶室"];
const roomIcons = [
    "room",
    "home",
    "device-management",
    "air-conditioner",
    "curtain",
    "more",
];
const colors = [
    { value: "#3478f6", label: "蓝色" },
    { value: "#20b86a", label: "绿色" },
    { value: "#19b6bd", label: "青色" },
    { value: "#825bea", label: "紫色" },
    { value: "#ff8a1f", label: "橙色" },
    { value: "#f05252", label: "红色" },
];

const confirm = async () => {
    if (!roomName.value.trim()) {
        nameError.value = "请输入房间名称";
        return;
    }
    nameError.value = "";
    loading.value = true;
    try {
        await createRoom({
            name: roomName.value.trim(),
            floor: floor.value,
            roomType: roomType.value,
            icon: selectedIcon.value,
            themeColor: selectedColor.value,
        });
        emit("room-created", roomName.value.trim());
        ElMessage.success("房间已创建");
        emit("update:modelValue", false);
    } catch (error) {
        ElMessage.error(getErrorMessage(error, "房间创建失败"));
    } finally {
        loading.value = false;
    }
};

watch(
    () => props.modelValue,
    (value) => {
        if (value) {
            roomName.value = "";
            nameError.value = "";
        }
    },
);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="添加房间"
        description="创建新的房间，完善家庭空间管理"
        :width="600"
        :loading="loading"
        confirm-text="创建房间"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="room-layout">
            <div class="room-form">
                <!-- 基本信息 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="room" size="sm" />
                        <span>基本信息</span>
                    </div>
                    <label class="field">
                        <span class="field-label">房间名称</span>
                        <div class="input-wrap">
                            <SvgIcon name="edit" size="sm" class="input-icon" />
                            <input
                                v-model="roomName"
                                maxlength="20"
                                placeholder="请输入房间名称"
                                @input="nameError = ''"
                            />
                            <span class="field-count">{{ roomName.length }}/20</span>
                        </div>
                        <span v-if="nameError" class="field-error">{{ nameError }}</span>
                    </label>
                    <div class="form-row">
                        <label class="field">
                            <span class="field-label">房间类型</span>
                            <div class="input-wrap">
                                <SvgIcon name="comfort" size="sm" class="input-icon" />
                                <select v-model="roomType">
                                    <option v-for="type in roomTypes" :key="type">{{ type }}</option>
                                </select>
                            </div>
                        </label>
                        <label class="field">
                            <span class="field-label">楼层 / 区域</span>
                            <div class="input-wrap">
                                <SvgIcon name="home" size="sm" class="input-icon" />
                                <select v-model="floor">
                                    <option>一楼</option>
                                    <option>二楼</option>
                                    <option>地下室</option>
                                </select>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- 外观设置 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="scene" size="sm" />
                        <span>外观设置</span>
                    </div>
                    <fieldset class="picker-group">
                        <legend>房间图标</legend>
                        <div class="icon-grid">
                            <button
                                v-for="icon in roomIcons"
                                :key="icon"
                                type="button"
                                :class="{ active: selectedIcon === icon }"
                                :title="icon"
                                @click="selectedIcon = icon"
                            >
                                <SvgIcon :name="icon" />
                            </button>
                        </div>
                    </fieldset>
                    <fieldset class="picker-group">
                        <legend>图标颜色</legend>
                        <div class="color-grid">
                            <button
                                v-for="c in colors"
                                :key="c.value"
                                type="button"
                                :class="{ active: selectedColor === c.value }"
                                :style="{ '--dot-color': c.value }"
                                class="color-dot"
                                :title="c.label"
                                @click="selectedColor = c.value"
                            >
                                <SvgIcon v-if="selectedColor === c.value" name="check" size="sm" class="color-check" />
                            </button>
                            <span class="color-label">{{ colors.find((c) => c.value === selectedColor)?.label ?? "" }}</span>
                        </div>
                    </fieldset>
                </div>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.room-layout {
    display: grid;
    gap: 16px;
}
.section-card {
    padding: 16px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-card-bg);
}
.section-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    font-size: 14px;
    font-weight: 800;
}
.field {
    display: grid;
    gap: 6px;
    margin-bottom: 12px;
}
.field-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-secondary);
}
.input-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 10px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-panel-background);
}
.input-wrap input,
.input-wrap select {
    width: 100%;
    height: 36px;
    border: none;
    background: transparent;
    color: var(--color-text-primary);
    outline: none;
}
.input-icon {
    color: var(--color-text-muted);
    flex-shrink: 0;
}
.field-count {
    color: var(--color-text-tertiary);
    font-size: 11px;
    flex-shrink: 0;
}
.field-error {
    color: var(--color-danger);
    font-size: 12px;
}
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.picker-group {
    border: none;
    padding: 0;
    margin: 0 0 14px;
}
.picker-group legend {
    margin-bottom: 8px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}
.icon-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.icon-grid button {
    display: grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
}
.icon-grid button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.color-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}
.color-dot {
    width: 28px;
    height: 28px;
    border: 2px solid transparent;
    border-radius: 50%;
    background: var(--dot-color, var(--color-primary-500));
    cursor: pointer;
}
.color-dot.active {
    border-color: var(--color-text-primary);
}
.color-check {
    color: #fff;
}
.color-label {
    font-size: 12px;
    color: var(--color-text-tertiary);
}
</style>