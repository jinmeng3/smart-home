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
const form = reactive<DeviceCreatePayload>({
  name: "",
  room: "",
  type: "light",
  brand: "",
  connection: "Home Assistant",
  firmware: "1.0.0",
  icon: "light",
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
        width="720px"
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
                    <section class="device-editor-hero">
                        <div class="device-hero-preview">
                            <img v-if="imagePreviewUrl" :src="imagePreviewUrl" alt="" />
                            <SvgIcon v-else :name="selectedTypeIcon" />
                        </div>
                        <div class="device-hero-body">
                            <div class="device-hero-actions">
                                <label class="device-upload-button">
                                    <SvgIcon name="plus" />
                                    上传
                                    <input
                                        accept="image/png,image/jpeg,image/webp"
                                        type="file"
                                        @change="handleImageChange"
                                    />
                                </label>
                                <button
                                    class="device-clear-button"
                                    :disabled="!imagePreviewUrl"
                                    type="button"
                                    @click="clearImage"
                                >
                                    移除
                                </button>
                            </div>
                        </div>
                    </section>

                    <section class="device-form-section">
                        <header>
                            <h3>设备信息</h3>
                            <span>名称、位置与接入信息</span>
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
                    </section>
                </div>

                <div class="device-form-right">
                    <section class="device-form-section">
                        <header>
                            <h3>类型与图标</h3>
                            <span>选择设备类型并自定义图标</span>
                        </header>
                        <div class="device-type-picker">
                            <span class="device-type-label">设备类型 <em>*</em></span>
                            <div class="device-type-grid">
                                <button
                                    v-for="item in deviceTypeOptions.filter(
                                        (item) => item.value,
                                    )"
                                    :key="item.value"
                                    :class="{ active: form.type === item.value }"
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
                                    @input="form.type = customTypeInput || '__custom__'"
                                />
                            </div>
                        </div>
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
/* ── 弹窗头部 ── */

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

/* ── 表单容器 ── */

.device-form {
    display: grid;
    gap: 16px;
    padding: 4px 0;
}

/* ── 顶部预览区 ── */

.device-editor-hero {
    display: grid;
    gap: 12px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-card-bg) 40%,
        var(--color-primary-50)
    );
    padding: 16px;
}

.device-hero-preview {
    display: grid;
    width: 100%;
    height: 160px;
    place-items: center;
    overflow: hidden;
    border: 2px dashed var(--color-border-strong);
    border-radius: 14px;
    background: var(--color-card-bg);
    color: var(--color-primary-500);
}

.device-hero-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.device-hero-preview svg {
    width: 64px;
    height: 64px;
    opacity: 0.7;
}

.device-hero-body {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-width: 0;
}

.device-hero-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.device-upload-actions small {
    display: none;
}

/* ── 表单区块 ── */

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

/* ── 双列布局 ── */

.device-form-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    align-items: stretch;
}

.device-form-left {
    display: grid;
    gap: 16px;
    align-content: start;
}

.device-form-right {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.device-form-right .device-form-section {
    flex: 1;
}

/* ── 设备类型选择器 ── */

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
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
}

.device-type-grid button {
    display: grid;
    grid-template-columns: 28px 1fr;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    padding: 8px 10px;
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
    width: 28px;
    height: 28px;
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

/* ── 自定义类型输入 ── */

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

/* ── 图标选择器 ── */

.device-icon-picker {
    display: grid;
    gap: 10px;
}

.device-icon-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 4px;
    max-height: 196px;
    overflow-y: auto;
    padding: 2px;
}

.device-icon-grid::-webkit-scrollbar {
    width: 3px;
}

.device-icon-grid::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border);
}

.device-icon-grid button {
    display: grid;
    width: 100%;
    aspect-ratio: 1;
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
    transform: scale(1.08);
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

/* ── 表单字段 ── */

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

/* ── 按钮共用 ── */

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
    animation: device-dialog-spin 900ms linear infinite;
}

/* ── 弹窗底部 ── */

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

@keyframes device-dialog-spin {
    to {
        transform: rotate(360deg);
    }
}

/* ── 响应式 ── */

@media (max-width: 640px) {
    .device-form-columns {
        grid-template-columns: 1fr;
    }

    .device-form-grid {
        grid-template-columns: 1fr;
    }

    .device-editor-hero {
        flex-wrap: wrap;
    }

    .device-hero-body {
        flex-wrap: wrap;
    }

    .device-icon-grid {
        max-height: 120px;
    }

    .device-dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .device-dialog-footer div {
        justify-content: flex-end;
    }

    .device-form-section header {
        display: grid;
    }

    .device-form-section header span {
        text-align: left;
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
