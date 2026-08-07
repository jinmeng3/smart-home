<script setup lang="ts">
import { reactive, ref, watch, computed } from "vue";
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

const deviceOptions = [
    { name: "灯光", icon: "light" },
    { name: "空调", icon: "air-conditioner" },
    { name: "传感器", icon: "sensor" },
    { name: "窗帘", icon: "curtain" },
    { name: "摄像头", icon: "camera" },
    { name: "门锁", icon: "lock" },
];

const deviceCount = computed(() => roomDevices.length);
const previewDevices = computed(() => roomDevices.slice(0, 3));
const dragIndex = ref<number | null>(null);

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
    const item = roomDevices.splice(from, 1)[0];
    if (item === undefined) return;
    roomDevices.splice(index, 0, item);
    dragIndex.value = null;
};

const handleDragEnd = () => {
    dragIndex.value = null;
};

const confirm = async () => {
    if (!roomName.value.trim()) {
        nameError.value = "请输入房间名称";
        return;
    }
    nameError.value = "";
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
        description="创建新的房间并绑定设备，完善家庭空间管理"
        :width="760"
        :loading="loading"
        confirm-text="创建房间"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="room-layout">
            <!-- ===== 左侧表单（可滑动） ===== -->
            <div class="form-stack">
                <div class="form-stack-scroll">
                <!-- 基本信息 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="room" size="sm" />
                        <span>基本信息</span>
                    </div>
                    <label class="field">
                        <span class="field-label">房间名称</span>
                        <div class="input-wrap" :class="{ 'is-error': nameError }">
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
                                    <option v-for="type in roomTypes" :key="type">
                                        {{ type }}
                                    </option>
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
                                colors.find((c) => c.value === selectedColor)?.label ?? ""
                            }}</span>
                        </div>
                    </fieldset>
                </div>

                <!-- 绑定设备 -->
                <div class="section-card">
                    <div class="section-head">
                        <SvgIcon name="device-management" size="sm" />
                        <span>绑定设备</span>
                        <sup class="device-badge">{{ deviceCount }}</sup>
                    </div>
                    <div class="device-grid">
                        <button
                            v-for="(item, index) in deviceOptions"
                            :key="item.name"
                            type="button"
                            :class="{
                                active: roomDevices.includes(item.name),
                                dragging: roomDevices.includes(item.name) && dragIndex === roomDevices.indexOf(item.name),
                            }"
                            :draggable="roomDevices.includes(item.name)"
                            @click="toggleValue(roomDevices, item.name)"
                            @dragstart="
                                roomDevices.includes(item.name) &&
                                    handleDragStart(roomDevices.indexOf(item.name), $event)
                            "
                            @dragover="
                                roomDevices.includes(item.name) &&
                                    handleDragOver(roomDevices.indexOf(item.name), $event)
                            "
                            @drop="
                                roomDevices.includes(item.name) &&
                                    handleDrop(roomDevices.indexOf(item.name), $event)
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
                </div>
            </div>

            <!-- ===== 右侧预览（固定，不滑动） ===== -->
            <aside class="room-preview">
                <div class="preview-header">
                    <SvgIcon name="scene" size="sm" />
                    <span>房间预览</span>
                </div>

                <!-- 预览卡片 — 与 RoomControl 页面一致的房间卡片样式 -->
                <article class="preview-room-card">
                    <header>
                        <span class="preview-room-avatar">{{ (roomName || roomType || '新').slice(0, 1) }}</span>
                        <div class="preview-room-title">
                            <h2>{{ roomName || roomType || "新房间" }}</h2>
                            <p class="preview-room-status">
                                <small>良好</small>
                                <b></b>
                                {{ roomType }} · {{ floor }}
                            </p>
                        </div>
                    </header>
                    <div class="preview-room-metrics">
                        <span>
                            <SvgIcon name="temperature" size="sm" />
                            --°C
                        </span>
                        <span>
                            <SvgIcon name="humidity" size="sm" />
                            --%
                        </span>
                        <span class="quality">
                            <SvgIcon name="air-quality" size="sm" />
                            --
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
                                    :name="deviceOptions.find((d) => d.name === item)?.icon ?? 'room'"
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
                    <span>调整左侧选项实时预览效果</span>
                </div>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* =============================================
   布局
   ============================================= */
.room-layout {
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 24px;
    align-items: start;
}

.form-stack {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.form-stack-scroll {
    overflow-y: auto;
    max-height: 460px;
    padding-right: 4px;
}

.form-stack-scroll::-webkit-scrollbar {
    width: 4px;
}

.form-stack-scroll::-webkit-scrollbar-track {
    background: transparent;
}

.form-stack-scroll::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border-strong);
}

/* =============================================
   分区卡片
   ============================================= */
.section-card {
    border: 1.5px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
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

/* =============================================
   表单字段
   ============================================= */
.field {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.field + .field {
    margin-top: 0;
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
    border: 1.5px solid var(--color-border-default);
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
    background: var(--color-panel-background);
}

.input-wrap.is-error input {
    border-color: var(--color-danger, #f05252);
    box-shadow: 0 0 0 3px #f0525214;
}

.input-wrap.is-error .input-icon {
    color: var(--color-danger, #f05252);
}

.field-error {
    font-size: 11px;
    color: var(--color-danger, #f05252);
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

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 12px;
}

/* =============================================
   选择器通用
   ============================================= */
.picker-group {
    border: 0;
    padding: 0;
    margin: 0;
}

.picker-group + .picker-group {
    margin-top: 16px;
}

.picker-group legend {
    width: 100%;
    margin-bottom: 10px;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    letter-spacing: 0.02em;
}

/* =============================================
   图标选择器
   ============================================= */
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
    border: 1.5px solid var(--color-border-default);
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

/* =============================================
   颜色选择器
   ============================================= */
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
    border: 1.5px solid var(--color-border-default);
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
    background: linear-gradient(
        135deg,
        var(--color-primary-50) 0%,
        var(--color-panel-background) 100%
    );
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
    background: var(--color-panel-background);
    border: 1px solid var(--color-border-default);
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
   预览面板
   ============================================= */
.room-preview {
    border: 1.5px solid var(--color-border-default);
    border-radius: 14px;
    background: linear-gradient(
        180deg,
        var(--color-panel-background) 0%,
        var(--color-surface-subtle) 100%
    );
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    align-self: stretch;
    justify-content: space-between;
}

.preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text);
    text-align: left;
}

/* 预览房间卡片 — 与 RoomControl 页面 RoomCard 一致 */
.preview-room-card {
    position: relative;
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-panel-background);
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
    background: var(--color-panel-background);
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
    justify-content: center;
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
@media (max-width: 800px) {
    .room-layout {
        grid-template-columns: 1fr;
    }

    .room-preview {
        position: static;
    }

    .device-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .device-grid {
        grid-template-columns: 1fr;
    }
}
</style>