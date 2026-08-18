<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import {
  deviceIconOptions,
  devicePlatformOptions,
  getDeviceTypeIcon,
  getDeviceTypeLabel,
  deviceTypeIconMap,
  deviceTypeOptions,
  deviceTypeLabelMap,
} from "./deviceMeta";
import { uploadDeviceImage } from "../../api/device";
import type {
  Device,
  DeviceCreatePayload,
  DeviceType,
} from "../../types/device";

const PRESET_TYPE_VALUES = new Set([
  "light",
  "air_conditioner",
  "lock",
  "camera",
  "sensor",
  "socket",
  "curtain",
]);

const props = defineProps<{
  modelValue: boolean;
  device: Device | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  submit: [payload: DeviceCreatePayload];
}>();

const platforms = devicePlatformOptions;

const deviceColors = [
  { value: "#6b7280", label: "灰色" },
  { value: "#3b82f6", label: "蓝色" },
  { value: "#22c55e", label: "绿色" },
  { value: "#f59e0b", label: "橙色" },
  { value: "#ef4444", label: "红色" },
  { value: "#8b5cf6", label: "紫色" },
  { value: "#14b8a6", label: "青色" },
  { value: "#ec4899", label: "粉色" },
];
const form = reactive<DeviceCreatePayload>({
  name: "",
  room: "",
  type: "light",
  brand: "",
  connection: "Home Assistant",
  firmware: "1.0.0",
  icon: "light",
  color: "#6b7280",
  imageUrl: "",
});
const imagePreviewUrl = ref("");
const imageFileName = ref("");
const pendingImageFile = ref<File | null>(null);
const customTypeInput = ref("");

const isCustomType = computed(() => !PRESET_TYPE_VALUES.has(form.type));

const selectedTypeMeta = computed(() =>
  deviceTypeOptions.find((item) => item.value === form.type),
);
const renderedTypeOptions = computed(() =>
  deviceTypeOptions.filter((item) => item.value),
);
const selectedTypeIcon = computed(() => form.icon || getDeviceTypeIcon(form.type));
const canSubmit = computed(
  () =>
    Boolean(form.name.trim()) &&
    Boolean(form.room.trim()) &&
    Boolean(form.brand.trim()) &&
    !props.loading,
);

const releasePreviewUrl = () => {
    if (imagePreviewUrl.value.startsWith("blob:")) {
        URL.revokeObjectURL(imagePreviewUrl.value);
    }
};

const resetForm = () => {
    releasePreviewUrl();
    pendingImageFile.value = null;
    form.name = props.device?.name ?? "";
    form.room = props.device?.room ?? "";
    form.type = props.device?.type ?? "light";
    customTypeInput.value = props.device?.type ?? "";
    form.brand = props.device?.brand ?? "";
    form.connection = props.device?.connection ?? "Home Assistant";
    form.firmware = props.device?.firmware ?? "1.0.0";
    form.icon = props.device?.icon ?? getDeviceTypeIcon(props.device?.type ?? "light");
    form.color = props.device?.color ?? "#6b7280";
    form.imageUrl = props.device?.image ?? "";
    imagePreviewUrl.value = props.device?.image ?? "";
    imageFileName.value = props.device?.image ? "已上传设备图片" : "";
};

const handleImageChange = (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
        return;
    }

    // 文件大小校验：设备图片限制 10MB
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        ElMessage.warning("设备图片文件大小不能超过 10MB");
        input.value = "";
        return;
    }

    // 文件类型校验
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"];
    if (!allowedTypes.includes(file.type)) {
        ElMessage.warning("仅支持 JPEG、PNG、WebP、GIF 或 SVG 格式的设备图片");
        input.value = "";
        return;
    }

    releasePreviewUrl();
    pendingImageFile.value = file;
    imagePreviewUrl.value = URL.createObjectURL(file);
    imageFileName.value = file.name;
};

const clearImage = () => {
    releasePreviewUrl();
    pendingImageFile.value = null;
    imagePreviewUrl.value = "";
    imageFileName.value = "";
    form.imageUrl = "";
};

const close = () => {
    if (props.loading) {
        return;
    }

    pendingImageFile.value = null;
    emit("update:modelValue", false);
};

const submit = async () => {
    if (!form.name.trim() || !form.room.trim() || !form.brand.trim()) {
        return;
    }

    if (pendingImageFile.value) {
        try {
            form.imageUrl = await uploadDeviceImage(pendingImageFile.value);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "图片上传失败",
            );
            return;
        }
    }

    emit("submit", {
        ...form,
        name: form.name.trim(),
        room: form.room.trim(),
        brand: form.brand.trim(),
        firmware: form.firmware?.trim() || "1.0.0",
        icon: form.icon?.trim() || getDeviceTypeIcon(form.type),
        color: form.color?.trim() || "#6b7280",
        imageUrl: form.imageUrl?.trim() || undefined,
    });
};

watch(
    () => [props.modelValue, props.device] as const,
    ([open]) => {
        if (open) resetForm();
    },
    { immediate: true },
);

// 当用户选择预设类型时，自动更新图标为对应类型的默认图标
watch(
    () => form.type,
    (newType) => {
        if (PRESET_TYPE_VALUES.has(newType) && !props.device) {
            form.icon = getDeviceTypeIcon(newType);
        }
    },
);

onBeforeUnmount(releasePreviewUrl);
</script>

<template>
    <BaseSmartModal
        :confirm-text="device ? '保存修改' : '添加设备'"
        :description="
            device ? '更新设备属性和接入信息' : '填写设备基础信息并接入家庭'
        "
        :loading="loading"
        :model-value="modelValue"
        :title="device ? '编辑设备' : '添加设备'"
        width="840px"
        @confirm="submit"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <header class="device-dialog-header">
                <span class="device-dialog-icon" aria-hidden="true">
                    <SvgIcon :name="selectedTypeIcon" />
                </span>
                <div>
                    <h2>{{ device ? "编辑设备" : "添加设备" }}</h2>
                    <p>
                        {{
                            device
                                ? "更新设备属性和接入信息"
                                : "填写设备信息并上传设备图片"
                        }}
                    </p>
                </div>
                <button
                    class="device-dialog-close"
                    :disabled="loading"
                    type="button"
                    aria-label="关闭"
                    @click="close"
                >
                    <SvgIcon name="close" />
                </button>
            </header>
        </template>

        <form class="device-form" @submit.prevent="submit">
            <div class="device-form-columns">
                <div class="device-form-left">
                    <section class="device-editor-preview">
                        <div
                            class="device-preview-card"
                            :style="{ '--preview-color': form.color || '#6b7280' }"
                        >
                            <div class="device-preview-header">
                                <span class="device-preview-status is-online">
                                    <i></i>在线
                                </span>
                            </div>
                            <div class="device-preview-icon">
                                <img
                                    v-if="imagePreviewUrl"
                                    :src="imagePreviewUrl"
                                    alt=""
                                />
                                <SvgIcon v-else :name="selectedTypeIcon" size="lg" />
                            </div>
                            <div class="device-preview-name">
                                {{ form.name || "设备名称" }}
                            </div>
                            <div class="device-preview-room">
                                <SvgIcon name="room" size="sm" />
                                {{ form.room || "所在房间" }}
                            </div>
                            <div class="device-preview-type">
                                {{ getDeviceTypeLabel(form.type) || form.type }}
                            </div>
                            <div class="device-preview-actions">
                                <label class="device-upload-button">
                                    <SvgIcon name="plus" size="sm" />
                                    上传图片
                                    <input
                                        accept="image/png,image/jpeg,image/webp"
                                        type="file"
                                        @change="handleImageChange"
                                    />
                                </label>
                                <button
                                    v-if="imagePreviewUrl"
                                    class="device-clear-button"
                                    type="button"
                                    @click="clearImage"
                                >
                                    移除
                                </button>
                            </div>
                        </div>
                    </section>

                    <section class="device-appearance-section">
                        <header>
                            <div>
                                <h3>外观设置</h3>
                                <span>选择设备图标与主题颜色</span>
                            </div>
                            <span
                                class="appearance-swatch"
                                :style="{ '--swatch-color': form.color || '#6b7280' }"
                                aria-hidden="true"
                            ></span>
                        </header>

                        <div class="device-icon-picker">
                            <span class="device-type-label">设备图标</span>
                            <div class="device-icon-grid">
                                <button
                                    v-for="item in deviceIconOptions"
                                    :key="item.value"
                                    :class="{ active: form.icon === item.value }"
                                    type="button"
                                    :title="item.label"
                                    @click="form.icon = item.value"
                                >
                                    <SvgIcon :name="item.value" />
                                </button>
                            </div>
                        </div>

                        <div class="device-icon-picker">
                            <span class="device-type-label">设备颜色</span>
                            <div class="icon-grid">
                                <button
                                    v-for="c in deviceColors"
                                    :key="c.value"
                                    type="button"
                                    :class="{ active: form.color === c.value }"
                                    class="color-dot"
                                    :style="{ '--dot-color': c.value }"
                                    :title="c.label"
                                    @click="form.color = c.value"
                                >
                                    <SvgIcon v-if="form.color === c.value" name="check" size="sm" />
                                </button>
                            </div>
                        </div>
                    </section>
                </div>

                <div class="device-form-right">
                    <section class="device-form-section">
                        <header>
                            <h3>基础信息</h3>
                            <span>名称、位置与品牌</span>
                        </header>
                        <div class="device-form-grid">
                            <label>
                                <span>设备名称 <em>*</em></span>
                                <input
                                    v-model="form.name"
                                    maxlength="80"
                                    placeholder="例如：客厅主灯"
                                />
                            </label>
                            <label>
                                <span>所在房间 <em>*</em></span>
                                <input
                                    v-model="form.room"
                                    maxlength="80"
                                    placeholder="例如：客厅"
                                />
                            </label>
                            <label>
                                <span>品牌 <em>*</em></span>
                                <input
                                    v-model="form.brand"
                                    maxlength="64"
                                    placeholder="例如：Aqara"
                                />
                            </label>
                        </div>
                    </section>

                    <section class="device-form-section">
                        <header>
                            <h3>接入配置</h3>
                            <span>类型、平台与外观</span>
                        </header>
                        <div class="device-form-grid">
                            <label>
                                <span>接入平台</span>
                                <select v-model="form.connection">
                                    <option
                                        v-for="platform in platforms"
                                        :key="platform"
                                        :value="platform"
                                    >
                                        {{ platform }}
                                    </option>
                                </select>
                            </label>
                            <label>
                                <span>固件版本</span>
                                <input
                                    v-model="form.firmware"
                                    maxlength="64"
                                    placeholder="1.0.0"
                                />
                            </label>
                        </div>

                        <div class="device-type-picker">
                            <span class="device-type-label"
                                >设备类型 <em>*</em></span
                            >
                            <div class="device-type-grid">
                                <button
                                    v-for="item in renderedTypeOptions"
                                    :key="item.value"
                                    :class="{
                                        active: form.type === item.value,
                                    }"
                                    type="button"
                                    @click="
                                        form.type = item.value;
                                        customTypeInput = '';
                                    "
                                >
                                    <i>
                                        <SvgIcon
                                            :name="getDeviceTypeIcon(item.value)"
                                        />
                                    </i>
                                    <b>{{ item.label }}</b>
                                </button>
                                <button
                                    :class="{ active: isCustomType }"
                                    type="button"
                                    @click="
                                        customTypeInput = isCustomType
                                            ? customTypeInput
                                            : form.type;
                                        form.type = '__custom__';
                                    "
                                >
                                    <i>
                                        <SvgIcon name="edit" />
                                    </i>
                                    <b>自定义</b>
                                </button>
                            </div>
                            <div
                                v-if="isCustomType"
                                class="device-custom-type-input"
                            >
                                <input
                                    v-model="customTypeInput"
                                    placeholder="输入自定义类型名称"
                                    @input="
                                        form.type =
                                            customTypeInput || '__custom__'
                                    "
                                />
                            </div>
                        </div>

                    </section>
                </div>
            </div>
        </form>

        <template #footer>
            <footer class="device-dialog-footer">
                <span>{{
                    form.imageUrl
                        ? "图片将在保存设备时关联"
                        : "未上传图片时使用设备类型 SVG 图标"
                }}</span>
                <div>
                    <button
                        class="device-cancel-button"
                        :disabled="loading"
                        type="button"
                        @click="close"
                    >
                        取消
                    </button>
                    <button
                        class="device-submit-button"
                        :disabled="!canSubmit"
                        type="button"
                        @click="submit"
                    >
                        <SvgIcon :name="loading ? 'refresh' : 'check-circle'" />
                        {{
                            loading
                                ? "保存中"
                                : device
                                  ? "保存修改"
                                  : "添加设备"
                        }}
                    </button>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
/* === 弹窗头部 === */

.device-dialog-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg) 50%,
        var(--color-primary-50)
    );
}

.device-dialog-icon {
    display: grid;
    width: 50px;
    height: 50px;
    flex: 0 0 50px;
    place-items: center;
    border-radius: 14px;
    color: var(--color-primary-700);
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    box-shadow: 0 2px 10px var(--color-focus-ring);
}

.device-dialog-icon svg {
    width: 24px;
    height: 24px;
}

.device-dialog-header h2,
.device-dialog-header p {
    margin: 0;
}

.device-dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 22px;
    font-weight: 900;
    line-height: 1.3;
}

.device-dialog-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 600;
}

.device-dialog-close {
    display: grid;
    width: 38px;
    height: 38px;
    margin-left: auto;
    place-items: center;
    border-radius: 999px;
    color: var(--color-text-tertiary);
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.device-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
    transform: translateY(-1px);
}

/* === 表单容器 === */

.device-form {
    display: grid;
    gap: 16px;
    padding: 2px 0;
}

/* === 顶部预览区 === */

/* === 左栏预览卡片 === */
.device-editor-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0;
}

.device-preview-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    width: 100%;
    min-height: 210px;
    justify-content: center;
    padding: 14px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: color-mix(
        in srgb,
        var(--preview-color, var(--color-primary-500)) 8%,
        var(--color-panel-background)
    );
    box-shadow: 0 10px 28px color-mix(in srgb, var(--preview-color, var(--color-primary-500)) 10%, transparent);
    transition: background-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
}

.device-preview-header {
    width: 100%;
    display: flex;
    justify-content: flex-end;
    margin-bottom: auto;
}

.device-preview-status {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 800;
    color: var(--color-success);
    background: var(--color-success-soft);
}

.device-preview-status i {
    width: 5px;
    height: 5px;
    border-radius: 999px;
    background: currentColor;
}

.device-preview-icon {
    display: grid;
    width: 56px;
    height: 56px;
    place-items: center;
    border-radius: 14px;
    background: color-mix(
        in srgb,
        var(--preview-color, var(--color-primary-500)) 14%,
        transparent
    );
    color: var(--preview-color, var(--color-primary-600));
}

.device-preview-icon img {
    width: 42px;
    height: 42px;
    object-fit: cover;
    border-radius: 8px;
}

.device-preview-icon svg {
    width: 28px;
    height: 28px;
}

.device-preview-name {
    font-size: 14px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    white-space: nowrap;
    margin-top: 2px;
}

.device-preview-room {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.device-preview-type {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.device-preview-actions {
    display: flex;
    gap: 6px;
    margin-top: 6px;
}

.device-appearance-section {
    display: grid;
    gap: 16px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 15px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.device-appearance-section > header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border-subtle);
}

.device-appearance-section h3,
.device-appearance-section header span {
    margin: 0;
}

.device-appearance-section h3 {
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

.device-appearance-section header div > span {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.appearance-swatch {
    width: 22px;
    height: 22px;
    flex: 0 0 22px;
    border: 3px solid var(--color-card-bg);
    border-radius: 999px;
    background: var(--swatch-color);
    box-shadow: 0 0 0 1px var(--color-border), 0 3px 8px color-mix(in srgb, var(--swatch-color) 35%, transparent);
    transition: background-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
}

.device-upload-actions small {
    display: none;
}

/* === 表单区块 === */

.device-form-section {
    display: grid;
    gap: 16px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.device-form-section header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding-bottom: 14px;
}

.device-form-section h3 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
}

.device-form-section header span {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    text-align: right;
}

/* === 双列布局 === */

.device-form-columns {
    display: grid;
    grid-template-columns: 250px minmax(0, 1fr);
    gap: 18px;
    align-items: stretch;
}

.device-form-left {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.device-form-right {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.device-form-left,
.device-form-right {
    min-width: 0;
}

.device-form-right .device-form-section {
    flex: 1;
}

/* === 设备类型选择器 === */

.device-type-picker {
    display: grid;
    gap: 10px;
}

.device-type-label {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.device-type-label em {
    color: var(--color-danger);
    font-style: normal;
}

.device-type-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 7px;
}

.device-type-grid button {
    display: grid;
    grid-template-columns: 24px minmax(0, 1fr);
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    min-height: 42px;
    padding: 6px 8px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    transition: all 180ms var(--motion-ease);
    cursor: pointer;
    text-align: left;
}

.device-type-grid button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px var(--color-focus-ring);
}

.device-type-grid button.active {
    border-color: var(--color-primary-600);
    background: linear-gradient(
        135deg,
        var(--color-primary-50),
        var(--color-primary-100)
    );
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.device-type-grid i {
    display: grid;
    width: 24px;
    height: 24px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-card-bg);
    color: inherit;
    font-style: normal;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    flex-shrink: 0;
}

.device-type-grid i svg {
    width: 16px;
    height: 16px;
}

.device-type-grid b {
    font-weight: 800;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* === 自定义类型输入 === */

.device-custom-type-input {
    margin-top: -4px;
}

.device-custom-type-input input {
    width: 100%;
    height: 42px;
    box-sizing: border-box;
    border: 2px solid var(--color-primary-300);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 14px;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 700;
    outline: none;
    transition: border-color 160ms, box-shadow 160ms;
}

.device-custom-type-input input:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.device-custom-type-input input::placeholder {
    color: var(--color-text-tertiary);
    font-weight: 600;
}

/* === 图标选择器 === */

.device-icon-picker {
    display: grid;
    gap: 10px;
}

.device-icon-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    grid-auto-rows: 40px;
    gap: 6px;
    /* 3 行图标 + 2 个行间距；与右侧配置卡高度协调并保持整行可见。 */
    height: 132px;
    max-height: 132px;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 0 4px 0 0;
    scrollbar-gutter: stable;
    overscroll-behavior: contain;
}

.device-icon-grid::-webkit-scrollbar {
    width: 4px;
}

.device-icon-grid::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: var(--color-border);
}

.device-icon-grid::-webkit-scrollbar-track {
    background: transparent;
}

.device-icon-grid button {
    display: grid;
    width: 100%;
    height: 40px;
    min-height: 40px;
    place-items: center;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-surface-subtle);
    color: var(--color-text-secondary);
    transition: all 140ms var(--motion-ease);
    cursor: pointer;
}

.device-icon-grid button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transform: translateY(-1px);
}

.device-icon-grid button.active {
    border-color: var(--color-primary-600);
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.device-icon-grid svg {
    width: 16px;
    height: 16px;
}

/* === 颜色选择器 === */

.icon-grid {
    display: grid;
    width: 100%;
    grid-template-columns: repeat(8, minmax(20px, 1fr));
    gap: 3px;
    padding: 3px 0 2px;
}

.color-dot {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    max-width: 100%;
    justify-self: center;
    border: 2px solid transparent;
    border-radius: 50%;
    background: var(--dot-color);
    color: #fff;
    cursor: pointer;
    transition: all 160ms var(--motion-ease);
    padding: 0;
}

.color-dot:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.color-dot.active {
    border-color: var(--color-text-primary);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
    transform: scale(1.1);
}

/* === 表单字段 === */

.device-form-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.device-form-grid label {
    display: grid;
    gap: 7px;
}

.device-form-grid span {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.device-form-grid em {
    color: var(--color-danger);
    font-style: normal;
}

.device-form-grid input,
.device-form-grid select {
    width: 100%;
    height: 42px;
    box-sizing: border-box;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-panel-background);
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 700;
    padding: 0 14px;
    outline: none;
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.device-form-grid input::placeholder {
    color: var(--color-text-tertiary);
    font-weight: 600;
}

.device-form-grid select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 14px;
    padding-right: 34px;
    cursor: pointer;
}

.device-form-grid select option {
    background: var(--color-panel-background);
    color: var(--color-text-primary);
}

.device-form-grid input:focus,
.device-form-grid select:focus {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

/* === 按钮共用 === */

.device-upload-button,
.device-clear-button,
.device-cancel-button,
.device-submit-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    height: 32px;
    border-radius: 8px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
    cursor: pointer;
}

.device-upload-button {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.device-upload-button:hover {
    background: var(--color-primary-700);
    border-color: var(--color-primary-700);
}

.device-upload-button input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
}

.device-clear-button,
.device-cancel-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.device-clear-button:hover,
.device-cancel-button:hover {
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
}

.device-submit-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 4px 12px var(--color-focus-ring);
}

.device-submit-button:hover:not(:disabled) {
    background: var(--color-primary-700);
    border-color: var(--color-primary-700);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.device-submit-button:disabled svg {
    animation: spin 900ms linear infinite;
}

/* === 弹窗底部 === */

.device-dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 16px 24px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}

.device-dialog-footer span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.device-dialog-footer div {
    display: flex;
    align-items: center;
    gap: 10px;
}

button:disabled {
    cursor: default;
    opacity: 0.55;
}

/* === 响应式 === */

@media (max-width: 640px) {
    .device-form-columns {
        grid-template-columns: 1fr;
    }

    .device-preview-card {
        min-height: 190px;
    }

    .device-type-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .device-form-grid {
        grid-template-columns: 1fr;
    }

    .device-dialog-footer {
        flex-direction: column;
    }

    .device-dialog-footer div {
        width: 100%;
    }

    .device-form-section header {
        flex-wrap: wrap;
    }

    .device-form-section header span {
        display: none;
    }

    .device-icon-grid {
        grid-template-columns: repeat(6, 1fr);
    }
}

@media (prefers-reduced-motion: reduce) {
    button,
    .device-upload-button,
    .device-form-grid input,
    .device-form-grid select {
        transition-duration: 1ms;
    }

    button:not(:disabled):hover,
    .device-upload-button:hover {
        transform: none;
    }
}
</style>
