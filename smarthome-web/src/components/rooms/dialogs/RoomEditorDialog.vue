<script setup lang="ts">
import { reactive, ref, watch, computed } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { listDevices } from "../../../api/device";
import { getDeviceTypeIcon } from "../../device/deviceMeta";
import type { Room } from "../../../types/room";
import type { Device } from "../../../types/device";

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
const customRoomType = ref("");
const selectedIcon = ref("room");
const selectedColor = ref("#2563eb");
const selectedDevices = reactive<number[]>([]);
const nameError = ref("");
const hoveredIcon = ref("");
const hoveredColor = ref("");

// 设备列表（从后端加载）
const deviceList = ref<Device[]>([]);
const loadingDevices = ref(false);

const roomIcons = [
    "room",
    "home",
    "device-management",
    "comfort",
    "scene",
    "automation",
    "light",
    "air-conditioner",
    "curtain",
    "lock",
    "camera",
    "sensor",
    "plug",
    "temperature",
    "humidity",
    "air-quality",
    "illumination",
    "noise",
    "power",
    "calendar",
    "clock",
    "scan",
    "group",
    "security",
    "energy",
    "location",
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
    { value: "custom", label: "自定义", icon: "edit" },
] as const;

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

const previewDevices = computed(() => {
    return selectedDevices.slice(0, 3).map((id) =>
        deviceList.value.find((d) => d.id === id),
    ).filter((d): d is Device => d !== undefined);
});

const dragIndex = ref<number | null>(null);

const toggleDevice = (deviceId: number) => {
    const idx = selectedDevices.indexOf(deviceId);
    if (idx >= 0) {
        selectedDevices.splice(idx, 1);
    } else {
        selectedDevices.push(deviceId);
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
    async () => {
        if (props.modelValue) {
            // 从后端加载设备列表
            loadingDevices.value = true;
            try {
                const response = await listDevices({
                    page: 1,
                    pageSize: 100,
                    keyword: "",
                    type: "",
                    status: "",
                    room: "",
                });
                deviceList.value = response.items;
            } catch (e) {
                console.error("加载设备列表失败", e);
                deviceList.value = [];
            } finally {
                loadingDevices.value = false;
            }

            if (props.mode === "edit" && props.room) {
                roomForm.name = props.room.name;
                roomForm.floor = props.room.floor;
                roomForm.roomType = props.room.roomType;
                selectedIcon.value = props.room.icon || "room";
                selectedColor.value = props.room.themeColor || "#2563eb";
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

    const finalRoomType = roomForm.roomType === "custom" ? customRoomType.value : roomForm.roomType;
    const formData = { ...roomForm, roomType: finalRoomType };

    if (props.mode === "edit" && props.room) {
        emit("update", { ...props.room, ...formData });
    } else {
        emit("create", {
            ...formData,
            icon: selectedIcon.value,
            themeColor: selectedColor.value,
            deviceIds: [...selectedDevices],
        });
    }
    close();
};

const roomTypeColorMap: Record<string, string> = {
    living: "var(--color-primary-500)",
    bedroom: "var(--tone-indigo)",
    study: "var(--color-teal-600)",
    kitchen: "var(--color-device-light)",
    balcony: "var(--color-success)",
    bathroom: "var(--color-info)",
};

const roomTypeBgMap: Record<string, string> = {
    living: "var(--color-primary-50)",
    bedroom: "var(--tone-indigo-soft)",
    study: "var(--color-teal-soft)",
    kitchen: "var(--color-warning-soft)",
    balcony: "var(--color-success-soft)",
    bathroom: "var(--color-info-soft)",
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
            <!-- ===== 左侧表单（可滑动） ===== -->
            <section class="editor-form">
                <div class="editor-form-scroll">
                <!-- 基本信息 -->
                <div class="section-card">
                    <div class="section-head">
                        <span class="section-head-icon"><SvgIcon name="room" size="sm" /></span>
                        <span>基本信息</span>
                    </div>
                    <div class="field-row">
                        <label class="field">
                            <span class="field-label">
                                <SvgIcon name="edit" size="sm" />
                                房间名称
                            </span>
                            <div class="input-wrap" :class="{ 'is-error': nameError }">
                                <input
                                    v-model="roomForm.name"
                                    maxlength="20"
                                    placeholder="请输入房间名称"
                                    @input="nameError = ''"
                                />
                                <span class="field-count">{{ roomForm.name.length }}/20</span>
                            </div>
                            <Transition name="field-error-enter">
                                <span v-if="nameError" class="field-error">{{ nameError }}</span>
                            </Transition>
                        </label>
                        <label class="field">
                            <span class="field-label">
                                <SvgIcon name="home" size="sm" />
                                楼层 / 区域
                            </span>
                            <div class="input-wrap">
                                <select v-model="roomForm.floor">
                                    <option value="1F">1F</option>
                                    <option value="2F">2F</option>
                                    <option value="B1">地下室</option>
                                </select>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- 房间类型快速选择 -->
                <div class="section-card">
                    <div class="section-head">
                        <span class="section-head-icon"><SvgIcon name="comfort" size="sm" /></span>
                        <span>房间类型</span>
                    </div>
                    <div class="type-grid">
                        <button
                            v-for="rt in roomTypes"
                            :key="rt.value"
                            type="button"
                            :class="{ active: roomForm.roomType === rt.value }"
                            :style="{
                                '--type-color': roomTypeColorMap[rt.value],
                                '--type-bg': roomTypeBgMap[rt.value],
                            }"
                            :title="rt.label"
                            @click="roomForm.roomType = rt.value"
                        >
                            <span
                                class="type-icon"
                                :style="{ '--icon-bg': roomTypeBgMap[rt.value] }"
                            >
                                <SvgIcon :name="rt.icon" size="sm" />
                            </span>
                            <span class="type-label">{{ rt.label }}</span>
                            <span class="type-check">
                                <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14">
                                    <path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.75.75 0 0 1 1.06-1.06L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0z" />
                                </svg>
                            </span>
                        </button>
                        <div v-if="roomForm.roomType === 'custom'" class="custom-type-field">
                            <input
                                v-model="customRoomType"
                                placeholder="输入自定义类型名称"
                                maxlength="20"
                            />
                        </div>
                    </div>
                </div>

                <!-- 房间图标 + 主题颜色 -->
                <div class="section-card">
                    <div class="section-head">
                        <span class="section-head-icon"><SvgIcon name="scene" size="sm" /></span>
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
                                    @mouseenter="hoveredIcon = icon"
                                    @mouseleave="hoveredIcon = ''"
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
                                    @mouseenter="hoveredColor = c.value"
                                    @mouseleave="hoveredColor = ''"
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
                        <span class="section-head-icon"><SvgIcon name="device-management" size="sm" /></span>
                        <span>
                            {{ mode === "edit" ? "已绑定设备" : "绑定设备" }}
                        </span>
                        <sup class="device-badge">{{ deviceCount }}</sup>
                    </div>
                    <div class="device-grid">
                        <button
                            v-for="(item, index) in deviceList"
                            :key="item.id"
                            type="button"
                            :class="{
                                active: selectedDevices.includes(item.id),
                                dragging: selectedDevices.includes(item.id) && dragIndex === selectedDevices.indexOf(item.id),
                            }"
                            @click="toggleDevice(item.id)"
                            :draggable="selectedDevices.includes(item.id)"
                            @dragstart="
                                selectedDevices.includes(item.id) &&
                                    handleDragStart(selectedDevices.indexOf(item.id), $event)
                            "
                            @dragover="
                                selectedDevices.includes(item.id) &&
                                    handleDragOver(selectedDevices.indexOf(item.id), $event)
                            "
                            @drop="
                                selectedDevices.includes(item.id) &&
                                    handleDrop(selectedDevices.indexOf(item.id), $event)
                            "
                            @dragend="handleDragEnd"
                        >
                            <span class="device-icon" :style="{ '--device-color': item.color || '#6b7280' }">
                                <SvgIcon :name="item.icon || getDeviceTypeIcon(item.type)" size="sm" />
                            </span>
                            <span class="device-name">{{ item.name }}</span>
                            <span class="device-check">
                                <svg viewBox="0 0 16 16" fill="currentColor" width="14" height="14">
                                    <path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.75.75 0 0 1 1.06-1.06L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0z" />
                                </svg>
                            </span>
                        </button>
                    </div>
                </div>
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
                            :style="{ '--avatar-color': roomTypeColorMap[roomForm.roomType] || 'var(--color-primary-500)' }"
                        >{{ (roomForm.name || '未命名').slice(0, 1) }}</span>
                        <div class="preview-room-title">
                            <h2>{{ roomForm.name || "未命名房间" }}</h2>
                            <p class="preview-room-status">
                                <small>{{ (room?.comfort ?? 81) >= 84 ? "舒适" : "良好" }}</small>
                                <span class="status-sep" />
                                {{
                                    roomForm.roomType === "custom"
                                        ? (customRoomType || "自定义")
                                        : (roomTypes.find((rt) => rt.value === roomForm.roomType)
                                            ?.label ?? roomForm.roomType)
                                }}
                                <span class="status-sep" />
                                {{ roomForm.floor }}
                            </p>
                        </div>
                    </header>
                    <div class="preview-room-devices">
                        <button
                            v-for="device in previewDevices"
                            :key="device.id"
                            type="button"
                            class="on"
                        >
                            <i :style="{ '--device-color': device.color || '#6b7280' }">
                                <SvgIcon
                                    :name="device.icon || getDeviceTypeIcon(device.type)"
                                    size="sm"
                                />
                            </i>
                            <span>{{ device.name }}</span>
                            <small>{{ device.status === "online" ? "开" : "关" }}</small>
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
    height: min(520px, calc(100vh - 260px));
    min-height: 0;
    grid-template-columns: 1.4fr 1fr;
    gap: 24px;
    align-items: stretch;
    overflow: hidden;
}

.editor-form {
    display: flex;
    min-height: 0;
    flex-direction: column;
    gap: 16px;
}

.editor-form-scroll {
    height: 100%;
    min-height: 0;
    overflow-y: auto;
    max-height: none;
    padding-right: 4px;
    scroll-behavior: smooth;
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
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 18px;
    box-shadow: var(--shadow-card);
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease);
}

.section-card:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
}

.section-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    font-size: 14px;
    font-weight: 700;
    color: var(--color-text-primary);
    letter-spacing: 0.01em;
}

.section-head-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--color-primary-50), var(--color-card-bg));
    color: var(--color-primary-600);
}

/* =============================================
   表单字段
   ============================================= */
.field-row {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    position: relative;
}

.field-label {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
    letter-spacing: 0.02em;
}

.field-label svg {
    width: 14px;
    height: 14px;
    color: var(--color-text-muted);
}

.input-wrap {
    position: relative;
    display: flex;
    align-items: center;
}

.input-wrap input,
.input-wrap select {
    width: 100%;
    height: 42px;
    padding: 0 14px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    font-size: 15px;
}

.input-wrap select {
    padding-right: 32px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    background-size: 14px;
}

.input-wrap select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.input-wrap input:hover,
.input-wrap select:hover {
    border-color: var(--color-primary-300);
    background: color-mix(in srgb, var(--color-card-bg) 92%, var(--color-primary-50));
}

.input-wrap input:focus,
.input-wrap select:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
    background: var(--color-card-bg);
}

.input-wrap.is-error input {
    border-color: var(--color-danger);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-danger) 14%, transparent);
}

.field-error {
    font-size: 12px;
    color: var(--color-danger);
    font-weight: 600;
    margin-top: 2px;
    padding-left: 2px;
}

.field-error-enter-enter-active {
    transition: opacity 200ms var(--motion-ease), transform 200ms var(--motion-ease);
}

.field-error-enter-enter-from {
    opacity: 0;
    transform: translateY(-4px);
}

.field-count {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    color: var(--color-text-muted);
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
    align-items: center;
    gap: 8px;
    height: 44px;
    padding: 0 12px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 14px;
    cursor: pointer;
    transition: all 220ms var(--motion-ease);
    position: relative;
    overflow: hidden;
}

.type-grid button::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 0 2px 2px 0;
    background: var(--type-color);
    opacity: 0;
    transition: opacity 220ms var(--motion-ease);
}

.type-grid button:hover {
    border-color: var(--type-color);
    background: var(--type-bg);
    color: var(--type-color);
    transform: translateY(-1px);
    box-shadow: 0 3px 10px color-mix(in srgb, var(--type-color) 10%, transparent);
}

.type-grid button.active {
    border-color: var(--type-color);
    background: linear-gradient(135deg, var(--type-bg), var(--color-card-bg));
    color: var(--type-color);
    font-weight: 700;
}

.type-grid button.active::before {
    opacity: 1;
}

.type-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 7px;
    background: var(--icon-bg, var(--color-card-bg));
    border: 1px solid color-mix(in srgb, var(--type-color, var(--color-border)) 20%, transparent);
    transition: all 220ms var(--motion-ease);
    flex-shrink: 0;
    color: var(--type-color, var(--color-text-tertiary));
}

.type-grid button.active .type-icon {
    border-color: transparent;
    background: color-mix(in srgb, var(--type-color) 16%, var(--color-card-bg));
    color: var(--type-color);
}

.type-label {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
    font-size: 14px;
    text-align: left;
}

.type-check {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--type-color);
    color: #fff;
    opacity: 0;
    transform: scale(0.3);
    transition: opacity 220ms var(--motion-ease),
                transform 280ms var(--motion-ease);
    flex-shrink: 0;
}

.type-grid button.active .type-check {
    opacity: 1;
    transform: scale(1);
}

.custom-type-field {
    grid-column: 1 / -1;
    margin-top: 4px;
}

.custom-type-field input {
    width: 100%;
    height: 36px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0 10px;
    font-size: 13px;
    outline: none;
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.custom-type-field input:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

/* =============================================
   外观设置 - 图标 + 颜色
   ============================================= */
.appearance-group {
    display: flex;
    flex-direction: column;
    gap: 18px;
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
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    letter-spacing: 0.02em;
}

/* 图标网格 */
.icon-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    max-height: 98px;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-gutter: stable;
}

.icon-grid::-webkit-scrollbar {
    width: 5px;
}

.icon-grid::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: var(--color-border);
}

.icon-grid::-webkit-scrollbar-track {
    background: transparent;
}

.icon-grid button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 44px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    cursor: pointer;
    transition: all 200ms var(--motion-ease);
}

.icon-grid button:hover {
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    transform: translateY(-2px);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
}

.icon-grid button.active {
    border-color: var(--color-primary-500);
    background: linear-gradient(135deg, var(--color-primary-50), color-mix(in srgb, var(--color-primary-50) 60%, var(--color-card-bg)));
    color: var(--color-primary-700);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

/* 颜色网格 */
.color-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
}

.color-dot {
    width: 32px;
    height: 32px;
    border: 3px solid transparent;
    border-radius: 50%;
    background: var(--dot-color);
    cursor: pointer;
    transition: all 280ms var(--motion-ease);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    position: relative;
}

.color-dot:hover {
    transform: scale(1.18);
    box-shadow: 0 2px 12px color-mix(in srgb, var(--dot-color) 40%, transparent);
}

.color-dot.active {
    border-color: var(--color-border);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--dot-color) 50%, transparent), 0 3px 12px rgba(0, 0, 0, 0.1);
    transform: scale(1.12);
}

.color-check {
    width: 14px;
    height: 14px;
    color: #fff;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.35));
}

.color-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-tertiary);
    margin-left: 4px;
    padding: 3px 10px;
    border-radius: 6px;
    background: var(--color-surface-subtle);
}

/* =============================================
   设备绑定
   ============================================= */
.device-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 7px;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600));
    color: #fff;
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
    margin-left: 4px;
    box-shadow: 0 2px 6px color-mix(in srgb, var(--color-primary-500) 30%, transparent);
}

.device-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    max-height: 220px;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-gutter: stable;
}

.device-grid::-webkit-scrollbar {
    width: 6px;
}

.device-grid::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: var(--color-border);
}

.device-grid::-webkit-scrollbar-track {
    background: transparent;
}

.device-grid button {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 44px;
    padding: 0 12px;
    border: 1.5px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 14px;
    cursor: pointer;
    transition: all 220ms var(--motion-ease);
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
    transition: opacity 220ms var(--motion-ease);
}

.device-grid button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
}

.device-grid button.active {
    border-color: var(--color-primary-500);
    background: linear-gradient(135deg, var(--color-primary-50), var(--color-card-bg));
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
    border-radius: 7px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    flex-shrink: 0;
    transition: all 220ms var(--motion-ease);
}

.device-grid button.active .device-icon {
    border-color: color-mix(in srgb, var(--device-color, #6b7280) 30%, transparent);
    background: color-mix(in srgb, var(--device-color, #6b7280) 20%, transparent);
    color: var(--device-color, #6b7280);
}

.device-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
}

.device-check {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--color-primary-500);
    color: #fff;
    opacity: 0;
    transform: scale(0.3);
    transition: opacity 220ms var(--motion-ease),
                transform 280ms var(--motion-ease);
    flex-shrink: 0;
}

.device-grid button.active .device-check {
    opacity: 1;
    transform: scale(1);
}

/* =============================================
   右侧预览面板
   ============================================= */
.room-preview {
    position: static;
    display: flex;
    width: 100%;
    box-sizing: border-box;
    flex-direction: column;
    gap: 14px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: linear-gradient(
        180deg,
        var(--color-card-bg) 0%,
        var(--color-surface-subtle) 100%
    );
    padding: 20px;
    align-self: center;
    transition: border-color 220ms var(--motion-ease);
}

.room-preview:hover {
    border-color: var(--color-border-strong);
}

.preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 700;
    color: var(--color-text-primary);
}

.preview-header svg {
    color: var(--color-primary-600);
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
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease);
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
    transition: background 300ms var(--motion-ease), color 300ms var(--motion-ease);
    box-shadow: 0 4px 12px var(--color-focus-ring);
}

.preview-room-avatar.is-living {
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary-500) 18%, transparent);
}
.preview-room-avatar.is-bedroom {
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--tone-indigo) 12%, var(--color-panel-background)),
        var(--tone-indigo-soft)
    );
    color: var(--color-scene-sleep);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--tone-indigo) 18%, transparent);
}
.preview-room-avatar.is-study {
    background: linear-gradient(135deg, var(--color-teal-soft), #f0fdfa);
    color: var(--color-teal-600);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-teal-600) 18%, transparent);
}
.preview-room-avatar.is-kitchen {
    background: linear-gradient(135deg, var(--color-warning-soft), #fffbeb);
    color: var(--color-device-light);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-device-light) 18%, transparent);
}
.preview-room-avatar.is-bathroom {
    background: linear-gradient(135deg, var(--color-info-soft), #f0f9ff);
    color: var(--color-info);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-info) 18%, transparent);
}
.preview-room-avatar.is-balcony {
    background: linear-gradient(135deg, var(--color-success-soft), #f0fdf4);
    color: var(--color-device-air);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-device-air) 18%, transparent);
}

.preview-room-title {
    min-width: 0;
    flex: 1;
}

.preview-room-title h2 {
    overflow: hidden;
    margin: 0;
    font-size: 17px;
    font-weight: 800;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.preview-room-status {
    display: flex;
    align-items: center;
    gap: 5px;
    margin: 5px 0 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 600;
}

.preview-room-status small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 1px 7px;
    color: var(--color-success);
    font-size: 11px;
    font-weight: 700;
    line-height: 1.5;
}

.status-sep {
    display: inline-block;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--color-text-muted);
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
    font-size: 13px;
    font-weight: 800;
    white-space: nowrap;
    transition: background 180ms var(--motion-ease);
}

.preview-room-metrics span:hover {
    background: var(--color-surface-hover);
}

.preview-room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.preview-room-metrics .quality:hover {
    background: color-mix(in srgb, var(--color-success-soft) 80%, var(--color-success));
}

.preview-room-devices {
    display: flex;
    gap: 7px;
    margin-top: 10px;
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
    transition: border-color 180ms var(--motion-ease),
                background 180ms var(--motion-ease),
                color 180ms var(--motion-ease),
                transform 180ms var(--motion-ease);
}

.preview-room-devices button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-surface-hover);
    transform: translateY(-1px);
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
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    font-style: normal;
    transition: background 180ms var(--motion-ease);
}

.preview-room-devices button.on i {
    background: var(--color-primary-100);
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
    font-size: 10px;
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
    color: var(--color-text-muted);
    font-size: 12px;
    font-weight: 600;
    flex: 1;
    transition: border-color 180ms var(--motion-ease),
                background 180ms var(--motion-ease);
}

.preview-device-empty:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
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
    transition: border-color 180ms var(--motion-ease),
                background 180ms var(--motion-ease);
}

.preview-device-more:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
}

.preview-device-more span {
    font-size: 14px;
    font-weight: 900;
    line-height: 1;
}

.preview-device-more small {
    font-size: 10px;
    color: var(--color-text-muted);
}

/* 提示条 */
.preview-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--color-primary-50), color-mix(in srgb, var(--color-primary-50) 60%, var(--color-card-bg)));
    font-size: 12px;
    color: var(--color-primary-600);
    font-weight: 600;
    transition: background 180ms var(--motion-ease);
}

.preview-tip:hover {
    background: var(--color-primary-50);
}

/* =============================================
   响应式
   ============================================= */
@media (max-width: 900px) {
    .room-editor {
        height: auto;
        grid-template-columns: 1fr;
        overflow: visible;
    }

    .room-preview {
        position: static;
    }

    .editor-form-scroll {
        height: auto;
        max-height: 520px;
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
