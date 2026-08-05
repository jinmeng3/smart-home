<script setup lang="ts">
import { reactive, ref, watch, computed } from "vue";
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
    create: [room: {
        name: string;
        floor: string;
        roomType: string;
        icon: string;
        themeColor: string;
        deviceIds: number[];
    }];
    update: [room: Room];
}>();

const roomForm = reactive({ name: "", floor: "1F", roomType: "living" });
const selectedIcon = ref("room");
const selectedColor = ref("#2563eb");
const selectedDevices = reactive<string[]>([]);
const nameError = ref("");

const roomIcons = [
    "room",
    "home",
    "device-management",
    "comfort",
    "scene",
    "automation",
] as const;

const roomColors = [
    { value: "#2563eb", label: "蓝色" },
    { value: "#8b5cf6", label: "紫色" },
    { value: "#14b8a6", label: "青色" },
    { value: "#22c55e", label: "绿色" },
    { value: "#f59e0b", label: "橙色" },
    { value: "#f43f5e", label: "红色" },
    { value: "#94a3b8", label: "灰色" },
] as const;

const roomTypes = [
    { value: "living", label: "客厅", icon: "home" },
    { value: "bedroom", label: "卧室", icon: "room" },
    { value: "study", label: "书房", icon: "comfort" },
    { value: "kitchen", label: "厨房", icon: "plug" },
    { value: "balcony", label: "阳台", icon: "illumination" },
    { value: "bathroom", label: "卫生间", icon: "humidity" },
] as const;

interface DeviceItem {
    name: string;
    icon: string;
}

const deviceList: DeviceItem[] = [
    { name: "灯光", icon: "light" },
    { name: "空调", icon: "air-conditioner" },
    { name: "窗帘", icon: "curtain" },
    { name: "插座", icon: "plug" },
    { name: "电视", icon: "device-management" },
    { name: "空气净化器", icon: "sensor" },
    { name: "摄像头", icon: "camera" },
    { name: "门锁", icon: "lock" },
    { name: "传感器", icon: "sensor" },
];

const title = computed(() =>
    props.mode === "edit" ? "编辑房间" : "添加房间",
);
const description = computed(() =>
    props.mode === "edit"
        ? "修改房间信息、设备分组与控制偏好"
        : "创建新房间并绑定设备，完善家庭空间管理",
);
const confirmText = computed(() =>
    props.mode === "edit" ? "保存修改" : "创建房间",
);

const deviceCount = computed(() => selectedDevices.length);

const previewDevices = computed(() => selectedDevices.slice(0, 3));

const dragIndex = ref<number | null>(null);

const toggleDevice = (device: string) => {
    const idx = selectedDevices.indexOf(device);
    if (idx >= 0) {
        selectedDevices.splice(idx, 1);
    } else {
        selectedDevices.push(device);
    }
};

const handleDragStart = (index: number, e: DragEvent) => {
    dragIndex.value = index;
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", String(index));
    }
};

const handleDragOver = (index: number, e: DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
};

const handleDrop = (index: number, e: DragEvent) => {
    e.preventDefault();
    const from = dragIndex.value;
    if (from === null || from === index) return;
    const item = selectedDevices.splice(from, 1)[0];
    if (item === undefined) return;
    selectedDevices.splice(index, 0, item);
    dragIndex.value = null;
};

const handleDragEnd = () => {
    dragIndex.value = null;
};

const validate = (): boolean => {
    if (!roomForm.name.trim()) {
        nameError.value = "请输入房间名称";
        return false;
    }
    nameError.value = "";
    return true;
};

watch(
    () => [props.modelValue, props.room, props.mode] as const,
    () => {
        if (props.modelValue) {
            if (props.mode === "edit" && props.room) {
                roomForm.name = props.room.name;
                roomForm.floor = props.room.floor;
                roomForm.roomType = props.room.roomType;
            } else {
                roomForm.name = "";
                roomForm.floor = "1F";
                roomForm.roomType = "living";
            }
            selectedDevices.splice(0);
            nameError.value = "";
        }
    },
    { immediate: true },
);

const close = () => emit("update:modelValue", false);

const confirm = () => {
    if (!validate()) return;

    if (props.mode === "edit" && props.room) {
        emit("update", { ...props.room, ...roomForm });
    } else {
        emit("create", {
            ...roomForm,
            icon: selectedIcon.value,
            themeColor: selectedColor.value,
            deviceIds: selectedDevices.map((_, i) => i + 1),
        });
    }
    close();
};

const preferenceItems = [
    { label: "常用设备置顶", desc: "在房间卡片中优先显示常用设备" },
    { label: "显示环境卡片", desc: "在房间卡片中显示温湿度等环境数据" },
    { label: "显示场景快捷入口", desc: "在房间卡片中显示场景切换入口" },
] as const;
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
            <!-- ===== 左侧表单（可滑动） ===== -->
            <section class="editor-form">
                <div class="editor-form-scroll">
                <!-- 基本信息 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="room" size="sm" />
                        <span>基本信息</span>
                    </div>
                    <div class="field-row">
                        <label class="field">
                            <span class="field-label">房间名称</span>
                            <div class="input-wrap" :class="{ 'is-error': nameError }">
                                <SvgIcon name="edit" size="sm" class="input-icon" />
                                <input
                                    v-model="roomForm.name"
                                    maxlength="20"
                                    placeholder="请输入房间名称"
                                    @input="nameError = ''"
                                />
                                <span class="field-count">{{ roomForm.name.length }}/20</span>
                            </div>
                            <span v-if="nameError" class="field-error">{{ nameError }}</span>
                        </label>
                        <label class="field">
                            <span class="field-label">楼层 / 区域</span>
                            <div class="input-wrap">
                                <SvgIcon name="more" size="sm" class="input-icon" />
                                <select v-model="roomForm.floor">
                                    <option value="1F">1F</option>
                                    <option value="2F">2F</option>
                                    <option value="B1">地下室</option>
                                </select>
                            </div>
                        </label>
                        <label v-if="mode === 'create'" class="field">
                            <span class="field-label">房间类型</span>
                            <div class="input-wrap">
                                <SvgIcon name="comfort" size="sm" class="input-icon" />
                                <select v-model="roomForm.roomType">
                                    <option
                                        v-for="rt in roomTypes"
                                        :key="rt.value"
                                        :value="rt.value"
                                    >
                                        {{ rt.label }}
                                    </option>
                                </select>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- 房间类型快速选择（创建模式） -->
                <div v-if="mode === 'create'" class="section-card">
                    <div class="section-head">
                        <SvgIcon name="comfort" size="sm" />
                        <span>快速选择房间类型</span>
                    </div>
                    <div class="type-grid">
                        <button
                            v-for="rt in roomTypes"
                            :key="rt.value"
                            type="button"
                            :class="{
                                active: roomForm.roomType === rt.value,
                                selected: roomForm.roomType === rt.value,
                            }"
                            :style="{
                                '--type-color':
                                    roomForm.roomType === rt.value
                                        ? selectedColor
                                        : 'var(--color-text-tertiary)',
                            }"
                            @click="roomForm.roomType = rt.value"
                        >
                            <span class="type-icon">
                                <SvgIcon :name="rt.icon" size="sm" />
                            </span>
                            <span class="type-label">{{ rt.label }}</span>
                        </button>
                    </div>
                </div>

                <!-- 房间图标 + 主题颜色 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="scene" size="sm" />
                        <span>外观设置</span>
                    </div>
                    <div class="appearance-group">
                        <fieldset class="icon-picker">
                            <legend>房间图标</legend>
                            <div class="icon-grid">
                                <button
                                    v-for="icon in roomIcons"
                                    :key="icon"
                                    :class="{ active: selectedIcon === icon }"
                                    type="button"
                                    :title="icon"
                                    @click="selectedIcon = icon"
                                >
                                    <SvgIcon :name="icon" />
                                </button>
                            </div>
                        </fieldset>

                        <fieldset class="color-picker">
                            <legend>主题颜色</legend>
                            <div class="color-grid">
                                <button
                                    v-for="c in roomColors"
                                    :key="c.value"
                                    type="button"
                                    :class="{ active: selectedColor === c.value }"
                                    :style="{ '--dot-color': c.value }"
                                    class="color-dot"
                                    :title="c.label"
                                    @click="selectedColor = c.value"
                                >
                                    <svg
                                        v-if="selectedColor === c.value"
                                        class="color-check"
                                        viewBox="0 0 16 16"
                                        fill="currentColor"
                                    >
                                        <path
                                            d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.75.75 0 0 1 1.06-1.06L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0z"
                                        />
                                    </svg>
                                </button>
                                <span class="color-label">{{
                                    roomColors.find((c) => c.value === selectedColor)?.label ??
                                    ""
                                }}</span>
                            </div>
                        </fieldset>
                    </div>
                </div>

                <!-- 设备绑定 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="device-management" size="sm" />
                        <span>
                            {{ mode === "edit" ? "已绑定设备" : "绑定设备" }}
                        </span>
                        <sup class="device-badge">{{ deviceCount }}</sup>
                    </div>
                    <div class="device-grid">
                        <button
                            v-for="(item, index) in deviceList"
                            :key="item.name"
                            type="button"
                            :class="{
                                active: selectedDevices.includes(item.name),
                                dragging: selectedDevices.includes(item.name) && dragIndex === selectedDevices.indexOf(item.name),
                            }"
                            @click="toggleDevice(item.name)"
                            :draggable="selectedDevices.includes(item.name)"
                            @dragstart="
                                selectedDevices.includes(item.name) &&
                                    handleDragStart(selectedDevices.indexOf(item.name), $event)
                            "
                            @dragover="
                                selectedDevices.includes(item.name) &&
                                    handleDragOver(selectedDevices.indexOf(item.name), $event)
                            "
                            @drop="
                                selectedDevices.includes(item.name) &&
                                    handleDrop(selectedDevices.indexOf(item.name), $event)
                            "
                            @dragend="handleDragEnd"
                        >
                            <span class="device-icon">
                                <SvgIcon :name="item.icon" size="sm" />
                            </span>
                            <span class="device-name">{{ item.name }}</span>
                            <span class="device-check">✓</span>
                        </button>
                    </div>
                </div>

                <!-- 快捷控制偏好（仅编辑模式） -->
                <section v-if="mode === 'edit'" class="section-card">
                    <div class="section-head">
                        <SvgIcon name="automation" size="sm" />
                        <span>快捷控制偏好</span>
                    </div>
                    <div class="pref-list">
                        <label
                            v-for="item in preferenceItems"
                            :key="item.label"
                            class="pref-item"
                        >
                            <span class="pref-text">
                                {{ item.label }}
                                <small>{{ item.desc }}</small>
                            </span>
                            <span class="toggle-switch">
                                <input type="checkbox" checked />
                                <span class="toggle-track" />
                            </span>
                        </label>
                    </div>
                </section>
                </div>
            </section>

            <!-- ===== 右侧预览（固定，不滑动） ===== -->
            <aside class="room-preview">
                <div class="preview-header">
                    <SvgIcon name="scene" size="sm" />
                    <span>房间预览</span>
                </div>

                <!-- 预览卡片 — 与 RoomControl 页面一致的房间卡片样式 -->
                <article class="preview-room-card">
                    <header>
                        <span
                            class="preview-room-avatar"
                            :class="roomForm.roomType ? `is-${roomForm.roomType}` : ''"
                        >{{ (roomForm.name || '未命名').slice(0, 1) }}</span>
                        <div class="preview-room-title">
                            <h2>{{ roomForm.name || "未命名房间" }}</h2>
                            <p class="preview-room-status">
                                <small>{{ (room?.comfort ?? 81) >= 84 ? "舒适" : "良好" }}</small>
                                <b></b>
                                {{
                                    roomTypes.find((rt) => rt.value === roomForm.roomType)
                                        ?.label ?? roomForm.roomType
                                }}
                                · {{ roomForm.floor }}
                            </p>
                        </div>
                    </header>
                    <div class="preview-room-metrics">
                        <span>
                            <SvgIcon name="temperature" size="sm" />
                            {{ room?.temperature ?? "--" }}°C
                        </span>
                        <span>
                            <SvgIcon name="humidity" size="sm" />
                            {{ room?.humidity ?? "--" }}%
                        </span>
                        <span class="quality">
                            <SvgIcon name="air-quality" size="sm" />
                            {{ room?.pm25 ?? "--" }}
                        </span>
                    </div>
                    <div class="preview-room-devices">
                        <button
                            v-for="item in previewDevices"
                            :key="item"
                            type="button"
                            class="on"
                        >
                            <i>
                                <SvgIcon
                                    :name="deviceList.find((d) => d.name === item)?.icon ?? 'room'"
                                    size="sm"
                                />
                            </i>
                            <span>{{ item }}</span>
                            <small>开</small>
                        </button>
                        <div v-if="deviceCount === 0" class="preview-device-empty">
                            <SvgIcon name="plus" size="sm" />
                            <span>请选择设备</span>
                        </div>
                        <div
                            v-if="deviceCount > 3"
                            class="preview-device-more"
                        >
                            <span>+{{ deviceCount - 3 }}</span>
                            <small>更多</small>
                        </div>
                    </div>
                </article>

                <div class="preview-tip">
                    <SvgIcon name="light" size="sm" />
                    <span>调整右侧选项实时预览效果</span>
                </div>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* =============================================
   主布局
   ============================================= */
.room-editor {
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 24px;
    align-items: start;
}

.editor-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.editor-form-scroll {
    overflow-y: auto;
    max-height: 460px;
    padding-right: 4px;
}

.editor-form-scroll::-webkit-scrollbar {
    width: 4px;
}

.editor-form-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.editor-form-scroll::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border-strong);
}

/* =============================================
   分区卡片
   ============================================= */
.section-card {
    border: 1.5px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 16px;
    transition: box-shadow 0.2s;
}

.section-card:hover {
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.section-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text);
    letter-spacing: 0.01em;
}

.section-head .section-head-icon {
    color: var(--color-primary-500);
}

/* =============================================
   表单字段
   ============================================= */
.field-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    position: relative;
}

.field-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-secondary);
    letter-spacing: 0.02em;
}

.input-wrap {
    position: relative;
    display: flex;
    align-items: center;
}

.input-wrap .input-icon {
    position: absolute;
    left: 11px;
    color: var(--color-text-tertiary);
    pointer-events: none;
    transition: color 0.2s;
}

.input-wrap:focus-within .input-icon {
    color: var(--color-primary-500);
}

.input-wrap input,
.input-wrap select {
    width: 100%;
    height: 40px;
    padding: 0 12px 0 34px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    font-size: 14px;
    color: var(--color-text-primary);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
    appearance: none;
    -webkit-appearance: none;
}

.input-wrap select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.input-wrap select {
    padding-right: 32px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 14px;
}

.input-wrap input:focus,
.input-wrap select:focus {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-primary-50);
    background: var(--color-card-bg);
}

.input-wrap.is-error input {
    border-color: var(--color-danger, #f43f5e);
    box-shadow: 0 0 0 3px #f43f5e14;
}

.input-wrap.is-error .input-icon {
    color: var(--color-danger, #f43f5e);
}

.field-error {
    font-size: 11px;
    color: var(--color-danger, #f43f5e);
    position: absolute;
    bottom: -18px;
    left: 0;
    font-weight: 600;
}

.field-count {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 11px;
    color: var(--color-text-tertiary);
    pointer-events: none;
    font-weight: 600;
}

/* =============================================
   房间类型快速选择
   ============================================= */
.type-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.type-grid button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 10px 6px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    cursor: pointer;
    transition: all 0.25s ease;
    color: var(--color-text-tertiary);
}

.type-grid button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.type-grid button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 3px var(--color-primary-100);
}

.type-icon {
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-card-bg);
    border: 1px solid var(--color-border);
    transition: all 0.25s;
}

.type-grid button.active .type-icon {
    border-color: transparent;
    background: var(--color-primary-100);
}

.type-label {
    font-size: 11px;
    font-weight: 700;
    line-height: 1.2;
}

/* =============================================
   外观设置 - 图标 + 颜色
   ============================================= */
.appearance-group {
    display: grid;
    gap: 16px;
}

.icon-picker,
.color-picker {
    border: 0;
    padding: 0;
    margin: 0;
}

.icon-picker legend,
.color-picker legend {
    width: 100%;
    margin-bottom: 10px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    letter-spacing: 0.02em;
}

/* 图标网格 */
.icon-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.icon-grid button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 40px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.icon-grid button:hover {
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.icon-grid button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 3px var(--color-primary-100);
}

/* 颜色网格 */
.color-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
}

.color-dot {
    width: 30px;
    height: 30px;
    border: 3px solid transparent;
    border-radius: 50%;
    background: var(--dot-color);
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    position: relative;
}

.color-dot:hover {
    transform: scale(1.2);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.18);
}

.color-dot.active {
    border-color: var(--color-border);
    box-shadow: 0 0 0 2px var(--color-primary-200), 0 3px 12px rgba(0, 0, 0, 0.12);
    transform: scale(1.15);
}

.color-check {
    width: 14px;
    height: 14px;
    color: #fff;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.35));
}

.color-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-tertiary);
    margin-left: 2px;
}

/* =============================================
   设备绑定
   ============================================= */
.device-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    border-radius: 10px;
    background: var(--color-primary-500);
    color: #fff;
    font-size: 10px;
    font-weight: 800;
    line-height: 1;
    margin-left: 2px;
}

.device-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.device-grid button {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 40px;
    padding: 0 10px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.device-grid button::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 0 2px 2px 0;
    background: var(--color-primary-500);
    opacity: 0;
    transition: opacity 0.2s;
}

.device-grid button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.device-grid button.active {
    border-color: var(--color-primary-500);
    background: linear-gradient(135deg, var(--color-primary-50) 0%, var(--color-card-bg) 100%);
    color: var(--color-primary-700);
}

.device-grid button.active::before {
    opacity: 1;
}

.device-grid button.dragging {
    opacity: 0.5;
    transform: scale(0.95);
    border-style: dashed;
}

.device-grid button[draggable="true"] {
    cursor: grab;
}

.device-grid button[draggable="true"]:active {
    cursor: grabbing;
}

.device-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 6px;
    background: var(--color-card-bg);
    border: 1px solid var(--color-border);
    transition: all 0.2s;
    flex-shrink: 0;
}

.device-grid button.active .device-icon {
    border-color: var(--color-primary-200);
    background: var(--color-primary-100);
}

.device-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-check {
    font-weight: 700;
    font-size: 11px;
    opacity: 0;
    transition: opacity 0.2s, transform 0.2s;
    transform: scale(0.5);
    width: 16px;
    text-align: center;
    flex-shrink: 0;
}

.device-grid button.active .device-check {
    opacity: 1;
    transform: scale(1);
    color: var(--color-primary-600);
}

/* =============================================
   快捷控制偏好（编辑模式）
   ============================================= */
.pref-list {
    display: flex;
    flex-direction: column;
}

.pref-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    cursor: pointer;
    border-radius: 6px;
    transition: background 0.15s;
    padding-left: 4px;
    padding-right: 4px;
}

.pref-item + .pref-item {
    border-top: 1px solid var(--color-border-subtle);
}

.pref-item:hover {
    background: var(--color-surface-subtle);
}

.pref-text {
    font-size: 13px;
    line-height: 1.3;
    user-select: none;
}

.pref-text small {
    display: block;
    font-size: 11px;
    color: var(--color-text-tertiary);
    margin-top: 2px;
}

/* 自定义 toggle switch */
.toggle-switch {
    position: relative;
    display: inline-flex;
    align-items: center;
    width: 36px;
    height: 20px;
    flex-shrink: 0;
}

.toggle-switch input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.toggle-track {
    width: 100%;
    height: 100%;
    border-radius: 10px;
    background: var(--color-border);
    transition: background 0.25s ease;
    cursor: pointer;
    position: relative;
}

.toggle-track::after {
    content: "";
    position: absolute;
    left: 2px;
    top: 2px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #fff;
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-switch input:checked + .toggle-track {
    background: var(--color-primary-500);
}

.toggle-switch input:checked + .toggle-track::after {
    transform: translateX(16px);
}

/* =============================================
   右侧预览面板
   ============================================= */
.room-preview {
    display: flex;
    flex-direction: column;
    gap: 14px;
    border: 1.5px solid var(--color-border);
    border-radius: 14px;
    background: linear-gradient(
        180deg,
        var(--color-card-bg) 0%,
        var(--color-surface-subtle) 100%
    );
    padding: 20px;
    align-self: center;
}

.preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text);
}

/* 预览房间卡片 — 与 RoomControl 页面 RoomCard 一致 */
.preview-room-card {
    position: relative;
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 16px;
    box-shadow: var(--shadow-card);
    transition: 160ms var(--motion-ease);
    overflow: hidden;
}

.preview-room-card:hover {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
}

.preview-room-card > header {
    display: flex;
    align-items: center;
    gap: 10px;
}

.preview-room-avatar {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 auto;
    place-items: center;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
    font-weight: 900;
    font-size: 18px;
}

.preview-room-avatar.is-living {
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
}
.preview-room-avatar.is-bedroom {
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--tone-indigo) 12%, var(--color-panel-background)),
        var(--tone-indigo-soft)
    );
    color: var(--color-scene-sleep);
}
.preview-room-avatar.is-study {
    background: linear-gradient(135deg, var(--color-teal-soft), #f0fdfa);
    color: var(--color-teal-600);
}
.preview-room-avatar.is-kitchen {
    background: linear-gradient(135deg, var(--color-warning-soft), #fffbeb);
    color: var(--color-device-light);
}
.preview-room-avatar.is-bathroom {
    background: linear-gradient(135deg, var(--color-info-soft), #f0f9ff);
    color: var(--color-info);
}
.preview-room-avatar.is-balcony {
    background: linear-gradient(135deg, var(--color-success-soft), #f0fdf4);
    color: var(--color-device-air);
}

.preview-room-title {
    min-width: 0;
    flex: 1;
}

.preview-room-title h2 {
    overflow: hidden;
    margin: 0;
    font-size: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-room-status {
    display: flex;
    align-items: center;
    gap: 5px;
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.preview-room-status small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 1px 6px;
    color: var(--color-success);
    font-size: 9px;
    line-height: 1.4;
}

.preview-room-status b {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
}

.preview-room-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 7px;
    margin-top: 14px;
}

.preview-room-metrics span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    min-height: 34px;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    padding: 5px 7px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
}

.preview-room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.preview-room-devices {
    display: flex;
    gap: 7px;
    margin-top: 8px;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding: 0 0 4px;
    scrollbar-width: thin;
}

.preview-room-devices::-webkit-scrollbar {
    height: 3px;
}

.preview-room-devices::-webkit-scrollbar-track {
    border-radius: 2px;
    background: var(--color-surface-subtle);
}

.preview-room-devices::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border-strong);
}

.preview-room-devices button {
    display: grid;
    min-width: 82px;
    flex: 0 0 auto;
    place-items: center;
    gap: 4px;
    min-height: 68px;
    border: 1px solid transparent;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    padding: 8px 10px;
    color: var(--color-text-tertiary);
    font-size: 10px;
    scroll-snap-align: start;
    transition: 160ms var(--motion-ease);
}

.preview-room-devices button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-surface-hover);
}

.preview-room-devices button.on {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.preview-room-devices i {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-card-bg);
    font-style: normal;
}

.preview-room-devices span {
    overflow: hidden;
    max-width: 100%;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 800;
}

.preview-room-devices small {
    color: var(--color-text-muted);
    font-size: 9px;
}

.preview-room-devices button.on small {
    color: var(--color-primary-600);
}

.preview-device-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
    min-height: 62px;
    border-radius: 10px;
    border: 1.5px dashed var(--color-border);
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
    flex: 1;
}

.preview-device-more {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-width: 52px;
    flex: 0 0 auto;
    min-height: 62px;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    border: 1px dashed var(--color-border);
    color: var(--color-text-tertiary);
    scroll-snap-align: start;
}

.preview-device-more span {
    font-size: 14px;
    font-weight: 900;
    line-height: 1;
}

.preview-device-more small {
    font-size: 9px;
    color: var(--color-text-muted);
}

/* 提示条 */
.preview-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 10px;
    border-radius: 8px;
    background: var(--color-primary-50);
    font-size: 11px;
    color: var(--color-primary-600);
    font-weight: 600;
}

/* =============================================
   响应式
   ============================================= */
@media (max-width: 900px) {
    .room-editor {
        grid-template-columns: 1fr;
    }

    .room-preview {
        position: static;
    }

    .field-row {
        grid-template-columns: 1fr;
    }

    .type-grid {
        grid-template-columns: repeat(3, 1fr);
    }

    .device-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .type-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .device-grid {
        grid-template-columns: 1fr;
    }
}
</style>